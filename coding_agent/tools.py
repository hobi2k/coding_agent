"""LangGraph 에이전트가 사용하는 도구 모음을 정의한다."""

from __future__ import annotations

import fnmatch
import json
import subprocess
import uuid
from pathlib import Path
from datetime import datetime, timezone

from langchain_core.tools import tool

from coding_agent.config import (
    IS_WINDOWS,
    IS_WSL,
    windows_to_wsl_path,
)
from coding_agent.workspace import get_active_workspace


MAX_FILE_LINES = 300
MAX_COMMAND_OUTPUT = 3000
DEFAULT_SEARCH_RESULTS = 50
RECOVERY_HISTORY_LIMIT = 20
BLOCKED_COMMAND_SNIPPETS = (
    "rm -rf /",
    "rm -rf ~",
    "sudo ",
    " shutdown",
    "reboot",
    "mkfs",
    "dd if=",
    "git reset --hard",
)


def _normalize(path: str) -> str:
    """필요하면 Windows 경로를 WSL 경로로 변환한다.

    Args:
        path: 정규화할 경로 문자열.

    Returns:
        현재 런타임에서 사용할 경로 문자열.
    """
    if IS_WSL and len(path) >= 2 and path[1] == ":":
        return windows_to_wsl_path(path)
    return path


def _workspace_root() -> Path:
    """workspace 루트 경로를 반환한다.

    Returns:
        프로젝트 루트 경로.
    """
    return get_active_workspace().resolve()


def _resolve_path(path: str) -> Path:
    """경로를 workspace 내부 절대 경로로 변환한다.

    Args:
        path: 사용자가 전달한 경로 문자열.

    Returns:
        workspace 내부 절대 경로.
    """
    raw = Path(_normalize(path)).expanduser()
    resolved = (raw if raw.is_absolute() else _workspace_root() / raw).resolve()
    root = _workspace_root()

    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise PermissionError(
            f"workspace 밖 접근은 허용되지 않습니다: {resolved}"
        ) from exc

    return resolved


def _truncate(text: str, limit: int = MAX_COMMAND_OUTPUT) -> str:
    """긴 문자열을 지정 길이로 자른다.

    Args:
        text: 원본 문자열.
        limit: 최대 문자 수.

    Returns:
        잘린 문자열.
    """
    if len(text) <= limit:
        return text
    return text[:limit] + "\n... (이하 생략)"


def _format_path(path: Path) -> str:
    """경로를 workspace 기준 상대 경로로 포맷한다.

    Args:
        path: 포맷할 경로.

    Returns:
        상대 경로 또는 원래 경로 문자열.
    """
    try:
        return str(path.relative_to(_workspace_root()))
    except ValueError:
        return str(path)


def _iter_files(root: Path):
    """workspace 내부 파일을 순회한다.

    Args:
        root: 순회 시작 경로.

    Returns:
        파일 경로 이터레이터.
    """
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part.startswith(".git") or part == ".agent_state" for part in path.parts):
            continue
        yield path


def _state_dir() -> Path:
    """상태 저장 디렉터리를 반환한다.

    Returns:
        `.agent_state` 디렉터리 경로.
    """
    return _workspace_root() / ".agent_state"


def _recovery_dir() -> Path:
    """복구 스냅샷 디렉터리를 반환한다.

    Returns:
        복구 스냅샷 저장 디렉터리 경로.
    """
    path = _state_dir() / "recovery"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _recovery_index_path() -> Path:
    """복구 인덱스 파일 경로를 반환한다.

    Returns:
        `recovery_index.json` 경로.
    """
    _state_dir().mkdir(parents=True, exist_ok=True)
    return _state_dir() / "recovery_index.json"


def _load_recovery_index() -> list[dict]:
    """복구 인덱스 파일을 읽는다.

    Returns:
        복구 이력 목록.
    """
    path = _recovery_index_path()
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_recovery_index(entries: list[dict]) -> None:
    """복구 인덱스를 저장한다.

    Args:
        entries: 저장할 복구 이력 목록.
    """
    path = _recovery_index_path()
    path.write_text(
        json.dumps(entries[-RECOVERY_HISTORY_LIMIT:], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _backup_name(tx_id: str, relpath: str) -> str:
    """복구 백업 파일 이름을 만든다.

    Args:
        tx_id: 복구 트랜잭션 ID.
        relpath: 대상 파일 상대 경로.

    Returns:
        백업 파일 이름.
    """
    safe = relpath.replace("/", "__").replace("\\", "__")
    return f"{tx_id}__{safe}.bak"


def _record_recovery(action: str, file_path: Path, previous_content: str | None, existed_before: bool) -> None:
    """복구 이력을 기록한다.

    Args:
        action: 수행한 도구 이름.
        file_path: 변경된 파일 경로.
        previous_content: 변경 전 파일 내용.
        existed_before: 변경 전 파일 존재 여부.
    """
    relpath = _format_path(file_path)
    tx_id = uuid.uuid4().hex
    entry = {
        "id": tx_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "files": [
            {
                "path": relpath,
                "existed_before": existed_before,
                "backup": None,
            }
        ],
        "restored": False,
    }

    if existed_before and previous_content is not None:
        backup_path = _recovery_dir() / _backup_name(tx_id, relpath)
        backup_path.write_text(previous_content, encoding="utf-8")
        entry["files"][0]["backup"] = str(backup_path)

    entries = _load_recovery_index()
    entries.append(entry)
    _save_recovery_index(entries)


def _prepare_file_write(path: str) -> tuple[Path, str | None, bool]:
    """파일 변경 전 상태를 읽는다.

    Args:
        path: 변경할 파일 경로.

    Returns:
        정규화된 파일 경로, 이전 내용, 기존 존재 여부.
    """
    file_path = _resolve_path(path)
    existed_before = file_path.exists()
    previous_content = None
    if existed_before:
        previous_content = file_path.read_text(encoding="utf-8")
    return file_path, previous_content, existed_before


@tool
def read_file(path: str, start_line: int = 1, end_line: int = 0) -> str:
    """파일 내용을 읽는다.

    Args:
        path: 읽을 파일 경로.
        start_line: 시작 줄 번호.
        end_line: 끝 줄 번호. `0`이면 자동으로 일부만 읽는다.

    Returns:
        파일 경로, 줄 범위, 본문이 포함된 문자열.
    """
    try:
        file_path = _resolve_path(path)
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()
        total = len(lines)

        if total == 0:
            return f"파일: {_format_path(file_path)}\n줄 수: 0\n내용 없음"

        if start_line < 1:
            return "ERROR: start_line은 1 이상이어야 합니다."

        if end_line and end_line < start_line:
            return "ERROR: end_line은 start_line 이상이거나 0이어야 합니다."

        start_idx = start_line - 1
        if start_idx >= total:
            return f"ERROR: start_line({start_line})이 전체 줄 수({total})를 초과합니다."

        if end_line == 0:
            end_idx = min(total, start_idx + MAX_FILE_LINES)
        else:
            end_idx = min(total, end_line)

        selected = lines[start_idx:end_idx]
        body = "\n".join(selected)
        omitted = total - end_idx
        suffix = f"\n\n... ({omitted}줄 생략)" if omitted > 0 and end_line == 0 else ""
        return (
            f"파일: {_format_path(file_path)}\n"
            f"줄 범위: {start_line}-{end_idx} / 총 {total}줄\n\n"
            f"{body}{suffix}"
        )
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except PermissionError as e:
        return f"ERROR: {e}"
    except UnicodeDecodeError:
        return f"ERROR: 텍스트 파일로 읽을 수 없음 — {path}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """파일에 내용을 저장한다.

    Args:
        path: 저장할 파일 경로.
        content: 저장할 텍스트 내용.

    Returns:
        저장 결과 문자열.
    """
    if "\x00" in content:
        return "ERROR: 바이너리 데이터 쓰기는 지원하지 않습니다."

    try:
        file_path, previous_content, existed_before = _prepare_file_write(path)
        _record_recovery("write_file", file_path, previous_content, existed_before)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return (
            f"✅ 저장 완료\n"
            f"파일: {_format_path(file_path)}\n"
            f"크기: {len(content.encode('utf-8'))} bytes"
        )
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def edit_file(path: str, old_str: str, new_str: str) -> str:
    """파일에서 특정 문자열을 치환한다.

    Args:
        path: 수정할 파일 경로.
        old_str: 기존 문자열.
        new_str: 새 문자열.

    Returns:
        편집 결과 문자열.
    """
    try:
        file_path, content, existed_before = _prepare_file_write(path)
        if not existed_before or content is None:
            return f"ERROR: 파일 없음 — {path}"
        count = content.count(old_str)
        if count == 0:
            return f"ERROR: 해당 문자열을 찾을 수 없음:\n{old_str}"
        if count > 1:
            return (
                f"ERROR: 동일한 문자열이 {count}곳에 존재합니다. "
                "주변 문맥을 더 포함해 old_str을 구체화하거나 replace_block을 사용하세요."
            )

        _record_recovery("edit_file", file_path, content, existed_before)
        new_content = content.replace(old_str, new_str, 1)
        file_path.write_text(new_content, encoding="utf-8")
        return (
            f"✅ 편집 완료\n"
            f"파일: {_format_path(file_path)}\n"
            f"변경 전 길이: {len(old_str)} chars\n"
            f"변경 후 길이: {len(new_str)} chars"
        )
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def replace_block(path: str, start_line: int, end_line: int, content: str) -> str:
    """줄 범위를 기준으로 블록을 교체한다.

    Args:
        path: 수정할 파일 경로.
        start_line: 시작 줄 번호.
        end_line: 끝 줄 번호.
        content: 새 블록 내용.

    Returns:
        블록 교체 결과 문자열.
    """
    if start_line < 1 or end_line < start_line:
        return "ERROR: start_line/end_line 범위가 올바르지 않습니다."

    try:
        file_path, original, existed_before = _prepare_file_write(path)
        if not existed_before or original is None:
            return f"ERROR: 파일 없음 — {path}"
        lines = original.splitlines()
        total = len(lines)

        if end_line > total:
            return f"ERROR: end_line({end_line})이 전체 줄 수({total})를 초과합니다."

        _record_recovery("replace_block", file_path, original, existed_before)
        replacement = content.splitlines()
        new_lines = lines[: start_line - 1] + replacement + lines[end_line:]
        trailing_newline = original.endswith("\n")
        new_text = "\n".join(new_lines) + ("\n" if trailing_newline else "")
        file_path.write_text(new_text, encoding="utf-8")
        return (
            f"✅ 블록 교체 완료\n"
            f"파일: {_format_path(file_path)}\n"
            f"교체 범위: {start_line}-{end_line}\n"
            f"새 블록 줄 수: {len(replacement)}"
        )
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def list_files(path: str = ".") -> str:
    """디렉터리 목록을 반환한다.

    Args:
        path: 조회할 디렉터리 경로.

    Returns:
        디렉터리 목록 문자열.
    """
    try:
        dir_path = _resolve_path(path)
        if not dir_path.is_dir():
            return f"ERROR: 디렉터리가 아님 — {path}"

        entries = []
        for item in sorted(dir_path.iterdir()):
            label = f"{item.name}/" if item.is_dir() else item.name
            prefix = "📁" if item.is_dir() else "📄"
            suffix = "" if item.is_dir() else f" ({item.stat().st_size:,} bytes)"
            entries.append(f"{prefix} {label}{suffix}")

        return "\n".join(entries) if entries else "(비어있음)"
    except FileNotFoundError:
        return f"ERROR: 디렉터리 없음 — {path}"
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def find_files(pattern: str, root: str = ".") -> str:
    """파일명을 패턴으로 검색한다.

    Args:
        pattern: glob 패턴.
        root: 검색 시작 디렉터리.

    Returns:
        검색 결과 문자열.
    """
    try:
        root_path = _resolve_path(root)
        matches = []
        for path in _iter_files(root_path):
            if fnmatch.fnmatch(path.name, pattern):
                matches.append(_format_path(path))
            if len(matches) >= DEFAULT_SEARCH_RESULTS:
                break

        if not matches:
            return f"검색 결과 없음: pattern={pattern}"
        return "\n".join(matches)
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def search_in_files(query: str, root: str = ".") -> str:
    """파일 내용에서 문자열을 검색한다.

    Args:
        query: 찾을 문자열.
        root: 검색 시작 디렉터리.

    Returns:
        파일 경로와 줄 번호를 포함한 검색 결과 문자열.
    """
    if not query.strip():
        return "ERROR: query가 비어 있습니다."

    try:
        root_path = _resolve_path(root)
        results = []

        for path in _iter_files(root_path):
            try:
                for lineno, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if query in line:
                        results.append(f"{_format_path(path)}:{lineno}: {line.strip()}")
                        if len(results) >= DEFAULT_SEARCH_RESULTS:
                            return "\n".join(results)
            except UnicodeDecodeError:
                continue

        return "\n".join(results) if results else f"검색 결과 없음: query={query}"
    except PermissionError as e:
        return f"ERROR: {e}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def show_last_changes(limit: int = 5) -> str:
    """최근 변경 이력을 보여준다.

    Args:
        limit: 표시할 최대 이력 수.

    Returns:
        최근 변경 이력 문자열.
    """
    if limit < 1:
        return "ERROR: limit은 1 이상이어야 합니다."

    entries = _load_recovery_index()
    if not entries:
        return "복구 가능한 변경 내역이 없습니다."

    lines = []
    for entry in reversed(entries[-limit:]):
        state = "복구됨" if entry.get("restored") else "복구 가능"
        files = ", ".join(file_info["path"] for file_info in entry["files"])
        lines.append(
            f"id: {entry['id']}\n"
            f"action: {entry['action']}\n"
            f"time: {entry['timestamp']}\n"
            f"files: {files}\n"
            f"state: {state}"
        )
    return "\n\n".join(lines)


@tool
def restore_last_changes(count: int = 1) -> str:
    """최근 변경을 복구한다.

    Args:
        count: 복구할 최근 변경 건수.

    Returns:
        복구 결과 문자열.
    """
    if count < 1:
        return "ERROR: count는 1 이상이어야 합니다."

    entries = _load_recovery_index()
    pending = [entry for entry in entries if not entry.get("restored")]
    if not pending:
        return "복구 가능한 변경 내역이 없습니다."

    to_restore_ids = {entry["id"] for entry in pending[-count:]}
    restored_files = []

    for entry in entries:
        if entry["id"] not in to_restore_ids or entry.get("restored"):
            continue

        for file_info in reversed(entry["files"]):
            file_path = _resolve_path(file_info["path"])
            if file_info["existed_before"]:
                backup_path = Path(file_info["backup"])
                original = backup_path.read_text(encoding="utf-8")
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(original, encoding="utf-8")
            else:
                if file_path.exists():
                    file_path.unlink()
            restored_files.append(file_info["path"])
        entry["restored"] = True

    _save_recovery_index(entries)
    return (
        f"복구 완료: {len(to_restore_ids)}건\n"
        f"대상 파일: {', '.join(restored_files) if restored_files else '(없음)'}"
    )


def _is_blocked_command(command: str) -> str | None:
    lowered = f" {command.lower()} "
    for snippet in BLOCKED_COMMAND_SNIPPETS:
        if snippet in lowered:
            return snippet.strip()
    return None


@tool
def run_command(command: str, cwd: str = ".") -> str:
    """workspace 내부 cwd에서 명령어를 실행하고 exit code/stdout/stderr를 반환한다."""
    blocked = _is_blocked_command(command)
    if blocked:
        return f"ERROR: 위험한 명령은 차단됩니다: {blocked}"

    try:
        resolved_cwd = _resolve_path(cwd)
    except PermissionError as e:
        return f"ERROR: {e}"

    if not resolved_cwd.is_dir():
        return f"ERROR: 작업 디렉터리가 아님 — {cwd}"

    cmd = ["powershell", "-Command", command] if IS_WINDOWS else ["bash", "-lc", command]
    try:
        result = subprocess.run(
            cmd,
            cwd=str(resolved_cwd),
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        stdout = _truncate(result.stdout.strip())
        stderr = _truncate(result.stderr.strip())
        stdout = stdout if stdout else "(없음)"
        stderr = stderr if stderr else "(없음)"
        return (
            f"exit_code: {result.returncode}\n"
            f"cwd: {resolved_cwd}\n"
            f"stdout:\n{stdout}\n\n"
            f"stderr:\n{stderr}"
        )
    except subprocess.TimeoutExpired:
        return "ERROR: 30초 타임아웃 초과"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def web_search(query: str) -> str:
    """DuckDuckGo로 웹을 검색하고 상위 결과를 반환한다."""
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for result in ddgs.text(query, max_results=5):
                results.append(
                    f"제목: {result['title']}\n"
                    f"URL: {result['href']}\n"
                    f"요약: {result['body']}\n"
                )
        return "\n---\n".join(results) if results else "검색 결과 없음"
    except Exception as e:
        return f"ERROR: 웹 검색 실패 — {e}"


TOOLS = [
    read_file,
    write_file,
    edit_file,
    replace_block,
    list_files,
    find_files,
    search_in_files,
    show_last_changes,
    restore_last_changes,
    run_command,
    web_search,
]
