# API Reference (Phase 5 Async MVP)

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
  - Validates:
    - empty file -> `400`
    - unsupported type -> `400`
    - oversized file -> `413`
  - `PROCESSING_MODE=async`:
    - creates document with status `queued`,
    - enqueues Celery task,
    - returns quickly.
  - `PROCESSING_MODE=sync`:
    - runs full pipeline inline.
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/text`
- `GET /documents/{id}/extraction`
- `POST /documents/{id}/reprocess`
  - owner/reviewer/admin only,
  - async mode: sets `queued` + enqueues task,
  - sync mode: runs inline,
  - regular user cannot reprocess others' documents.
- `GET /documents/{id}/export.json`
- `GET /documents/{id}/export.csv`
  - export allowed only for `approved` or `exported`,
  - any other status -> `409`,
  - each export creates new export record + audit event.

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

## Status lifecycle
- Intake: `uploaded` (sync only) or `queued` (async)
- Worker: `processing`
- Review handoff: `needs_review`
- Review outcome: `approved` or `rejected`
- Exported: `exported`
- Failure: `failed`

## Permission summary
- `user`: only own documents, no review queue, no audit logs.
- `reviewer`: review queue + review actions, can access docs under current policy.
- `admin`: reviewer permissions + audit logs access.

## Export payload (JSON)
`GET /api/documents/{id}/export.json` returns:
- document metadata (`document_id`, `owner_id`, filename, status, type),
- confidence and `structured_fields`,
- review fields (`review_status`, `reviewer_comment`),
- export metadata (`exported_at`, `exported_by_id`).

## Interactive docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
