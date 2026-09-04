import pytest
from backends.gpu_node import cli


def test_download_writes_model_path_on_success(registry_path, monkeypatch, capsys):
    model_path = "/cache/model.gguf"
    monkeypatch.setattr(cli, "ensure_model_downloaded", lambda entry: model_path)

    exit_code = cli.run(["download", "qwen3-1.7b-q4", "--registry", str(registry_path)])

    assert exit_code == 0
    assert model_path in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv",
    [
        ["download", "does-not-exist"],
        ["serve", "llama-cpp", "does-not-exist"],
    ],
    ids=["download", "serve"],
)
def test_unknown_model_raises(registry_path, argv):
    with pytest.raises(ValueError, match="not found"):
        cli.run([*argv, "--registry", str(registry_path)])


def test_resolve_entry_warns_when_not_tagged_gpu(non_gpu_registry_path):
    with pytest.warns(UserWarning, match="node_types"):
        entry = cli._resolve_entry(non_gpu_registry_path, "qwen3-1.7b-q4")

    assert entry.name == "qwen3-1.7b-q4"


@pytest.mark.parametrize(
    ("engine_name", "extra_argv", "expected_kwargs"),
    [
        (
            "llama-cpp",
            ["--port", "9000"],
            {"port": 9000, "ngl": 99, "ctx_size": 4096, "llama_server_bin": "llama-server"},
        ),
        ("ollama", [], {"ollama_bin": "ollama"}),
    ],
    ids=["llama-cpp", "ollama"],
)
def test_serve_dispatches_to_selected_engine_on_success(
    registry_path, monkeypatch, engine_name, extra_argv, expected_kwargs
):
    captured = {}

    def fake_serve(entry, **kwargs):
        captured["entry"] = entry
        captured["kwargs"] = kwargs
        return 0

    monkeypatch.setattr(cli.ENGINES[engine_name], "serve", fake_serve)

    exit_code = cli.run(
        ["serve", engine_name, "qwen3-1.7b-q4", "--registry", str(registry_path), *extra_argv]
    )

    assert exit_code == 0
    assert captured["entry"].name == "qwen3-1.7b-q4"
    assert captured["kwargs"] == expected_kwargs
