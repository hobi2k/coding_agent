# Tool Reference

이 문서는 에이전트가 사용하는 도구를 설명합니다.

## File Tools

### `read_file`

- 파일 읽기
- 줄 범위 지정 지원
- 큰 파일은 일부만 읽음

### `write_file`

- 새 파일 생성
- 전체 덮어쓰기
- workspace 밖 경로 차단

### `edit_file`

- 정확히 한 번 등장하는 문자열 치환

### `replace_block`

- 줄 범위 기반 블록 치환

## Search Tools

### `list_files`

- 디렉터리 목록 보기

### `find_files`

- 파일명 패턴 검색

### `search_in_files`

- 파일 내용 검색

## Recovery Tools

### `show_last_changes`

- 최근 변경 이력 조회

### `restore_last_changes`

- 최근 변경 복구

## Execution Tool

### `run_command`

- workspace 내부 `cwd`에서 명령 실행
- `exit_code`, `stdout`, `stderr` 반환
- 일부 위험 명령 차단

## External Search

### `web_search`

- DuckDuckGo 검색

## Design Rules

- 원문은 필요할 때 다시 읽는다.
- 가능한 한 workspace 밖 접근은 막는다.
- 수정 전에는 복구 가능성을 위해 스냅샷을 남긴다.

## Source

- [`coding_agent/tools.py`](../../coding_agent/tools.py)
