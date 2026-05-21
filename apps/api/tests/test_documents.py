from io import BytesIO

from app.models.document import Document, DocumentExtraction
from app.models.enums import DocumentStatus, DocumentType, UserRole


def test_upload_and_list_documents(client):
    client.post(
        "/api/auth/register",
        json={
            "email": "uploader@example.com",
            "full_name": "Uploader",
            "password": "StrongPass123!",
        },
    )
    login = client.post(
        "/api/auth/login",
        json={"email": "uploader@example.com", "password": "StrongPass123!"},
    )
    token = login.json()["access_token"]

    files = {"file": ("invoice.txt", BytesIO(b"Invoice #42\nAmount: $150.00"), "text/plain")}
    upload = client.post(
        "/api/documents/upload",
        headers={"Authorization": f"Bearer {token}"},
        files=files,
    )
    assert upload.status_code == 201
    assert upload.json()["status"] == "queued"

    listing = client.get("/api/documents", headers={"Authorization": f"Bearer {token}"})
    assert listing.status_code == 200
    assert listing.json()["total"] == 1


def test_export_json_for_approved_document(client, db_session, create_user):
    owner = create_user(email="owner@example.com", password="OwnerPass123!", role=UserRole.USER)

    doc = Document(
        owner_id=owner.id,
        original_filename="report.txt",
        stored_filename="report.txt",
        file_type="txt",
        status=DocumentStatus.APPROVED,
        document_type=DocumentType.REPORT,
        ai_confidence_score=0.9,
    )
    db_session.add(doc)
    db_session.commit()
    db_session.refresh(doc)

    extraction = DocumentExtraction(
        document_id=doc.id,
        structured_fields={"title": "Quarterly report", "summary": "Q1 summary"},
        raw_response={},
        confidence_score=0.9,
    )
    db_session.add(extraction)
    db_session.commit()

    login = client.post(
        "/api/auth/login",
        json={"email": "owner@example.com", "password": "OwnerPass123!"},
    )
    token = login.json()["access_token"]

    exported = client.get(
        f"/api/documents/{doc.id}/export.json",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert exported.status_code == 200
    payload = exported.json()
    assert payload["structured_fields"]["title"] == "Quarterly report"
