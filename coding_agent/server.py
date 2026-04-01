"""
vllm 서버 실행 엔트리포인트.

사용법:
    uv run agent-server
    uv run agent-server --model bigatuna/Qwen3.5-9b-Sushi-Coder
    uv run agent-server --port 8001 --gpu-util 0.85
"""

import sys
import argparse
import subprocess
from coding_agent.config import (
    DEFAULT_MODEL, DEFAULT_HOST, DEFAULT_PORT,
    MODELS_DIR, PLATFORM_NAME, IS_WINDOWS,
)


def main():
    parser = argparse.ArgumentParser(description="vllm 서버 실행")
    parser.add_argument("--model",    default=DEFAULT_MODEL)
    parser.add_argument("--host",     default=DEFAULT_HOST)
    parser.add_argument("--port",     default=DEFAULT_PORT, type=int)
    parser.add_argument("--gpu-util", default=0.90, type=float)
    parser.add_argument("--max-len",  default=32768, type=int,
                        help="컨텍스트 길이. Qwen3.5는 최소 32768 권장")
    args = parser.parse_args()

    print(f"플랫폼   : {PLATFORM_NAME}")
    print(f"모델     : {args.model}")
    print(f"주소     : http://{args.host}:{args.port}")
    print(f"모델폴더 : {MODELS_DIR}")
    print()

    if IS_WINDOWS:
        print("⚠  Windows 감지: vllm은 WSL(Ubuntu)에서 실행해야 합니다.")
        print("   WSL 터미널을 열고 동일 명령어를 다시 실행하세요.")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "vllm.entrypoints.openai.api_server",
        "--model",                  args.model,
        "--host",                   args.host,
        "--port",                   str(args.port),
        "--dtype",                  "float16",
        "--gpu-memory-utilization", str(args.gpu_util),
        "--max-model-len",          str(args.max_len),
        "--download-dir",           str(MODELS_DIR / "hub"),
        # Qwen3.5 thinking 모드
        "--reasoning-parser",       "qwen3",
        # Qwen3.5 네이티브 tool calling
        "--enable-auto-tool-choice",
        "--tool-call-parser",       "qwen3_coder",
    ]

    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n서버 종료")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 서버 실행 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()