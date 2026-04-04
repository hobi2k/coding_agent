# Quickstart

이 문서는 처음 보는 개발자를 위한 가장 짧은 시작 가이드입니다.

## What This Project Is

`coding_agent`는 로컬 모델을 `vLLM`으로 서빙하고, 그 위에 파일/명령/복구 도구를 붙여 코딩 작업을 수행하는 CLI 에이전트입니다.

## Read This Next

- 구조를 먼저 보고 싶다면 [Architecture Overview](../reference/architecture.md)
- 바로 실행하고 싶다면 [First Run](./first-run.md)
- 복구 기능이 궁금하면 [Restore Workflow](./restore-workflow.md)

## Main Commands

```bash
uv run agent-dl
uv run agent-server
uv run agent
```

## Main Files

- [`coding_agent/config.py`](../../coding_agent/config.py)
- [`coding_agent/server.py`](../../coding_agent/server.py)
- [`coding_agent/agent.py`](../../coding_agent/agent.py)
- [`coding_agent/tools.py`](../../coding_agent/tools.py)
- [`coding_agent/cli.py`](../../coding_agent/cli.py)

## Mental Model

1. 모델을 다운로드한다.
2. vLLM 서버를 띄운다.
3. CLI 에이전트를 실행한다.
4. 에이전트는 도구를 사용해 파일을 읽고 수정하고 검증한다.
5. 잘못된 수정은 복구할 수 있다.

## Important Notes

- 모델 파일은 프로젝트 루트 `models/` 아래에 저장된다.
- 작업 중 메모리/세션 상태는 `.agent_state/`에 저장된다.
- 변경 복구를 위해 최근 수정 이력이 기록된다.

## Next

- [First Run](./first-run.md)
