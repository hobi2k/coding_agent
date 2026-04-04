# 로컬 코딩 에이전트

GGUF + Ollama + OpenAI 호환 API로 동작하는 개인 코딩 에이전트입니다. 모델 파일은 프로젝트 루트의 [`models`](/home/hosung/pytorch-demo/coding_agent/models)에 저장되고, 에이전트는 현재 실행한 폴더를 작업 workspace로 사용합니다.

## 한눈에 보기

- 모델 형식: GGUF
- 기본 런타임: Ollama
- 기본 런타임 모델 이름: `coding-agent-qwen2.5-coder-7b-gguf`
- 기본 GGUF 저장소: `QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF`
- 기본 서버 주소: `http://localhost:11434`
- 작업 방식: CLI 에이전트 + 파일/검색/실행/복구 도구

## 원하는 폴더에서 시작

`agent`는 실행한 현재 폴더를 자동으로 workspace로 사용합니다.

```bash
cd /path/to/your-project
agent --url http://localhost:11434
```

명시적으로 지정하고 싶으면:

```bash
agent --workspace /path/to/your-project --url http://localhost:11434
```

WSL에서 Ollama 서버를 띄우고 Windows에서 CLI를 실행하는 흐름도 가능합니다. 반대로 Windows에서 서버를 띄우고 WSL에서 CLI를 쓰는 것도 가능합니다. 핵심은 CLI가 연결할 OpenAI 호환 URL만 맞추는 것입니다.

## 빠른 시작

```bash
# 1. 의존성 설치
uv sync --dev

# 2. GGUF 다운로드 + Modelfile 생성
uv run agent-dl

# 3. Ollama 서버 시작
uv run agent-server

# 4. 원하는 프로젝트 폴더에서 에이전트 실행
cd /path/to/your-project
agent --model coding-agent-qwen2.5-coder-7b-gguf --url http://localhost:11434
```

`ollama`가 시스템에 없으면 프로젝트는 공식 배포 파일을 내려받아 [`.vendor/ollama`](/home/hosung/pytorch-demo/coding_agent/.vendor/ollama) 아래에 프로젝트 로컬 런타임을 준비합니다. 즉 사용자가 별도로 전역 설치를 먼저 할 필요는 없습니다.

기본 `agent-dl` 동작:

- `QuantFactory/Qwen2.5-Coder-7B-Instruct-GGUF`에서 GGUF 파일 선택
- 기본 양자화 `Q4_K_M` 우선 선택
- [`models/gguf`](/home/hosung/pytorch-demo/coding_agent/models/gguf)에 저장
- [`models/ollama`](/home/hosung/pytorch-demo/coding_agent/models/ollama)에 `Modelfile` 생성
- 가능하면 `ollama create coding-agent-qwen2.5-coder-7b-gguf` 실행
- `ollama`가 없으면 프로젝트 로컬 런타임 자동 준비

## 왜 GGUF/Ollama인가

이 프로젝트는 원래 vLLM 기반으로 시도했지만, 실제 실행 확인 기준으로 `Qwen/Qwen2.5-Coder-7B-Instruct`조차 `vLLM + fp16`에서 RTX 5080 16GB 메모리를 거의 가득 사용했습니다. 공유 GPU 데스크탑에서 다른 작업도 병행하려면 GGUF + Ollama 쪽이 훨씬 현실적이었습니다.

즉 현재 방향은:

- 무거운 fp16 서빙보다 양자화된 GGUF 우선
- OpenAI 호환 API는 Ollama로 제공
- 코딩 에이전트 기능은 LangGraph + 도구 계층으로 구현

## 구조

```text
coding_agent/
├── coding_agent/
│   ├── config.py
│   ├── download.py
│   ├── server.py
│   ├── tools.py
│   ├── agent.py
│   ├── cli.py
│   └── workspace.py
├── docs/
├── models/
│   ├── gguf/
│   └── ollama/
├── tests/
├── pyproject.toml
└── README.md
```

핵심 역할:

- [config.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/config.py): 기본 모델/경로/서버 주소 설정
- [download.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/download.py): GGUF 다운로드와 Modelfile 생성
- [server.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/server.py): `ollama serve` 실행
- [agent.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/agent.py): LangGraph 에이전트와 작업 메모리
- [tools.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/tools.py): 파일/검색/실행/복구 도구
- [cli.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/cli.py): 대화형 CLI
- [workspace.py](/home/hosung/pytorch-demo/coding_agent/coding_agent/workspace.py): multi-workspace 상태 관리

## 기능

- 현재 폴더 자동 workspace 시작
- `/add_dir`, `/use_dir`, `/workspaces` 지원
- 파일 읽기, 쓰기, 편집, 블록 교체
- 파일 검색과 내용 검색
- 명령 실행과 검증 결과 요약
- 최근 변경 이력 조회와 복구
- 작업 메모리와 compact summary 유지
- 문서 기반 지시 해석

## 문서 허브

문서는 [docs/README.md](/home/hosung/pytorch-demo/coding_agent/docs/README.md)를 시작점으로 보면 됩니다.

- 빠른 시작: [start-here.md](/home/hosung/pytorch-demo/coding_agent/docs/cookbook/start-here.md)
- 첫 실행: [first-run.md](/home/hosung/pytorch-demo/coding_agent/docs/cookbook/first-run.md)
- 복구 흐름: [restore-workflow.md](/home/hosung/pytorch-demo/coding_agent/docs/cookbook/restore-workflow.md)
- 구조 설명: [architecture.md](/home/hosung/pytorch-demo/coding_agent/docs/reference/architecture.md)
- 서버/런타임: [server.md](/home/hosung/pytorch-demo/coding_agent/docs/reference/server.md)

## 연동 예시

VSCode Continue:

```json
{
  "models": [
    {
      "title": "Local Coding Agent",
      "provider": "openai",
      "model": "coding-agent-qwen2.5-coder-7b-gguf",
      "apiBase": "http://localhost:11434/v1",
      "apiKey": "dummy"
    }
  ]
}
```

Unity:

```csharp
[SerializeField] string apiUrl = "http://localhost:11434/v1/chat/completions";
[SerializeField] string model  = "coding-agent-qwen2.5-coder-7b-gguf";
```
