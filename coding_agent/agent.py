"""
LangGraph 기반 코딩 에이전트.

구조:
  사용자 입력
      ↓
  [llm_node]  — LLM이 응답 생성. 도구 호출 포함 시 tool_node로
      ↓ (tool_calls 있음)
  [tool_node] — 도구 실행 후 결과를 상태에 추가, llm_node로 복귀
      ↓ (tool_calls 없음)
  END
"""

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from typing import TypedDict, Annotated
import operator

from coding_agent.config import API_BASE, DEFAULT_MODEL, PLATFORM_NAME
from coding_agent.tools import TOOLS


SYSTEM_PROMPT = f"""당신은 전문 코딩 에이전트입니다.
현재 플랫폼: {PLATFORM_NAME}

사용 가능한 도구:
- read_file    : 파일 내용 읽기
- write_file   : 파일 생성 또는 전체 덮어쓰기
- edit_file    : 파일의 특정 문자열을 찾아 교체 (부분 편집 시 사용)
- list_files   : 디렉토리 목록 확인
- run_command  : 터미널 명령 실행
- web_search   : DuckDuckGo 웹 검색

작업 원칙:
- 파일 수정 시 전체를 다시 쓰지 말고 edit_file로 필요한 부분만 교체하라
- 코드 작성 후 run_command로 실행해 동작을 검증하라
- 모르는 라이브러리나 API는 web_search로 먼저 찾아라
- 오류 발생 시 원인을 분석하고 수정하라
- 모든 답변은 한국어로 작성하라
"""


# ── 그래프 상태 정의 ──────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]


# ── 에이전트 빌더 ─────────────────────────────────────

def build_agent(base_url: str = API_BASE, model: str = DEFAULT_MODEL):
    """LangGraph 에이전트 그래프를 생성하고 컴파일해 반환."""

    llm = ChatOpenAI(
        base_url=f"{base_url}/v1",
        api_key="dummy",           # vllm은 API 키 불필요
        model=model,
        temperature=0.3,
        max_tokens=4096,
    ).bind_tools(TOOLS)

    tool_node = ToolNode(TOOLS)

    # ── 노드 함수 ────────────────────────────────────

    def llm_node(state: AgentState) -> AgentState:
        messages = state["messages"]
        # system 메시지가 없으면 맨 앞에 추가
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        last = state["messages"][-1]
        if isinstance(last, AIMessage) and last.tool_calls:
            return "tools"
        return END

    # ── 그래프 구성 ──────────────────────────────────

    graph = StateGraph(AgentState)
    graph.add_node("llm",   llm_node)
    graph.add_node("tools", tool_node)

    graph.set_entry_point("llm")
    graph.add_conditional_edges("llm", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "llm")

    return graph.compile()


# ── 대화 래퍼 ─────────────────────────────────────────

class CodingAgent:
    """대화 히스토리를 유지하며 LangGraph 에이전트를 실행하는 래퍼."""

    def __init__(self, base_url: str = API_BASE, model: str = DEFAULT_MODEL):
        self.app      = build_agent(base_url, model)
        self.history: list = [SystemMessage(content=SYSTEM_PROMPT)]

    def run(self, user_input: str, on_tool_call=None, on_tool_result=None) -> str:
        self.history.append(HumanMessage(content=user_input))

        final_state = self.app.invoke(
            {"messages": self.history},
            config={"callbacks": _make_callbacks(on_tool_call, on_tool_result)},
        )

        # 히스토리 업데이트 (system 제외한 새 메시지만 추가)
        new_messages = final_state["messages"][len(self.history):]
        self.history.extend(new_messages)

        # 마지막 AI 메시지 텍스트 반환
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                return str(msg.content)
        return "(응답 없음)"

    def reset(self):
        self.history = [SystemMessage(content=SYSTEM_PROMPT)]


# ── 콜백 헬퍼 ────────────────────────────────────────

def _make_callbacks(on_tool_call, on_tool_result):
    """도구 호출/결과 콜백을 LangChain 콜백 핸들러로 변환."""
    if not on_tool_call and not on_tool_result:
        return []

    from langchain_core.callbacks import BaseCallbackHandler

    class _Handler(BaseCallbackHandler):
        def on_tool_start(self, serialized, input_str, **kwargs):
            if on_tool_call:
                name = serialized.get("name", "?")
                on_tool_call(name, input_str)

        def on_tool_end(self, output, **kwargs):
            if on_tool_result:
                on_tool_result(str(output))

    return [_Handler()]