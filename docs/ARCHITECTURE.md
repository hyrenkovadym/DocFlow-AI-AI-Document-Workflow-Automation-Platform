# Architecture

DocFlow AI is an API-first full-stack system with async processing and operational observability.

## Components
- Web (`apps/web`): Next.js UI for auth, dashboard, documents, upload, review, and audit visibility.
- API (`apps/api`): FastAPI for auth, intake, review, export, audit, health/readiness/system endpoints.
- Worker (`apps/api/app/workers`): Celery worker for document processing.
- PostgreSQL: system of record for users, documents, extractions, review tasks, exports, audits.
- Redis: Celery broker/result backend.

## Backend layers
- `api/routes/*`: HTTP contracts and access boundaries.
- `services/*`: business logic.
- `services/ai/*`: AI provider abstraction (`mock` + `openai`).
- `models/*`: SQLAlchemy entities.
- `schemas/*`: Pydantic schemas.
- `workers/*`: Celery app + tasks.
- `core/*`: config, security, logging, request context.

## Async processing topology
1. API receives upload.
2. API persists file metadata and sets document to `queued`.
3. API enqueues Celery task.
4. Worker sets `processing`, extracts text, calls AI provider, writes extraction/review task.
5. Worker sets `needs_review` (or `failed` with error metadata).

## Observability architecture
- Request ID middleware:
  - reads/generates `X-Request-ID`,
  - returns header in response,
  - injects request ID into logging context.
- Structured JSON logging:
  - API and worker use consistent log payload shape.
- Audit enrichment:
  - audit metadata includes request ID when available.
- Processing metrics:
  - `processing_started_at`, `processing_finished_at`, `processing_duration_ms` stored in document metadata.

## Health model
- `/api/health`: app-level liveness.
- `/api/ready`: dependency readiness (`database`, `redis`) + mode/provider context.
- `/api/system/info`: safe runtime metadata (non-secret only).

## Text diagram
```text
[Next.js Frontend]
        |
        | HTTP + JWT + X-Request-ID
        v
[FastAPI API] ------------------------------> [PostgreSQL]
        |                                         ^
        | enqueue process_document_task           |
        v                                         |
      [Redis] ------------------------------> [Celery Worker]
                                                  |
                                                  +--> parse + AI + review task + audits
```
