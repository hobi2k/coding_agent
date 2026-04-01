import requests
from coding_agent.config import API_BASE, DEFAULT_MODEL


class LLMClient:
    def __init__(
        self,
        base_url: str = API_BASE,
        model: str = DEFAULT_MODEL,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ):
        self.base_url    = base_url.rstrip("/")
        self.model       = model
        self.temperature = temperature
        self.max_tokens  = max_tokens

    def chat(self, messages: list[dict]) -> dict:
        try:
            resp = requests.post(
                f"{self.base_url}/v1/chat/completions",
                json={
                    "model":       self.model,
                    "messages":    messages,
                    "temperature": self.temperature,
                    "max_tokens":  self.max_tokens,
                    "stream":      False,
                },
                timeout=120,
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "vllm 서버에 연결할 수 없습니다.\n"
                "먼저 서버를 실행하세요:\n\n"
                "  uv run agent-server\n"
            )
        except requests.exceptions.Timeout:
            raise RuntimeError("서버 응답 시간 초과 (120초)")

    def extract_text(self, response: dict) -> str:
        return response["choices"][0]["message"]["content"]
