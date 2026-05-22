import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Index, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base
from app.models.enums import DocumentStatus, DocumentType


def enum_values(enum_cls):
    return [member.value for member in enum_cls]


json_type = JSON().with_variant(JSONB, "postgresql")


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("ix_documents_status_created", "status", "created_at"),
        Index("ix_documents_owner_created", "owner_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(
        Enum(DocumentStatus, values_callable=enum_values), default=DocumentStatus.UPLOADED, nullable=False, index=True
    )
    document_type: Mapped[DocumentType] = mapped_column(
        Enum(DocumentType, values_callable=enum_values), default=DocumentType.UNKNOWN, nullable=False, index=True
    )
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    processing_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict] = mapped_column(json_type, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    owner = relationship("User", back_populates="documents")
    extraction = relationship("DocumentExtraction", back_populates="document", uselist=False)
    review_task = relationship("ReviewTask", back_populates="document", uselist=False)
    exports = relationship("ExportRecord", back_populates="document")


class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id"), nullable=False, unique=True, index=True)
    structured_fields: Mapped[dict] = mapped_column(json_type, default=dict, nullable=False)
    raw_response: Mapped[dict] = mapped_column(json_type, default=dict, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    document = relationship("Document", back_populates="extraction")
