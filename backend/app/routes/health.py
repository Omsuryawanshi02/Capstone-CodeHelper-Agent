"""Health check route."""

import time
from fastapi import APIRouter, Depends, Request
from ..schemas import HealthResponse
from ..config import check_required_env_vars, ADK_APP_NAME

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def get_health(request: Request) -> HealthResponse:
    """Return backend health and upstream dependency readiness.

    Never includes API keys, tokens, or raw secrets in the response.
    """
    adk_client = request.app.state.adk_client
    adk_healthy = await adk_client.check_health()
    env_status = check_required_env_vars()
    config_valid = env_status["nvidia_configured"] and env_status["pinecone_configured"]

    overall_status = "ok"
    if not adk_healthy or not config_valid:
        overall_status = "degraded"

    return HealthResponse(
        status=overall_status,
        backend_running=True,
        adk_reachable=adk_healthy,
        adk_app_name=ADK_APP_NAME,
        config_valid=config_valid,
        timestamp=time.time(),
    )
