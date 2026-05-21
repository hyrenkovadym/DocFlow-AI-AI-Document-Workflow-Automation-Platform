from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.db.session import get_db
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole
from app.models.user import User
from app.schemas.review import ReviewDecisionRequest, ReviewFieldsPatchRequest
from app.services.audit_service import log_event
from app.services.workflow_service import approve_document, reject_document

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/queue")
def review_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.REVIEWER)),
) -> list[dict]:
    query = select(Document).where(Document.status == DocumentStatus.NEEDS_REVIEW).order_by(Document.created_at.asc())
    documents = list(db.scalars(query))
    queue = []
    for doc in documents:
        queue.append(
            {
                "document_id": str(doc.id),
                "filename": doc.original_filename,
                "document_type": doc.document_type.value,
                "confidence_score": doc.ai_confidence_score,
                "owner_id": str(doc.owner_id),
                "created_at": doc.created_at.isoformat(),
            }
        )
    return queue


@router.post("/{document_id}/approve")
def approve(
    document_id: UUID,
    payload: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.REVIEWER)),
) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    approve_document(db, document=document, reviewer_id=str(current_user.id), reviewer_comment=payload.reviewer_comment)
    return {"status": "approved", "document_id": str(document_id)}


@router.post("/{document_id}/reject")
def reject(
    document_id: UUID,
    payload: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.REVIEWER)),
) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    reject_document(db, document=document, reviewer_id=str(current_user.id), reviewer_comment=payload.reviewer_comment)
    return {"status": "rejected", "document_id": str(document_id)}


@router.patch("/{document_id}/fields")
def patch_fields(
    document_id: UUID,
    payload: ReviewFieldsPatchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.REVIEWER)),
) -> dict:
    document = db.get(Document, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    extraction = db.scalar(select(DocumentExtraction).where(DocumentExtraction.document_id == document.id))
    if not extraction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Extraction not found")

    extraction.structured_fields = payload.structured_fields
    db.commit()

    log_event(
        db,
        action="review_fields_updated",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=str(current_user.id),
    )

    return {"status": "updated", "document_id": str(document_id)}
