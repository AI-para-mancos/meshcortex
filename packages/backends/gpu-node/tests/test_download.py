from pathlib import Path

import pytest
from backends.gpu_node import download
from model_entry_factory import make_model_entry

VALID_URL = (
    "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/Qwen_Qwen3-1.7B-Q4_K_M.gguf"
)


def test_parse_hf_source_url_splits_repo_and_filename():
    repo_id, filename = download.parse_hf_source_url(VALID_URL)

    assert repo_id == "bartowski/Qwen_Qwen3-1.7B-GGUF"
    assert filename == "Qwen_Qwen3-1.7B-Q4_K_M.gguf"


@pytest.mark.parametrize(
    "malformed_url",
    [
        "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF",
        "https://huggingface.co/bartowski/Qwen_Qwen3-1.7B-GGUF/resolve/main/",
        "https://huggingface.co/resolve/main/model.gguf",
    ],
)
def test_parse_hf_source_url_rejects_non_resolve_urls(malformed_url):
    with pytest.raises(ValueError, match="Hugging Face file URL"):
        download.parse_hf_source_url(malformed_url)


@pytest.mark.parametrize("bad_format", ["safetensors", "awq", "gptq"])
def test_ensure_model_downloaded_rejects_non_gguf_format(bad_format):
    entry = make_model_entry(format=bad_format)

    with pytest.raises(ValueError, match="gguf"):
        download.ensure_model_downloaded(entry)


def test_ensure_model_downloaded_calls_hf_hub_download_with_parsed_repo_and_filename(monkeypatch):
    entry = make_model_entry(source_url=VALID_URL)
    captured = {}

    def fake_hf_hub_download(*, repo_id, filename):
        captured["repo_id"] = repo_id
        captured["filename"] = filename
        return f"/cache/{filename}"

    monkeypatch.setattr(download, "hf_hub_download", fake_hf_hub_download)

    result = download.ensure_model_downloaded(entry)

    assert captured["repo_id"] == "bartowski/Qwen_Qwen3-1.7B-GGUF"
    assert captured["filename"] == "Qwen_Qwen3-1.7B-Q4_K_M.gguf"
    assert result == Path("/cache/Qwen_Qwen3-1.7B-Q4_K_M.gguf")
