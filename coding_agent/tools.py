"""
파일 읽기/쓰기, 터미널 실행 도구.
WSL / Windows / Linux 경로를 모두 처리.
"""

import subprocess
import os
import sys
import json
from pathlib import Path
from coding_agent.config import IS_WINDOWS, IS_WSL, windows_to_wsl_path


# ── 도구 설명 (프롬프트 삽입용) ───────────────────────

TOOL_DESCRIPTIONS = """
사용 가능한 도구:

1. read_file(path)            - 파일 내용 읽기
2. write_file(path, content)  - 파일 쓰기/생성
3. run_command(command)       - 터미널 명령 실행
4. list_files(path=".")       - 디렉토리 목록 확인

도구 호출 시 반드시 아래 JSON 형식으로만 응답하세요:
{"tool": "도구이름", "args": {"인자명": "값"}}

최종 답변은 JSON 없이 일반 텍스트로 작성하세요.
"""


# ── 경로 정규화 ───────────────────────────────────────

def _normalize_path(path: str) -> str:
    """
    WSL 환경에서 Windows 경로(C:\\...)가 들어오면 WSL 경로로 변환.
    그 외엔 그대로 반환.
    """
    if IS_WSL and len(path) >= 2 and path[1] == ":":
        return windows_to_wsl_path(path)
    return path


# ── 도구 구현 ─────────────────────────────────────────

def read_file(path: str) -> str:
    path = _normalize_path(path)
    try:
        content = Path(path).read_text(encoding="utf-8")
        lines = content.splitlines()
        if len(lines) > 300:
            content = "\n".join(lines[:300]) + f"\n... ({len(lines)-300}줄 생략)"
        return content
    except FileNotFoundError:
        return f"ERROR: 파일 없음 — {path}"
    except Exception as e:
        return f"ERROR: {e}"


def write_file(path: str, content: str) -> str:
    path = _normalize_path(path)
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ 저장 완료: {path} ({len(content.encode())} bytes)"
    except Exception as e:
        return f"ERROR: {e}"


def run_command(command: str, timeout: int = 30) -> str:
    """
    WSL: bash -c 로 실행
    Windows: PowerShell로 실행
    Linux: bash -c 로 실행
    """
    if IS_WINDOWS:
        cmd = ["powershell", "-Command", command]
    else:
        cmd = ["bash", "-c", command]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        output = (result.stdout + result.stderr).strip()
        if not output:
            return "(출력 없음)"
        if len(output) > 3000:
            output = output[:3000] + "\n... (이하 생략)"
        return output
    except subprocess.TimeoutExpired:
        return f"ERROR: {timeout}초 타임아웃 초과"
    except Exception as e:
        return f"ERROR: {e}"


def list_files(path: str = ".") -> str:
    path = _normalize_path(path)
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


# ── 도구 파싱 및 디스패처 ─────────────────────────────

TOOL_MAP = {
    "read_file":   read_file,
    "write_file":  write_file,
    "run_command": run_command,
    "list_files":  list_files,
}


def parse_tool_call(text: str) -> dict | None:
    """LLM 응답에서 {"tool": ..., "args": ...} JSON을 추출."""
    text = text.strip()

    # 마크다운 코드 펜스 안에 있는 경우
    if "```" in text:
        for block in text.split("```"):
            cleaned = block.strip().lstrip("json").strip()
            try:
                parsed = json.loads(cleaned)
                if "tool" in parsed:
                    return parsed
            except Exception:
                pass

    # 텍스트 전체가 JSON
    try:
        parsed = json.loads(text)
        if "tool" in parsed:
            return parsed
    except Exception:
        pass

    # 텍스트 안에 JSON이 섞인 경우 (중괄호 범위 탐색)
    start = text.find("{")
    while start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    try:
                        parsed = json.loads(text[start:i+1])
                        if "tool" in parsed:
                            return parsed
                    except Exception:
                        pass
                    break
        start = text.find("{", start + 1)

    return None


def execute_tool(call: dict) -> str:
    name = call.get("tool", "")
    args = call.get("args", {})
    fn   = TOOL_MAP.get(name)
    if not fn:
        return f"ERROR: 알 수 없는 도구 '{name}'. 사용 가능: {list(TOOL_MAP)}"
    try:
        return fn(**args)
    except TypeError as e:
        return f"ERROR: 인자 오류 — {e}"
    except Exception as e:
        return f"ERROR: {e}"
