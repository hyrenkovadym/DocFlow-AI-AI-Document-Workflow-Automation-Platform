from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from redis import Redis
from sqlalchemy import text

from app.core.config import get_settings
from app.db.session import engine

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "app": settings.project_name,
        "version": settings.app_version,
    }


@router.get("/ready")
def ready() -> JSONResponse:
    settings = get_settings()

    database_ok = False
    redis_ok = False

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        database_ok = True
    except Exception:
        database_ok = False

    if settings.is_redis_configured:
        try:
            redis_client = Redis.from_url(
                settings.redis_url,
                socket_connect_timeout=1,
                socket_timeout=1,
                decode_responses=True,
            )
            redis_ok = bool(redis_client.ping())
        except Exception:
            redis_ok = False

    redis_required = settings.normalized_processing_mode == "async"
    overall_ready = database_ok and (redis_ok or not redis_required)

    payload = {
        "status": "ready" if overall_ready else "degraded",
        "dependencies": {
            "database": {"ok": database_ok},
            "redis": {"ok": redis_ok, "required": redis_required},
        },
        "processing_mode": settings.normalized_processing_mode,
        "ai_provider": settings.resolved_ai_provider,
    }

    return JSONResponse(status_code=200 if overall_ready else 503, content=payload)
