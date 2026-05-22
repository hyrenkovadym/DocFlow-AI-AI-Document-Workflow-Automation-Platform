import logging

from app.core.request_context import reset_request_id, set_request_id
from app.services.workflow_service import process_document_pipeline
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="process_document_task")
def process_document_task(
    document_id: str,
    actor_id: str | None = None,
    request_id: str | None = None,
) -> None:
    token = set_request_id(request_id)
    logger.info(
        "worker.task.received",
        extra={
            "event": "worker_task_received",
            "document_id": document_id,
            "user_id": actor_id,
            "request_id": request_id,
            "processing_status": "queued",
        },
    )
    try:
        process_document_pipeline(document_id=document_id, actor_id=actor_id)
        logger.info(
            "worker.task.completed",
            extra={
                "event": "worker_task_completed",
                "document_id": document_id,
                "user_id": actor_id,
                "request_id": request_id,
            },
        )
    except Exception:
        logger.exception(
            "worker.task.failed",
            extra={
                "event": "worker_task_failed",
                "document_id": document_id,
                "user_id": actor_id,
                "request_id": request_id,
            },
        )
        raise
    finally:
        reset_request_id(token)
