from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.document import (
    DocumentDetailResponse,
    DocumentExtractionResponse,
    DocumentListResponse,
    DocumentResponse,
)
from app.services.document_service import (
    create_document_and_process,
    get_document_extraction,
    get_document_for_user,
    list_documents_for_user,
    reprocess_document,
)
from app.services.export_service import export_document_csv, export_document_json

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    content = await file.read()
    return create_document_and_process(
        db, owner=current_user, filename=file.filename or "uploaded.txt", content=content
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    items = list_documents_for_user(db, current_user)
    return DocumentListResponse(items=items, total=len(items))


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    return get_document_for_user(db, document_id=str(document_id), user=current_user)


@router.get("/{document_id}/text")
def get_document_text(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    document = get_document_for_user(db, document_id=str(document_id), user=current_user)
    return {"document_id": str(document.id), "text": document.extracted_text or ""}


@router.get("/{document_id}/extraction", response_model=DocumentExtractionResponse)
def get_extraction(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentExtractionResponse:
    extraction = get_document_extraction(db, document_id=str(document_id), user=current_user)
    return DocumentExtractionResponse(
        document_id=extraction.document_id,
        structured_fields=extraction.structured_fields,
        raw_response=extraction.raw_response,
        confidence_score=extraction.confidence_score,
    )


@router.post("/{document_id}/reprocess", response_model=DocumentResponse)
def reprocess(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    return reprocess_document(db, document_id=str(document_id), user=current_user)


@router.get("/{document_id}/export.json")
def export_json(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    document = get_document_for_user(db, document_id=str(document_id), user=current_user)
    return export_document_json(db, document=document, user=current_user)


@router.get("/{document_id}/export.csv", response_class=PlainTextResponse)
def export_csv(
    document_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> str:
    document = get_document_for_user(db, document_id=str(document_id), user=current_user)
    return export_document_csv(db, document=document, user=current_user)
