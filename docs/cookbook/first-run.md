# First Run

이 문서는 처음 실행하는 순서를 설명합니다.

## 1. Install Dependencies

```bash
uv sync --dev
```

## 2. Download The Default GGUF

현재 기본 GGUF 저장소는 `QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF`입니다.

```bash
uv run agent-dl
```

직접 저장소를 지정할 수도 있습니다.

```bash
uv run agent-dl QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF
```

유용한 옵션:

```bash
uv run agent-dl --quant Q4_K_M
uv run agent-dl --runtime-model my-local-gguf
uv run agent-dl --skip-ollama-create
```

## 3. Start Ollama

```bash
uv run agent-server
```

`ollama`가 시스템에 없다면, 프로젝트는 공식 배포 파일을 `.vendor/ollama` 아래에 내려받아 프로젝트 로컬 런타임을 준비합니다.

포트를 바꾸고 싶으면:

```bash
uv run agent-server --port 11435
```

## 4. Start The Agent

```bash
cd /path/to/your-project
agent --model coding-agent-qwen2.5-coder-7b-gguf --url http://localhost:11434
```

Windows에서 CLI를 실행하고 WSL에서 Ollama 서버를 띄우는 구조도 가능합니다. 반대로 WSL에서 CLI를 실행하고 Windows Ollama에 붙는 구조도 가능합니다. 중요한 건 `--url`이 실제 서버 주소를 가리키는지입니다.

## 5. Try A Small Task

예:

- "현재 디렉터리 구조를 파악해줘"
- "README와 실제 구조가 다른지 확인해줘"
- "tests 폴더를 찾아서 어떤 테스트가 있는지 요약해줘"

## Related Docs

- [Quickstart](./start-here.md)
- [Server And Runtime](../reference/server.md)
- [Architecture Overview](../reference/architecture.md)
