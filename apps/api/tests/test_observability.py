from io import BytesIO
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.document import Document
from app.models.enums import DocumentStatus


def _register_and_login(client, *, email: str, password: str = "StrongPass123!") -> str:
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "full_name": "Observer",
            "password": password,
        },
    )
    login_response = client.post("/api/auth/login", json={"email": email, "password": password})
    return login_response.json()["access_token"]


def test_request_id_header_is_added_when_missing(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert isinstance(request_id, str)
    assert len(request_id) > 0


def test_custom_request_id_is_preserved(client):
    response = client.get("/api/health", headers={"X-Request-ID": "req-observability-001"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "req-observability-001"


@pytest.fixture()
def async_mode(monkeypatch: pytest.MonkeyPatch):
    from app.core.config import get_settings

    monkeypatch.setenv("PROCESSING_MODE", "async")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_processing_duration_is_recorded_in_document_metadata_and_audit(client, db_session, monkeypatch, async_mode):
    from app.services import document_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    token = _register_and_login(client, email="duration@example.com")
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
        files={"file": ("invoice.txt", BytesIO(b"Invoice #907\nAmount: $907.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]
    process_document_task(document_id=document_id)

    db_session.expire_all()
    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.NEEDS_REVIEW
    assert isinstance(document.metadata_json.get("processing_duration_ms"), int)
    assert document.metadata_json.get("processing_duration_ms") >= 0
    assert isinstance(document.metadata_json.get("processing_started_at"), str)
    assert isinstance(document.metadata_json.get("processing_finished_at"), str)

    ai_completed = db_session.scalar(
        select(AuditLog).where(
            AuditLog.entity_type == "document",
            AuditLog.entity_id == document_id,
            AuditLog.action == "ai_extraction_completed",
        )
    )
    assert ai_completed is not None
    assert isinstance(ai_completed.metadata_json.get("duration_ms"), int)


def test_audit_metadata_does_not_include_api_keys(client, db_session):
    token = _register_and_login(client, email="audit-safe@example.com")
    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #500"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    events = list(
        db_session.scalars(
            select(AuditLog).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        )
    )
    assert events
    for event in events:
        serialized_metadata = str(event.metadata_json).lower()
        assert "openai_api_key" not in serialized_metadata
        assert "secret_key" not in serialized_metadata
        assert "authorization" not in serialized_metadata
