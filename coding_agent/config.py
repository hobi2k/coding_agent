"""플랫폼과 프로젝트 경로를 설정한다."""

import os
import platform
from pathlib import Path


def _project_root() -> Path:
    """프로젝트 루트를 계산한다.

    Returns:
        `pyproject.toml`이 있는 프로젝트 루트 경로.
    """
    return Path(__file__).resolve().parent.parent


def _is_wsl() -> bool:
    """WSL 환경인지 판별한다.

    Returns:
        현재 실행 환경이 WSL이면 `True`, 아니면 `False`.
    """
    if platform.system() != "Linux":
        return False
    try:
        release = Path("/proc/version").read_text().lower()
        return "microsoft" in release or "wsl" in release
    except Exception:
        return False


def _is_windows() -> bool:
    """Windows 환경인지 판별한다.

    Returns:
        현재 실행 환경이 Windows이면 `True`, 아니면 `False`.
    """
    return platform.system() == "Windows"


# ── 플랫폼 정보 ──────────────────────────────────────
IS_WINDOWS = _is_windows()
IS_WSL     = _is_wsl()
IS_LINUX   = platform.system() == "Linux" and not IS_WSL

PLATFORM_NAME = "windows" if IS_WINDOWS else ("wsl" if IS_WSL else "linux")

# ── 경로 설정 ─────────────────────────────────────────
PROJECT_ROOT = _project_root()
MODELS_DIR   = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# vllm은 HF_HOME 환경변수로 모델 캐시 위치를 제어함
# 프로젝트 폴더 안으로 고정
os.environ["HF_HOME"]            = str(MODELS_DIR)
os.environ["HUGGINGFACE_HUB_CACHE"] = str(MODELS_DIR / "hub")
os.environ["TRANSFORMERS_CACHE"] = str(MODELS_DIR / "hub")

# ── 기본 모델 설정 ────────────────────────────────────
DEFAULT_MODEL  = "bigatuna/Qwen3.5-9b-Sushi-Coder"
DEFAULT_HOST   = "0.0.0.0"
DEFAULT_PORT   = 8000
API_BASE       = f"http://localhost:{DEFAULT_PORT}"

# ── WSL ↔ Windows 경로 변환 유틸 ─────────────────────

def to_native_path(path: Path | str) -> str:
    """현재 플랫폼에 맞는 경로 문자열을 반환한다.

    Args:
        path: 변환할 경로.

    Returns:
        현재 플랫폼에서 쓰기 좋은 문자열 경로.
    """
    p = Path(path)
    if IS_WINDOWS:
        return str(p).replace("/", "\\")
    return str(p)


def wsl_to_windows_path(wsl_path: str) -> str:
    """WSL 경로를 Windows 경로로 변환한다.

    Args:
        wsl_path: `/mnt/c/...` 형태의 WSL 경로.

    Returns:
        Windows 형식 문자열 경로.
    """
    if wsl_path.startswith("/mnt/") and len(wsl_path) > 6:
        drive = wsl_path[5]          # /mnt/c → c
        rest  = wsl_path[6:].replace("/", "\\")
        return f"{drive.upper()}:{rest}"
    return wsl_path


def windows_to_wsl_path(win_path: str) -> str:
    """Windows 경로를 WSL 경로로 변환한다.

    Args:
        win_path: `C:\\...` 형태의 Windows 경로.

    Returns:
        `/mnt/c/...` 형태의 WSL 경로.
    """
    if len(win_path) >= 2 and win_path[1] == ":":
        drive = win_path[0].lower()
        rest  = win_path[2:].replace("\\", "/")
        return f"/mnt/{drive}{rest}"
    return win_path
