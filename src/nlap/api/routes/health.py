"""Health check API routes."""

from fastapi import APIRouter, Depends, HTTPException

from nlap.api.dependencies import get_opensearch_manager
from nlap.models.base import HealthCheckResponse
from nlap.opensearch.client import OpenSearchManager
from nlap.opensearch.models import ConnectionHealth
from nlap.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthCheckResponse)
async def health_check(
    opensearch_manager: OpenSearchManager = Depends(get_opensearch_manager),
) -> HealthCheckResponse:
    """Health check endpoint for the application.

    Returns:
        HealthCheckResponse with status of application components
    """
    components = {}

    # Check OpenSearch connection
    opensearch_health = await opensearch_manager.test_connection()
    components["opensearch"] = {
        "healthy": opensearch_health.healthy,
        "cluster_name": opensearch_health.cluster_name,
        "version": opensearch_health.version,
        "error": opensearch_health.error,
    }

    # Determine overall health status
    all_healthy = all(
        comp.get("healthy", False) for comp in components.values() if isinstance(comp, dict)
    )
    status = "healthy" if all_healthy else "degraded"

    logger.debug("Health check performed", status=status, components=list(components.keys()))

    if not all_healthy:
        logger.warning("Health check detected issues", components=components)
        raise HTTPException(
            status_code=503 if status == "degraded" else 200,
            detail={"status": status, "components": components},
        )

    return HealthCheckResponse(
        success=True,
        message="All systems operational",
        status=status,
        version="0.1.0",
        components=components,
    )


@router.get("/readiness")
async def readiness_check() -> dict:
    """Readiness check endpoint (lighter than full health check).

    Returns:
        Simple readiness status
    """
    return {"status": "ready"}


@router.get("/liveness")
async def liveness_check() -> dict:
    """Liveness check endpoint.

    Returns:
        Simple liveness status
    """
    return {"status": "alive"}

