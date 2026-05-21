# Workflows (Phase 4 Hardened MVP)

## UI flow: login -> upload -> review -> export
1. User logs in at `/login`.
2. User uploads `txt`/`pdf`/`docx` from `/upload`.
3. Backend processes synchronously and sets status to `needs_review` (or `failed` on error).
4. Reviewer/admin opens `/reviews`, optionally patches fields, approves/rejects.
5. Approved/exported documents can be exported from `/documents/{id}`.
6. Admin inspects audit trail at `/audit-logs`.

## Processing lifecycle
1. Upload validation:
   - empty file -> `400`
   - unsupported type -> `400`
   - oversized file -> `413`
2. Sync pipeline:
   - `document_processing_started`
   - text extraction
   - `document_text_extracted`
   - mock AI classify/extract
   - `ai_extraction_completed`
   - review task creation (`review_task_created`)
3. Status becomes `needs_review`.

## Review outcomes
- Approve -> `approved` + `document_approved`.
- Reject -> `rejected` + `document_rejected`.
- Field patch -> extraction updated + `review_fields_updated`.

## Export outcomes
- Export allowed for `approved` and `exported`.
- Re-export is allowed.
- Every export creates new `ExportRecord` + `document_exported` event.
- Other statuses return `409`.

## Reprocess outcomes
`POST /api/documents/{id}/reprocess`:
- allowed for owner/reviewer/admin,
- denied for unauthorized users,
- reruns full sync pipeline,
- resets document to `needs_review` after successful reprocess,
- works for `failed`, `approved`, and `exported` documents.

## Failure path
If extraction or processing fails:
1. status -> `failed`,
2. `processing_error` is saved,
3. `document_processing_failed` audit event is written.
