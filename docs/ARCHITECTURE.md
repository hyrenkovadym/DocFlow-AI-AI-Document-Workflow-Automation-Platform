# Architecture

DocFlow AI is a full-stack API-first system with asynchronous document processing and human review controls.

## Core components
- **Web (`apps/web`)**: Next.js UI for auth, dashboard, upload, documents, reviews, and audit visibility.
- **API (`apps/api`)**: FastAPI app for auth, permissions, intake, review, export, and audit endpoints.
- **Worker (`apps/api/app/workers`)**: Celery worker that executes document extraction/classification pipeline.
- **PostgreSQL**: system of record for users, documents, extraction data, review tasks, exports, and audit logs.
- **Redis**: Celery broker/result backend for async task dispatch.

## Backend layering
- `api/routes/*`: endpoint definitions and request/response boundaries.
- `services/*`: business workflows (document, workflow, parser, AI, export, audit).
- `models/*`: SQLAlchemy entities and relationships.
- `schemas/*`: Pydantic models.
- `workers/*`: Celery app + tasks.

## Frontend architecture
- `app/*`: route pages (`/login`, `/dashboard`, `/documents`, `/upload`, `/reviews`, `/audit-logs`).
- `components/*`: reusable UI primitives.
- `lib/api.ts`: centralized fetch client + HTTP error normalization.
- `lib/auth.ts`: JWT storage/session helpers.
- `lib/types.ts`: shared API contracts.

## Processing topology
1. Client uploads file to `POST /api/documents/upload`.
2. API validates file and stores metadata.
3. API sets status `queued` and enqueues Celery task.
4. Worker sets status `processing`, extracts text, runs Mock AI, writes extraction/review task.
5. Worker sets status `needs_review` (or `failed` on errors).
6. Reviewer/admin resolves review; approved docs become exportable.

## Processing modes
- `PROCESSING_MODE=async` (default): API enqueues and returns quickly.
- `PROCESSING_MODE=sync`: API executes pipeline inline (fallback for tests/debugging).

## Text diagram
```text
[Next.js Frontend]
        |
        | HTTP + JWT
        v
[FastAPI API] ------------------------------> [PostgreSQL]
        |
        | enqueue process_document_task
        v
      [Redis]
        |
        v
[Celery Worker] ---> parse + mock classify + extract + review task + audits
```

## Docker notes
- `api` and `worker` share the same uploads volume so worker can read files stored by API.
- `postgres` and `redis` are provided in `infra/docker-compose.yml`.
