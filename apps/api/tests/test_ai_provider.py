from io import BytesIO
from uuid import UUID

import httpx
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.models.audit import AuditLog
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.services.ai.base import AIProviderConfigurationError, AIProviderResponseError
from app.services.ai.factory import get_ai_provider
from app.services.ai.mock_provider import MockAIProvider
from app.services.ai.openai_provider import OpenAICompatibleProvider


class _StubResponse:
    def __init__(self, payload: dict, status_code: int = 200):
        self._payload = payload
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.example.com/chat/completions")
            response = httpx.Response(self.status_code, request=request, json=self._payload)
            raise httpx.HTTPStatusError("request failed", request=request, response=response)

    def json(self) -> dict:
        return self._payload


class _StubClient:
    def __init__(self, responses: list[_StubResponse]):
        self._responses = responses

    def post(self, _path: str, json: dict) -> _StubResponse:
        if not self._responses:
            raise AssertionError("No stub responses left")
        return self._responses.pop(0)


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


def test_default_provider_is_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("AI_PROVIDER", raising=False)
    get_settings.cache_clear()
    try:
        provider = get_ai_provider()
        assert isinstance(provider, MockAIProvider)
    finally:
        get_settings.cache_clear()


def test_explicit_mock_provider_is_used(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "mock")
    get_settings.cache_clear()
    try:
        provider = get_ai_provider()
        assert isinstance(provider, MockAIProvider)
    finally:
        get_settings.cache_clear()


def test_openai_provider_without_key_raises_configuration_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()
    try:
        with pytest.raises(AIProviderConfigurationError):
            get_ai_provider()
    finally:
        get_settings.cache_clear()


def test_openai_provider_parses_valid_mocked_json_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    try:
        settings = get_settings()
        client = _StubClient(
            [
                _StubResponse(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        '{"document_type":"invoice","confidence_score":0.91,'
                                        '"reasoning":"Detected invoice signals"}'
                                    )
                                }
                            }
                        ]
                    }
                ),
                _StubResponse(
                    {
                        "choices": [
                            {
                                "message": {
                                    "content": (
                                        '{"document_type":"invoice","title":"Invoice #101","summary":"Invoice summary",'
                                        '"dates":["2026-05-22"],"people_or_companies":["Contoso"],"amount":"$120.00",'
                                        '"priority":"medium","recommended_action":"review_financials","confidence_score":0.87}'
                                    )
                                }
                            }
                        ]
                    }
                ),
            ]
        )
        provider = OpenAICompatibleProvider(settings=settings, client=client)
        classification = provider.classify_document("Invoice #101")
        extraction = provider.extract_fields("Invoice #101", "invoice")

        assert classification.document_type.value == "invoice"
        assert extraction.document_type.value == "invoice"
        assert extraction.priority == "medium"
        assert extraction.confidence_score == 0.87
    finally:
        get_settings.cache_clear()


def test_openai_provider_handles_invalid_json_response(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    try:
        provider = OpenAICompatibleProvider(
            settings=get_settings(),
            client=_StubClient([_StubResponse({"choices": [{"message": {"content": "not json at all"}}]})]),
        )
        with pytest.raises(AIProviderResponseError):
            provider.classify_document("Some document text")
    finally:
        get_settings.cache_clear()


def test_openai_provider_handles_schema_validation_error(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    get_settings.cache_clear()
    try:
        provider = OpenAICompatibleProvider(
            settings=get_settings(),
            client=_StubClient([_StubResponse({"choices": [{"message": {"content": '{"document_type":"invoice"}'}}]})]),
        )
        with pytest.raises(AIProviderResponseError):
            provider.classify_document("Some document text")
    finally:
        get_settings.cache_clear()


@pytest.fixture()
def async_mode(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PROCESSING_MODE", "async")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_worker_pipeline_uses_provider_factory(client, db_session, monkeypatch, async_mode):
    from app.services import document_service, workflow_service
    from app.services.ai.mock_provider import MockAIProvider
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    token = _register_and_login(client, email="provider-factory@example.com")
    monkeypatch.setattr(document_service.process_document_task, "delay", lambda **_kwargs: None)
    monkeypatch.setattr(
        "app.workers.tasks.process_document_pipeline",
        lambda document_id, actor_id=None: process_document_pipeline_sync(
            db_session, document_id=document_id, actor_id=actor_id
        ),
    )

    called = {"factory_called": False}

    def _provider_factory(*, settings=None):
        called["factory_called"] = True
        return MockAIProvider()

    monkeypatch.setattr(workflow_service, "get_ai_provider", _provider_factory)

    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("invoice.txt", BytesIO(b"Invoice #155\nAmount: $155.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    process_document_task(document_id=document_id)
    assert called["factory_called"] is True


def test_worker_ai_provider_failure_sets_failed_document(client, db_session, monkeypatch, async_mode):
    from app.services import document_service
    from app.services.workflow_service import process_document_pipeline_sync
    from app.workers.tasks import process_document_task

    token = _register_and_login(client, email="provider-failure@example.com")
    monkeypatch.setenv("AI_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    get_settings.cache_clear()

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
        files={"file": ("invoice.txt", BytesIO(b"Invoice #300\nAmount: $300.00"), "text/plain")},
    )
    assert upload.status_code == 201
    document_id = upload.json()["id"]

    process_document_task(document_id=document_id)

    db_session.expire_all()
    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.FAILED
    assert document.processing_error is not None
    assert "OPENAI_API_KEY is required when AI_PROVIDER=openai" in document.processing_error

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        ).all()
    }
    assert "document_processing_failed" in actions
    assert "ai_extraction_failed" in actions
