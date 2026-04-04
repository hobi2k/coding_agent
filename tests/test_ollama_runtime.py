from __future__ import annotations

from pathlib import Path

from coding_agent import ollama_runtime


def test_platform_download_url_matches_platform(monkeypatch) -> None:
    monkeypatch.setattr(ollama_runtime, "IS_WINDOWS", False)
    assert ollama_runtime._platform_download_url().endswith("ollama-linux-amd64.tar.zst")


def test_candidate_paths_include_linux_vendor_layout(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ollama_runtime, "IS_WINDOWS", False)
    paths = ollama_runtime._candidate_paths(tmp_path)
    assert tmp_path / "usr" / "bin" / "ollama" in paths


def test_build_ollama_env_sets_models_dir(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(ollama_runtime, "MODELS_DIR", tmp_path)
    env = ollama_runtime.build_ollama_env("127.0.0.1", 11434)
    assert env["OLLAMA_MODELS"] == str(tmp_path / "ollama-store")
    assert env["OLLAMA_HOST"] == "127.0.0.1:11434"


def test_get_ollama_binary_prefers_system(monkeypatch, tmp_path: Path) -> None:
    system_binary = tmp_path / "ollama"
    system_binary.write_text("", encoding="utf-8")
    monkeypatch.setattr(ollama_runtime.shutil, "which", lambda name: str(system_binary))
    assert ollama_runtime.get_ollama_binary() == system_binary
