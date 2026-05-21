from io import BytesIO
from pathlib import Path
from uuid import UUID

from sqlalchemy import select

from app.core.config import get_settings
from app.models.audit import AuditLog
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole


def _login(client, *, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _upload_document(client, token: str, filename: str, content: bytes) -> str:
    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": (filename, BytesIO(content), "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_anonymous_user_cannot_reprocess_document(client, create_user):
    create_user(email="reprocess-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    owner_token = _login(client, email="reprocess-owner@example.com", password="OwnerPass123!")
    document_id = _upload_document(client, owner_token, "request.txt", b"Request initial")

    response = client.post(f"/api/documents/{document_id}/reprocess")
    assert response.status_code == 401


def test_regular_user_cannot_reprocess_other_users_document(client, create_user):
    create_user(email="owner-rp@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="outsider-rp@example.com", password="OutPass123!", role=UserRole.USER)

    owner_token = _login(client, email="owner-rp@example.com", password="OwnerPass123!")
    outsider_token = _login(client, email="outsider-rp@example.com", password="OutPass123!")
    document_id = _upload_document(client, owner_token, "request.txt", b"Request initial")

    response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Access denied"


def test_reviewer_and_admin_can_reprocess_document(client, create_user):
    create_user(email="owner-role-rp@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer-role-rp@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)
    create_user(email="admin-role-rp@example.com", password="AdminPass123!", role=UserRole.ADMIN)

    owner_token = _login(client, email="owner-role-rp@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reviewer-role-rp@example.com", password="ReviewerPass123!")
    admin_token = _login(client, email="admin-role-rp@example.com", password="AdminPass123!")

    document_id = _upload_document(client, owner_token, "request.txt", b"Request initial")

    reviewer_response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    admin_response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {admin_token}"},
    )

    assert reviewer_response.status_code == 200
    assert admin_response.status_code == 200


def test_reprocess_updates_extraction_and_audit_events(client, db_session, create_user):
    create_user(email="reprocess-update-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    owner_token = _login(client, email="reprocess-update-owner@example.com", password="OwnerPass123!")

    document_id = _upload_document(client, owner_token, "request.txt", b"Request for office chairs")
    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.document_type.value == "request"

    settings = get_settings()
    stored_path = Path(settings.resolved_upload_dir) / document.stored_filename
    stored_path.write_text("Invoice #909\nAmount: $99.00", encoding="utf-8")

    reprocess_response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "needs_review"

    extraction = db_session.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == UUID(document_id))
    )
    assert extraction is not None
    assert extraction.structured_fields["document_type"] == "invoice"

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        ).all()
    }
    assert "document_reprocess_requested" in actions
    assert "document_processing_started" in actions
    assert "ai_extraction_completed" in actions


def test_failed_document_can_be_reprocessed(client, db_session, create_user, monkeypatch):
    from app.services import workflow_service

    create_user(email="failed-reprocess-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    owner_token = _login(client, email="failed-reprocess-owner@example.com", password="OwnerPass123!")

    monkeypatch.setattr(workflow_service, "extract_text_from_file", lambda *_args, **_kwargs: "")
    failed_upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("broken.txt", BytesIO(b"failing"), "text/plain")},
    )
    assert failed_upload.status_code == 201
    document_id = failed_upload.json()["id"]
    assert failed_upload.json()["status"] == "failed"

    monkeypatch.setattr(workflow_service, "extract_text_from_file", lambda *_args, **_kwargs: "Invoice #1")
    reprocess_response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "needs_review"

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.NEEDS_REVIEW
    assert document.processing_error is None


def test_approved_or_exported_document_reprocess_sets_needs_review(client, db_session, create_user):
    create_user(email="reprocess-owner-approved@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reprocess-reviewer-approved@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = _login(client, email="reprocess-owner-approved@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reprocess-reviewer-approved@example.com", password="ReviewerPass123!")

    document_id = _upload_document(client, owner_token, "invoice.txt", b"Invoice #4\nAmount: $40.00")

    approve_response = client.post(
        f"/api/reviews/{document_id}/approve",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"reviewer_comment": "Approved"},
    )
    assert approve_response.status_code == 200

    export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert export_response.status_code == 200

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.EXPORTED

    settings = get_settings()
    stored_path = Path(settings.resolved_upload_dir) / document.stored_filename
    stored_path.write_text("Contract Agreement\nDate: 2026-05-21", encoding="utf-8")

    reprocess_response = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert reprocess_response.status_code == 200
    assert reprocess_response.json()["status"] == "needs_review"

    refreshed = db_session.get(Document, UUID(document_id))
    assert refreshed is not None
    assert refreshed.status == DocumentStatus.NEEDS_REVIEW
