"""활성 workspace와 등록된 작업 디렉터리를 관리한다."""

from __future__ import annotations

import json
from pathlib import Path

from coding_agent.config import PROJECT_ROOT


def _registry_dir() -> Path:
    """workspace 레지스트리 디렉터리를 반환한다.

    Returns:
        중앙 `.agent_state` 디렉터리 경로.
    """
    path = PROJECT_ROOT / ".agent_state"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _registry_path() -> Path:
    """workspace 레지스트리 파일 경로를 반환한다.

    Returns:
        `workspaces.json` 파일 경로.
    """
    return _registry_dir() / "workspaces.json"


def _default_registry() -> dict:
    """기본 workspace 레지스트리를 반환한다.

    Returns:
        기본 레지스트리 딕셔너리.
    """
    root = str(PROJECT_ROOT.resolve())
    return {
        "active": root,
        "workspaces": [
            {
                "name": PROJECT_ROOT.name,
                "path": root,
            }
        ],
    }


def load_workspace_registry() -> dict:
    """workspace 레지스트리를 읽는다.

    Returns:
        현재 workspace 레지스트리 딕셔너리.
    """
    path = _registry_path()
    if not path.exists():
        registry = _default_registry()
        save_workspace_registry(registry)
        return registry
    try:
        registry = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        registry = _default_registry()
        save_workspace_registry(registry)
        return registry

    if "active" not in registry or "workspaces" not in registry:
        registry = _default_registry()
        save_workspace_registry(registry)
    return registry


def save_workspace_registry(registry: dict) -> None:
    """workspace 레지스트리를 저장한다.

    Args:
        registry: 저장할 workspace 레지스트리.
    """
    _registry_path().write_text(
        json.dumps(registry, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def get_active_workspace() -> Path:
    """현재 활성 workspace를 반환한다.

    Returns:
        현재 활성 workspace 절대 경로.
    """
    registry = load_workspace_registry()
    return Path(registry["active"]).resolve()


def list_workspaces() -> list[dict]:
    """등록된 workspace 목록을 반환한다.

    Returns:
        등록된 workspace 정보 목록.
    """
    return load_workspace_registry()["workspaces"]


def add_workspace(path: str, name: str | None = None) -> tuple[bool, str]:
    """새 workspace를 등록한다.

    Args:
        path: 등록할 디렉터리 경로.
        name: 표시용 이름. 없으면 폴더 이름을 사용한다.

    Returns:
        성공 여부와 결과 메시지.
    """
    target = Path(path).expanduser().resolve()
    if not target.exists():
        return False, f"디렉터리가 없습니다: {target}"
    if not target.is_dir():
        return False, f"디렉터리가 아닙니다: {target}"

    registry = load_workspace_registry()
    existing = next((item for item in registry["workspaces"] if item["path"] == str(target)), None)
    if existing:
        return True, f"이미 등록된 workspace입니다: {existing['name']} -> {existing['path']}"

    workspace_name = name or target.name
    registry["workspaces"].append({"name": workspace_name, "path": str(target)})
    save_workspace_registry(registry)
    return True, f"workspace 추가됨: {workspace_name} -> {target}"


def set_active_workspace(identifier: str) -> tuple[bool, str]:
    """활성 workspace를 변경한다.

    Args:
        identifier: workspace 이름 또는 경로.

    Returns:
        성공 여부와 결과 메시지.
    """
    registry = load_workspace_registry()
    target_path = str(Path(identifier).expanduser().resolve())

    workspace = next(
        (
            item for item in registry["workspaces"]
            if item["name"] == identifier or item["path"] == target_path
        ),
        None,
    )
    if workspace is None:
        return False, f"등록되지 않은 workspace입니다: {identifier}"

    registry["active"] = workspace["path"]
    save_workspace_registry(registry)
    return True, f"활성 workspace 변경됨: {workspace['name']} -> {workspace['path']}"


def format_workspaces() -> str:
    """등록된 workspace 목록을 사람이 읽기 쉽게 포맷한다.

    Returns:
        workspace 목록 문자열.
    """
    registry = load_workspace_registry()
    active = registry["active"]
    lines = []
    for item in registry["workspaces"]:
        marker = "*" if item["path"] == active else "-"
        lines.append(f"{marker} {item['name']}: {item['path']}")
    return "\n".join(lines)
