# API Reference (v1.0.0)

Base prefix: `/api`

## Auth
- `POST /auth/register`
- `POST /auth/login`
- `GET /auth/me`

## Documents
- `POST /documents/upload`
- `GET /documents`
- `GET /documents/{id}`
- `GET /documents/{id}/text`
- `GET /documents/{id}/extraction`
- `POST /documents/{id}/reprocess`
- `GET /documents/{id}/export.json`
- `GET /documents/{id}/export.csv`

## Review
- `GET /reviews/queue`
- `POST /reviews/{document_id}/approve`
- `POST /reviews/{document_id}/reject`
- `PATCH /reviews/{document_id}/fields`

## Audit
- `GET /audit-logs`

## Operational endpoints
- `GET /health`
  - liveness-oriented app status.
- `GET /ready`
  - readiness/dependency status:
    - `dependencies.database.ok`
    - `dependencies.redis.ok`
    - `dependencies.redis.required`
  - includes `processing_mode` and `ai_provider`.
- `GET /system/info`
  - safe runtime metadata:
    - `app_name`
    - `version`
    - `app_env`
    - `processing_mode`
    - `ai_provider`
    - `redis_configured`
    - `docs_url`
    - `openapi_url`

## Request ID behavior
- API accepts optional request header: `X-Request-ID`.
- If provided, API preserves it.
- If missing, API generates one.
- Response always returns `X-Request-ID`.

## Status lifecycle
- `queued` -> `processing` -> `needs_review`
- final states: `approved`, `rejected`, `exported`, `failed`

## AI provider runtime
- `AI_PROVIDER=mock` (default)
- `AI_PROVIDER=openai` (optional)
  - requires `OPENAI_API_KEY`
  - supports configurable base URL/model/timeout/retries

## Secrets policy
Operational endpoints and standard responses never expose:
- API keys
- JWT secrets
- database/redis passwords

## Interactive docs
- Swagger UI: `/docs`
- OpenAPI JSON: `/openapi.json`
