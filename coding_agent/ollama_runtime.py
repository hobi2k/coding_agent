"""Ollama 런타임의 탐색과 프로젝트 로컬 설치를 담당한다."""

from __future__ import annotations

import os
import shutil
import subprocess
import tarfile
import time
import urllib.request
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from coding_agent.config import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    IS_WINDOWS,
    MODELS_DIR,
    PLATFORM_NAME,
    PROJECT_ROOT,
)

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
        import zstandard

        with archive.open("rb") as compressed:
            dctx = zstandard.ZstdDecompressor()
            with dctx.stream_reader(compressed) as reader:
                with tarfile.open(fileobj=reader, mode="r|") as tar:
                    tar.extractall(path=root)

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


def ollama_base_url(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> str:
    """Ollama 서버의 기본 URL을 반환한다.

    Args:
        host: 서버 호스트.
        port: 서버 포트.

    Returns:
        `http://host:port` 형식 문자열.
    """
    return f"http://{host}:{port}"


def is_ollama_server_running(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> bool:
    """Ollama 서버 응답 여부를 확인한다.

    Args:
        host: 서버 호스트.
        port: 서버 포트.

    Returns:
        응답 가능하면 `True`.
    """
    try:
        with urlopen(f"{ollama_base_url(host, port)}/api/tags", timeout=2) as response:
            return response.status == 200
    except (URLError, TimeoutError, OSError):
        return False


def _server_log_path() -> Path:
    """프로젝트 로컬 Ollama 서버 로그 파일 경로를 반환한다.

    Returns:
        로그 파일 경로.
    """
    path = VENDOR_ROOT / "ollama-server.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def start_ollama_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> subprocess.Popen:
    """프로젝트 로컬 Ollama 서버를 백그라운드로 시작한다.

    Args:
        host: 서버 호스트.
        port: 서버 포트.

    Returns:
        시작된 프로세스 핸들.
    """
    binary = ensure_ollama_binary(auto_install=True)
    env = build_ollama_env(host, port)
    log_path = _server_log_path()
    log_file = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(
        [str(binary), "serve"],
        env=env,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def wait_for_ollama_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, timeout: float = 30.0) -> bool:
    """Ollama 서버가 준비될 때까지 기다린다.

    Args:
        host: 서버 호스트.
        port: 서버 포트.
        timeout: 최대 대기 시간(초).

    Returns:
        준비되면 `True`.
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        if is_ollama_server_running(host, port):
            return True
        time.sleep(0.5)
    return False


def ensure_ollama_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT) -> tuple[bool, str]:
    """Ollama 서버가 실행 중이도록 보장한다.

    Args:
        host: 서버 호스트.
        port: 서버 포트.

    Returns:
        성공 여부와 상태 메시지.
    """
    if is_ollama_server_running(host, port):
        return True, "ollama 서버 이미 실행 중"

    process = start_ollama_server(host, port)
    if wait_for_ollama_server(host, port, timeout=30.0):
        return True, f"ollama 서버 시작 완료 (pid={process.pid})"
    return False, f"ollama 서버 시작 실패 (pid={process.pid})"
