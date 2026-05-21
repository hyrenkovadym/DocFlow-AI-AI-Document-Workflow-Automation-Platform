from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.enums import ReviewStatus


class ReviewTaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    reviewer_id: UUID | None
    status: ReviewStatus
    reviewer_comment: str | None
    reviewed_at: datetime | None
    created_at: datetime


class ReviewDecisionRequest(BaseModel):
    reviewer_comment: str | None = None


class ReviewFieldsPatchRequest(BaseModel):
    structured_fields: dict
