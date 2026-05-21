from io import BytesIO
from uuid import UUID

from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole
from app.models.review import ReviewTask


def _register_and_login(client, *, email: str, password: str = "StrongPass123!") -> str:
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Uploader",
            "password": password,
        },
    )
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    return login_response.json()["access_token"]


def test_authenticated_user_can_upload_txt_and_process_sync(client, db_session):
    token = _register_and_login(client, email="uploader@example.com")

    files = {
        "file": (
            "invoice.txt",
            BytesIO(
                b"Invoice #42\nCompany: Contoso\nDate: 2026-05-20\nAmount: $150.00\nPlease review urgently."
            ),
            "text/plain",
        )
    }
    response = client.post("/api/documents/upload", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert response.status_code == 201
    payload = response.json()

    assert payload["status"] == DocumentStatus.NEEDS_REVIEW.value
    assert payload["document_type"] == "invoice"
    document_id = payload["id"]

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.extracted_text is not None
    assert "Invoice #42" in document.extracted_text
    assert document.status == DocumentStatus.NEEDS_REVIEW

    extraction = db_session.scalar(select(DocumentExtraction).where(DocumentExtraction.document_id == document.id))
    assert extraction is not None
    assert extraction.structured_fields["document_type"] == "invoice"
    assert extraction.confidence_score > 0

    review_task = db_session.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
    assert review_task is not None
    assert review_task.status.value == "pending"

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == str(document.id))
        ).all()
    }
    assert "document_uploaded" in actions
    assert "document_processing_started" in actions
    assert "document_text_extracted" in actions
    assert "ai_extraction_completed" in actions
    assert "review_task_created" in actions


def test_anonymous_user_cannot_upload_document(client):
    files = {"file": ("invoice.txt", BytesIO(b"Invoice #42"), "text/plain")}
    response = client.post("/api/documents/upload", files=files)
    assert response.status_code == 401


def test_unsupported_file_type_is_rejected(client):
    token = _register_and_login(client, email="unsupported@example.com")
    files = {"file": ("payload.exe", BytesIO(b"MZ"), "application/octet-stream")}
    response = client.post("/api/documents/upload", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type"


def test_approved_document_can_be_exported_as_json(client, create_user):
    owner = create_user(email="owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    reviewer = create_user(email="reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_login = client.post("/api/auth/login", json={"email": owner.email, "password": "OwnerPass123!"})
    owner_token = owner_login.json()["access_token"]

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #77\nAmount: $900.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    reviewer_login = client.post("/api/auth/login", json={"email": reviewer.email, "password": "ReviewerPass123!"})
    reviewer_token = reviewer_login.json()["access_token"]
    approve = client.post(
        f"/api/reviews/{document_id}/approve",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"reviewer_comment": "Approved for export"},
    )
    assert approve.status_code == 200

    export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert export_response.status_code == 200
    export_payload = export_response.json()
    assert export_payload["document_id"] == document_id
    assert export_payload["review_status"] == "approved"
    assert export_payload["structured_fields"]["document_type"] == "invoice"
    assert "exported_at" in export_payload


def test_non_approved_document_cannot_be_exported(client):
    token = _register_and_login(client, email="pending@example.com")
    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("request.txt", BytesIO(b"Request for travel budget"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert export_response.status_code == 409
    assert export_response.json()["detail"] == "Only approved documents can be exported"
