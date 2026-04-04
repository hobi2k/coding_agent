# Current Status

기준 시각: 2026-04-04

## Summary

이 프로젝트는 GGUF + Ollama 기반의 로컬 코딩 에이전트로 전환된 상태입니다. 파일 도구, 명령 실행, 복구, 작업 메모리, 대화 compact, multi-workspace CLI까지 들어가 있습니다.

## What Exists Today

### Runtime

- `uv run agent-dl`
- `uv run agent-server`
- `agent`
- GGUF 다운로드와 Modelfile 생성
- Ollama OpenAI 호환 서버 연결

### Agent

- LangGraph 기반 에이전트 루프
- OpenAI 호환 API 연결
- 서버 연결 체크
- 복구 의도 라우팅
- working memory / compact

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

### Workspace

- 현재 폴더 자동 workspace 시작
- `/add_dir`
- `/use_dir`
- `/workspaces`

### Safety And State

- workspace 바깥 경로 접근 차단
- 위험한 명령 일부 차단
- 변경 전 스냅샷 저장 기반 복구
- `.agent_state/working_memory.json`
- `.agent_state/session_summary.md`
- 오래된 대화 compact

### Tests

- 도구/에이전트/복구/compact/workspace 테스트
- GGUF 다운로드 헬퍼 테스트
- Ollama 서버 명령 구성 테스트

## What Changed Recently

- 기존 Hugging Face/vLLM 캐시 삭제
- [`models`](/home/hosung/pytorch-demo/coding_agent/models) 아래 구조를 `gguf/`, `ollama/` 중심으로 정리
- 기본 런타임을 Ollama로 전환
- 기본 GGUF 저장소를 `QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF`로 전환
- 문서와 README를 새 구조 기준으로 재정리

## Current Limitations

- 시스템에 `ollama`가 없더라도 프로젝트 로컬 런타임 자동 준비 경로가 들어가 있습니다. 다만 실제 다운로드와 실기동은 아직 이 세션에서 끝까지 검증하지 않았습니다.
- planner 품질은 여전히 시스템 프롬프트 + 도구 조합 수준입니다.
- 장기 세션 저장은 파일 기반이며 DB는 아직 없습니다.

## Suggested Next Work

1. Ollama 설치 후 실제 `agent-dl -> agent-server -> agent` 실기동 검증
2. Windows/WSL 교차 실행 문서 보강
3. planner/self-check 루프 강화
4. GGUF 모델 프로필 선택 UX 개선
