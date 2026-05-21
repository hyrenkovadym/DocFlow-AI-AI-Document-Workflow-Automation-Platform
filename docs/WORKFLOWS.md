# Workflows

## Upload and process
1. User uploads PDF/DOCX/TXT.
2. API creates document with `uploaded` then `queued`.
3. Celery worker sets `processing`, parses text, calls AI provider.
4. Worker stores extraction and marks document `needs_review`.

## Review and approve/reject
1. Reviewer opens review queue.
2. Reviewer inspects extracted fields and edits if needed.
3. Reviewer approves (`approved`) or rejects (`rejected`).

## Export
1. Approved document is exported to JSON or CSV.
2. Export action writes `ExportRecord` and audit event.
3. Status becomes `exported` after export request.

## Admin audit review
1. Admin opens audit logs page/API.
2. Admin traces user actions and processing events for compliance.
