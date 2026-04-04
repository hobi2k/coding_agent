from __future__ import annotations

import json
import shutil
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from coding_agent import agent
from coding_agent.config import PROJECT_ROOT
from coding_agent.workspace import set_active_workspace


def _reset_agent_state() -> None:
    set_active_workspace(str(PROJECT_ROOT))
    state_dir = PROJECT_ROOT / ".agent_state"
    if state_dir.exists():
        shutil.rmtree(state_dir)


def test_system_prompt_mentions_tools_and_korean_policy() -> None:
    prompt = agent.SYSTEM_PROMPT

    assert "read_file" in prompt
    assert "write_file" in prompt
    assert "edit_file" in prompt
    assert "replace_block" in prompt
    assert "find_files" in prompt
    assert "search_in_files" in prompt
    assert "show_last_changes" in prompt
    assert "restore_last_changes" in prompt
    assert "run_command" in prompt
    assert "모든 답변은 한국어" in prompt
    assert "마크다운 문서" in prompt
    assert "복구" in prompt
    assert "키워드 일치만 보지 말고" in agent.detect_restore_intent.__doc__


def test_make_callbacks_routes_tool_events() -> None:
    events: list[tuple[str, str]] = []

    callbacks = agent._make_callbacks(
        on_tool_call=lambda name, payload: events.append((name, str(payload))),
        on_tool_result=lambda result: events.append(("result", result)),
    )

    assert len(callbacks) == 1
    handler = callbacks[0]
    handler.on_tool_start({"name": "read_file"}, "sample.txt")
    handler.on_tool_end("done")

    assert events[0][0] == "read_file"
    assert events[1] == ("result", "done")


def test_coding_agent_reset_restores_initial_history(monkeypatch) -> None:
    _reset_agent_state()

    class DummyApp:
        def invoke(self, state, config=None):
            return {"messages": state["messages"] + [AIMessage(content="응답")]}

    monkeypatch.setattr(agent, "build_agent", lambda base_url, model: DummyApp())
    monkeypatch.setattr(agent, "detect_restore_intent", lambda **kwargs: (False, "normal"))

    coding_agent = agent.CodingAgent(base_url="http://localhost:8000", model="dummy")

    assert len(coding_agent.history) == 1
    assert isinstance(coding_agent.history[0], SystemMessage)

    answer = coding_agent.run("안녕")
    assert answer == "응답"
    assert any(isinstance(msg, HumanMessage) for msg in coding_agent.history)
    assert any(isinstance(msg, AIMessage) for msg in coding_agent.history)

    coding_agent.reset()
    assert len(coding_agent.history) == 1
    assert isinstance(coding_agent.history[0], SystemMessage)


def test_coding_agent_restores_when_router_marks_restore(monkeypatch) -> None:
    _reset_agent_state()

    class DummyApp:
        def invoke(self, state, config=None):
            raise AssertionError("복구 경로에서는 일반 에이전트 invoke가 호출되면 안 됩니다.")

    monkeypatch.setattr(agent, "build_agent", lambda base_url, model: DummyApp())
    monkeypatch.setattr(
        agent, "detect_restore_intent", lambda **kwargs: (True, "recent_change_mismatch")
    )
    monkeypatch.setattr(agent.show_last_changes, "func", lambda limit=3: "id: 123")
    monkeypatch.setattr(agent.restore_last_changes, "func", lambda count=1: "복구 완료: 1건")

    coding_agent = agent.CodingAgent(base_url="http://localhost:8000", model="dummy")

    answer = coding_agent.run("방금 바뀐 게 내 의도랑 달라")

    assert "복구 완료" in answer
    assert "recent_change_mismatch" in answer
    assert isinstance(coding_agent.history[-1], AIMessage)


def test_server_connection_helper_success(monkeypatch) -> None:
    class DummyResponse:
        ok = True
        status_code = 200

    monkeypatch.setattr(agent.requests, "get", lambda *args, **kwargs: DummyResponse())

    ok, message = agent.check_server_connection("http://localhost:8000")

    assert ok is True
    assert "OK" in message


def test_server_connection_helper_failure(monkeypatch) -> None:
    def raising_get(*args, **kwargs):
        raise agent.requests.RequestException("boom")

    monkeypatch.setattr(agent.requests, "get", raising_get)

    ok, message = agent.check_server_connection("http://localhost:8000")

    assert ok is False
    assert "boom" in message


def test_detect_restore_intent_returns_false_when_no_changes() -> None:
    ok, reason = agent.detect_restore_intent(
        user_input="방금 한 작업이 좀 이상해",
        recent_changes="복구 가능한 변경 내역이 없습니다.",
        base_url="http://localhost:8000",
        model="dummy",
    )

    assert ok is False
    assert reason == "recent_changes_empty"


def test_working_memory_is_saved_after_run(monkeypatch) -> None:
    _reset_agent_state()

    class DummyApp:
        def invoke(self, state, config=None):
            return {"messages": state["messages"] + [AIMessage(content="메모 저장 응답")]}

    monkeypatch.setattr(agent, "build_agent", lambda base_url, model: DummyApp())
    monkeypatch.setattr(agent, "detect_restore_intent", lambda **kwargs: (False, "normal"))
    monkeypatch.setattr(agent.show_last_changes, "func", lambda limit=3: "id: 123\nfiles: foo.py")

    coding_agent = agent.CodingAgent(base_url="http://localhost:8000", model="dummy")
    answer = coding_agent.run("foo.py를 수정해")

    assert answer == "메모 저장 응답"
    memory = json.loads((PROJECT_ROOT / ".agent_state" / "working_memory.json").read_text(encoding="utf-8"))
    assert memory["current_task"] == "foo.py를 수정해"
    assert "foo.py" in memory["recent_changes"]
    assert memory["last_response"] == "메모 저장 응답"


def test_recent_verification_is_saved_from_run_command(monkeypatch) -> None:
    _reset_agent_state()

    class DummyApp:
        def invoke(self, state, config=None):
            callbacks = config["callbacks"]
            callbacks[0].on_tool_start({"name": "run_command"}, "pytest -q")
            callbacks[0].on_tool_end("exit_code: 0\ncwd: /tmp\nstdout:\npassed\n\nstderr:\n(없음)")
            return {"messages": state["messages"] + [AIMessage(content="검증 완료")]}

    monkeypatch.setattr(agent, "build_agent", lambda base_url, model: DummyApp())
    monkeypatch.setattr(agent, "detect_restore_intent", lambda **kwargs: (False, "normal"))
    monkeypatch.setattr(agent.show_last_changes, "func", lambda limit=3: "복구 가능한 변경 내역이 없습니다.")

    coding_agent = agent.CodingAgent(base_url="http://localhost:8000", model="dummy")
    coding_agent.run("테스트 돌려")

    memory = json.loads((PROJECT_ROOT / ".agent_state" / "working_memory.json").read_text(encoding="utf-8"))
    assert memory["recent_verification"] == "exit_code: 0"
    assert memory["recent_tools"][-1]["tool"] == "run_command"


def test_history_is_compacted_when_it_grows(monkeypatch) -> None:
    _reset_agent_state()

    class DummyApp:
        def invoke(self, state, config=None):
            return {"messages": state["messages"] + [AIMessage(content="짧은 응답")]}

    monkeypatch.setattr(agent, "build_agent", lambda base_url, model: DummyApp())
    monkeypatch.setattr(agent, "detect_restore_intent", lambda **kwargs: (False, "normal"))
    monkeypatch.setattr(agent.show_last_changes, "func", lambda limit=3: "복구 가능한 변경 내역이 없습니다.")

    coding_agent = agent.CodingAgent(base_url="http://localhost:8000", model="dummy")
    for i in range(8):
        coding_agent.run(f"요청 {i}")

    assert len(coding_agent.history) <= 1 + 1 + agent.MAX_HISTORY_MESSAGES
    assert isinstance(coding_agent.history[1], SystemMessage)
    assert str(coding_agent.history[1].content).startswith(agent.SUMMARY_PREFIX)

    session_summary = (PROJECT_ROOT / ".agent_state" / "session_summary.md").read_text(encoding="utf-8")
    assert "Compact Summary" in session_summary
