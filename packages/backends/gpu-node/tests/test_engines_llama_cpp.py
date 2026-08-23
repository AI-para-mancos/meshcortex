import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from backends.gpu_node.engines import llama_cpp
from model_entry_factory import make_model_entry

MODEL_PATH = Path("/models/model.gguf")


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        (
            {},
            [
                "llama-server",
                "-m",
                str(MODEL_PATH),
                "--port",
                "8080",
                "-ngl",
                "99",
                "--ctx-size",
                "4096",
            ],
        ),
        (
            {"port": 9000, "ngl": 20, "ctx_size": 2048, "llama_server_bin": "/opt/llama-server"},
            [
                "/opt/llama-server",
                "-m",
                str(MODEL_PATH),
                "--port",
                "9000",
                "-ngl",
                "20",
                "--ctx-size",
                "2048",
            ],
        ),
    ],
    ids=["defaults", "overrides"],
)
def test_build_command(kwargs, expected):
    assert llama_cpp.build_command(MODEL_PATH, **kwargs) == expected


def test_serve_downloads_then_runs_llama_server_and_returns_exit_code(tmp_path, monkeypatch):
    entry = make_model_entry()
    model_path = tmp_path / "model.gguf"

    monkeypatch.setattr(llama_cpp, "ensure_model_downloaded", lambda passed_entry: model_path)

    mock_run = MagicMock(return_value=subprocess.CompletedProcess(args=[], returncode=7))
    monkeypatch.setattr(llama_cpp.subprocess, "run", mock_run)

    exit_code = llama_cpp.serve(entry, port=8081)

    assert exit_code == 7
    mock_run.assert_called_once_with(llama_cpp.build_command(model_path, port=8081))
