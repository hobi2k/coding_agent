# Memory And Compact

이 문서는 파일 기반 메모리와 compact 전략을 설명합니다.

## Files

### `.agent_state/working_memory.json`

저장 내용:

- `current_task`
- `last_response`
- `recent_changes`
- `recent_verification`
- `recent_tools`
- `compact_summary`

### `.agent_state/session_summary.md`

사람이 바로 읽을 수 있는 세션 요약 문서입니다.

## Compact Strategy

- 오래된 대화를 그대로 모두 들고 가지 않는다.
- 일정 길이를 넘으면 `[COMPACT SUMMARY]` 시스템 메시지로 요약한다.
- 최근 메시지만 그대로 유지한다.

## Why No Vector DB Yet

현재 프로젝트 단계에서는:

- 코드와 문서는 파일시스템에 이미 존재하고
- 필요하면 다시 읽을 수 있으며
- 세션 상태는 짧은 메모로 충분하기 때문에

벡터 DB보다 파일 기반 메모리가 더 단순하고 실용적입니다.

## Future Direction

- 필요하면 SQLite로 확장 가능
- 더 큰 다중 프로젝트 기억이 필요할 때만 벡터 DB 검토

## Source

- [`coding_agent/agent.py`](../../coding_agent/agent.py)
