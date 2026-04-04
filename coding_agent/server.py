"""vLLM 서버 실행 CLI를 제공한다."""

import sys
import argparse
import subprocess
from coding_agent.config import (
    DEFAULT_MODEL, DEFAULT_HOST, DEFAULT_PORT,
    MODELS_DIR, PLATFORM_NAME, IS_WINDOWS,
)


def main():
    """vLLM OpenAI 호환 서버를 실행한다."""
    parser = argparse.ArgumentParser(description="vllm 서버 실행")
    parser.add_argument("--model",    default=DEFAULT_MODEL)
    parser.add_argument("--host",     default=DEFAULT_HOST)
    parser.add_argument("--port",     default=DEFAULT_PORT, type=int)
    parser.add_argument("--gpu-util", default=0.60, type=float)
    parser.add_argument("--max-len",  default=4096, type=int,
                        help="컨텍스트 길이.")
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
        "--reasoning-parser",       "qwen3",
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
