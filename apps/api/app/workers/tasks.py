from app.services.workflow_service import process_document_pipeline
from app.workers.celery_app import celery_app


@celery_app.task(name="process_document_task")
def process_document_task(document_id: str) -> None:
    process_document_pipeline(document_id)
