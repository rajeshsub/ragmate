"""Health check endpoint."""

from fastapi import APIRouter

from ragmate import __version__
from ragmate.api.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)
