# AI Pipeline (Phase 6)

## Overview
DocFlow AI uses a background worker pipeline. The API enqueues processing, and Celery workers execute extraction and AI classification.

## Stage 1: Text extraction
Supported parsers:
- TXT: UTF-8 read (`errors="ignore"`).
- PDF: `pypdf`.
- DOCX: `python-docx`.

If extraction fails or output is empty, document is marked `failed`.

## Stage 2: Classification
`AIProvider.classify_document(text)` returns:
- `invoice`
- `contract`
- `request`
- `report`
- `unknown`

## Stage 3: Structured field extraction
`AIProvider.extract_fields(text, document_type)` returns:
- `document_type`
- `title`
- `summary`
- `dates`
- `people_or_companies`
- `amount`
- `priority`
- `recommended_action`
- `confidence_score`

Allowed values:
- `document_type`: `invoice`, `contract`, `request`, `report`, `unknown`
- `priority`: `low`, `medium`, `high`
- `confidence_score`: `0..1`

## Stage 4: Validation and persistence
- AI output is validated by Pydantic schemas before persistence.
- Structured payload is stored in `DocumentExtraction`.
- `document_type`, confidence, and pipeline metadata are stored on `Document`.

## Stage 5: Human review handoff
- Review task is created/updated to `pending`.
- Document status transitions to `needs_review`.
- Reviewer/admin makes final decision (`approve`/`reject`).

## Providers
### MockAIProvider (default)
- deterministic keyword-based behavior,
- safe for local dev/CI,
- no external network dependency.

### OpenAICompatibleProvider (optional)
- enabled by `AI_PROVIDER=openai`,
- requires `OPENAI_API_KEY`,
- supports custom `OPENAI_BASE_URL`, model, timeout, and retries,
- requests strict JSON output and validates with Pydantic,
- malformed/invalid outputs are treated as document-level failures (worker remains healthy),
- never used in tests (tests mock all external calls).

## Prompt safety rules
Prompts enforce:
- JSON-only response,
- no invented values,
- use `null`/empty arrays when unknown,
- output is preliminary automation assistance, not final business truth.

## Failure handling
- Missing API key in openai mode -> document status `failed` with clear `processing_error`.
- Timeout/network/rate-limit/invalid JSON/schema failures -> document status `failed`.
- Worker process does not crash; failures are isolated per document.

## Key audit events
- `document_uploaded`
- `document_processing_started`
- `document_text_extracted`
- `ai_extraction_completed`
- `ai_extraction_failed`
- `review_task_created`
- `document_processing_failed`
