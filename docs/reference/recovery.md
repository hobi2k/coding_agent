# Recovery And Rollback

이 문서는 복구 메커니즘을 설명합니다.

## Why It Exists

코딩 에이전트는 문법 오류보다 "사용자 의도와 다르게 고친 것"이 더 위험할 수 있습니다.
그래서 이 프로젝트는 최근 변경을 되돌릴 수 있는 복구 계층을 둡니다.

## Stored State

- 복구 메타데이터: `.agent_state/recovery_index.json`
- 이전 파일 스냅샷: `.agent_state/recovery/`

## What Gets Tracked

- `write_file`
- `edit_file`
- `replace_block`

## Recovery Flow

1. 파일 수정 전 이전 상태 저장
2. 최근 변경 이력 조회 가능
3. 사용자의 복구 의도를 문맥으로 판단
4. 최근 변경을 되돌림

## Tool Contract

### `show_last_changes(limit=5)`

- 최근 변경 내역 출력
- 복구 가능 여부 표시

### `restore_last_changes(count=1)`

- 최근 변경부터 복구
- 새로 생성한 파일은 삭제될 수 있음
- 기존 파일은 저장된 이전 상태로 되돌아감

## Source

- [`coding_agent/tools.py`](../../coding_agent/tools.py)
- [`coding_agent/agent.py`](../../coding_agent/agent.py)
