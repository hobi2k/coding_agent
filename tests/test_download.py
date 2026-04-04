from __future__ import annotations

from pathlib import Path

from coding_agent import download


def test_select_gguf_file_prefers_requested_quant() -> None:
    files = [
        "README.md",
        "Qwen2.5-Coder-7B-Instruct-Q8_0.gguf",
        "Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf",
    ]

    selected = download._select_gguf_file(files, preferred_quant="Q4_K_M")

    assert selected.endswith("Q4_K_M.gguf")


def test_select_gguf_file_falls_back_to_first_sorted() -> None:
    files = [
        "b-model.gguf",
        "a-model.gguf",
    ]

    selected = download._select_gguf_file(files, preferred_quant="Q6_K")

    assert selected == "a-model.gguf"


def test_write_modelfile_points_to_local_gguf(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(download, "MODELS_DIR", tmp_path)
    gguf_path = tmp_path / "gguf" / "model.gguf"
    gguf_path.parent.mkdir(parents=True, exist_ok=True)
    gguf_path.write_text("dummy", encoding="utf-8")

    modelfile = download._write_modelfile("coding-agent-qwen", gguf_path, num_ctx=8192)

    content = modelfile.read_text(encoding="utf-8")
    assert f"FROM {gguf_path.resolve()}" in content
    assert "PARAMETER num_ctx 8192" in content
