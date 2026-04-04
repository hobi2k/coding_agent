# Restore Workflow

이 문서는 에이전트가 잘못 수정했을 때 어떻게 복구하는지 설명합니다.

## What Exists

에이전트는 파일 변경 전에 최근 상태를 기록합니다.
이 정보는 `.agent_state/` 아래 복구 메타데이터로 남습니다.

## Main Recovery Tools

- `show_last_changes`
- `restore_last_changes`

상세 계약은 [Recovery And Rollback](../reference/recovery.md)을 보세요.

## Natural Language Examples

다음과 같은 표현은 복구 의도로 해석될 수 있습니다.

- "방금 변경 복구해줘"
- "내 의도랑 다르게 바뀌었어"
- "원래대로 돌려줘"
- "직전 수정 취소해줘"

복구 판단은 최근 변경 이력과 사용자 발화를 함께 보고 결정합니다.

## Expected Flow

1. 에이전트가 최근 변경 이력을 확인한다.
2. 사용자의 발화가 최근 수정 취소 의도인지 판단한다.
3. 맞다고 판단되면 최근 변경을 복구한다.
4. 필요하면 남은 변경 이력을 다시 보여준다.

## Developer Notes

- 복구 기록은 [`coding_agent/tools.py`](../../coding_agent/tools.py)에 있다.
- 복구 의도 라우팅은 [`coding_agent/agent.py`](../../coding_agent/agent.py)에 있다.

## Related Docs

- [Recovery And Rollback](../reference/recovery.md)
- [Working With Memory](./working-with-memory.md)
