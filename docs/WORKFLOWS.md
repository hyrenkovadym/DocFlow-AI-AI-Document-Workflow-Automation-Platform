# Workflows (v1.0.0)

## End-to-end flow
1. User logs in.
2. User uploads document (`txt`/`pdf`/`docx`).
3. API stores file metadata and enqueues worker task.
4. Worker transitions status:
   - `queued` -> `processing` -> `needs_review` (or `failed`).
5. Reviewer/admin approves or rejects.
6. Approved/exported documents can be exported.

## Observability flow
1. Client sends request (optionally with `X-Request-ID`).
2. API middleware preserves or generates request ID.
3. Request ID is returned in response and attached to structured logs.
4. Audit entries include request ID metadata when available.

## Processing timing flow
On worker processing:
- `processing_started_at` is set,
- `processing_finished_at` is set on completion/failure,
- `processing_duration_ms` is recorded.

These fields are stored in document metadata and reflected in UI detail view.

## Failure debugging flow
If document ends in `failed`:
1. Open document detail and inspect `processing_error`.
2. Check recent audit events:
   - `document_processing_failed`
   - `ai_extraction_failed` (if AI-specific).
3. Check worker logs for matching `document_id` and `request_id`.
4. Reprocess document after fixing root cause.

## Operational checks
- `/api/health`: quick liveness check.
- `/api/ready`: dependency readiness.
- `/api/system/info`: safe runtime metadata (non-secret).
