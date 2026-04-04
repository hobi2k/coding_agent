from __future__ import annotations

from pathlib import Path

from coding_agent import cli


def test_cli_uses_requested_workspace_on_start(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "project_a"
    target.mkdir()
    events: list[str] = []

    class DummyAgent:
        def __init__(self, base_url: str, model: str):
            self.base_url = base_url
            self.model = model

    monkeypatch.setattr(
        cli,
        "prompt",
        lambda *args, **kwargs: (_ for _ in ()).throw(EOFError()),
    )
    monkeypatch.setattr(cli, "CodingAgent", DummyAgent)
    monkeypatch.setattr(cli, "render_status", lambda url: events.append(f"status:{url}"))
    monkeypatch.setattr(cli.console, "print", lambda *args, **kwargs: events.append("print"))
    monkeypatch.setattr(cli, "FileHistory", lambda path: path)
    monkeypatch.setattr(
        cli,
        "ensure_workspace",
        lambda path: (True, f"활성 workspace 변경됨: {Path(path).resolve()}"),
    )
    monkeypatch.setattr(
        cli,
        "get_active_workspace",
        lambda: target.resolve(),
    )
    monkeypatch.setattr(
        cli.argparse.ArgumentParser,
        "parse_args",
        lambda self: cli.argparse.Namespace(
            model="dummy-model",
            url="http://localhost:8000",
            workspace=str(target),
        ),
    )

    cli.main()

    assert events
