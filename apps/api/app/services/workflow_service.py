from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, DocumentType, ReviewStatus
from app.models.review import ReviewTask
from app.services.ai.base import AIProviderError
from app.services.ai.factory import get_ai_provider
from app.services.audit_service import log_event
from app.services.parser_service import UnsupportedDocumentTypeError, extract_text_from_file

logger = logging.getLogger(__name__)


def process_document_pipeline(document_id: str, actor_id: str | None = None) -> None:
    db = SessionLocal()
    try:
        _process_document_pipeline_in_session(db, document_id=document_id, actor_id=actor_id)
    finally:
        db.close()


def process_document_pipeline_sync(db: Session, *, document_id: str, actor_id: str | None = None) -> None:
    _process_document_pipeline_in_session(db, document_id=document_id, actor_id=actor_id)


def _process_document_pipeline_in_session(db: Session, *, document_id: str, actor_id: str | None = None) -> None:
    settings = get_settings()
    processing_started_at: datetime | None = None
    processing_started_perf: float | None = None

    try:
        document_uuid = UUID(document_id)
        document = db.get(Document, document_uuid)
        if not document:
            return

        processing_started_at = datetime.now(UTC)
        processing_started_perf = perf_counter()
        _merge_document_metadata(
            document,
            {
                "processing_started_at": processing_started_at.isoformat(),
                "processing_finished_at": None,
                "processing_duration_ms": None,
                "processing_status": "processing",
                "ai_provider": settings.resolved_ai_provider,
            },
        )
        document.status = DocumentStatus.PROCESSING
        db.commit()

        log_event(
            db,
            action="document_processing_started",
            entity_type="document",
            entity_id=document_id,
            actor_id=actor_id or str(document.owner_id),
            metadata={
                "stored_filename": document.stored_filename,
                "ai_provider": settings.resolved_ai_provider,
                "processing_status": "processing",
            },
        )
        logger.info(
            "document.processing.started",
            extra={
                "event": "document_processing_started",
                "document_id": document_id,
                "user_id": actor_id or str(document.owner_id),
                "processing_status": "processing",
                "ai_provider": settings.resolved_ai_provider,
            },
        )

        file_path = Path(settings.resolved_upload_dir) / document.stored_filename
        extracted_text = extract_text_from_file(file_path, document.file_type)
        if not extracted_text.strip():
            raise ValueError("Extracted text is empty")
        document.extracted_text = extracted_text
        db.commit()

        log_event(
            db,
            action="document_text_extracted",
            entity_type="document",
            entity_id=document_id,
            actor_id=actor_id or str(document.owner_id),
            metadata={"characters": len(extracted_text)},
        )
        logger.info(
            "document.text.extracted",
            extra={
                "event": "document_text_extracted",
                "document_id": document_id,
                "processing_status": "processing",
                "status": document.status.value,
            },
        )

        ai_provider = get_ai_provider(settings=settings)
        classification = ai_provider.classify_document(extracted_text)
        fields = ai_provider.extract_fields(extracted_text, classification.document_type.value)

        try:
            document.document_type = DocumentType(fields.document_type.value)
        except Exception:
            document.document_type = DocumentType.UNKNOWN
        document.ai_confidence_score = fields.confidence_score

        extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.document_id == document.id))
        if extraction:
            extraction.structured_fields = fields.model_dump(mode="json")
            extraction.raw_response = {
                "classification": classification.model_dump(mode="json"),
                "fields": fields.model_dump(mode="json"),
            }
            extraction.confidence_score = fields.confidence_score
        else:
            extraction = DocumentExtraction(
                document_id=document.id,
                structured_fields=fields.model_dump(mode="json"),
                raw_response={
                    "classification": classification.model_dump(mode="json"),
                    "fields": fields.model_dump(mode="json"),
                },
                confidence_score=fields.confidence_score,
            )
            db.add(extraction)

        review_task = db.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
        if not review_task:
            review_task = ReviewTask(document_id=document.id)
            db.add(review_task)
        review_task.status = ReviewStatus.PENDING

        processing_finished_at = datetime.now(UTC)
        processing_duration_ms = _compute_duration_ms(processing_started_perf)
        document.status = DocumentStatus.NEEDS_REVIEW
        document.processing_error = None
        _merge_document_metadata(
            document,
            {
                "ai_provider": settings.resolved_ai_provider,
                "classification_reasoning": classification.reasoning,
                "classifier_confidence": classification.confidence_score,
                "min_confidence_threshold": settings.ai_min_confidence,
                "below_threshold": fields.confidence_score < settings.ai_min_confidence,
                "processing_finished_at": processing_finished_at.isoformat(),
                "processing_duration_ms": processing_duration_ms,
                "processing_status": "needs_review",
            },
        )
        db.commit()

        log_event(
            db,
            action="ai_extraction_completed",
            entity_type="document",
            entity_id=document_id,
            actor_id=actor_id or str(document.owner_id),
            metadata={
                "ai_provider": settings.resolved_ai_provider,
                "document_type": document.document_type.value,
                "confidence_score": fields.confidence_score,
                "duration_ms": processing_duration_ms,
            },
        )
        log_event(
            db,
            action="review_task_created",
            entity_type="document",
            entity_id=document_id,
            actor_id=actor_id or str(document.owner_id),
            metadata={
                "review_status": review_task.status.value,
                "duration_ms": processing_duration_ms,
            },
        )
        logger.info(
            "document.processing.completed",
            extra={
                "event": "document_processing_completed",
                "document_id": document_id,
                "user_id": actor_id or str(document.owner_id),
                "status": document.status.value,
                "processing_status": "needs_review",
                "duration_ms": processing_duration_ms,
                "ai_provider": settings.resolved_ai_provider,
            },
        )
    except AIProviderError as exc:
        _fail_document(
            db,
            document_id,
            f"AI provider error: {exc}",
            actor_id=actor_id,
            failure_stage="ai_provider",
            processing_started_at=processing_started_at,
            processing_started_perf=processing_started_perf,
            ai_provider=settings.resolved_ai_provider,
        )
    except FileNotFoundError as exc:
        _fail_document(
            db,
            document_id,
            f"Stored document file is missing: {exc}",
            actor_id=actor_id,
            failure_stage="parser_file_missing",
            processing_started_at=processing_started_at,
            processing_started_perf=processing_started_perf,
            ai_provider=settings.resolved_ai_provider,
        )
    except (UnsupportedDocumentTypeError, ValueError) as exc:
        _fail_document(
            db,
            document_id,
            str(exc),
            actor_id=actor_id,
            failure_stage="parser_or_validation",
            processing_started_at=processing_started_at,
            processing_started_perf=processing_started_perf,
            ai_provider=settings.resolved_ai_provider,
        )
    except Exception as exc:
        _fail_document(
            db,
            document_id,
            f"Unexpected processing error: {exc}",
            actor_id=actor_id,
            failure_stage="unexpected",
            processing_started_at=processing_started_at,
            processing_started_perf=processing_started_perf,
            ai_provider=settings.resolved_ai_provider,
        )


def _fail_document(
    db: Session,
    document_id: str,
    error_message: str,
    actor_id: str | None = None,
    failure_stage: str | None = None,
    processing_started_at: datetime | None = None,
    processing_started_perf: float | None = None,
    ai_provider: str | None = None,
) -> None:
    document = db.get(Document, UUID(document_id))
    if not document:
        return
    finished_at = datetime.now(UTC)
    duration_ms = _compute_duration_ms(processing_started_perf)
    _merge_document_metadata(
        document,
        {
            "processing_started_at": processing_started_at.isoformat() if processing_started_at else None,
            "processing_finished_at": finished_at.isoformat(),
            "processing_duration_ms": duration_ms,
            "processing_status": "failed",
            "ai_provider": ai_provider,
            "failure_reason": error_message,
        },
    )
    document.status = DocumentStatus.FAILED
    document.processing_error = error_message
    db.commit()

    log_event(
        db,
        action="document_processing_failed",
        entity_type="document",
        entity_id=document_id,
        actor_id=actor_id or str(document.owner_id),
        metadata={
            "error": error_message,
            "failure_stage": failure_stage or "general",
            "duration_ms": duration_ms,
            "ai_provider": ai_provider,
            "processing_status": "failed",
        },
    )

    if failure_stage == "ai_provider":
        log_event(
            db,
            action="ai_extraction_failed",
            entity_type="document",
            entity_id=document_id,
            actor_id=actor_id or str(document.owner_id),
            metadata={
                "error": error_message,
                "duration_ms": duration_ms,
                "ai_provider": ai_provider,
            },
        )
    logger.warning(
        "document.processing.failed",
        extra={
            "event": "document_processing_failed",
            "document_id": document_id,
            "user_id": actor_id or str(document.owner_id),
            "status": document.status.value,
            "processing_status": "failed",
            "failure_reason": error_message,
            "duration_ms": duration_ms,
            "ai_provider": ai_provider,
        },
    )


def approve_document(db, *, document: Document, reviewer_id: str, reviewer_comment: str | None = None) -> None:
    reviewer_uuid = UUID(str(reviewer_id))
    review = db.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
    if not review:
        review = ReviewTask(document_id=document.id)
        db.add(review)

    review.reviewer_id = reviewer_uuid
    review.reviewer_comment = reviewer_comment
    review.status = ReviewStatus.APPROVED
    review.reviewed_at = datetime.now(UTC)

    document.status = DocumentStatus.APPROVED
    db.commit()

    log_event(
        db,
        action="document_approved",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=reviewer_uuid,
        metadata={"comment": reviewer_comment or ""},
    )


def reject_document(db, *, document: Document, reviewer_id: str, reviewer_comment: str | None = None) -> None:
    reviewer_uuid = UUID(str(reviewer_id))
    review = db.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
    if not review:
        review = ReviewTask(document_id=document.id)
        db.add(review)

    review.reviewer_id = reviewer_uuid
    review.reviewer_comment = reviewer_comment
    review.status = ReviewStatus.REJECTED
    review.reviewed_at = datetime.now(UTC)

    document.status = DocumentStatus.REJECTED
    db.commit()

    log_event(
        db,
        action="document_rejected",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=reviewer_uuid,
        metadata={"comment": reviewer_comment or ""},
    )


def _merge_document_metadata(document: Document, updates: dict) -> None:
    metadata = dict(document.metadata_json or {})
    for key, value in updates.items():
        metadata[key] = value
    document.metadata_json = metadata


def _compute_duration_ms(started_at_perf: float | None) -> int | None:
    if started_at_perf is None:
        return None
    return int((perf_counter() - started_at_perf) * 1000)
