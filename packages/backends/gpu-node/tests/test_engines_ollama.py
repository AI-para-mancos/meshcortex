import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backends.gpu_node.engines import ollama
from model_entry_factory import make_model_entry


def _completed(returncode):
    return subprocess.CompletedProcess(args=[], returncode=returncode)


@pytest.fixture
def mock_server_process(monkeypatch):
    """A fake `ollama serve` `subprocess.Popen`, already "exited" unless a test says otherwise."""
    process = MagicMock(spec=subprocess.Popen)
    process.poll.return_value = 0
    process.wait.return_value = 0
    monkeypatch.setattr(ollama.subprocess, "Popen", MagicMock(return_value=process))
    return process


def test_build_modelfile_points_at_local_path():
    model_path = Path("/models/model.gguf")

    assert ollama.build_modelfile(model_path) == f"FROM {model_path}\n"


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [({}, "http://localhost:8080"), ({"port": 11434}, "http://localhost:11434")],
    ids=["default", "override"],
)
def test_endpoint(kwargs, expected):
    assert ollama.endpoint(**kwargs) == expected


def test_serve_launches_own_server_and_reports_endpoint(
    tmp_path, monkeypatch, capsys, mock_server_process
):
    entry = make_model_entry()
    model_path = tmp_path / "model.gguf"
    monkeypatch.setattr(ollama, "ensure_model_downloaded", lambda passed_entry: model_path)
    mock_run = MagicMock(return_value=_completed(0))
    monkeypatch.setattr(ollama.subprocess, "run", mock_run)

    exit_code = ollama.serve(entry, port=9000)

    assert exit_code == 0

    popen_call = ollama.subprocess.Popen.call_args
    assert popen_call.args[0] == ["ollama", "serve"]
    assert popen_call.kwargs["env"]["OLLAMA_HOST"] == "127.0.0.1:9000"

    modelfile_path = model_path.parent / "Modelfile"
    assert modelfile_path.read_text() == ollama.build_modelfile(model_path)

    create_call = mock_run.call_args
    assert create_call.args[0] == ["ollama", "create", entry.name, "-f", str(modelfile_path)]
    assert create_call.kwargs["env"]["OLLAMA_HOST"] == "127.0.0.1:9000"
    mock_run.assert_called_once()
    mock_server_process.wait.assert_called_once()

    stderr = capsys.readouterr().err
    assert ollama.endpoint(9000) in stderr
    assert entry.name in stderr


@pytest.mark.parametrize(
    (
        "run_side_effect",
        "poll_return_value",
        "expected_exit_code",
        "expected_attempts",
        "expected_terminate_calls",
    ),
    [
        pytest.param([_completed(1), _completed(0)], 0, 0, 2, 0, id="succeeds-on-retry"),
        pytest.param(
            [_completed(1)] * ollama.CREATE_RETRIES,
            None,
            1,
            ollama.CREATE_RETRIES,
            1,
            id="never-succeeds",
        ),
    ],
)
def test_serve_create_retries(
    tmp_path,
    monkeypatch,
    mock_server_process,
    run_side_effect,
    poll_return_value,
    expected_exit_code,
    expected_attempts,
    expected_terminate_calls,
):
    entry = make_model_entry()
    monkeypatch.setattr(ollama, "ensure_model_downloaded", lambda passed_entry: tmp_path / "m.gguf")
    mock_run = MagicMock(side_effect=run_side_effect)
    monkeypatch.setattr(ollama.subprocess, "run", mock_run)
    monkeypatch.setattr(ollama.time, "sleep", lambda seconds: None)
    mock_server_process.poll.return_value = poll_return_value

    exit_code = ollama.serve(entry)

    assert exit_code == expected_exit_code
    assert mock_run.call_count == expected_attempts
    assert mock_server_process.terminate.call_count == expected_terminate_calls
