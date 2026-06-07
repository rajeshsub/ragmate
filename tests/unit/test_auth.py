"""Unit tests for API key auth."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi import HTTPException

from ragmate.api.auth import require_api_key


def test_valid_key_accepted() -> None:
    with patch("ragmate.api.auth.get_settings") as mock:
        mock.return_value.api_key = "secret"
        result = require_api_key("secret")
    assert result == "secret"


def test_invalid_key_raises_401() -> None:
    with patch("ragmate.api.auth.get_settings") as mock:
        mock.return_value.api_key = "secret"
        with pytest.raises(HTTPException) as exc_info:
            require_api_key("wrong")
    assert exc_info.value.status_code == 401


def test_missing_key_raises_401() -> None:
    with patch("ragmate.api.auth.get_settings") as mock:
        mock.return_value.api_key = "secret"
        with pytest.raises(HTTPException) as exc_info:
            require_api_key(None)
    assert exc_info.value.status_code == 401
