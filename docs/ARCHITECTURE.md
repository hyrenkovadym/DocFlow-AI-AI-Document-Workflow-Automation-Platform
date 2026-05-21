# Architecture

DocFlow AI is organized as a full-stack web app with a clear API-first backend and a Next.js frontend.

## Components
- **Web (`apps/web`)**: Next.js App Router UI for auth, dashboard, documents, upload, review, and audit pages.
- **API (`apps/api`)**: FastAPI service for auth, document intake, synchronous processing pipeline, review, export, and audit.
- **Database (PostgreSQL)**: persistent storage for users, documents, extractions, review tasks, audit logs, and exports.
- **Redis**: present in infrastructure for future async jobs; not required in active MVP runtime path.
- **Worker scaffold (`apps/api/app/workers`)**: kept for future Celery phase, not used in current MVP flow.

## Frontend architecture
- `app/*`: route pages (`/login`, `/dashboard`, `/documents`, `/upload`, `/reviews`, `/audit-logs`).
- `components/*`: reusable UI components (`Layout`, `Sidebar`, `Card`, `DataTable`, `StatusBadge`, states, buttons).
- `lib/api.ts`: centralized API client and error handling.
- `lib/auth.ts`: token/role session helpers for demo-mode auth persistence.
- `lib/types.ts`: shared TypeScript contracts for API payloads.

## Backend architecture
- `api/routes`: HTTP endpoints and access boundaries.
- `services`: business logic (auth, document, workflow, export, audit, AI, parser).
- `models`: SQLAlchemy entities.
- `schemas`: Pydantic request/response schemas.
- `alembic`: schema migrations.

## Frontend <-> backend communication
1. User logs in via `POST /api/auth/login`.
2. Frontend stores JWT token in local storage (demo mode).
3. All protected requests include `Authorization: Bearer <token>`.
4. Frontend pages call backend endpoints directly through `lib/api.ts`.
5. API errors (`401`, `403`, validation errors) are surfaced as clear UI messages.

## Data flow (current MVP)
1. User uploads document from UI.
2. API stores metadata and file bytes.
3. API runs synchronous pipeline: parse -> mock classify -> extract fields.
4. API stores extraction + review task and sets status `needs_review`.
5. Reviewer/admin approves or rejects.
6. Approved document can be exported.
7. Audit events are persisted across all critical steps.

## Text diagram

```text
[Next.js Frontend]
        |
        | HTTP (JWT)
        v
[FastAPI API] --------------------> [PostgreSQL]
        |
        +-- synchronous parse + mock AI + review task creation

[Redis + Celery worker scaffold exists for future async phase]
```

## Extension points
- Switch from mock AI to OpenAI-compatible provider via config.
- Activate async worker execution using existing scaffolding.
- Add OCR/image intake and external export integrations.
- Add multi-tenant boundaries and advanced observability.
