# Current Status

기준 시각: 2026-04-04

## Summary

이 프로젝트는 "로컬 모델 + vLLM + 도구 기반 코딩 에이전트"의 1차 동작 버전입니다.
단순 챗봇 수준은 넘었고, 파일 읽기/쓰기/편집, 명령 실행, 복구, 작업 메모, 대화 compact까지 들어간 상태입니다.

## What Exists Today

### Runtime

- 프로젝트 루트 `models/` 아래로 Hugging Face 캐시를 고정
- `uv run agent-dl`
- `uv run agent-server`
- `uv run agent`

### Agent

- LangGraph 기반 에이전트 루프
- vLLM OpenAI 호환 API 연결
- 서버 연결 체크
- 최근 변경 복구 라우팅

### Tools

- `read_file`
- `write_file`
- `edit_file`
- `replace_block`
- `list_files`
- `find_files`
- `search_in_files`
- `show_last_changes`
- `restore_last_changes`
- `run_command`
- `web_search`

### Safety And State

- workspace 바깥 경로 접근 차단
- 위험한 명령 일부 차단
- 변경 전 스냅샷 저장 기반 복구
- `.agent_state/working_memory.json`
- `.agent_state/session_summary.md`
- 오래된 대화 compact

### Tests

- pytest 기반 테스트 추가
- 도구/에이전트/복구/compact 흐름 검증

## Current Limitations

- 기본 서버 파라미터는 아직 사용자 GPU 현실에 맞게 더 보수적으로 조정될 필요가 있음
- 기본 모델이 `bigatuna/Qwen3.5-9b-Sushi-Coder`라서 16GB VRAM 환경에서는 여유가 적을 수 있음
- 복구 의도 라우팅은 문맥 기반으로 바뀌었지만, 여전히 더 정교한 self-check 루프가 가능함
- 문서 지시 해석 능력은 시스템 프롬프트와 도구 조합 수준이며, 별도 planner 노드는 아직 없음
- 검증 결과 축적은 파일 기반 메모리 중심이며 장기 세션 분석용 DB는 아직 없음

## Suggested Next Work

1. 서버 기본 파라미터를 더 현실적인 값으로 조정
2. 모델 프로필을 "전용 실행"과 "공유 GPU"로 분리
3. self-check와 verification planning 강화
4. 문서 기반 작업 계획 노드 추가

## Related Docs

- [Documentation Hub](./README.md)
- [Quickstart](./cookbook/start-here.md)
- [Architecture](./reference/architecture.md)
- [Memory And Compact](./reference/memory.md)
- [Recovery And Rollback](./reference/recovery.md)
