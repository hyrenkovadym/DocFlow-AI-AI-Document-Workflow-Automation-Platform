# AI Pipeline (Phase 7)

## Provider strategy
- Default: `MockAIProvider` (`AI_PROVIDER=mock`)
- Optional: `OpenAICompatibleProvider` (`AI_PROVIDER=openai`)

OpenAI mode is optional and never required for tests or local demo.

## Extraction schema
Validated fields:
- `document_type` (`invoice|contract|request|report|unknown`)
- `title`
- `summary`
- `dates`
- `people_or_companies`
- `amount`
- `priority` (`low|medium|high`)
- `recommended_action`
- `confidence_score` (`0..1`)

## Runtime flow
1. Worker extracts text.
2. Provider classifies document.
3. Provider extracts structured fields.
4. Pydantic validation enforces schema.
5. Document extraction + metadata are persisted.
6. Review task is created/updated.

## Safety and failure handling
- Missing key in openai mode -> document-level failure.
- Timeout/network/rate-limit/invalid JSON/schema errors -> document-level failure.
- Worker process remains healthy; failures are isolated to document records.

## Confidence and review
- Confidence score is persisted.
- `below_threshold` flag is set from configured minimum confidence.
- Human review remains required before export decisions.

## Observability
- Structured logs track AI stage events.
- Audit events:
  - `ai_extraction_completed`
  - `ai_extraction_failed` (when applicable)
- Duration metadata is attached (`processing_duration_ms`) for operational visibility.

## Logging policy
AI logs intentionally avoid:
- API keys,
- raw token values,
- full extracted document text.
