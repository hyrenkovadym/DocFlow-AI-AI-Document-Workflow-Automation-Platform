from io import BytesIO
from uuid import UUID

from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole
from app.models.export import ExportRecord
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


def test_empty_file_is_rejected(client):
    token = _register_and_login(client, email="empty@example.com")
    files = {"file": ("empty.txt", BytesIO(b""), "text/plain")}
    response = client.post("/api/documents/upload", headers={"Authorization": f"Bearer {token}"}, files=files)
    assert response.status_code == 400
    assert response.json()["detail"] == "File is empty"


def test_oversized_file_is_rejected(client, monkeypatch):
    from app.core.config import get_settings

    token = _register_and_login(client, email="oversized@example.com")
    monkeypatch.setenv("MAX_UPLOAD_SIZE_MB", "0")
    get_settings.cache_clear()

    try:
        files = {"file": ("large.txt", BytesIO(b"x"), "text/plain")}
        response = client.post("/api/documents/upload", headers={"Authorization": f"Bearer {token}"}, files=files)
        assert response.status_code == 413
        assert response.json()["detail"] == "File is too large"
    finally:
        get_settings.cache_clear()


def test_approved_and_exported_document_can_be_exported_multiple_times(client, db_session, create_user):
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

    first_export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert first_export_response.status_code == 200
    export_payload = first_export_response.json()
    assert export_payload["document_id"] == document_id
    assert export_payload["review_status"] == "approved"
    assert export_payload["structured_fields"]["document_type"] == "invoice"
    assert "exported_at" in export_payload
    assert export_payload["status"] == "approved"

    second_export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert second_export_response.status_code == 200
    second_payload = second_export_response.json()
    assert second_payload["document_id"] == document_id
    assert second_payload["status"] == "exported"

    export_records = list(
        db_session.scalars(select(ExportRecord).where(ExportRecord.document_id == UUID(document_id)))
    )
    assert len(export_records) == 2


def test_needs_review_document_cannot_be_exported(client):
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
    assert export_response.json()["detail"] == "Only approved or exported documents can be exported"


def test_rejected_document_cannot_be_exported(client, create_user):
    owner = create_user(email="owner-rejected@example.com", password="OwnerPass123!", role=UserRole.USER)
    reviewer = create_user(email="reviewer-rejected@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = client.post("/api/auth/login", json={"email": owner.email, "password": "OwnerPass123!"}).json()[
        "access_token"
    ]
    reviewer_token = client.post(
        "/api/auth/login", json={"email": reviewer.email, "password": "ReviewerPass123!"}
    ).json()["access_token"]

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("request.txt", BytesIO(b"Request document"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    reject = client.post(
        f"/api/reviews/{document_id}/reject",
        json={"reviewer_comment": "Rejected for testing"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert reject.status_code == 200

    export_response = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert export_response.status_code == 409
    assert export_response.json()["detail"] == "Only approved or exported documents can be exported"


def test_user_cannot_read_or_export_another_users_document(client, create_user):
    owner = create_user(email="doc-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    outsider = create_user(email="doc-outsider@example.com", password="OutPass123!", role=UserRole.USER)
    reviewer = create_user(email="doc-reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = client.post("/api/auth/login", json={"email": owner.email, "password": "OwnerPass123!"}).json()[
        "access_token"
    ]
    outsider_token = client.post(
        "/api/auth/login", json={"email": outsider.email, "password": "OutPass123!"}
    ).json()["access_token"]
    reviewer_token = client.post(
        "/api/auth/login", json={"email": reviewer.email, "password": "ReviewerPass123!"}
    ).json()["access_token"]

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #404\nAmount: $100.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    read_other_doc = client.get(
        f"/api/documents/{document_id}",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert read_other_doc.status_code == 403
    assert read_other_doc.json()["detail"] == "Access denied"

    export_other_doc = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {outsider_token}"},
    )
    assert export_other_doc.status_code == 403
    assert export_other_doc.json()["detail"] == "Access denied"

    approve = client.post(
        f"/api/reviews/{document_id}/approve",
        json={"reviewer_comment": "Approved by reviewer"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert approve.status_code == 200

    reviewer_export = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert reviewer_export.status_code == 200


def test_regular_user_sees_only_own_documents(client, create_user):
    create_user(email="list-owner-a@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="list-owner-b@example.com", password="OwnerPass123!", role=UserRole.USER)

    token_a = client.post(
        "/api/auth/login",
        json={"email": "list-owner-a@example.com", "password": "OwnerPass123!"},
    ).json()["access_token"]
    token_b = client.post(
        "/api/auth/login",
        json={"email": "list-owner-b@example.com", "password": "OwnerPass123!"},
    ).json()["access_token"]

    upload_a = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token_a}"},
        files={"file": ("a.txt", BytesIO(b"Invoice #A"), "text/plain")},
    )
    upload_b = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token_b}"},
        files={"file": ("b.txt", BytesIO(b"Invoice #B"), "text/plain")},
    )
    assert upload_a.status_code == 201
    assert upload_b.status_code == 201

    list_a = client.get("/api/documents", headers={"Authorization": f"Bearer {token_a}"})
    list_b = client.get("/api/documents", headers={"Authorization": f"Bearer {token_b}"})
    assert list_a.status_code == 200
    assert list_b.status_code == 200
    assert list_a.json()["total"] == 1
    assert list_b.json()["total"] == 1
    assert list_a.json()["items"][0]["original_filename"] == "a.txt"
    assert list_b.json()["items"][0]["original_filename"] == "b.txt"


def test_extraction_failure_sets_failed_status_and_audit_event(client, db_session, monkeypatch):
    from app.services import workflow_service

    token = _register_and_login(client, email="failing-parser@example.com")
    monkeypatch.setattr(workflow_service, "extract_text_from_file", lambda *_args, **_kwargs: "")

    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("broken.txt", BytesIO(b"Will fail extraction"), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "failed"
    document_id = response.json()["id"]

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert document.processing_error == "Extracted text is empty"

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        ).all()
    }
    assert "document_processing_failed" in actions
