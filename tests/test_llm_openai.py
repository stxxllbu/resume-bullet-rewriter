"""OpenAI client tests: mocked HTTP only (no real network or API key required)."""

from __future__ import annotations

import io
import json
import os
from unittest.mock import MagicMock, patch

import pytest

from llm_openai import OpenAIRewriteError, rewrite_with_openai


def test_openai_empty_input_without_key() -> None:
    """Empty bullet returns early; must not require OPENAI_API_KEY."""
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        r = rewrite_with_openai("   ")
        assert r.original == ""
        assert r.rewritten == ""
        assert r.changes == ["(empty input: skipped)"]
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


def test_openai_missing_key_raises() -> None:
    old = os.environ.pop("OPENAI_API_KEY", None)
    try:
        with pytest.raises(OpenAIRewriteError, match="OPENAI_API_KEY"):
            rewrite_with_openai("worked on the API")
    finally:
        if old is not None:
            os.environ["OPENAI_API_KEY"] = old


@patch("llm_openai.urllib.request.urlopen")
def test_openai_success_parses_first_non_empty_line(mock_urlopen: MagicMock) -> None:
    payload = {
        "choices": [
            {
                "message": {
                    "content": "\n\n  Rewritten line one.  \nSecond ignored.\n",
                }
            }
        ]
    }
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(json.dumps(payload).encode("utf-8"))
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with patch.dict(
        os.environ,
        {"OPENAI_API_KEY": "sk-test", "OPENAI_MODEL": "gpt-test"},
        clear=False,
    ):
        r = rewrite_with_openai("worked on the API")

    assert r.original == "worked on the API"
    assert r.rewritten == "Rewritten line one."
    assert r.changes == ["OpenAI rewrite (gpt-test)"]

    mock_urlopen.assert_called_once()
    _args, kwargs = mock_urlopen.call_args
    assert kwargs.get("timeout") == 60.0


@patch("llm_openai.urllib.request.urlopen")
def test_openai_http_error_wraps(mock_urlopen: MagicMock) -> None:
    import urllib.error

    err = urllib.error.HTTPError("url", 401, "Unauthorized", hdrs=None, fp=None)
    err.read = MagicMock(return_value=b'{"error":{"message":"bad"}}')
    mock_urlopen.side_effect = err

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with pytest.raises(OpenAIRewriteError, match="HTTP 401"):
            rewrite_with_openai("hello")


@patch("llm_openai.urllib.request.urlopen")
def test_openai_bad_response_shape(mock_urlopen: MagicMock) -> None:
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(b'{"choices":[]}')
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with pytest.raises(OpenAIRewriteError, match="Unexpected API response"):
            rewrite_with_openai("hello")


@patch("llm_openai.urllib.request.urlopen")
def test_openai_non_string_content_raises(mock_urlopen: MagicMock) -> None:
    payload = {"choices": [{"message": {"content": None}}]}
    mock_cm = MagicMock()
    mock_cm.__enter__.return_value = io.BytesIO(json.dumps(payload).encode("utf-8"))
    mock_cm.__exit__.return_value = None
    mock_urlopen.return_value = mock_cm

    with patch.dict(os.environ, {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with pytest.raises(OpenAIRewriteError, match="non-string"):
            rewrite_with_openai("hello")
