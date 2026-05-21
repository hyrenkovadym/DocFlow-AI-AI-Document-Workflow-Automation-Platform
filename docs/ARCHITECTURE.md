# Architecture

DocFlow AI is split into API, worker, database, cache/queue, and web UI layers.

## Components
- **Web (`apps/web`)**: Next.js dashboard for authentication, upload, review, and audit visibility.
- **API (`apps/api`)**: FastAPI service exposing REST endpoints and business workflow orchestration.
- **Worker (`apps/api/app/workers`)**: Celery consumer that performs asynchronous parsing + AI extraction.
- **Database (PostgreSQL)**: durable storage for users, documents, extractions, review tasks, audit logs, exports.
- **Redis**: Celery broker/backend for background jobs.

## Data flow
1. User authenticates and uploads a document.
2. API stores file metadata and queues `process_document_task`.
3. Worker extracts text, classifies document, extracts structured fields, persists extraction and review task.
4. Reviewer updates fields and approves/rejects.
5. Approved records can be exported as JSON or CSV.
6. Each important action writes an audit event.

## Text diagram

```text
[Next.js Web]
     |
     v
[FastAPI API] -----> [PostgreSQL]
     |
     +---- enqueue ----> [Redis] ---> [Celery Worker]
                               |            |
                               +------------+
                               text parsing + AI extraction
```

## Backend layering
- `api/routes`: transport layer and request validation.
- `services`: domain logic (auth, documents, workflow, export, audit, AI).
- `models`: SQLAlchemy entities.
- `schemas`: Pydantic contracts.
- `workers`: async task runtime.

## Extension points
- AI provider interface can support multiple vendors.
- Document parser can add OCR/image intake later.
- Export pipeline can add webhooks/Google Sheets/CRM sinks.
