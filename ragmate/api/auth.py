"""Static API key authentication via X-API-Key header."""

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ragmate.api.dependencies import get_settings
from ragmate.config import Settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(
    api_key: str | None = Security(_api_key_header),
    settings: Settings = Depends(get_settings),
) -> str:
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )

    valid_keys = [key.strip() for key in settings.api_key.split(",") if key.strip()]
    if api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
    return api_key
