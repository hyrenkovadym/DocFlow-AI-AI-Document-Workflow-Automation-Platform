# API Reference (Phase 4 Hardened MVP)

Base prefix: `/api`

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

## Documents
- `POST /documents/upload`
  - Auth required.
  - Multipart field: `file`.
  - Supported types: `txt`, `pdf`, `docx`.
  - Server-side file validation:
    - empty file -> `400`
    - unsupported type -> `400`
    - oversized file -> `413`
  - Runs synchronous parse + mock extraction pipeline.
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/text`
- `GET /documents/{id}/extraction`
- `POST /documents/{id}/reprocess`
  - Allowed for owner/reviewer/admin.
  - For `failed`, `approved`, `exported`, reprocess is allowed and returns document to `needs_review`.
- `GET /documents/{id}/export.json`
- `GET /documents/{id}/export.csv`
  - Export allowed only for statuses: `approved`, `exported`.
  - Other statuses -> `409`.
  - Every export request creates export/audit records.

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

## Permission rules summary
- `user` sees only own documents.
- `user` cannot access review queue.
- `user` cannot approve/reject.
- `user` cannot access audit logs.
- `reviewer`/`admin` can access review queue and review actions.
- `admin` can access audit logs.

## Export payload
`GET /api/documents/{id}/export.json` returns:
- metadata (`document_id`, `owner_id`, filename, status, type),
- `structured_fields`,
- review metadata (`review_status`, `reviewer_comment`),
- export metadata (`exported_at`, `exported_by_id`).

## Interactive docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
