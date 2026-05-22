from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info")
def system_info() -> dict:
    settings = get_settings()
    return {
        "processing_mode": settings.normalized_processing_mode,
        "ai_provider": settings.resolved_ai_provider,
        "app_env": settings.environment,
    }
