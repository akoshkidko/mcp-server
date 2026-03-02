"""HTTP /health endpoint router."""

from fastapi import APIRouter
from pydantic import BaseModel

from repohealth_mcp import __version__
from repohealth_mcp.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health() -> HealthResponse:
    """Return a simple liveness response.

    Used by Docker HEALTHCHECK and load-balancer probes.
    """
    return HealthResponse(
        status="ok",
        service=settings.service_name,
        version=__version__,
    )
