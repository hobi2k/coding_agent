"""
코딩 에이전트 CLI.

사용법:
    uv run agent
    uv run agent --model bigatuna/Qwen3.5-9b-Sushi-Coder
    uv run agent --url http://localhost:8001
"""

import argparse

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory

from coding_agent.config import API_BASE, DEFAULT_MODEL, PLATFORM_NAME, PROJECT_ROOT
from coding_agent.agent import CodingAgent

console = Console()


def on_tool_call(name: str, args):
    args_str = str(args)[:80]
    console.print(f"  [yellow]🔧 {name}[/yellow]([dim]{args_str}[/dim])")


def on_tool_result(result: str):
    preview = result.strip().replace("\n", " ")[:160]
    if len(result.strip()) > 160:
        preview += "..."
    console.print(f"  [dim]↳ {preview}[/dim]")


def main():
    parser = argparse.ArgumentParser(description="로컬 코딩 에이전트")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--url",   default=API_BASE)
    args = parser.parse_args()

    console.print(Panel.fit(
        f"[bold cyan]🤖 로컬 코딩 에이전트[/bold cyan]\n"
        f"[dim]플랫폼 : {PLATFORM_NAME}[/dim]\n"
        f"[dim]모델   : {args.model}[/dim]\n"
        f"[dim]서버   : {args.url}[/dim]\n"
        f"[dim]도구   : read/write/edit_file · list_files · run_command · web_search[/dim]\n"
        f"[dim]명령어 : reset · help · exit[/dim]",
        border_style="cyan",
    ))

    agent   = CodingAgent(base_url=args.url, model=args.model)
    history = FileHistory(str(PROJECT_ROOT / ".agent_history"))

    while True:
        try:
            user_input = prompt("You> ", history=history).strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[dim]👋 종료합니다[/dim]")
            break

        if not user_input:
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
                    "  reset  - 대화 히스토리 초기화\n"
                    "  help   - 도움말\n"
                    "  exit   - 종료\n"
                )
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