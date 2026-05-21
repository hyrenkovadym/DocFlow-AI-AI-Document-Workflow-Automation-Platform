# DocFlow AI

**AI-powered document intake and workflow automation platform**

DocFlow AI is a production-style full-stack portfolio project for document operations. Users upload business files, the backend extracts text and structured fields with a mock AI provider, reviewers approve or reject results, and approved data can be exported.

## Problem statement
Teams often process invoices, contracts, requests, and reports manually. This causes inconsistent outputs, slow handoffs, and weak traceability.

DocFlow AI addresses this with:
- secure upload + parsing,
- structured AI extraction with validation,
- human-in-the-loop approval,
- full audit trail,
- export-ready data.

## Current MVP status (Phase 2)
This repository currently implements the first complete backend MVP flow:
- upload document,
- synchronous extraction + mock AI processing,
- review queue + approve/reject + field edits,
- export approved document,
- audit logs for key actions.

Processing is intentionally synchronous in this phase (no Celery runtime required).

## Tech stack
- Backend: Python, FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis (reserved for next phase), Pydantic
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Tooling: pytest, ruff, Docker Compose, GitHub Actions

## Core features
- JWT auth + RBAC (`admin`, `reviewer`, `user`)
- Upload intake (`txt`, `pdf`, `docx`) with size/type validation
- Mock AI provider abstraction (`AIProvider` / `MockAIProvider`)
- Document workflow states (`uploaded`, `processing`, `needs_review`, `approved`, `rejected`, `exported`, `failed`)
- Review queue with reviewer/admin permissions
- JSON/CSV export with export records
- Audit logs for all key workflow events

## Architecture overview
- `apps/api`: FastAPI API, services, models, migrations
- `apps/web`: Next.js dashboard (basic MVP UI)
- `infra/docker-compose.yml`: local Postgres/Redis/API/worker/web services
- `docs/`: architecture, workflows, API, AI, DB, security, roadmap

## Project structure
```text
docflow-ai/
|- apps/
|  |- api/
|  |  |- app/
|  |  |  |- api/routes
|  |  |  |- core
|  |  |  |- db
|  |  |  |- models
|  |  |  |- schemas
|  |  |  |- services
|  |  |  |- workers
|  |  |- alembic/
|  |  |- tests/
|  |- web/
|- infra/
|- docs/
|- .github/workflows/
|- README.md
|- .env.example
```

## Local setup
### 1. Clone and configure
```bash
git clone <repo-url>
cd docflow-ai
cp .env.example .env
```

### 2. Start PostgreSQL and Redis
```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
```

### 3. Backend setup
```bash
cd apps/api
pip install -e .[dev]
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000
```

### 4. Frontend setup (optional for backend-only validation)
```bash
cd apps/web
npm install
npm run dev
```

## Docker setup
Run full stack:
```bash
docker compose -f infra/docker-compose.yml up --build
```

Stop stack:
```bash
docker compose -f infra/docker-compose.yml down
```

## Environment variables
Use `.env.example` as the source of truth.

Important keys:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `UPLOAD_DIR`
- `MAX_UPLOAD_SIZE_MB`
- `ALLOWED_FILE_TYPES`
- `AI_PROVIDER=mock|openai`
- `OPENAI_API_KEY` (optional, not required for MVP)
- `NEXT_PUBLIC_API_BASE_URL`

## API docs and health
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- Health: `http://localhost:8000/api/health`
- Ready: `http://localhost:8000/api/ready`

See also: `docs/API.md`.

## Tests
Backend tests:
```bash
cd apps/api
pytest -q
```

Lint:
```bash
cd apps/api
ruff check .
```

Test database note:
- Tests intentionally run on isolated SQLite for speed and deterministic CI.
- Runtime application uses PostgreSQL.

## Mock AI mode
Default mode is `AI_PROVIDER=mock`.
- No real AI key is required for local development/tests.
- No external AI calls are made in tests.

## Demo credentials (seed)
- Admin: `admin@docflow.local` / `AdminPass123!`
- Reviewer: `reviewer@docflow.local` / `ReviewerPass123!`
- User: `user@docflow.local` / `UserPass123!`

## Manual MVP flow
1. Login as `user`.
2. Upload a TXT/PDF/DOCX file via `POST /api/documents/upload`.
3. Confirm status becomes `needs_review`.
4. Login as `reviewer`, approve/reject from review endpoints.
5. Export approved document via `GET /api/documents/{id}/export.json`.
6. Login as `admin`, inspect `GET /api/audit-logs`.

## Security notes
- No real secrets are committed.
- JWT auth + RBAC on protected routes.
- File type and size validation at upload.
- AI output validated with Pydantic before persistence.
- Audit events retained for traceability.

See: `docs/SECURITY.md` and root `SECURITY.md`.

## Limitations (current MVP)
- Synchronous processing (no asynchronous worker path yet).
- OCR/image ingestion not implemented yet.
- Export is per-document (no bulk export endpoint yet).
- Multi-tenant/company isolation not implemented yet.

## Roadmap
See `docs/ROADMAP.md` for planned next phases:
- async background workers,
- OCR support,
- webhooks/integrations,
- advanced observability,
- deployment hardening.

## Employer-facing summary
I built **DocFlow AI**, a full-stack AI-powered document workflow automation platform with FastAPI, PostgreSQL, Next.js, role-based access control, audit logs, human-in-the-loop review, structured extraction, Docker, tests, and CI-ready engineering practices.
