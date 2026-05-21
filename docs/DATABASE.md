# Database Design

## Tables
- `users`
- `documents`
- `document_extractions`
- `review_tasks`
- `audit_logs`
- `export_records`

## Relationships
- `users` 1..N `documents`
- `documents` 1..1 `document_extractions`
- `documents` 1..1 `review_tasks`
- `users` 1..N `audit_logs`
- `documents` 1..N `export_records`

## Important indexes
- `documents(status, created_at)`
- `documents(owner_id, created_at)`
- `users(email)` unique
- `audit_logs(created_at)`

## Document statuses
- uploaded
- queued
- processing
- needs_review
- approved
- rejected
- exported
- failed

## Notes
- UUID primary keys for entity consistency.
- JSON/JSONB-compatible payload fields for extraction and metadata.
- Audit table stores append-only activity stream.
