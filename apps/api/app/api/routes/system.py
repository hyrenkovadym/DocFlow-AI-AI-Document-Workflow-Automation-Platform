from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
def system_info() -> dict:
    settings = get_settings()
    return {
        "app_name": settings.project_name,
        "version": settings.app_version,
        "processing_mode": settings.normalized_processing_mode,
        "ai_provider": settings.resolved_ai_provider,
        "app_env": settings.environment,
        "redis_configured": settings.is_redis_configured,
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }
