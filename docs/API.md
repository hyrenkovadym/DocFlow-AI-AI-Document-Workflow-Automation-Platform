# API Reference (MVP)

Base URL: `/api`

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

### Register request
```json
{
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "password": "StrongPass123!"
}
```

## Documents
- `POST /documents/upload` (multipart `file`)
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/text`
- `GET /documents/{id}/extraction`
- `POST /documents/{id}/reprocess`
- `GET /documents/{id}/export.json`
- `GET /documents/{id}/export.csv`

## Reviews
- `GET /reviews/queue` (reviewer/admin)
- `POST /reviews/{document_id}/approve`
- `POST /reviews/{document_id}/reject`
- `PATCH /reviews/{document_id}/fields`

## Audit
- `GET /audit-logs` (admin)

## Health
- `GET /health`
- `GET /ready`

## Interactive docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
