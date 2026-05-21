# API Reference (Phase 2 MVP)

Base prefix: `/api`

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

## Documents
- `POST /documents/upload`
  - Auth required.
  - Accepts multipart `file`.
  - Supported types: `txt`, `pdf`, `docx`.
  - Validates max size by `MAX_UPLOAD_SIZE_MB`.
  - Runs synchronous processing pipeline and returns updated document state.
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/text`
- `GET /documents/{id}/extraction`
- `POST /documents/{id}/reprocess`
- `GET /documents/{id}/export.json`
- `GET /documents/{id}/export.csv`

## Review
- `GET /reviews/queue` (reviewer/admin)
- `POST /reviews/{document_id}/approve` (reviewer/admin)
- `POST /reviews/{document_id}/reject` (reviewer/admin)
- `PATCH /reviews/{document_id}/fields` (reviewer/admin)

## Audit
- `GET /audit-logs` (admin only)

## Health
- `GET /health`
- `GET /ready`

## Example: Upload document
`POST /api/documents/upload` with multipart field `file`.

Expected flow:
1. record created with metadata,
2. text extracted,
3. mock AI classification + field extraction,
4. extraction/review task persisted,
5. status set to `needs_review`.

## Example: Export JSON response shape
`GET /api/documents/{id}/export.json` returns payload including:
- document metadata (`document_id`, `owner_id`, filename, status, type),
- `structured_fields`,
- `review_status`,
- `exported_at`, `exported_by_id`.

Export rules:
- only `approved` documents are exportable,
- non-approved exports return `409 Conflict`.

## Interactive docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
