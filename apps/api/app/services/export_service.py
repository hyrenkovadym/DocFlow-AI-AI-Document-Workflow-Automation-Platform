import csv
import io

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus
from app.models.export import ExportRecord
from app.models.user import User
from app.services.audit_service import log_event


def _build_payload(document: Document, extraction: DocumentExtraction | None) -> dict:
    return {
        "document_id": str(document.id),
        "owner_id": str(document.owner_id),
        "original_filename": document.original_filename,
        "status": document.status.value,
        "document_type": document.document_type.value,
        "confidence_score": document.ai_confidence_score,
        "structured_fields": extraction.structured_fields if extraction else {},
        "created_at": document.created_at.isoformat(),
        "updated_at": document.updated_at.isoformat(),
    }


def export_document_json(db: Session, *, document: Document, user: User) -> dict:
    if document.status != DocumentStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document must be approved")

    extraction = document.extraction
    payload = _build_payload(document, extraction)

    export_record = ExportRecord(
        document_id=document.id,
        exported_by_id=user.id,
        export_type="json",
        payload=payload,
    )
    db.add(export_record)
    document.status = DocumentStatus.EXPORTED
    db.commit()

    log_event(
        db,
        action="document_exported",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=str(user.id),
        metadata={"export_type": "json"},
    )

    return payload


def export_document_csv(db: Session, *, document: Document, user: User) -> str:
    if document.status != DocumentStatus.APPROVED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document must be approved")

    extraction = document.extraction
    payload = _build_payload(document, extraction)

    flat_data = {
        "document_id": payload["document_id"],
        "owner_id": payload["owner_id"],
        "original_filename": payload["original_filename"],
        "status": payload["status"],
        "document_type": payload["document_type"],
        "confidence_score": payload["confidence_score"],
        "title": payload["structured_fields"].get("title"),
        "summary": payload["structured_fields"].get("summary"),
        "amount": payload["structured_fields"].get("amount"),
        "priority": payload["structured_fields"].get("priority"),
        "recommended_action": payload["structured_fields"].get("recommended_action"),
    }

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(flat_data.keys()))
    writer.writeheader()
    writer.writerow(flat_data)

    export_record = ExportRecord(
        document_id=document.id,
        exported_by_id=user.id,
        export_type="csv",
        payload=payload,
    )
    db.add(export_record)
    document.status = DocumentStatus.EXPORTED
    db.commit()

    log_event(
        db,
        action="document_exported",
        entity_type="document",
        entity_id=str(document.id),
        actor_id=str(user.id),
        metadata={"export_type": "csv"},
    )

    return output.getvalue()
