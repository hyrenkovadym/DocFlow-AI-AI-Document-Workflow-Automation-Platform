from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Document


def get_document(db: Session, document_id: UUID) -> Document | None:
    return db.get(Document, document_id)


def list_documents(db: Session, *, owner_id: UUID | None = None) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if owner_id:
        query = query.where(Document.owner_id == owner_id)
    return list(db.scalars(query))
