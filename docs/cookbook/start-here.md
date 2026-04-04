# Quickstart

이 문서는 처음 보는 개발자를 위한 가장 짧은 시작 가이드입니다.

## 이 프로젝트는 무엇인가

`coding_agent`는:

1. GGUF 모델을 내려받고
2. Ollama로 OpenAI 호환 서버를 띄우고
3. 현재 폴더를 workspace로 삼는 CLI 에이전트로
4. 파일 수정, 검색, 검증, 복구까지 수행하는 로컬 코딩 에이전트입니다.

## 가장 짧은 실행 순서

```bash
uv sync --dev
uv run agent-dl
uv run agent-server

cd /path/to/your-project
agent --model coding-agent-qwen2.5-coder-7b-gguf --url http://localhost:11434
```

## 머릿속 모델

- 모델 파일은 [`models/gguf`](/home/hosung/pytorch-demo/coding_agent/models/gguf)에 저장됩니다.
- Ollama용 `Modelfile`은 [`models/ollama`](/home/hosung/pytorch-demo/coding_agent/models/ollama)에 저장됩니다.
- 세션 메모리와 복구 이력은 각 workspace의 `.agent_state/`에 저장됩니다.
- `agent`는 실행한 현재 폴더를 자동 workspace로 사용합니다.

## 다음에 읽을 문서

- 실제 실행 흐름: [First Run](./first-run.md)
- 구조 설명: [Architecture Overview](../reference/architecture.md)
- 도구 설명: [Tool Reference](../reference/tools.md)
- 복구 설명: [Restore Workflow](./restore-workflow.md)
