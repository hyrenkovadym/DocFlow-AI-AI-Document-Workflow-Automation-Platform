# AI Pipeline (Phase 5)

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

## Stage 4: Validation and persistence
- AI output is validated by Pydantic schemas.
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

### OpenAICompatibleProvider (available, not activated by default)
- enabled by `AI_PROVIDER=openai`,
- requires environment API key/base URL/model,
- not used in tests.

## Key audit events
- `document_uploaded`
- `document_processing_started`
- `document_text_extracted`
- `ai_extraction_completed`
- `review_task_created`
- `document_processing_failed`
