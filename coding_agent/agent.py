from coding_agent.llm import LLMClient
from coding_agent.tools import TOOL_DESCRIPTIONS, parse_tool_call, execute_tool
from coding_agent.config import PLATFORM_NAME

SYSTEM_PROMPT = f"""당신은 전문 코딩 에이전트입니다.
현재 플랫폼: {PLATFORM_NAME}

{TOOL_DESCRIPTIONS}

작업 원칙:
- 파일이 필요하면 read_file로 먼저 읽어라
- 코드를 작성하면 write_file로 저장 후 run_command로 실행해 검증하라
- 오류 발생 시 원인 분석 후 수정하라
- 모르면 list_files로 구조를 먼저 파악하라
- 모든 답변은 한국어로 작성하라
"""


class CodingAgent:
    def __init__(self, llm: LLMClient, max_iterations: int = 15):
        self.llm            = llm
        self.max_iterations = max_iterations
        self.conversation: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def run(
        self,
        user_input: str,
        on_tool_call=None,
        on_tool_result=None,
    ) -> str:
        self.conversation.append({"role": "user", "content": user_input})

        for _ in range(self.max_iterations):
            response  = self.llm.chat(self.conversation)
            text      = self.llm.extract_text(response)
            tool_call = parse_tool_call(text)

            if tool_call is None:
                self.conversation.append({"role": "assistant", "content": text})
                return text

            if on_tool_call:
                on_tool_call(tool_call.get("tool", ""), tool_call.get("args", {}))

            result = execute_tool(tool_call)

            if on_tool_result:
                on_tool_result(result)

            self.conversation.append({"role": "assistant", "content": text})
            self.conversation.append({
                "role":    "user",
                "content": f"[도구 결과 — {tool_call.get('tool')}]\n{result}",
            })

        return "최대 반복 횟수에 도달했습니다."

    def reset(self):
        self.conversation = [self.conversation[0]]
