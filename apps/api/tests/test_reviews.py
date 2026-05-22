from io import BytesIO
from uuid import UUID

from sqlalchemy import select

from app.models.audit import AuditLog
from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, UserRole


def _login(client, *, email: str, password: str) -> str:
    response = client.post("/api/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _upload_needs_review_document(client, owner_token: str) -> str:
    response = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {owner_token}"},
        files={"file": ("contract.txt", BytesIO(b"Contract Agreement\nDate: 2026-05-20"), "text/plain")},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "needs_review"
    return response.json()["id"]


def test_reviewer_can_approve_document(client, db_session, create_user):
    create_user(email="owner2@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = _login(client, email="owner2@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reviewer@example.com", password="ReviewerPass123!")
    document_id = _upload_needs_review_document(client, owner_token)

    approve_response = client.post(
        f"/api/reviews/{document_id}/approve",
        json={"reviewer_comment": "Looks good"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert approve_response.status_code == 200

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.APPROVED

    actions = {
        row[0]
        for row in db_session.execute(
            select(AuditLog.action).where(AuditLog.entity_type == "document", AuditLog.entity_id == document_id)
        ).all()
    }
    assert "document_approved" in actions


def test_reviewer_can_reject_document(client, db_session, create_user):
    create_user(email="owner3@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer2@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = _login(client, email="owner3@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reviewer2@example.com", password="ReviewerPass123!")
    document_id = _upload_needs_review_document(client, owner_token)

    reject_response = client.post(
        f"/api/reviews/{document_id}/reject",
        json={"reviewer_comment": "Missing required details"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert reject_response.status_code == 200

    document = db_session.get(Document, UUID(document_id))
    assert document is not None
    assert document.status == DocumentStatus.REJECTED


def test_regular_user_cannot_approve_or_reject(client, create_user):
    create_user(email="owner4@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer3@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)
    create_user(email="regular@example.com", password="RegularPass123!", role=UserRole.USER)

    owner_token = _login(client, email="owner4@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reviewer3@example.com", password="ReviewerPass123!")
    regular_token = _login(client, email="regular@example.com", password="RegularPass123!")
    document_id = _upload_needs_review_document(client, owner_token)

    approve_as_user = client.post(
        f"/api/reviews/{document_id}/approve",
        json={"reviewer_comment": "I should not approve"},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    reject_as_user = client.post(
        f"/api/reviews/{document_id}/reject",
        json={"reviewer_comment": "I should not reject"},
        headers={"Authorization": f"Bearer {regular_token}"},
    )
    assert approve_as_user.status_code == 403
    assert reject_as_user.status_code == 403
    assert approve_as_user.json()["detail"] == "Insufficient permissions"
    assert reject_as_user.json()["detail"] == "Insufficient permissions"

    approve_as_reviewer = client.post(
        f"/api/reviews/{document_id}/approve",
        json={"reviewer_comment": "Valid reviewer action"},
        headers={"Authorization": f"Bearer {reviewer_token}"},
    )
    assert approve_as_reviewer.status_code == 200


def test_regular_user_cannot_access_review_queue(client, create_user):
    create_user(email="queue-user@example.com", password="UserPass123!", role=UserRole.USER)
    token = _login(client, email="queue-user@example.com", password="UserPass123!")

    response = client.get("/api/reviews/queue", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_reviewer_and_admin_can_access_review_queue(client, create_user):
    create_user(email="queue-owner@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="queue-reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)
    create_user(email="queue-admin@example.com", password="AdminPass123!", role=UserRole.ADMIN)

    owner_token = _login(client, email="queue-owner@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="queue-reviewer@example.com", password="ReviewerPass123!")
    admin_token = _login(client, email="queue-admin@example.com", password="AdminPass123!")

    _upload_needs_review_document(client, owner_token)

    reviewer_response = client.get("/api/reviews/queue", headers={"Authorization": f"Bearer {reviewer_token}"})
    admin_response = client.get("/api/reviews/queue", headers={"Authorization": f"Bearer {admin_token}"})

    assert reviewer_response.status_code == 200
    assert admin_response.status_code == 200
    assert len(reviewer_response.json()) >= 1
    assert len(admin_response.json()) >= 1


def test_reviewer_can_patch_extracted_fields(client, db_session, create_user):
    create_user(email="owner5@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer4@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    owner_token = _login(client, email="owner5@example.com", password="OwnerPass123!")
    reviewer_token = _login(client, email="reviewer4@example.com", password="ReviewerPass123!")
    document_id = _upload_needs_review_document(client, owner_token)

    patch_response = client.patch(
        f"/api/reviews/{document_id}/fields",
        headers={"Authorization": f"Bearer {reviewer_token}"},
        json={
            "structured_fields": {
                "document_type": "contract",
                "title": "Updated Contract Title",
                "summary": "Updated by reviewer",
                "dates": ["2026-05-20"],
                "people_or_companies": ["Contoso Ltd"],
                "amount": None,
                "priority": "medium",
                "recommended_action": "review_content",
                "confidence_score": 0.91,
            }
        },
    )
    assert patch_response.status_code == 200

    extraction = db_session.scalar(
        select(DocumentExtraction).where(DocumentExtraction.document_id == UUID(document_id))
    )
    assert extraction is not None
    assert extraction.structured_fields["title"] == "Updated Contract Title"
