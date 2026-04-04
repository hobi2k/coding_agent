# 로컬 코딩 에이전트

RTX GPU + vllm + HuggingFace 모델로 동작하는 개인 코딩 에이전트.
모델은 프로젝트 루트의 `./models/` 폴더에 저장됩니다.
CLI와 다운로드 관리는 Windows/WSL/Linux에서 가능하지만, `vllm` 서버 실행은 Linux/WSL이 필요합니다.

## 구조

```text
coding_agent/
├── coding_agent/
│   ├── config.py    # 플랫폼 감지, 프로젝트 루트/모델 경로 설정
│   ├── download.py  # Hugging Face 모델 다운로드 CLI
│   ├── server.py    # vllm OpenAI 호환 서버 실행 CLI
│   ├── tools.py     # 파일/터미널/검색 도구
│   ├── agent.py     # LangGraph 에이전트 + ChatOpenAI(vllm) 연결
│   └── cli.py       # 대화형 CLI 인터페이스
├── docs/
│   ├── README.md
│   ├── cookbook/
│   ├── reference/
│   ├── current-status.md
│   └── plan.md
├── models/          # 모델 캐시 및 다운로드 저장 위치
├── tests/
├── pyproject.toml
├── uv.lock
└── README.md
```

현재 구조에는 `llm.py`가 없고, vLLM OpenAI 호환 클라이언트 연결은 `coding_agent/agent.py`에서 직접 구성합니다.

## 문서 허브

문서는 [`docs/README.md`](./docs/README.md)를 시작점으로 읽으면 됩니다.

- 빠른 시작: [`docs/cookbook/start-here.md`](./docs/cookbook/start-here.md)
- 첫 실행: [`docs/cookbook/first-run.md`](./docs/cookbook/first-run.md)
- 복구 흐름: [`docs/cookbook/restore-workflow.md`](./docs/cookbook/restore-workflow.md)
- 구조 설명: [`docs/reference/architecture.md`](./docs/reference/architecture.md)

## 설치 및 실행

> **vllm은 Linux/WSL에서만 실행됩니다.**  
> Windows라면 WSL 터미널을 열고 진행하세요.

```bash
# 1. uv 설치 (없으면)
curl -Lsf https://astral.sh/uv/install.sh | sh

# 2. 의존성 설치
uv sync

# 3. 모델 다운로드 (./models/ 에 저장됨)
uv run agent-dl
# 현재 기본 모델:
# bigatuna/Qwen3.5-9b-Sushi-Coder
# 다른 모델 지정:
uv run agent-dl bigatuna/Qwen3.5-9b-Sushi-Coder

# 4. vllm 서버 시작 (터미널 1)
uv run agent-server

# 5. 에이전트 실행 (터미널 2)
uv run agent
```

### 옵션

```bash
# 모델/포트 변경
uv run agent-server --model bigatuna/Qwen3.5-9b-Sushi-Coder --port 8001
uv run agent --model bigatuna/Qwen3.5-9b-Sushi-Coder --url http://localhost:8001

# GPU 메모리 사용률 조정 (기본 90%)
uv run agent-server --gpu-util 0.85
```

---

## VSCode 연동

1. VSCode Marketplace에서 **Continue** 확장 설치
2. `~/.continue/config.json` 수정:

```json
{
  "models": [
    {
      "title": "내 로컬 모델",
      "provider": "openai",
      "model": "bigatuna/Qwen3.5-9b-Sushi-Coder",
      "apiBase": "http://localhost:8000/v1",
      "apiKey": "dummy"
    }
  ]
}
```

---

## Unity 연동

`Assets/Scripts/LLMClient.cs` 로 저장:

```csharp
using UnityEngine;
using UnityEngine.Networking;
using System.Collections;
using System.Text;

public class LLMClient : MonoBehaviour
{
    [SerializeField] string apiUrl = "http://localhost:8000/v1/chat/completions";
    [SerializeField] string model  = "bigatuna/Qwen3.5-9b-Sushi-Coder";

    public void Ask(string message, System.Action<string> onResult)
    {
        StartCoroutine(Send(message, onResult));
    }

    IEnumerator Send(string message, System.Action<string> onResult)
    {
        string body = $"{{\"model\":\"{model}\",\"messages\":[{{\"role\":\"user\",\"content\":{JsonUtility.ToJson(message)}}}]}}";
        using var req = new UnityWebRequest(apiUrl, "POST");
        req.uploadHandler   = new UploadHandlerRaw(Encoding.UTF8.GetBytes(body));
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        yield return req.SendWebRequest();

        if (req.result == UnityWebRequest.Result.Success)
        {
            // 간단 파싱: "content":"..." 값 추출
            string resp    = req.downloadHandler.text;
            int    ci      = resp.IndexOf("\"content\":\"") + 11;
            int    end     = resp.IndexOf("\"", ci);
            string content = resp.Substring(ci, end - ci);
            onResult?.Invoke(content);
        }
        else
        {
            Debug.LogError($"LLM 오류: {req.error}");
        }
    }
}
```

---

## 현재 기본 모델

| 항목 | 값 |
|------|----|
| 기본 모델 | `bigatuna/Qwen3.5-9b-Sushi-Coder` |
| 모델 저장 위치 | `./models/` |
| vLLM 다운로드 경로 | `./models/hub` |

## 후보 모델 (예시)

| 모델 | HuggingFace ID | 특징 |
|------|---------------|------|
| Qwen3.5-9B Sushi Coder | `bigatuna/Qwen3.5-9b-Sushi-Coder` | 현재 코드 기본값 |
| Qwen2.5-Coder-7B | `Qwen/Qwen2.5-Coder-7B-Instruct` | 비교적 가벼운 코딩 모델 |
| Qwen2.5-Coder-14B | `Qwen/Qwen2.5-Coder-14B-Instruct` | 더 강한 성능 기대 |
| DeepSeek-Coder-V2-Lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | 대안 모델 후보 |

모델 변경 시 `agent-dl`로 다운로드 후 `--model` 인자만 바꾸면 됩니다.
