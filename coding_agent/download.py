"""GGUF 모델 다운로드와 Ollama 등록 CLI를 제공한다."""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from coding_agent.config import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_GGUF_QUANT,
    DEFAULT_GGUF_REPO,
    DEFAULT_MODEL,
    MODELS_DIR,
)
from coding_agent.ollama_runtime import (
    build_ollama_env,
    ensure_ollama_binary,
    ensure_ollama_server,
)


def _safe_repo_name(repo_id: str) -> str:
    """저장용 디렉터리 이름을 만든다.

    Args:
        repo_id: Hugging Face 저장소 ID.

    Returns:
        파일시스템 친화적인 문자열.
    """
    return repo_id.replace("/", "--")


def _safe_model_name(name: str) -> str:
    """Ollama 모델 이름을 안전한 소문자 문자열로 변환한다.

    Args:
        name: 원본 모델 이름.

    Returns:
        Ollama 모델 이름으로 쓰기 쉬운 문자열.
    """
    normalized = re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-").lower()
    return normalized or DEFAULT_MODEL


def _select_gguf_file(files: list[str], preferred_quant: str = DEFAULT_GGUF_QUANT) -> str:
    """GGUF 파일 목록에서 기본 다운로드 대상을 고른다.

    Args:
        files: 저장소 파일 목록.
        preferred_quant: 선호 양자화 문자열.

    Returns:
        선택된 GGUF 파일 경로.
    """
    gguf_files = [name for name in files if name.lower().endswith(".gguf")]
    if not gguf_files:
        raise ValueError("GGUF 파일을 찾지 못했습니다.")

    preferred_quant = preferred_quant.lower()
    exact = [name for name in gguf_files if preferred_quant in Path(name).name.lower()]
    if exact:
        return sorted(exact)[0]
    return sorted(gguf_files)[0]


def _gguf_dir(repo_id: str) -> Path:
    """GGUF 저장 디렉터리를 반환한다.

    Args:
        repo_id: Hugging Face 저장소 ID.

    Returns:
        GGUF 저장 디렉터리.
    """
    path = MODELS_DIR / "gguf" / _safe_repo_name(repo_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ollama_dir(model_name: str) -> Path:
    """Ollama Modelfile 저장 디렉터리를 반환한다.

    Args:
        model_name: 로컬 Ollama 모델 이름.

    Returns:
        Ollama 모델 디렉터리.
    """
    path = MODELS_DIR / "ollama" / _safe_model_name(model_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_modelfile(model_name: str, gguf_path: Path, num_ctx: int = 8192) -> Path:
    """GGUF 파일을 참조하는 Ollama Modelfile을 만든다.

    Args:
        model_name: 로컬 Ollama 모델 이름.
        gguf_path: 다운로드된 GGUF 파일 경로.
        num_ctx: 기본 컨텍스트 길이.

    Returns:
        생성된 Modelfile 경로.
    """
    model_dir = _ollama_dir(model_name)
    modelfile = model_dir / "Modelfile"
    modelfile.write_text(
        "\n".join(
            [
                f"FROM {gguf_path.resolve()}",
                f"PARAMETER num_ctx {num_ctx}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return modelfile


def _try_create_ollama_model(model_name: str, modelfile: Path) -> tuple[bool, str]:
    """가능하면 Ollama 로컬 모델을 생성한다.

    Args:
        model_name: 생성할 로컬 모델 이름.
        modelfile: 사용할 Modelfile 경로.

    Returns:
        생성 성공 여부와 메시지.
    """
    try:
        binary = ensure_ollama_binary(auto_install=True)
        ok, message = ensure_ollama_server(DEFAULT_HOST, DEFAULT_PORT)
        if not ok:
            return False, message
        subprocess.run(
            [str(binary), "create", model_name, "-f", str(modelfile)],
            check=True,
            env=build_ollama_env(),
        )
        return True, f"{message}\nollama create 완료: {model_name}"
    except subprocess.CalledProcessError as exc:
        return False, f"ollama create 실패: {exc}"
    except Exception as exc:
        return False, f"ollama create 실패: {exc}"


def main():
    """GGUF 다운로드 CLI를 실행한다."""
    from huggingface_hub import hf_hub_download, list_repo_files
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    parser = argparse.ArgumentParser(description="GGUF 모델 다운로드")
    parser.add_argument("repo_id", nargs="?", default=DEFAULT_GGUF_REPO)
    parser.add_argument("--quant", default=DEFAULT_GGUF_QUANT)
    parser.add_argument("--runtime-model", default=DEFAULT_MODEL)
    parser.add_argument("--skip-ollama-create", action="store_true")
    args = parser.parse_args()

    console.print(Panel.fit(
        f"[bold cyan]GGUF 모델 다운로드[/bold cyan]\n"
        f"[dim]저장소 : {args.repo_id}[/dim]\n"
        f"[dim]양자화 : {args.quant}[/dim]\n"
        f"[dim]런타임 모델 : {_safe_model_name(args.runtime_model)}[/dim]\n"
        f"[dim]경로 : {_gguf_dir(args.repo_id)}[/dim]",
        border_style="cyan",
    ))
    console.print("[yellow]처음 실행 시 수 GB를 다운로드합니다. 잠시 기다려주세요...[/yellow]\n")

    try:
        files = list_repo_files(args.repo_id)
        filename = _select_gguf_file(files, preferred_quant=args.quant)
        local_dir = _gguf_dir(args.repo_id)
        path = hf_hub_download(
            repo_id=args.repo_id,
            filename=filename,
            local_dir=str(local_dir),
        )
        gguf_path = Path(path)
        modelfile = _write_modelfile(args.runtime_model, gguf_path)

        console.print(f"\n[green]✅ 다운로드 완료[/green]")
        console.print(f"[dim]GGUF 파일: {gguf_path}[/dim]")
        console.print(f"[dim]Modelfile: {modelfile}[/dim]")

        if not args.skip_ollama_create:
            ok, message = _try_create_ollama_model(_safe_model_name(args.runtime_model), modelfile)
            style = "green" if ok else "yellow"
            console.print(f"[{style}]{message}[/{style}]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ 다운로드 중단됨[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ 다운로드 실패: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
