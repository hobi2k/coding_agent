"""LangGraph 기반 코딩 에이전트를 정의한다."""

import operator
import json
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Annotated, TypedDict

import requests
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from coding_agent.config import API_BASE, DEFAULT_MODEL, PLATFORM_NAME
from coding_agent.tools import TOOLS, restore_last_changes, show_last_changes
from coding_agent.workspace import get_active_workspace

SUMMARY_PREFIX = "[COMPACT SUMMARY]"
MAX_HISTORY_MESSAGES = 12
KEEP_RECENT_MESSAGES = 6

SYSTEM_PROMPT = f"""당신은 전문 코딩 에이전트입니다.
현재 플랫폼: {PLATFORM_NAME}

사용 가능한 도구:
- read_file    : 파일 내용 읽기 (줄 범위 지원)
- write_file   : 파일 생성 또는 전체 덮어쓰기
- edit_file    : 파일의 특정 문자열을 찾아 교체 (부분 편집 시 사용)
- replace_block: 줄 범위를 기준으로 블록 교체
- list_files   : 디렉토리 목록 확인
- find_files   : 파일명 패턴 검색
- search_in_files : 파일 내용 검색
- show_last_changes : 최근 변경 내역 조회
- restore_last_changes : 최근 변경 복구
- run_command  : 터미널 명령 실행
- web_search   : DuckDuckGo 웹 검색

작업 원칙:
- 사용자의 요청에 plan.md, README.md, TODO 문서 같은 마크다운 문서가 포함되면 작업 지시서처럼 읽고 반영하라
- 파일 수정 전에는 관련 파일과 문서를 먼저 읽어 현재 상태를 확인하라
- 기존 파일 수정 시 전체를 다시 쓰기보다 edit_file 또는 replace_block을 우선 사용하라
- 파일명이나 위치를 모르면 list_files, find_files, search_in_files로 먼저 찾아라
- 사용자가 최근 변경이 의도와 다르다고 말하거나 이전 상태로 되돌리고 싶다는 뜻을 보이면 최근 변경 내역을 확인하고 복구 도구 사용을 검토하라
- 코드 작성 후 run_command로 실행해 동작을 검증하라
- 수정 후에는 가능한 테스트, 빌드, 실행 검증을 최소 1회 이상 시도하라
- 수정 후에는 무엇을 바꿨는지와 사용자의 의도에 맞는지 짧게 self-check하라
- 모르는 라이브러리나 API는 web_search로 먼저 찾아라
- 오류 발생 시 원인을 분석하고 수정하라
- 모든 답변은 한국어로 작성하라
"""


# ── 그래프 상태 정의 ──────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list, operator.add]


def _state_dir() -> Path:
    """에이전트 상태 저장 디렉터리를 반환한다.

    Returns:
        `.agent_state` 디렉터리 경로.
    """
    path = get_active_workspace() / ".agent_state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _working_memory_path() -> Path:
    """작업 메모 파일 경로를 반환한다.

    Returns:
        `working_memory.json` 경로.
    """
    return _state_dir() / "working_memory.json"


def _session_summary_path() -> Path:
    """세션 요약 파일 경로를 반환한다.

    Returns:
        `session_summary.md` 경로.
    """
    return _state_dir() / "session_summary.md"


def _message_role(message: BaseMessage) -> str:
    """메시지 역할 이름을 반환한다.

    Args:
        message: 역할을 판별할 LangChain 메시지.

    Returns:
        정규화된 역할 문자열.
    """
    if isinstance(message, HumanMessage):
        return "user"
    if isinstance(message, AIMessage):
        return "assistant"
    if isinstance(message, ToolMessage):
        return "tool"
    if isinstance(message, SystemMessage):
        return "system"
    return type(message).__name__.lower()


def _content_preview(content, limit: int = 240) -> str:
    """긴 내용을 짧은 미리보기 문자열로 줄인다.

    Args:
        content: 요약할 원본 내용.
        limit: 최대 문자 수.

    Returns:
        줄바꿈이 정리된 미리보기 문자열.
    """
    text = content if isinstance(content, str) else str(content)
    text = " ".join(text.split())
    return text if len(text) <= limit else text[:limit] + "..."


def _summarize_messages(messages: list[BaseMessage], limit: int = 10) -> str:
    """메시지 목록을 짧은 불릿 요약으로 변환한다.

    Args:
        messages: 요약할 메시지 목록.
        limit: 그대로 반영할 최대 메시지 수.

    Returns:
        메시지 목록 요약 문자열.
    """
    lines = []
    for message in messages[:limit]:
        role = _message_role(message)
        preview = _content_preview(getattr(message, "content", ""))
        if preview:
            lines.append(f"- {role}: {preview}")
    if len(messages) > limit:
        lines.append(f"- ...(추가 메시지 {len(messages) - limit}개 생략)")
    return "\n".join(lines) if lines else "- 요약할 메시지 없음"


def _compact_history(history: list[BaseMessage]) -> tuple[list[BaseMessage], str | None]:
    """오래된 대화를 요약으로 압축한다.

    Args:
        history: 현재 대화 히스토리.

    Returns:
        압축된 히스토리와 새 compact summary 문자열.
    """
    if len(history) <= 1 + MAX_HISTORY_MESSAGES:
        return history, None

    system = history[0]
    rest = history[1:]
    existing_summary = None
    if rest and isinstance(rest[0], SystemMessage) and str(rest[0].content).startswith(SUMMARY_PREFIX):
        existing_summary = rest[0]
        rest = rest[1:]

    if len(rest) <= MAX_HISTORY_MESSAGES:
        return history, None

    old_messages = rest[:-KEEP_RECENT_MESSAGES]
    recent_messages = rest[-KEEP_RECENT_MESSAGES:]

    summary_parts = []
    if existing_summary:
        summary_parts.append(str(existing_summary.content))
    summary_parts.append(_summarize_messages(old_messages))
    summary_text = SUMMARY_PREFIX + "\n" + "\n".join(summary_parts)
    compacted = [system, SystemMessage(content=summary_text), *recent_messages]
    return compacted, summary_text


def _load_working_memory() -> dict:
    """작업 메모 파일을 읽는다.

    Returns:
        저장된 작업 메모 딕셔너리.
    """
    path = _working_memory_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_working_memory(memory: dict) -> None:
    """작업 메모를 파일에 저장한다.

    Args:
        memory: 저장할 작업 메모 딕셔너리.
    """
    _working_memory_path().write_text(
        json.dumps(memory, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _save_session_summary(memory: dict) -> None:
    """사람이 읽기 쉬운 세션 요약 문서를 저장한다.

    Args:
        memory: 세션 요약에 반영할 작업 메모 딕셔너리.
    """
    summary_lines = [
        "# Session Summary",
        "",
        f"- updated_at: {memory.get('updated_at', '')}",
        f"- current_task: {memory.get('current_task', '')}",
        f"- recent_changes: {memory.get('recent_changes', '')}",
        f"- recent_verification: {memory.get('recent_verification', '')}",
        "",
        "## Compact Summary",
        "",
        memory.get("compact_summary", "(없음)"),
        "",
        "## Recent Tools",
        "",
    ]
    recent_tools = memory.get("recent_tools", [])
    if recent_tools:
        summary_lines.extend(
            f"- {item.get('tool')}: {item.get('preview')}" for item in recent_tools
        )
    else:
        summary_lines.append("- (없음)")
    _session_summary_path().write_text("\n".join(summary_lines), encoding="utf-8")


def _verification_summary(result: str) -> str:
    """검증 결과 문자열에서 핵심 상태만 추출한다.

    Args:
        result: 도구가 반환한 검증 결과 문자열.

    Returns:
        `exit_code` 중심의 검증 요약 문자열.
    """
    match = re.search(r"exit_code:\s*\d+", result)
    if match:
        return match.group(0)
    preview = _content_preview(result, 160)
    return preview or "(없음)"


def _update_working_memory(
    *,
    current_task: str,
    recent_changes: str,
    recent_tools: list[dict],
    recent_verification: str,
    compact_summary: str | None,
    last_response: str,
) -> dict:
    """작업 메모와 세션 요약을 갱신한다.

    Args:
        current_task: 현재 작업 설명.
        recent_changes: 최근 변경 이력 요약.
        recent_tools: 최근 사용한 도구 목록.
        recent_verification: 최근 검증 결과 요약.
        compact_summary: 최신 compact summary 문자열.
        last_response: 마지막 에이전트 응답.

    Returns:
        갱신 후 작업 메모 딕셔너리.
    """
    memory = _load_working_memory()
    memory.update(
        {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "current_task": current_task,
            "last_response": _content_preview(last_response, 400),
            "recent_changes": _content_preview(recent_changes, 400),
            "recent_verification": recent_verification,
            "recent_tools": recent_tools[-5:],
        }
    )
    if compact_summary is not None:
        memory["compact_summary"] = compact_summary
    else:
        memory.setdefault("compact_summary", "(없음)")
    _save_working_memory(memory)
    _save_session_summary(memory)
    return memory


def check_server_connection(base_url: str = API_BASE, timeout: float = 3.0) -> tuple[bool, str]:
    """vLLM OpenAI 호환 서버의 연결 상태를 점검한다.

    Args:
        base_url: 점검할 서버 주소.
        timeout: 요청 타임아웃 초 단위 값.

    Returns:
        연결 성공 여부와 상태 설명 문자열.
    """
    normalized = base_url.rstrip("/")

    checks = [
        (f"{normalized}/health", "health"),
        (f"{normalized}/v1/models", "models"),
    ]
    errors = []

    for url, name in checks:
        try:
            response = requests.get(url, timeout=timeout)
            if response.ok:
                return True, f"{name} OK ({response.status_code})"
            errors.append(f"{name} {response.status_code}")
        except requests.RequestException as exc:
            errors.append(f"{name} {exc.__class__.__name__}: {exc}")

    return False, " / ".join(errors)


def detect_restore_intent(
    user_input: str,
    recent_changes: str,
    base_url: str = API_BASE,
    model: str = DEFAULT_MODEL,
) -> tuple[bool, str]:
    """최근 변경과 사용자 발화를 함께 보고 복구 의도인지 판단한다.

    키워드 일치만 보지 말고 최근 변경과 사용자 불만 맥락을 함께 본다.

    Args:
        user_input: 사용자의 현재 요청.
        recent_changes: 최근 변경 이력 요약.
        base_url: 라우터가 호출할 서버 주소.
        model: 라우팅에 사용할 모델 이름.

    Returns:
        복구 의도 여부와 판단 근거 문자열.
    """
    if "복구 가능한 변경 내역이 없습니다." in recent_changes:
        return False, "recent_changes_empty"

    router = ChatOpenAI(
        base_url=f"{base_url}/v1",
        api_key="dummy",
        model=model,
        temperature=0,
        max_tokens=120,
    )

    messages = [
        SystemMessage(
            content=(
                "당신은 코딩 에이전트의 의도 라우터다. "
                "사용자 발화가 '최근 변경을 되돌리거나 원상복구하고 싶은 의도'인지 문맥으로만 판단하라. "
                "단순 키워드 일치만 보지 말고, 최근 변경에 대한 불만, 원래대로 되돌리고 싶음, "
                "내 의도와 다르게 바뀌었다는 불만, 직전 작업 취소 의도를 함께 고려하라. "
                "복구 의도면 JSON으로 {\"restore\": true, \"reason\": \"...\"}, "
                "아니면 {\"restore\": false, \"reason\": \"...\"}만 출력하라."
            )
        ),
        HumanMessage(
            content=(
                f"[사용자 발화]\n{user_input}\n\n"
                f"[최근 변경 이력]\n{recent_changes}"
            )
        ),
    ]

    try:
        response = router.invoke(messages)
        content = response.content if isinstance(response.content, str) else str(response.content)
        data = json.loads(content)
        restore = bool(data.get("restore", False))
        reason = str(data.get("reason", "")).strip() or "model_router"
        return restore, reason
    except Exception as exc:
        return False, f"router_error: {exc.__class__.__name__}"


# ── 에이전트 빌더 ─────────────────────────────────────

def build_agent(base_url: str = API_BASE, model: str = DEFAULT_MODEL):
    """LangGraph 에이전트 그래프를 생성한다.

    Args:
        base_url: vLLM OpenAI 호환 서버 주소.
        model: 사용할 모델 이름.

    Returns:
        컴파일된 LangGraph 애플리케이션.
    """

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
        """LLM 노드를 실행한다.

        Args:
            state: 현재 그래프 상태.

        Returns:
            새 AI 메시지가 추가된 상태 조각.
        """
        messages = state["messages"]
        if not messages or not isinstance(messages[0], SystemMessage):
            messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages
        response = llm.invoke(messages)
        return {"messages": [response]}

    def should_continue(state: AgentState) -> str:
        """도구 노드로 갈지 종료할지 결정한다.

        Args:
            state: 현재 그래프 상태.

        Returns:
            다음 노드 이름 또는 `END`.
        """
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
    """대화 히스토리와 파일 기반 작업 메모를 유지하는 에이전트 래퍼."""

    def __init__(self, base_url: str = API_BASE, model: str = DEFAULT_MODEL):
        """에이전트 래퍼를 초기화한다.

        Args:
            base_url: vLLM OpenAI 호환 서버 주소.
            model: 사용할 모델 이름.
        """
        self.base_url = base_url
        self.model = model
        self.app      = build_agent(base_url, model)
        self.history: list = [SystemMessage(content=SYSTEM_PROMPT)]
        _update_working_memory(
            current_task="",
            recent_changes="복구 가능한 변경 내역이 없습니다.",
            recent_tools=[],
            recent_verification="(없음)",
            compact_summary="(없음)",
            last_response="",
        )

    def run(self, user_input: str, on_tool_call=None, on_tool_result=None) -> str:
        """사용자 요청을 처리하고 응답을 반환한다.

        Args:
            user_input: 사용자의 현재 요청.
            on_tool_call: 도구 시작 시 호출할 콜백.
            on_tool_result: 도구 종료 시 호출할 콜백.

        Returns:
            에이전트의 최종 응답 문자열.
        """
        recent_changes = show_last_changes.func(3)
        should_restore, restore_reason = detect_restore_intent(
            user_input=user_input,
            recent_changes=recent_changes,
            base_url=self.base_url,
            model=self.model,
        )

        if should_restore:
            result = restore_last_changes.func(1)
            answer = (
                f"{result}\n\n"
                f"판단 근거: {restore_reason}\n"
                f"필요하면 `show_last_changes`로 남은 변경 이력을 다시 확인할 수 있습니다."
            )
            self.history.append(HumanMessage(content=user_input))
            self.history.append(AIMessage(content=answer))
            self.history, compact_summary = _compact_history(self.history)
            _update_working_memory(
                current_task=user_input,
                recent_changes=show_last_changes.func(3),
                recent_tools=[{"tool": "restore_last_changes", "preview": _content_preview(result, 160)}],
                recent_verification="복구 경로 실행",
                compact_summary=compact_summary,
                last_response=answer,
            )
            return answer

        tool_events: list[dict] = []

        def wrapped_tool_call(name: str, args):
            tool_events.append({"tool": name, "args": _content_preview(str(args), 160)})
            if on_tool_call:
                on_tool_call(name, args)

        def wrapped_tool_result(result: str):
            if tool_events:
                tool_events[-1]["preview"] = _content_preview(result, 200)
            if on_tool_result:
                on_tool_result(result)

        self.history.append(HumanMessage(content=user_input))

        final_state = self.app.invoke(
            {"messages": self.history},
            config={"callbacks": _make_callbacks(wrapped_tool_call, wrapped_tool_result)},
        )

        # 히스토리 업데이트 (system 제외한 새 메시지만 추가)
        new_messages = final_state["messages"][len(self.history):]
        self.history.extend(new_messages)
        self.history, compact_summary = _compact_history(self.history)

        # 마지막 AI 메시지 텍스트 반환
        answer = "(응답 없음)"
        for msg in reversed(final_state["messages"]):
            if isinstance(msg, AIMessage) and msg.content:
                answer = str(msg.content)
                break

        verification_entries = [item for item in tool_events if item.get("tool") == "run_command"]
        recent_verification = (
            _verification_summary(verification_entries[-1].get("preview", ""))
            if verification_entries
            else "(없음)"
        )
        _update_working_memory(
            current_task=user_input,
            recent_changes=show_last_changes.func(3),
            recent_tools=tool_events,
            recent_verification=recent_verification,
            compact_summary=compact_summary,
            last_response=answer,
        )
        return answer

    def reset(self):
        """대화 히스토리와 작업 메모를 초기 상태로 되돌린다."""
        self.history = [SystemMessage(content=SYSTEM_PROMPT)]
        _update_working_memory(
            current_task="",
            recent_changes=show_last_changes.func(3),
            recent_tools=[],
            recent_verification="(없음)",
            compact_summary="(없음)",
            last_response="",
        )


# ── 콜백 헬퍼 ────────────────────────────────────────

def _make_callbacks(on_tool_call, on_tool_result):
    """도구 콜백을 LangChain 콜백 핸들러로 변환한다.

    Args:
        on_tool_call: 도구 시작 시 호출할 콜백.
        on_tool_result: 도구 종료 시 호출할 콜백.

    Returns:
        LangChain 콜백 핸들러 목록.
    """
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
