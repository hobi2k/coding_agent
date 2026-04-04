# Server And Runtime

이 문서는 모델 다운로드, Ollama 서버 실행, 런타임 연결 방식을 설명합니다.

## 기본 설정

- 기본 GGUF 저장소: `QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF`
- 기본 양자화: `Q4_K_M`
- 기본 런타임 모델 이름: `coding-agent-qwen2.5-coder-7b-gguf`
- 기본 서버 주소: `http://localhost:11434`

## 왜 GGUF + Ollama인가

이 프로젝트는 원래 vLLM 경로를 실험했지만, 실제 실행 확인에서 `Qwen/Qwen2.5-Coder-7B-Instruct`조차 RTX 5080 16GB 메모리를 거의 가득 사용했습니다. 공유 GPU 데스크탑에서 다른 작업도 병행하려면 GGUF + Ollama 쪽이 더 현실적이었습니다.

현재 기본 전략은:

- 양자화된 GGUF 사용
- Ollama로 OpenAI 호환 서버 제공
- 에이전트는 그 위에 도구 계층을 얹어 동작

## 다운로드 흐름

`agent-dl`은 다음을 수행합니다.

1. Hugging Face 저장소의 파일 목록을 조회
2. `.gguf` 파일 중 원하는 양자화를 선택
3. [`models/gguf`](/home/hosung/pytorch-demo/coding_agent/models/gguf)에 다운로드
4. [`models/ollama`](/home/hosung/pytorch-demo/coding_agent/models/ollama)에 `Modelfile` 생성
5. 가능하면 `ollama create` 실행

`ollama` 바이너리가 시스템에 없으면 프로젝트는 `.vendor/ollama/<platform>` 아래에 공식 배포 파일을 내려받아 프로젝트 로컬 런타임으로 사용합니다.

주요 옵션:

- `--quant`: 원하는 양자화 선택
- `--runtime-model`: 로컬 Ollama 모델 이름 지정
- `--skip-ollama-create`: Modelfile만 만들고 `ollama create`는 건너뜀

## 서버 실행

기본 실행:

```bash
uv run agent-server
```

포트 변경:

```bash
uv run agent-server --port 11435
```

내부적으로는 `OLLAMA_HOST=<host>:<port>`를 설정한 뒤 `ollama serve`를 실행합니다.
필요하면 프로젝트 로컬 Ollama 바이너리를 자동으로 준비한 뒤 그 바이너리를 사용합니다.

## 에이전트 연결

기본 연결:

```bash
agent --model coding-agent-qwen2.5-coder-7b-gguf --url http://localhost:11434
```

다른 포트:

```bash
agent --model coding-agent-qwen2.5-coder-7b-gguf --url http://localhost:11435
```

## 실행 환경

- Ollama는 Windows와 Linux/WSL 모두에서 사용할 수 있습니다.
- CLI도 Windows와 WSL 모두에서 사용할 수 있습니다.
- 서버와 CLI가 다른 쪽에 있어도 URL만 맞으면 연결할 수 있습니다.

예:

- WSL: `uv run agent-server`
- Windows: `agent --url http://localhost:11434`

## 저장 위치

- GGUF 파일: [`models/gguf`](/home/hosung/pytorch-demo/coding_agent/models/gguf)
- Ollama Modelfile: [`models/ollama`](/home/hosung/pytorch-demo/coding_agent/models/ollama)

## Source

- [`download.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/download.py)
- [`server.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/server.py)
- [`config.py`](/home/hosung/pytorch-demo/coding_agent/coding_agent/config.py)
