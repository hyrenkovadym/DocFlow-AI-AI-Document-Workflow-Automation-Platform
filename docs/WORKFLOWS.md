# Workflows (Phase 6 Async + AI Provider)

## UI flow: login -> upload -> review -> export
1. User logs in at `/login`.
2. User uploads `txt`/`pdf`/`docx` at `/upload`.
3. API returns quickly with status `queued`.
4. Worker processes in background (`processing -> needs_review` or `failed`).
5. Reviewer/admin opens `/reviews`, optionally patches fields, approves/rejects.
6. Approved/exported documents are exportable from `/documents/{id}`.
7. Admin inspects audit trail at `/audit-logs`.

## Upload and async processing
1. Validate file type/size/content.
2. Save file metadata and local upload path.
3. Write `document_uploaded` audit event.
4. Enqueue `process_document_task`.
5. Worker lifecycle:
   - set `processing` + `document_processing_started`,
   - extract text + `document_text_extracted`,
   - resolve AI provider (`mock` by default, `openai` optional),
   - run classification/extraction + `ai_extraction_completed`,
   - create/update review task + `review_task_created`,
   - set status `needs_review`.
6. On errors: status `failed` + `processing_error` + `document_processing_failed`.
7. AI-specific failures also emit `ai_extraction_failed`.

## Review outcomes
- Approve -> `approved` + `document_approved`.
- Reject -> `rejected` + `document_rejected`.
- Field patch -> extraction updated + `review_fields_updated`.

## Export outcomes
- Allowed statuses: `approved`, `exported`.
- Re-export is allowed.
- Each export creates new `ExportRecord` and `document_exported`.
- Other statuses return `409`.

## Reprocess outcomes
`POST /api/documents/{id}/reprocess`:
- allowed for owner/reviewer/admin,
- async mode: status becomes `queued` and task is enqueued,
- sync mode: full pipeline runs inline,
- regular user cannot reprocess someone else's document.

## Frontend async UX
- Document list shows `queued`/`processing` badges.
- Document detail includes refresh action and background-processing note.
- Upload page informs user that processing runs in background.
