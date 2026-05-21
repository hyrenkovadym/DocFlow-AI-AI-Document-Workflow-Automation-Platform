# Workflows (Phase 3 MVP)

## UI workflow: login -> upload -> review -> export
1. User opens `/login` and authenticates.
2. User uploads file on `/upload` (`txt`, `pdf`, `docx`).
3. Backend processes synchronously and sets status to `needs_review`.
4. Reviewer/admin opens `/reviews`, optionally edits fields, then approves/rejects.
5. Approved document can be exported from `/documents/{id}`.
6. Admin inspects events on `/audit-logs`.

## Backend processing flow
1. API validates file type and size.
2. File is stored in local upload directory.
3. Pipeline executes:
   - `document_processing_started`
   - text extraction
   - `document_text_extracted`
   - mock AI classification + fields
   - `ai_extraction_completed`
   - review task creation
   - `review_task_created`
4. Document status becomes `needs_review`.

## Review outcomes
- Approve -> status `approved` + `document_approved` audit event.
- Reject -> status `rejected` + `document_rejected` audit event.
- Field patch -> extraction updated via `PATCH /api/reviews/{id}/fields`.

## Export rules
- Only `approved` documents are exportable.
- Export writes `ExportRecord` + `document_exported` audit event.
- Current backend marks document as `exported` after export.

## Failure path
If parsing/processing fails:
1. status becomes `failed`,
2. `processing_error` is stored,
3. `document_processing_failed` audit event is written.
