"""Unit tests for API key auth."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from ragmate.api.auth import require_api_key


def _mock_settings(api_key: str) -> MagicMock:
    s = MagicMock()
    s.api_key = api_key
    return s


def test_valid_key_accepted() -> None:
    result = require_api_key("secret", _mock_settings("secret"))
    assert result == "secret"


def test_invalid_key_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("wrong", _mock_settings("secret"))
    assert exc_info.value.status_code == 401


def test_missing_key_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_api_key(None, _mock_settings("secret"))
    assert exc_info.value.status_code == 401
