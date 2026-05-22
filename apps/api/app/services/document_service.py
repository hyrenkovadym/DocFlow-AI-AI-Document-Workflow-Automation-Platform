import logging
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.request_context import get_request_id
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.services.audit_service import log_event
from app.services.workflow_service import process_document_pipeline_sync
from app.utils.file_storage import ensure_directory, write_bytes
from app.workers.tasks import process_document_task

logger = logging.getLogger(__name__)


def _validate_upload(filename: str, content: bytes) -> str:
    settings = get_settings()

    if not filename or "." not in filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    if len(content) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")

    extension = filename.rsplit(".", 1)[1].lower()
    if extension not in settings.allowed_file_extensions:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")

    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="File is too large")

    return extension


def _enqueue_document_processing(*, document_id: str, actor_id: str) -> None:
    process_document_task.delay(document_id=document_id, actor_id=actor_id, request_id=get_request_id())


def create_document_and_process(db: Session, *, owner: User, filename: str, content: bytes) -> Document:
    extension = _validate_upload(filename, content)
    settings = get_settings()

    ensure_directory(settings.resolved_upload_dir)
    stored_filename = f"{uuid.uuid4()}.{extension}"
    file_path = Path(settings.resolved_upload_dir) / stored_filename
    write_bytes(file_path, content)

    document = Document(
        owner_id=owner.id,
        original_filename=filename,
        stored_filename=stored_filename,
        file_type=extension,
        status=DocumentStatus.QUEUED if settings.is_async_processing else DocumentStatus.UPLOADED,
        metadata_json={"stored_path": str(file_path)},
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    log_event(
        db,
        action="document_uploaded",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=str(owner.id),
        metadata={
            "filename": filename,
            "file_type": extension,
            "stored_filename": stored_filename,
            "stored_path": str(file_path),
            "processing_mode": settings.normalized_processing_mode,
        },
    )

    if settings.is_async_processing:
        try:
            _enqueue_document_processing(document_id=str(document.id), actor_id=str(owner.id))
            db.refresh(document)
            logger.info(
                "document.enqueued",
                extra={
                    "event": "document_enqueued",
                    "document_id": str(document.id),
                    "user_id": str(owner.id),
                    "status": document.status.value,
                },
            )
            return document
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.processing_error = f"Unable to enqueue background processing task: {exc}"
            db.commit()

            log_event(
                db,
                action="document_processing_failed",
                entity_type="document",
                entity_id=str(document.id),
                actor_id=str(owner.id),
                metadata={"error": document.processing_error},
            )
            logger.exception(
                "document.enqueue.failed",
                extra={
                    "event": "document_enqueue_failed",
                    "document_id": str(document.id),
                    "user_id": str(owner.id),
                    "status": document.status.value,
                    "failure_reason": document.processing_error,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processing queue is unavailable",
            ) from exc

    process_document_pipeline_sync(db, document_id=str(document.id), actor_id=str(owner.id))
    db.expire_all()
    processed_document = db.get(Document, document.id)
    if not processed_document:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document was not found")
    return processed_document


def create_document_and_enqueue(db: Session, *, owner: User, filename: str, content: bytes) -> Document:
    # Backwards-compatible alias.
    return create_document_and_process(db, owner=owner, filename=filename, content=content)


def list_documents_for_user(db: Session, user: User) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if user.role == UserRole.USER:
        query = query.where(Document.owner_id == user.id)
    return list(db.scalars(query))


def get_document_for_user(db: Session, *, document_id: str, user: User) -> Document:
    try:
        document_uuid = UUID(document_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found") from exc

    document = db.get(Document, document_uuid)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    if user.role == UserRole.USER and document.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return document


def get_document_extraction(db: Session, *, document_id: str, user: User) -> DocumentExtraction:
    document = get_document_for_user(db, document_id=document_id, user=user)
    extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.document_id == document.id))
    if not extraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No extraction available")
    return extraction


def reprocess_document(db: Session, *, document_id: str, user: User) -> Document:
    settings = get_settings()
    document = get_document_for_user(db, document_id=document_id, user=user)
    document.status = DocumentStatus.QUEUED if settings.is_async_processing else DocumentStatus.UPLOADED
    document.processing_error = None
    db.commit()
    db.refresh(document)

    log_event(
        db,
        action="document_reprocess_requested",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=str(user.id),
        metadata={"processing_mode": settings.normalized_processing_mode},
    )

    if settings.is_async_processing:
        try:
            _enqueue_document_processing(document_id=str(document.id), actor_id=str(user.id))
            db.refresh(document)
            logger.info(
                "document.reprocess.enqueued",
                extra={
                    "event": "document_reprocess_enqueued",
                    "document_id": str(document.id),
                    "user_id": str(user.id),
                    "status": document.status.value,
                },
            )
            return document
        except Exception as exc:
            document.status = DocumentStatus.FAILED
            document.processing_error = f"Unable to enqueue background processing task: {exc}"
            db.commit()
            log_event(
                db,
                action="document_processing_failed",
                entity_type="document",
                entity_id=str(document.id),
                actor_id=str(user.id),
                metadata={"error": document.processing_error},
            )
            logger.exception(
                "document.reprocess.enqueue.failed",
                extra={
                    "event": "document_reprocess_enqueue_failed",
                    "document_id": str(document.id),
                    "user_id": str(user.id),
                    "status": document.status.value,
                    "failure_reason": document.processing_error,
                },
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Document processing queue is unavailable",
            ) from exc

    process_document_pipeline_sync(db, document_id=str(document.id), actor_id=str(user.id))
    db.expire_all()
    processed_document = db.get(Document, document.id)
    if not processed_document:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Document was not found")
    return processed_document
