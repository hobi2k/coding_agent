from __future__ import annotations

from pathlib import Path
import shutil

from coding_agent import tools
from coding_agent.config import PROJECT_ROOT
from coding_agent.workspace import set_active_workspace


def _call(tool, *args, **kwargs):
    return tool.func(*args, **kwargs)


def _workspace_tmp(name: str) -> Path:
    set_active_workspace(str(PROJECT_ROOT))
    path = PROJECT_ROOT / ".tmp_tests" / name
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cleanup_agent_state() -> None:
    set_active_workspace(str(PROJECT_ROOT))
    state_dir = PROJECT_ROOT / ".agent_state"
    if state_dir.exists():
        shutil.rmtree(state_dir)


def test_read_write_edit_and_list_files_round_trip() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("round_trip")
    target = tmp_path / "nested" / "sample.txt"

    assert "저장 완료" in _call(tools.write_file, str(target), "hello\nworld")
    assert target.read_text(encoding="utf-8") == "hello\nworld"

    content = _call(tools.read_file, str(target))
    assert "파일:" in content
    assert "hello\nworld" in content
    assert "편집 완료" in _call(tools.edit_file, str(target), "world", "agent")
    assert "hello\nagent" in _call(tools.read_file, str(target))

    listing = _call(tools.list_files, str(tmp_path))
    assert "nested/" in listing


def test_read_file_range_support() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("ranges")
    target = tmp_path / "range.txt"
    target.write_text("line-1\nline-2\nline-3\nline-4\n", encoding="utf-8")

    content = _call(tools.read_file, str(target), 2, 3)

    assert "줄 범위: 2-3" in content
    assert "line-2" in content
    assert "line-3" in content
    assert "line-1" not in content


def test_read_file_truncates_long_files() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("long")
    target = tmp_path / "long.txt"
    target.write_text("\n".join(f"line-{i}" for i in range(320)), encoding="utf-8")

    content = _call(tools.read_file, str(target))

    assert "line-0" in content
    assert "line-299" in content
    assert "line-300" not in content
    assert "20줄 생략" in content


def test_replace_block_and_search_helpers() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("search")
    target = tmp_path / "notes.txt"
    target.write_text("alpha\nbeta\ngamma\n", encoding="utf-8")

    assert "블록 교체 완료" in _call(
        tools.replace_block, str(target), 2, 3, "BETA\nDELTA"
    )
    assert "notes.txt" in _call(tools.find_files, "*.txt", str(tmp_path))
    search_result = _call(tools.search_in_files, "DELTA", str(tmp_path))
    assert "notes.txt:3: DELTA" in search_result


def test_run_command_returns_structured_output() -> None:
    _cleanup_agent_state()
    result = _call(tools.run_command, "printf 'hello\\n'", ".")

    assert isinstance(result, str)
    assert "exit_code: 0" in result
    assert "cwd:" in result
    assert "stdout:" in result
    assert "hello" in result


def test_workspace_boundary_is_enforced() -> None:
    _cleanup_agent_state()
    result = _call(tools.read_file, "../README.md")
    assert "workspace 밖 접근" in result


def test_show_last_changes_and_restore_last_changes() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("restore")
    target = tmp_path / "restore.txt"

    _call(tools.write_file, str(target), "before\n")
    _call(tools.edit_file, str(target), "before", "after")

    changes = _call(tools.show_last_changes, 2)
    assert "restore.txt" in changes
    assert "edit_file" in changes
    assert "복구 가능" in changes

    result = _call(tools.restore_last_changes, 1)
    assert "복구 완료" in result
    assert target.read_text(encoding="utf-8") == "before\n"


def test_restore_can_remove_newly_created_file() -> None:
    _cleanup_agent_state()
    tmp_path = _workspace_tmp("restore_new_file")
    target = tmp_path / "created.txt"

    _call(tools.write_file, str(target), "created\n")
    assert target.exists()

    result = _call(tools.restore_last_changes, 1)
    assert "복구 완료" in result
    assert not target.exists()
