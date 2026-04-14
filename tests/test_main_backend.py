"""Tests for unified --backend argument and dispatch logic in main.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

import main
from rewriter import RewriteResult


def test_parse_args_defaults_to_rules_backend() -> None:
    args = main.parse_args(["worked on the internal API"])
    assert args.backend == "rules"
    assert args.bullet == "worked on the internal API"


def test_parse_args_accepts_openai_backend() -> None:
    args = main.parse_args(["--backend", "openai", "worked on the internal API"])
    assert args.backend == "openai"


def test_parse_args_accepts_ollama_backend() -> None:
    args = main.parse_args(["--backend", "ollama", "worked on the internal API"])
    assert args.backend == "ollama"


def test_parse_args_rejects_invalid_backend() -> None:
    with pytest.raises(SystemExit):
        main.parse_args(["--backend", "invalid", "worked on the internal API"])


def test_rewrite_with_backend_rules_dispatch() -> None:
    with patch("main.rewrite") as mock_rules:
        mock_rules.return_value = RewriteResult("a", "b", ["rules"])
        result = main.rewrite_with_backend("hello", "rules")
    mock_rules.assert_called_once_with("hello")
    assert result.rewritten == "b"


def test_rewrite_with_backend_openai_dispatch() -> None:
    with patch("main.rewrite_with_openai") as mock_openai:
        mock_openai.return_value = RewriteResult("a", "b", ["openai"])
        result = main.rewrite_with_backend("hello", "openai")
    mock_openai.assert_called_once_with("hello")
    assert result.changes == ["openai"]


def test_rewrite_with_backend_ollama_dispatch() -> None:
    with patch("main.rewrite_with_ollama") as mock_ollama:
        mock_ollama.return_value = RewriteResult("a", "b", ["ollama"])
        result = main.rewrite_with_backend("hello", "ollama")
    mock_ollama.assert_called_once_with("hello")
    assert result.changes == ["ollama"]


def test_rewrite_with_backend_invalid_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported backend"):
        main.rewrite_with_backend("hello", "bad")
