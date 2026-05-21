# DocFlow AI

**AI-powered document intake and workflow automation platform**

DocFlow AI is a production-style full-stack system for operational document processing. Teams can upload business files, run AI-assisted extraction, review structured output, keep audit trails, and export approved data.

## Problem statement
Business operations teams often process invoices, contracts, requests, and reports manually. This slows workflows, creates inconsistent outputs, and makes auditing difficult.

DocFlow AI addresses this with a human-in-the-loop workflow:
- asynchronous text extraction and AI structuring,
- reviewer approval gates,
- role-based access,
- export-ready normalized data.

## Target users
- Operations specialists
- Back-office/review teams
- Internal automation engineering teams
- Admin/compliance owners

## Core features
- FastAPI backend with JWT authentication and RBAC (`admin`, `reviewer`, `user`)
- Upload intake for `PDF`, `DOCX`, `TXT`
- Background processing with Celery + Redis
- AI provider abstraction:
  - `MockAIProvider` for local/demo/tests
  - `OpenAICompatibleProvider` via environment variables
- Structured extraction validation through Pydantic
- Human review queue with approve/reject + field edits
- Audit logs for critical actions
- JSON/CSV export for approved documents
- Next.js dashboard with upload, status table, review queue, audit view
- Docker Compose local stack
- Backend tests + CI workflow

## Architecture overview
- `apps/api`: FastAPI API + domain services + worker tasks
- `apps/web`: Next.js frontend dashboard
- `infra/docker-compose.yml`: PostgreSQL, Redis, API, worker, web
- `docs/`: architecture/API/security/database/workflow documentation

See detailed architecture: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)

## Tech stack
- Backend: Python, FastAPI, SQLAlchemy 2.x, Alembic, Celery, Redis, PostgreSQL, Pydantic
- Frontend: Next.js 14, React, TypeScript, Tailwind CSS
- Tooling: pytest, ruff, GitHub Actions, Docker Compose

## Project structure
```text
docflow-ai/
+- apps/
¦  +- api/
¦  ¦  +- app/
¦  ¦  ¦  +- api/routes
¦  ¦  ¦  +- core
¦  ¦  ¦  +- db
¦  ¦  ¦  +- models
¦  ¦  ¦  +- schemas
¦  ¦  ¦  +- services
¦  ¦  ¦  +- workers
¦  ¦  ¦  L- scripts
¦  ¦  +- alembic/
¦  ¦  L- tests/
¦  L- web/
+- infra/
+- docs/
L- .github/workflows/
```

## Local setup
### 1. Clone and configure
```bash
git clone <repo-url>
cd docflow-ai
cp .env.example .env
```

### 2. Backend setup
```bash
cd apps/api
pip install -e .[dev]
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000
```

### 3. Worker setup
```bash
cd apps/api
celery -A app.workers.celery_app.celery_app worker -l info
```

### 4. Frontend setup
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
Use `.env.example` as source of truth.

Key values:
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `AI_PROVIDER=mock|openai`
- `OPENAI_API_KEY` (optional for real provider)
- `NEXT_PUBLIC_API_BASE_URL`

## API docs
- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

Reference: [`docs/API.md`](docs/API.md)

## Tests
Backend tests:
```bash
cd apps/api
pytest
```

Lint:
```bash
cd apps/api
ruff check .
```

Frontend checks:
```bash
cd apps/web
npm run lint
npm run typecheck
npm run build
```

## Demo credentials (seed)
- Admin: `admin@docflow.local` / `AdminPass123!`
- Reviewer: `reviewer@docflow.local` / `ReviewerPass123!`
- User: `user@docflow.local` / `UserPass123!`

## Demo flow
1. Login as `user`, upload a TXT/PDF/DOCX document.
2. Wait for worker processing.
3. Login as `reviewer`, open review queue and approve/reject.
4. Export approved document as JSON or CSV.
5. Login as `admin`, inspect audit logs.

## Security notes
- No hardcoded secrets in repository.
- Mock AI default for local/CI.
- AI output is validated before persistence.
- Uploaded files are constrained by type and size.

See: [`docs/SECURITY.md`](docs/SECURITY.md) and root [`SECURITY.md`](SECURITY.md)

## Limitations (current MVP)
- No OCR pipeline for images yet.
- No multi-tenant company/workspace segmentation.
- Export is per-document, not bulk yet.

## Roadmap
See [`docs/ROADMAP.md`](docs/ROADMAP.md) for planned OCR, webhooks, external integrations, observability, and Kubernetes direction.

## Portfolio summary
I built **DocFlow AI**, a full-stack AI-powered document workflow automation platform with FastAPI, PostgreSQL, Redis workers, Next.js, role-based access control, audit logs, human-in-the-loop review, structured AI extraction, Docker, tests, CI, and professional documentation.
