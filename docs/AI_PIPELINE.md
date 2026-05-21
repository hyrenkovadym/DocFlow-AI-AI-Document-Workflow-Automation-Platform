# AI Pipeline (Phase 2 MVP)

## Overview
Current MVP uses a synchronous, backend-only pipeline with a mock AI provider by default.

## Step 1: File text extraction
Supported parsers:
- TXT: direct UTF-8/ignore read
- PDF: `pypdf`
- DOCX: `python-docx`

If file type is unsupported or extraction result is empty, processing fails and is audited.

## Step 2: Classification
`AIProvider.classify_document(text)` returns one of:
- `invoice`
- `contract`
- `request`
- `report`
- `unknown`

## Step 3: Structured extraction
`AIProvider.extract_fields(text, document_type)` returns validated fields:
- `document_type`
- `title`
- `summary`
- `dates`
- `people_or_companies`
- `amount`
- `priority`
- `recommended_action`
- `confidence_score`

## Step 4: Validation and persistence
- All AI output is validated by Pydantic schemas.
- Structured data is stored in `DocumentExtraction`.
- Confidence and classification metadata are stored on `Document`.

## Step 5: Human-in-the-loop handoff
- Document status transitions to `needs_review`.
- `ReviewTask` is created/updated as `pending`.
- Reviewer/admin makes final approve/reject decision.

## Providers
### MockAIProvider (default)
- deterministic keyword-based behavior,
- safe for local development and CI,
- no network dependency.

### OpenAICompatibleProvider (available but not required in this phase)
- enabled with `AI_PROVIDER=openai`,
- uses OpenAI-compatible chat completions endpoint,
- never used in tests.

## Key audit events
- `document_processing_started`
- `document_text_extracted`
- `ai_extraction_completed`
- `review_task_created`
- `document_processing_failed`
