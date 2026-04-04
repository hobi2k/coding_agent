"""Ollama 서버 실행 CLI를 제공한다."""

import sys
import argparse
import subprocess
from pathlib import Path
from coding_agent.config import (
    DEFAULT_MODEL, DEFAULT_HOST, DEFAULT_PORT,
    MODELS_DIR, PLATFORM_NAME,
)
from coding_agent.ollama_runtime import build_ollama_env, ensure_ollama_binary

def build_ollama_command(binary_path: Path | str) -> list[str]:
    """Ollama 서버 실행 명령을 반환한다.

    Args:
        binary_path: 사용할 Ollama 바이너리 경로.

    Returns:
        subprocess에 넘길 명령어 목록.
    """
    return [str(binary_path), "serve"]


def main():
    """Ollama OpenAI 호환 서버를 실행한다."""
    parser = argparse.ArgumentParser(description="ollama 서버 실행")
    parser.add_argument("--model",    default=DEFAULT_MODEL)
    parser.add_argument("--host",     default=DEFAULT_HOST)
    parser.add_argument("--port",     default=DEFAULT_PORT, type=int)
    args = parser.parse_args()

    print(f"플랫폼   : {PLATFORM_NAME}")
    print(f"모델     : {args.model}")
    print(f"주소     : http://{args.host}:{args.port}")
    print(f"모델폴더 : {MODELS_DIR}")
    print()

    binary = ensure_ollama_binary(auto_install=True)
    env = build_ollama_env(args.host, args.port)
    cmd = build_ollama_command(binary)

    try:
        subprocess.run(cmd, check=True, env=env)
    except KeyboardInterrupt:
        print("\n서버 종료")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 서버 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
