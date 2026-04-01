"""
HuggingFace 모델을 ./models/ 폴더에 다운로드.

사용법:
    uv run agent-dl                                      # 기본 모델
    uv run agent-dl Qwen/Qwen2.5-Coder-14B-Instruct     # 모델 지정
"""

import sys
from coding_agent.config import DEFAULT_MODEL, MODELS_DIR


def main():
    # config import 시 HF_HOME이 설정되므로 이후 huggingface_hub가 올바른 경로 사용
    from huggingface_hub import snapshot_download
    from rich.console import Console
    from rich.panel import Panel

    console = Console()
    model_id = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL

    console.print(Panel.fit(
        f"[bold cyan]모델 다운로드[/bold cyan]\n"
        f"[dim]모델 : {model_id}[/dim]\n"
        f"[dim]경로 : {MODELS_DIR / 'hub'}[/dim]",
        border_style="cyan",
    ))
    console.print("[yellow]처음 실행 시 수 GB를 다운로드합니다. 잠시 기다려주세요...[/yellow]\n")

    try:
        path = snapshot_download(
            repo_id=model_id,
            cache_dir=str(MODELS_DIR / "hub"),
            ignore_patterns=["*.msgpack", "*.h5", "flax_model*", "tf_model*"],
        )
        console.print(f"\n[green]✅ 다운로드 완료[/green]")
        console.print(f"[dim]저장 위치: {path}[/dim]")
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ 다운로드 중단됨[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ 다운로드 실패: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
