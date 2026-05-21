# AI Pipeline

## Step 1: Text extraction
- TXT: raw text read.
- PDF: page text extraction with `pypdf`.
- DOCX: paragraph extraction with `python-docx`.

## Step 2: Classification
`AIProvider.classify_document(text)` predicts one of:
- invoice
- contract
- request
- report
- unknown

## Step 3: Structured extraction
`AIProvider.extract_fields(text, document_type)` returns:
- title
- summary
- dates
- people_or_companies
- amount
- priority
- recommended_action
- confidence_score

## Step 4: Validation
- All AI outputs are validated by Pydantic schemas.
- Invalid payloads fail processing and create `processing_failed` audit event.

## Step 5: Human-in-the-loop
- Worker always creates a review task.
- Reviewer can patch extracted fields before approval.
- Low confidence is persisted in document metadata for reviewer context.

## Providers
- `MockAIProvider`: deterministic local behavior for tests/demo.
- `OpenAICompatibleProvider`: runtime calls to OpenAI-compatible `/chat/completions` API.
