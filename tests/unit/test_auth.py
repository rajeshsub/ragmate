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


def test_comma_separated_keys_first_key_valid() -> None:
    result = require_api_key("key1", _mock_settings("key1,key2,key3"))
    assert result == "key1"


def test_comma_separated_keys_middle_key_valid() -> None:
    result = require_api_key("key2", _mock_settings("key1,key2,key3"))
    assert result == "key2"


def test_comma_separated_keys_last_key_valid() -> None:
    result = require_api_key("key3", _mock_settings("key1,key2,key3"))
    assert result == "key3"


def test_comma_separated_keys_with_spaces() -> None:
    result = require_api_key("key2", _mock_settings("key1, key2 , key3"))
    assert result == "key2"


def test_comma_separated_keys_trailing_comma() -> None:
    result = require_api_key("key2", _mock_settings("key1,key2,"))
    assert result == "key2"


def test_comma_separated_keys_trailing_comma_with_spaces() -> None:
    result = require_api_key("key3", _mock_settings("key1, key2, key3, "))
    assert result == "key3"


def test_comma_separated_keys_invalid_key_raises_401() -> None:
    with pytest.raises(HTTPException) as exc_info:
        require_api_key("wrong", _mock_settings("key1,key2,key3"))
    assert exc_info.value.status_code == 401
