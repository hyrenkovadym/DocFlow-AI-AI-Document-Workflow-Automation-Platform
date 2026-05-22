from io import BytesIO
from uuid import UUID

import pytest
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


@pytest.fixture()
def async_mode(monkeypatch: pytest.MonkeyPatch):
    from app.core.config import get_settings

    monkeypatch.setenv("PROCESSING_MODE", "async")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_async_upload_sets_queued_and_enqueues_task(client, db_session, monkeypatch, async_mode):
    from app.services import document_service

    token = _register_and_login(client, email="async-uploader@example.com")
    enqueued: dict[str, str | None] = {}

    def fake_delay(*, document_id: str, actor_id: str | None = None, request_id: str | None = None):
        enqueued["document_id"] = document_id
        enqueued["actor_id"] = actor_id
        enqueued["request_id"] = request_id
        return None

    monkeypatch.setattr(document_service.process_document_task, "delay", fake_delay)

    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #123\nAmount: $350.00"), "text/plain")},
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == DocumentStatus.QUEUED.value

    document_id = payload["id"]
    assert enqueued["document_id"] == document_id
    assert enqueued["actor_id"] is not None
    assert enqueued["request_id"] is not None

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.QUEUED


def test_async_task_processing_creates_extraction_review_and_audits(client, db_session, monkeypatch, async_mode):
    from app.services import document_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    token = _register_and_login(client, email="async-process@example.com")
    monkeypatch.setattr(document_service.process_document_task, "delay", lambda **_kwargs: None)
    monkeypatch.setattr(
        "app.workers.tasks.process_document_pipeline",
        lambda document_id, actor_id=None: process_document_pipeline_sync(
            db_session, document_id=document_id, actor_id=actor_id
        ),
    )

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #501\nDate: 2026-05-21\nAmount: $42.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    process_document_task(document_id=document_id)

    db_session.expire_all()
    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.NEEDS_REVIEW
    assert document.document_type.value == "invoice"
    assert document.extracted_text is not None

    extraction = db_session.scalar(select(DocumentExtraction).where(DocumentExtraction.document_id == document.id))
    assert extraction is not None
    assert extraction.structured_fields["document_type"] == "invoice"

    review_task = db_session.scalar(select(ReviewTask).where(ReviewTask.document_id == document.id))
    assert review_task is not None
    assert review_task.status.value == "pending"

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        ).all()
    }
    assert "document_uploaded" in actions
    assert "document_processing_started" in actions
    assert "document_text_extracted" in actions
    assert "ai_extraction_completed" in actions
    assert "review_task_created" in actions


def test_async_task_failure_sets_failed_and_processing_error(client, db_session, monkeypatch, async_mode):
    from app.services import document_service, workflow_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    token = _register_and_login(client, email="async-fail@example.com")
    monkeypatch.setattr(document_service.process_document_task, "delay", lambda **_kwargs: None)
    monkeypatch.setattr(
        "app.workers.tasks.process_document_pipeline",
        lambda document_id, actor_id=None: process_document_pipeline_sync(
            db_session, document_id=document_id, actor_id=actor_id
        ),
    )

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("broken.txt", BytesIO(b"broken"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    monkeypatch.setattr(workflow_service, "extract_text_from_file", lambda *_args, **_kwargs: "")
    process_document_task(document_id=document_id)

    db_session.expire_all()
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


def test_async_reprocess_sets_queued_and_enqueues_task(client, db_session, create_user, monkeypatch, async_mode):
    from app.services import document_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    owner = create_user(email="async-reprocess-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    owner_token = client.post("/api/auth/login", json={"email": owner.email, "password": "OwnerPass123!"}).json()[
        "access_token"
    ]

    enqueued_ids: list[str] = []

    def fake_delay(*, document_id: str, actor_id: str | None = None, request_id: str | None = None):
        enqueued_ids.append(document_id)
        return None

    monkeypatch.setattr(document_service.process_document_task, "delay", fake_delay)
    monkeypatch.setattr(
        "app.workers.tasks.process_document_pipeline",
        lambda document_id, actor_id=None: process_document_pipeline_sync(
            db_session, document_id=document_id, actor_id=actor_id
        ),
    )

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("request.txt", BytesIO(b"Request initial"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]
    assert upload.json()["status"] == "queued"
    assert enqueued_ids[-1] == document_id

    process_document_task(document_id=document_id)

    reprocess = client.post(
        f"/api/documents/{document_id}/reprocess",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert reprocess.status_code == 200
    assert reprocess.json()["status"] == "queued"
    assert enqueued_ids[-1] == document_id

    db_session.expire_all()
    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.QUEUED


def test_export_still_works_after_async_processing_and_approval(
    client, db_session, create_user, monkeypatch, async_mode
):
    from app.services import document_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    owner = create_user(email="async-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    reviewer = create_user(email="async-reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = client.post("/api/auth/login", json={"email": owner.email, "password": "OwnerPass123!"}).json()[
        "access_token"
    ]
    reviewer_token = client.post(
        "/api/auth/login", json={"email": reviewer.email, "password": "ReviewerPass123!"}
    ).json()["access_token"]

    monkeypatch.setattr(document_service.process_document_task, "delay", lambda **_kwargs: None)
    monkeypatch.setattr(
        "app.workers.tasks.process_document_pipeline",
        lambda document_id, actor_id=None: process_document_pipeline_sync(
            db_session, document_id=document_id, actor_id=actor_id
        ),
    )

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #808\nAmount: $500.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    process_document_task(document_id=document_id)

    approve = client.post(
        f"/api/reviews/{document_id}/approve",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={"reviewer_comment": "Approved"},
    )
    assert approve.status_code == 200

    export = client.get(
        f"/api/documents/{document_id}/export.json",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert export.status_code == 200
    assert export.json()["document_id"] == document_id
