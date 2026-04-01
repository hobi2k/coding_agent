"""
LangChain @tool 형식으로 정의한 도구 모음.
LangGraph 에이전트가 직접 바인딩해서 사용.

도구 목록:
  read_file    - 파일 읽기
  write_file   - 파일 생성/덮어쓰기
  edit_file    - 특정 문자열 찾아 교체 (부분 편집)
  list_files   - 디렉토리 목록
  run_command  - 터미널 명령 실행
  web_search   - DuckDuckGo 웹 검색
"""

import subprocess
from pathlib import Path
from langchain_core.tools import tool
from coding_agent.config import IS_WINDOWS, IS_WSL, windows_to_wsl_path


# ── 경로 정규화 ───────────────────────────────────────

def _normalize(path: str) -> str:
    """WSL 환경에서 Windows 경로(C:\\...)를 WSL 경로로 변환."""
    if IS_WSL and len(path) >= 2 and path[1] == ":":
        return windows_to_wsl_path(path)
    return path


# ── 파일 도구 ─────────────────────────────────────────

@tool
def read_file(path: str) -> str:
    """파일 내용을 읽어 반환한다. 긴 파일은 앞 300줄만 반환."""
    path = _normalize(path)
    try:
        content = Path(path).read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) > 300:
            content = "\n".join(lines[:300]) + f"\n\n... ({len(lines) - 300}줄 생략)"
        return content
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def write_file(path: str, content: str) -> str:
    """파일에 내용을 쓴다. 없으면 생성, 있으면 전체 덮어쓰기."""
    path = _normalize(path)
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ 저장 완료: {path} ({len(content.encode())} bytes)"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def edit_file(path: str, old_str: str, new_str: str) -> str:
    """파일에서 old_str을 찾아 new_str로 교체한다 (부분 편집).
    old_str은 파일 내에서 정확히 1회만 등장해야 한다."""
    path = _normalize(path)
    try:
        content = Path(path).read_text(encoding="utf-8")
        count = content.count(old_str)
        if count == 0:
            return f"ERROR: 해당 문자열을 찾을 수 없음:\n{old_str}"
        if count > 1:
            return (
                f"ERROR: 동일한 문자열이 {count}곳에 존재. "
                "더 많은 컨텍스트를 포함해 old_str을 더 구체적으로 지정하세요."
            )
        new_content = content.replace(old_str, new_str, 1)
        Path(path).write_text(new_content, encoding="utf-8")
        return f"✅ 편집 완료: {path}"
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except Exception as e:
        return f"ERROR: {e}"


@tool
def list_files(path: str = ".") -> str:
    """디렉토리의 파일과 폴더 목록을 반환한다."""
    path = _normalize(path)
    try:
        entries = []
        for item in sorted(Path(path).iterdir()):
            if item.is_dir():
                entries.append(f"📁 {item.name}/")
            else:
                size = item.stat().st_size
                entries.append(f"📄 {item.name} ({size:,} bytes)")
        return "\n".join(entries) if entries else "(비어있음)"
    except FileNotFoundError:
        return f"ERROR: 디렉토리 없음 — {path}"
    except Exception as e:
        return f"ERROR: {e}"


# ── 터미널 도구 ───────────────────────────────────────

@tool
def run_command(command: str) -> str:
    """터미널 명령어를 실행하고 stdout/stderr를 반환한다. 타임아웃 30초."""
    cmd = ["powershell", "-Command", command] if IS_WINDOWS else ["bash", "-c", command]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "(출력 없음)"
        return output[:3000] + "\n... (이하 생략)" if len(output) > 3000 else output
    except subprocess.TimeoutExpired:
        return "ERROR: 30초 타임아웃 초과"
    except Exception as e:
        return f"ERROR: {e}"


# ── 웹 검색 도구 ──────────────────────────────────────

@tool
def web_search(query: str) -> str:
    """DuckDuckGo로 웹을 검색하고 상위 결과를 반환한다."""
    try:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                results.append(
                    f"제목: {r['title']}\n"
                    f"URL: {r['href']}\n"
                    f"요약: {r['body']}\n"
                )
        return "\n---\n".join(results) if results else "검색 결과 없음"
    except Exception as e:
        return f"ERROR: 웹 검색 실패 — {e}"


# ── 도구 목록 (LangGraph 바인딩용) ───────────────────

TOOLS = [
    read_file,
    write_file,
    edit_file,
    list_files,
    run_command,
    web_search,
]