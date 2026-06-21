"""Health check endpoint."""

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ragmate import __version__
from ragmate.api.models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Liveness check")
async def health() -> HealthResponse:
    return HealthResponse(version=__version__)


@router.get("/healthz", response_class=PlainTextResponse, summary="Readiness probe")
async def healthz() -> str:
    return "OK"
