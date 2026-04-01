# 로컬 코딩 에이전트

RTX GPU + vllm + HuggingFace 모델로 동작하는 개인 코딩 에이전트.  
모델은 `./models/` 폴더에 저장되며, WSL과 Windows 모두 지원.

## 구조

```
coding-agent/
├── coding_agent/
│   ├── config.py    # 플랫폼 감지, 경로 설정
│   ├── download.py  # 모델 다운로드
│   ├── server.py    # vllm 서버 실행
│   ├── llm.py       # vllm 클라이언트
│   ├── tools.py     # 파일/터미널 도구
│   ├── agent.py     # ReAct 루프
│   └── cli.py       # CLI 인터페이스
├── models/          # 모델 저장 위치 (자동 생성)
├── pyproject.toml
└── README.md
```

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
# 다른 모델 지정:
uv run agent-dl Qwen/Qwen2.5-Coder-14B-Instruct

# 4. vllm 서버 시작 (터미널 1)
uv run agent-server

# 5. 에이전트 실행 (터미널 2)
uv run agent
```

### 옵션

```bash
# 모델/포트 변경
uv run agent-server --model Qwen/Qwen2.5-Coder-14B-Instruct --port 8001
uv run agent --model Qwen/Qwen2.5-Coder-14B-Instruct --url http://localhost:8001

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
      "model": "Qwen/Qwen2.5-Coder-7B-Instruct",
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
    [SerializeField] string model  = "Qwen/Qwen2.5-Coder-7B-Instruct";

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

## 추천 모델 (16 GB VRAM)

| 모델 | HuggingFace ID | 특징 |
|------|---------------|------|
| Qwen2.5-Coder-7B  | `Qwen/Qwen2.5-Coder-7B-Instruct`  | 빠름, 코딩 특화, 기본값 |
| Qwen2.5-Coder-14B | `Qwen/Qwen2.5-Coder-14B-Instruct` | 16 GB에서 동작, 더 강력 |
| DeepSeek-Coder-V2-Lite | `deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct` | MoE 구조, 강력 |

모델 변경 시 `agent-dl`로 다운로드 후 `--model` 인자만 바꾸면 됩니다.
