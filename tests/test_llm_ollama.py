"""Ollama client tests: mocked HTTP only (no real Ollama or network required)."""

from __future__ import annotations

import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from llm_ollama import OllamaRewriteError, rewrite_with_ollama


def test_ollama_empty_input_no_request() -> None:
    """Empty bullet returns early; must not call Ollama."""
    with patch("llm_ollama.urllib.request.urlopen") as mock_urlopen:
        r = rewrite_with_ollama("   ")
    mock_urlopen.assert_not_called()
    assert r.original == ""
    assert r.rewritten == ""
    assert r.changes == ["(empty input: skipped)"]


@patch("llm_ollama.urllib.request.urlopen")
def test_ollama_success_parses_first_non_empty_line(mock_urlopen: MagicMock) -> None:
    payload = {
        "model": "qwen-test",
        "message": {
            "role": "assistant",
            "content": "\n\n  Rewritten line one.  \nSecond ignored.\n",
        },
        "done": True,
    }
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(json.dumps(payload).encode("utf-8"))
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with patch.dict(
        os.environ,
        {"OLLAMA_MODEL": "qwen-test"},
        clear=False,
    ):
        r = rewrite_with_ollama("worked on the API")

    assert r.original == "worked on the API"
    assert r.rewritten == "Rewritten line one."
    assert r.changes == ["Ollama rewrite (qwen-test)"]

    mock_urlopen.assert_called_once()
    _args, kwargs = mock_urlopen.call_args
    assert kwargs.get("timeout") == 60.0


@patch("llm_ollama.urllib.request.urlopen")
def test_ollama_http_error_wraps(mock_urlopen: MagicMock) -> None:
    import urllib.error

    err = urllib.error.HTTPError("url", 401, "Unauthorized", hdrs=None, fp=None)
    err.read = MagicMock(return_value=b'{"error":"bad"}')
    mock_urlopen.side_effect = err

    with pytest.raises(OllamaRewriteError, match="HTTP 401"):
        rewrite_with_ollama("hello")


@patch("llm_ollama.urllib.request.urlopen")
def test_ollama_url_error_wraps(mock_urlopen: MagicMock) -> None:
    import urllib.error

    mock_urlopen.side_effect = urllib.error.URLError("Connection refused")

    with pytest.raises(OllamaRewriteError, match="Request failed"):
        rewrite_with_ollama("hello")


@patch("llm_ollama.urllib.request.urlopen")
def test_ollama_bad_response_shape(mock_urlopen: MagicMock) -> None:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(b'{"message":{}}')
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with pytest.raises(OllamaRewriteError, match="Unexpected API response"):
        rewrite_with_ollama("hello")


@patch("llm_ollama.urllib.request.urlopen")
def test_ollama_non_string_content_raises(mock_urlopen: MagicMock) -> None:
    payload = {"message": {"role": "assistant", "content": None}}
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(json.dumps(payload).encode("utf-8"))
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with pytest.raises(OllamaRewriteError, match="non-string"):
        rewrite_with_ollama("hello")
