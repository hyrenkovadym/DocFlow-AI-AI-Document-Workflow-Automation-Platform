from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, DocumentType, UserRole


def test_reviewer_can_approve_document(client, db_session, create_user):
    owner = create_user(email="owner2@example.com", password="OwnerPass123!", role=UserRole.USER)
    create_user(email="reviewer@example.com", password="ReviewerPass123!", role=UserRole.REVIEWER)

    doc = Document(
        owner_id=owner.id,
        original_filename="contract.txt",
        stored_filename="contract.txt",
        file_type="txt",
        status=DocumentStatus.NEEDS_REVIEW,
        document_type=DocumentType.CONTRACT,
        ai_confidence_score=0.72,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    extraction = DocumentExtraction(
        document_id=doc.id,
        structured_fields={"title": "Contract"},
        raw_response={},
        confidence_score=0.72,
    )
    db_session.add(extraction)
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"email": "reviewer@example.com", "password": "ReviewerPass123!"},
    )
    token = login.json()["access_token"]

    approve = client.post(
        f"/api/reviews/{doc.id}/approve",
        json={"reviewer_comment": "Looks good"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert approve.status_code == 200

    db_session.refresh(doc)
    assert doc.status == DocumentStatus.APPROVED
