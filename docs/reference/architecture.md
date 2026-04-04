# Architecture Overview

이 문서는 프로젝트 구조와 런타임 흐름을 설명합니다.

## Top Level Structure

```text
coding_agent/
├── coding_agent/
├── docs/
│   ├── cookbook/
│   └── reference/
├── models/
├── tests/
├── pyproject.toml
└── README.md
```

## Core Modules

### `config.py`

- 프로젝트 루트 계산
- 플랫폼 감지
- `models/` 경로 설정
- Hugging Face 캐시 환경변수 고정

### `download.py`

- `agent-dl` 엔트리포인트
- Hugging Face `snapshot_download()` 호출

### `server.py`

- `agent-server` 엔트리포인트
- `vllm.entrypoints.openai.api_server` 실행

### `tools.py`

- 파일, 검색, 명령 실행, 복구 관련 도구 정의

### `agent.py`

- LangGraph 기반 메인 에이전트
- 시스템 프롬프트
- 복구 의도 라우팅
- working memory / compact 관리

### `cli.py`

- 대화형 CLI
- 상태 표시
- 도구 로그 출력

## Runtime Flow

1. 사용자가 CLI에 요청한다.
2. 에이전트는 최근 변경과 복구 의도를 먼저 확인한다.
3. 복구 요청이면 복구 경로로 간다.
4. 일반 요청이면 LangGraph 루프가 돈다.
5. 도구 호출 결과와 최근 상태가 working memory에 저장된다.
6. 히스토리가 길어지면 compact가 실행된다.

## Related Docs

- [Tool Reference](./tools.md)
- [Memory And Compact](./memory.md)
- [Recovery And Rollback](./recovery.md)
