# Architecture Overview

이 문서는 프로젝트 구조와 런타임 원리를 설명합니다.

## 핵심 원리

이 프로젝트는 모델 서빙과 에이전트 로직을 분리합니다.

- 모델 서빙: GGUF + Ollama
- 에이전트 로직: LangGraph + 도구 계층
- 연결 방식: OpenAI 호환 HTTP API

즉 모델이 무엇이든 OpenAI 호환 API만 맞으면 에이전트는 같은 코드로 붙을 수 있습니다.

## 상위 구조

```text
coding_agent/
├── coding_agent/
├── docs/
├── models/
│   ├── gguf/
│   └── ollama/
├── tests/
├── pyproject.toml
└── README.md
```

## Core Modules

### `config.py`

- 프로젝트 루트 계산
- 플랫폼 감지
- 기본 모델 이름과 기본 서버 주소 설정
- `models/` 경로 설정

### `download.py`

- `agent-dl` 엔트리포인트
- GGUF 저장소 파일 목록 조회
- 원하는 양자화 파일 선택
- GGUF 파일 다운로드
- Ollama `Modelfile` 생성
- 가능하면 `ollama create` 실행

### `server.py`

- `agent-server` 엔트리포인트
- `OLLAMA_HOST`를 설정한 뒤 `ollama serve` 실행

### `tools.py`

- 파일 읽기, 쓰기, 편집
- 디렉터리/파일 검색
- 명령 실행
- 복구 이력 저장과 복구
- workspace 경계 보호

### `agent.py`

- LangGraph 기반 메인 에이전트
- 시스템 프롬프트
- 복구 의도 라우팅
- working memory / compact 관리
- OpenAI 호환 서버 연결 확인

### `cli.py`

- 대화형 CLI
- 현재 폴더 자동 workspace 시작
- `/add_dir`, `/use_dir`, `/workspaces`
- 서버 상태 표시

### `workspace.py`

- 활성 workspace 관리
- 등록된 workspace 목록 유지
- 현재 세션의 작업 디렉터리 결정

## Runtime Flow

1. `agent-dl`이 GGUF를 내려받고 `Modelfile`을 만든다.
2. `agent-server`가 Ollama 서버를 띄운다.
3. 사용자가 원하는 폴더에서 `agent`를 실행한다.
4. CLI는 현재 폴더를 workspace로 활성화한다.
5. 에이전트는 요청을 받고 복구 의도 여부를 먼저 본다.
6. 일반 요청이면 LangGraph 루프가 도구를 호출한다.
7. 결과는 working memory와 recovery state에 기록된다.
8. 대화가 길어지면 compact가 실행된다.

## 왜 이 구조인가

- GGUF는 공유 GPU 환경에서 더 현실적이다.
- Ollama는 OpenAI 호환 API를 제공해 연결 계층이 단순하다.
- 에이전트는 모델 자체보다 도구 계층과 검증 루프가 더 중요하다.
- workspace 분리를 통해 Codex/Claude Code와 비슷한 사용성에 가까워진다.

## Related Docs

- [Tool Reference](./tools.md)
- [Memory And Compact](./memory.md)
- [Recovery And Rollback](./recovery.md)
- [Server And Runtime](./server.md)
