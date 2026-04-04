"""대화형 코딩 에이전트 CLI를 제공한다."""

import argparse
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

from coding_agent.config import API_BASE, DEFAULT_MODEL, PLATFORM_NAME
from coding_agent.agent import CodingAgent, check_server_connection
from coding_agent.workspace import (
    add_workspace,
    ensure_workspace,
    format_workspaces,
    get_active_workspace,
    set_active_workspace,
)

console = Console()


def on_tool_call(name: str, args):
    """도구 호출 로그를 출력한다.

    Args:
        name: 호출된 도구 이름.
        args: 도구 입력 인자.
    """
    args_str = str(args)[:80]
    console.print(f"  [yellow]🔧 {name}[/yellow]([dim]{args_str}[/dim])")


def on_tool_result(result: str):
    """도구 실행 결과 미리보기를 출력한다.

    Args:
        result: 도구가 반환한 문자열 결과.
    """
    preview = result.strip().replace("\n", " ")[:160]
    if len(result.strip()) > 160:
        preview += "..."
    console.print(f"  [dim]↳ {preview}[/dim]")


def render_status(url: str):
    """서버 연결 상태를 출력한다.

    Args:
        url: 점검할 서버 주소.
    """
    ok, message = check_server_connection(url)
    status = Text()
    status.append("서버상태: ", style="dim")
    status.append("연결됨", style="green" if ok else "red")
    status.append(f" ({message})", style="dim")
    console.print(status)
    console.print(f"[dim]active workspace: {get_active_workspace()}[/dim]")


def _history_path() -> str:
    """현재 활성 workspace의 히스토리 파일 경로를 반환한다.

    Returns:
        `.agent_history` 파일 경로 문자열.
    """
    return str(get_active_workspace() / ".agent_history")


def _handle_slash_command(user_input: str, agent: CodingAgent) -> tuple[bool, CodingAgent]:
    """CLI slash 명령을 처리한다.

    Args:
        user_input: 사용자가 입력한 원문.
        agent: 현재 에이전트 인스턴스.

    Returns:
        처리 여부와 이후 사용할 에이전트 인스턴스.
    """
    if user_input.startswith("/add_dir "):
        target = user_input[len("/add_dir "):].strip()
        ok, message = add_workspace(target)
        style = "green" if ok else "red"
        console.print(f"[{style}]{message}[/{style}]")
        return True, agent

    if user_input.startswith("/use_dir "):
        target = user_input[len("/use_dir "):].strip()
        ok, message = set_active_workspace(target)
        style = "green" if ok else "red"
        console.print(f"[{style}]{message}[/{style}]")
        if ok:
            agent = CodingAgent(base_url=agent.base_url, model=agent.model)
            console.print("[green]✅ workspace 전환에 맞춰 세션을 새로 열었습니다.[/green]")
        return True, agent

    if user_input == "/workspaces":
        console.print(format_workspaces())
        return True, agent

    return False, agent


def main():
    """대화형 코딩 에이전트 CLI를 실행한다."""
    parser = argparse.ArgumentParser(description="로컬 코딩 에이전트")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--url",   default=API_BASE)
    parser.add_argument(
        "--workspace",
        default=".",
        help="시작할 작업 디렉터리. 기본값은 현재 폴더.",
    )
    args = parser.parse_args()

    ok, message = ensure_workspace(args.workspace)
    if not ok:
        console.print(f"[red]{message}[/red]")
        raise SystemExit(1)

    console.print(Panel.fit(
        f"[bold cyan]🤖 로컬 코딩 에이전트[/bold cyan]\n"
        f"[dim]플랫폼 : {PLATFORM_NAME}[/dim]\n"
        f"[dim]모델   : {args.model}[/dim]\n"
        f"[dim]서버   : {args.url}[/dim]\n"
        f"[dim]작업폴더: {Path(get_active_workspace())}[/dim]\n"
        f"[dim]도구   : read/write/edit/replace_block · list/find/search · change-log/restore · run_command · web_search[/dim]\n"
        f"[dim]명령어 : reset · status · help · exit · /add_dir · /use_dir · /workspaces[/dim]",
        border_style="cyan",
    ))
    if message:
        console.print(f"[dim]{message}[/dim]")
    render_status(args.url)

    agent   = CodingAgent(base_url=args.url, model=args.model)

    while True:
        try:
            user_input = prompt("You> ", history=FileHistory(_history_path())).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]👋 종료합니다[/dim]")
            break

        if not user_input:
            continue

        handled, agent = _handle_slash_command(user_input, agent)
        if handled:
            console.print()
            continue

        match user_input.lower():
            case "exit" | "quit" | "종료":
                console.print("[dim]👋 종료합니다[/dim]")
                break
            case "reset" | "초기화":
                agent.reset()
                console.print("[green]✅ 대화 초기화됨[/green]\n")
                continue
            case "help" | "도움말":
                console.print(
                    "\n[bold]명령어[/bold]\n"
                    "  /add_dir <path> - 작업 디렉터리 등록\n"
                    "  /use_dir <name|path> - 활성 workspace 전환\n"
                    "  /workspaces - 등록된 workspace 목록 확인\n"
                    "  status - 서버 연결 상태 확인\n"
                    "  reset  - 대화 히스토리 초기화\n"
                    "  help   - 도움말\n"
                    "  exit   - 종료\n"
                )
                continue
            case "status" | "상태":
                render_status(args.url)
                console.print()
                continue

        console.print("[dim]🤔 처리 중...[/dim]")
        try:
            answer = agent.run(
                user_input,
                on_tool_call=on_tool_call,
                on_tool_result=on_tool_result,
            )
            console.print(Panel(
                Markdown(answer),
                title="[cyan]에이전트[/cyan]",
                border_style="cyan",
                padding=(0, 1),
            ))
        except RuntimeError as e:
            console.print(Panel(str(e), title="[red]연결 오류[/red]", border_style="red"))
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ 중단됨[/yellow]\n")
        except Exception as e:
            console.print(f"[red]❌ 오류: {e}[/red]")

        console.print()


if __name__ == "__main__":
    main()
