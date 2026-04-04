"""Ollama 런타임의 탐색과 프로젝트 로컬 설치를 담당한다."""

from __future__ import annotations

import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

from coding_agent.config import IS_WINDOWS, IS_WSL, MODELS_DIR, PLATFORM_NAME, PROJECT_ROOT

VENDOR_ROOT = PROJECT_ROOT / ".vendor" / "ollama"


def _platform_download_url() -> str:
    """현재 플랫폼용 Ollama 다운로드 URL을 반환한다.

    Returns:
        플랫폼별 공식 다운로드 URL.
    """
    if IS_WINDOWS:
        return "https://ollama.com/download/ollama-windows-amd64.zip"
    return "https://ollama.com/download/ollama-linux-amd64.tar.zst"


def _install_root() -> Path:
    """프로젝트 로컬 Ollama 설치 디렉터리를 반환한다.

    Returns:
        플랫폼별 설치 루트 경로.
    """
    path = VENDOR_ROOT / PLATFORM_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _download_path() -> Path:
    """플랫폼별 다운로드 파일 경로를 반환한다.

    Returns:
        아카이브 저장 경로.
    """
    suffix = ".zip" if IS_WINDOWS else ".tar.zst"
    return _install_root() / f"ollama{suffix}"


def _candidate_paths(root: Path | None = None) -> list[Path]:
    """가능한 Ollama 바이너리 후보 경로를 반환한다.

    Args:
        root: 탐색 기준 루트. 없으면 기본 설치 루트를 사용한다.

    Returns:
        후보 경로 목록.
    """
    base = root or _install_root()
    if IS_WINDOWS:
        return [
            base / "ollama.exe",
            base / "bin" / "ollama.exe",
        ]
    return [
        base / "usr" / "bin" / "ollama",
        base / "bin" / "ollama",
        base / "ollama",
    ]


def get_ollama_binary() -> Path | None:
    """사용 가능한 Ollama 바이너리 경로를 반환한다.

    Returns:
        실행 가능한 Ollama 경로. 없으면 `None`.
    """
    system = shutil.which("ollama")
    if system:
        return Path(system)

    for candidate in _candidate_paths():
        if candidate.exists():
            return candidate
    return None


def _prepare_env() -> dict[str, str]:
    """프로젝트 로컬 Ollama 실행 환경을 만든다.

    Returns:
        subprocess용 환경 변수 사전.
    """
    env = os.environ.copy()
    env.setdefault("OLLAMA_MODELS", str(MODELS_DIR / "ollama-store"))

    install_root = _install_root()
    if not IS_WINDOWS:
        lib_dirs = [
            install_root / "usr" / "lib" / "ollama",
            install_root / "lib" / "ollama",
        ]
        existing = [str(path) for path in lib_dirs if path.exists()]
        if existing:
            current = env.get("LD_LIBRARY_PATH", "")
            env["LD_LIBRARY_PATH"] = ":".join(existing + ([current] if current else []))
    return env


def install_project_local_ollama() -> Path:
    """프로젝트 로컬 Ollama 런타임을 설치한다.

    Returns:
        설치 후 사용할 Ollama 바이너리 경로.
    """
    binary = get_ollama_binary()
    if binary is not None:
        return binary

    root = _install_root()
    archive = _download_path()
    urllib.request.urlretrieve(_platform_download_url(), archive)

    if IS_WINDOWS:
        shutil.unpack_archive(str(archive), str(root))
    else:
        subprocess.run(
            ["tar", "--zstd", "-xf", str(archive), "-C", str(root)],
            check=True,
        )

    binary = get_ollama_binary()
    if binary is None:
        raise RuntimeError("Ollama 설치 후 바이너리를 찾지 못했습니다.")
    return binary


def ensure_ollama_binary(auto_install: bool = True) -> Path:
    """Ollama 바이너리를 보장한다.

    Args:
        auto_install: 없을 때 프로젝트 로컬 설치를 시도할지 여부.

    Returns:
        사용할 Ollama 바이너리 경로.
    """
    binary = get_ollama_binary()
    if binary is not None:
        return binary
    if not auto_install:
        raise RuntimeError("`ollama`를 찾지 못했습니다.")
    return install_project_local_ollama()


def build_ollama_env(host: str | None = None, port: int | None = None) -> dict[str, str]:
    """Ollama 실행용 환경 변수를 구성한다.

    Args:
        host: 바인드할 호스트.
        port: 바인드할 포트.

    Returns:
        subprocess용 환경 변수 사전.
    """
    env = _prepare_env()
    if host is not None and port is not None:
        env["OLLAMA_HOST"] = f"{host}:{port}"
    return env
