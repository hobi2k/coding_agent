from __future__ import annotations

from coding_agent.server import build_ollama_command


def test_build_ollama_command() -> None:
    command = build_ollama_command("/tmp/ollama")
    assert command == ["/tmp/ollama", "serve"]
