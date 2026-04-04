# First Run

이 문서는 처음 실행하는 순서를 설명합니다.

## 1. Install Dependencies

```bash
uv sync --dev
```

## 2. Download The Default Model

현재 기본 모델은 `bigatuna/Qwen3.5-9b-Sushi-Coder`입니다.

```bash
uv run agent-dl
```

직접 모델을 지정할 수도 있습니다.

```bash
uv run agent-dl bigatuna/Qwen3.5-9b-Sushi-Coder
```

## 3. Start vLLM

상세 파라미터는 [Server And Runtime Tuning](../reference/server.md)을 보세요.

기본 실행 예:

```bash
uv run agent-server
```

## 4. Start The Agent

```bash
uv run agent
```

CLI에서 `status`를 입력하면 서버 연결 상태를 다시 확인할 수 있습니다.

## 5. Try A Small Task

예:

- "현재 디렉터리 구조를 파악해줘"
- "README와 실제 구조가 다른지 확인해줘"
- "tests 폴더를 찾아서 어떤 테스트가 있는지 요약해줘"

## Related Docs

- [Quickstart](./start-here.md)
- [Tool Reference](../reference/tools.md)
- [Architecture Overview](../reference/architecture.md)
