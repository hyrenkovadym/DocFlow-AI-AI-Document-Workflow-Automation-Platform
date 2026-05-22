# DocFlow AI

**Full-Stack AI Document Workflow Automation Platform**

DocFlow AI is a production-style portfolio project that demonstrates how to build a realistic internal business automation platform: document intake, AI-assisted extraction, human review, auditability, and export workflows.

## Product Overview
DocFlow AI helps teams process incoming business documents (TXT/PDF/DOCX) and turn unstructured text into reviewable structured data.

### Problem statement
Many teams still process invoices, requests, reports, and contracts manually:
- inconsistent data capture,
- poor traceability,
- slow review loops,
- limited operational visibility.

DocFlow AI addresses this with asynchronous processing, AI provider abstraction, role-based workflows, and auditable actions.

### Target users
- Operations teams handling incoming business documents.
- Finance/admin teams reviewing extraction outputs.
- Internal automation teams that need a safe, extensible workflow platform.

## Key Features
- JWT authentication and RBAC (`user`, `reviewer`, `admin`)
- Document upload with validation (`txt`, `pdf`, `docx`)
- Async processing with Redis + Celery (`queued -> processing -> needs_review`)
- AI provider abstraction:
  - `MockAIProvider` (default)
  - `OpenAICompatibleProvider` (optional)
- Human-in-the-loop review queue (approve/reject/edit fields)
- JSON/CSV export for approved/exported records
- Full audit log trail
- Observability:
  - structured JSON logs,
  - request tracing via `X-Request-ID`,
  - readiness and safe system-info endpoints,
  - processing duration metadata

## Tech Stack
- Backend: FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Celery, Pydantic
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Tooling: pytest, ruff, Docker Compose, GitHub Actions CI

## Architecture Overview
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
                                                  +--> parse + AI + review + audit
```

More detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Screenshots / Demo Assets
Screenshot placeholders are prepared:
- `docs/screenshots/dashboard.png`
- `docs/screenshots/upload-page.png`
- `docs/screenshots/document-detail.png`
- `docs/screenshots/review-queue.png`
- `docs/screenshots/audit-logs.png`
- `docs/screenshots/swagger-docs.png`

Reference notes: [docs/screenshots/README.md](docs/screenshots/README.md)

Screenshots can be added after running the local demo.

## Demo Flow
1. Login as `user@example.com`.
2. Upload a TXT document.
3. Watch status `queued -> processing -> needs_review`.
4. Login as `reviewer@example.com` and approve.
5. Export JSON from document detail.
6. Login as `admin@example.com` and inspect audit logs.
7. Check `/api/ready`, `/api/system/info`, and request ID behavior.

Detailed checklist: [docs/DEMO_CHECKLIST.md](docs/DEMO_CHECKLIST.md)

## Quick Start (Docker)
```bash
docker compose -f infra/docker-compose.yml up --build
docker exec docflow-api alembic upgrade head
docker exec docflow-api python -m app.scripts.seed
```

Useful URLs:
- Frontend: `http://localhost:3000`
- Backend API docs (Swagger): `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/health`
- Backend readiness: `http://localhost:8000/api/ready`
- Backend system info: `http://localhost:8000/api/system/info`

Worker logs:
```bash
docker logs -f docflow-worker
```

## Local Development Setup
1. Clone and configure:
```bash
git clone <repo-url>
cd docflow-ai
cp .env.example .env
```
2. Start dependencies:
```bash
docker compose -f infra/docker-compose.yml up -d postgres redis
```
3. Backend:
```bash
cd apps/api
pip install -e .[dev]
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000
```
4. Worker:
```bash
cd apps/api
celery -A app.workers.celery_app worker --loglevel=info
```
5. Frontend:
```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## Environment Variables
See `.env.example` for the full list.

Core:
- `DATABASE_URL`
- `REDIS_URL`
- `CELERY_BROKER_URL`
- `CELERY_RESULT_BACKEND`
- `PROCESSING_MODE` (`async`/`sync`)
- `AI_PROVIDER` (`mock`/`openai`)

OpenAI-compatible mode:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `OPENAI_MAX_RETRIES`

Frontend:
- `NEXT_PUBLIC_API_BASE_URL`

## Mock AI Mode (Default)
No external AI key required.
```bash
AI_PROVIDER=mock
```

## OpenAI-Compatible Mode (Optional)
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_TIMEOUT_SECONDS=30
OPENAI_MAX_RETRIES=2
```

## Demo Seed Credentials (Local Only)
Created by `python -m app.scripts.seed`:
- Admin: `admin@example.com` / `Password123!`
- Reviewer: `reviewer@example.com` / `Password123!`
- User: `user@example.com` / `Password123!`

These credentials are for local development/demo only.

## Test & Quality Commands
Backend tests:
```bash
cd apps/api
pytest -q
```

Backend lint:
```bash
cd apps/api
ruff check .
```

Frontend lint/build:
```bash
cd apps/web
npm run lint
npm run build
```

Compose validation:
```bash
docker compose -f infra/docker-compose.yml config
```

## Security Notes
- No secrets should be committed to the repository.
- `.env`, credentials files, service account files, and uploads are git-ignored.
- JWT secret must be replaced with a strong value in non-local environments.
- OpenAI key is optional and only read from env vars.
- Frontend token storage is currently demo-level (`localStorage`).
- Uploaded files are treated as untrusted.
- Production deployments should enforce HTTPS.

More: [docs/SECURITY.md](docs/SECURITY.md)

## Known Limitations
- No OCR/image ingestion in current release.
- No multi-tenancy boundaries.
- No external integrations (Sheets/webhooks/email) in v1.0 scope.
- Local file storage for uploads in dev mode.

## Roadmap
See: [docs/ROADMAP.md](docs/ROADMAP.md)

## Repository Metadata Suggestions
Suggested repository description:
`Full-stack AI document workflow automation platform with FastAPI, Next.js, PostgreSQL, Redis, Celery, RBAC, audit logs and OpenAI-compatible provider support.`

Suggested GitHub topics:
- `fastapi`
- `nextjs`
- `postgresql`
- `redis`
- `celery`
- `docker`
- `ai`
- `automation`
- `document-processing`
- `workflow-automation`
- `fullstack`
- `typescript`
- `python`

## Portfolio Summary: What This Project Demonstrates
- End-to-end full-stack architecture (backend + frontend + worker)
- Asynchronous workflow design with Redis/Celery
- AI provider abstraction with safe fallback strategy
- Production-minded auth, RBAC, audit, and export patterns
- Operational readiness via structured logging, request tracing, readiness checks, and safe runtime metadata
- Testable, dockerized, and CI-ready engineering workflow

---

**Employer-facing summary**
DocFlow AI is a full-stack AI document workflow automation platform built with FastAPI, Next.js, PostgreSQL, Redis, Celery, Docker, JWT/RBAC, human review, audit logs, structured AI extraction, OpenAI-compatible provider support, observability, tests and professional documentation.
