# Workflows (Phase 2 MVP)

## 1. Upload and process document
1. Authenticated user uploads `txt`/`pdf`/`docx`.
2. API validates file type and file size.
3. File is stored in local upload directory.
4. Pipeline runs synchronously:
   - `document_processing_started`
   - text extraction
   - `document_text_extracted`
   - mock AI classification/field extraction
   - `ai_extraction_completed`
   - review task creation
   - `review_task_created`
5. Document status becomes `needs_review`.

## 2. Review queue and decision
1. Reviewer/admin opens `/api/reviews/queue`.
2. Reviewer inspects extraction and optionally updates fields.
3. Reviewer approves or rejects:
   - approve => document status `approved`, audit `document_approved`
   - reject => document status `rejected`, audit `document_rejected`

## 3. Export
1. Only approved documents are exportable.
2. Owner/reviewer/admin can export JSON (and CSV if needed).
3. Export creates `ExportRecord`, audit `document_exported`, and marks status `exported`.

## 4. Audit review
1. Admin opens `/api/audit-logs`.
2. Admin can trace user actions and workflow lifecycle events for compliance/debugging.

## Failure path
If parsing/processing fails:
1. document status becomes `failed`,
2. processing error is stored,
3. audit event `document_processing_failed` is written.
