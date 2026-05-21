from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import DocumentStatus, DocumentType


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    owner_id: UUID
    original_filename: str
    file_type: str
    status: DocumentStatus
    document_type: DocumentType
    ai_confidence_score: float | None
    processing_error: str | None
    created_at: datetime
    updated_at: datetime


class DocumentDetailResponse(DocumentResponse):
    extracted_text: str | None
    metadata_json: dict


class DocumentExtractionResponse(BaseModel):
    document_id: UUID
    structured_fields: dict
    raw_response: dict
    confidence_score: float


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int
