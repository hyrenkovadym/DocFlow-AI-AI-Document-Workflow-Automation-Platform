from typing import Literal

from pydantic import BaseModel, Field

from app.models.enums import DocumentType


class DocumentClassification(BaseModel):
    document_type: DocumentType
    confidence_score: float = Field(ge=0, le=1)
    reasoning: str | None = None


class ExtractedFields(BaseModel):
    document_type: DocumentType
    title: str
    summary: str
    dates: list[str] = Field(default_factory=list)
    people_or_companies: list[str] = Field(default_factory=list)
    amount: str | None = None
    priority: Literal["low", "medium", "high"] = "medium"
    recommended_action: str = "review"
    confidence_score: float = Field(ge=0, le=1)
