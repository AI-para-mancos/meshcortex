import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backends.gpu_node.engines import ollama
from model_entry_factory import make_model_entry


def test_build_modelfile_points_at_local_path():
    model_path = Path("/models/model.gguf")

    assert ollama.build_modelfile(model_path) == f"FROM {model_path}\n"


@pytest.mark.parametrize(
    ("returncode", "expect_endpoint_message"),
    [(0, True), (1, False)],
    ids=["success", "failure"],
)
def test_serve_runs_ollama_create_and_reports_result(
    tmp_path, monkeypatch, capsys, returncode, expect_endpoint_message
):
    entry = make_model_entry()
    model_path = tmp_path / "model.gguf"
    modelfile_path = tmp_path / "Modelfile"

    monkeypatch.setattr(ollama, "ensure_model_downloaded", lambda passed_entry: model_path)

    mock_run = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=returncode))
    monkeypatch.setattr(ollama.subprocess, "run", mock_run)

    exit_code = ollama.serve(entry)

    assert exit_code == returncode
    # The Modelfile is written next to the model before `ollama create` runs, regardless
    # of whether that command succeeds.
    assert modelfile_path.read_text() == ollama.build_modelfile(model_path)
    mock_run.assert_called_once_with(["ollama", "create", entry.name, "-f", str(modelfile_path)])

    stderr = capsys.readouterr().err
    if expect_endpoint_message:
        assert ollama.DEFAULT_ENDPOINT in stderr
    else:
        assert stderr == ""
