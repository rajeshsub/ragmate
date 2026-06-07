"""Static API key authentication via X-API-Key header."""

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from ragmate.config import get_settings

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(api_key: str | None = Security(_api_key_header)) -> str:
    settings = get_settings()
    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key. Provide X-API-Key header.",
        )
    return api_key
