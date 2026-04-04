from __future__ import annotations

import json
import shutil
from pathlib import Path

from coding_agent.config import PROJECT_ROOT
from coding_agent import workspace


def _reset_registry() -> None:
    state_dir = PROJECT_ROOT / ".agent_state"
    if state_dir.exists():
        shutil.rmtree(state_dir)


def test_default_registry_points_to_project_root() -> None:
    _reset_registry()

    registry = workspace.load_workspace_registry()

    assert registry["active"] == str(PROJECT_ROOT.resolve())
    assert registry["workspaces"][0]["path"] == str(PROJECT_ROOT.resolve())


def test_add_and_switch_workspace(tmp_path: Path) -> None:
    _reset_registry()
    target = tmp_path / "other_project"
    target.mkdir()

    ok, message = workspace.add_workspace(str(target))
    assert ok is True
    assert "workspace 추가됨" in message

    ok, message = workspace.set_active_workspace(str(target))
    assert ok is True
    assert "활성 workspace 변경됨" in message
    assert workspace.get_active_workspace() == target.resolve()


def test_format_workspaces_marks_active(tmp_path: Path) -> None:
    _reset_registry()
    target = tmp_path / "proj"
    target.mkdir()

    workspace.add_workspace(str(target), name="proj")
    workspace.set_active_workspace("proj")

    output = workspace.format_workspaces()
    assert "* proj:" in output


def test_registry_file_is_saved() -> None:
    _reset_registry()

    registry = workspace.load_workspace_registry()
    path = PROJECT_ROOT / ".agent_state" / "workspaces.json"

    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8"))["active"] == registry["active"]


def test_ensure_workspace_adds_and_activates(tmp_path: Path) -> None:
    _reset_registry()
    target = tmp_path / "current_project"
    target.mkdir()

    ok, message = workspace.ensure_workspace(str(target))

    assert ok is True
    assert "활성 workspace 변경됨" in message
    assert workspace.get_active_workspace() == target.resolve()


def test_ensure_workspace_reuses_existing_entry(tmp_path: Path) -> None:
    _reset_registry()
    target = tmp_path / "reuse_project"
    target.mkdir()
    workspace.add_workspace(str(target))

    ok, message = workspace.ensure_workspace(str(target))

    assert ok is True
    assert "활성 workspace 변경됨" in message
    assert workspace.get_active_workspace() == target.resolve()
