import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit_logs, auth, documents, health, reviews, system
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.request_context import reset_request_id, set_request_id

settings = get_settings()
configure_logging()
logger = logging.getLogger("app.request")

app = FastAPI(
    title="DocFlow AI API",
    version=settings.app_version,
    description="AI-powered document intake and workflow automation platform.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix=settings.api_v1_prefix)
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(documents.router, prefix=settings.api_v1_prefix)
app.include_router(reviews.router, prefix=settings.api_v1_prefix)
app.include_router(audit_logs.router, prefix=settings.api_v1_prefix)
app.include_router(system.router, prefix=settings.api_v1_prefix)


@app.middleware("http")
async def request_id_middleware(request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    token = set_request_id(request_id)
    started = perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = int((perf_counter() - started) * 1000)
        logger.exception(
            "request.failed",
            extra={
                "event": "http_request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": duration_ms,
                "status": 500,
            },
        )
        raise
    finally:
        reset_request_id(token)

    duration_ms = int((perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request.completed",
        extra={
            "event": "http_request_completed",
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
        },
    )
    return response


@app.get("/")
def root() -> dict:
    return {"name": settings.project_name, "docs": "/docs", "health": f"{settings.api_v1_prefix}/health"}
