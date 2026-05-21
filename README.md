# DocFlow AI

**AI-powered document intake and workflow automation platform**

DocFlow AI is a production-style full-stack portfolio project for internal business document operations.

## What is implemented now
- Backend MVP workflow (Phase 2): upload -> parse -> mock AI extraction -> review -> export -> audit.
- Frontend MVP (Phase 3): login/register, dashboard, documents, upload, detail, review queue, audit logs.
- Processing is synchronous in the current phase.
- No real OpenAI key is required.

## Tech stack
- Backend: FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Pydantic
- Frontend: Next.js (App Router), React, TypeScript, Tailwind CSS
- Tooling: pytest, ruff, Docker Compose, GitHub Actions

## Core features
- JWT auth + RBAC (`admin`, `reviewer`, `user`)
- File upload (`txt`, `pdf`, `docx`) with validation
- Mock AI provider for classification and structured extraction
- Human-in-the-loop review queue with approve/reject and field patching
- Audit logs for key document lifecycle events
- JSON/CSV export from approved records

## Frontend pages
- `/login`
- `/register`
- `/dashboard`
- `/documents`
- `/upload`
- `/documents/{id}`
- `/reviews`
- `/audit-logs`

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

### 3. Run backend
```bash
cd apps/api
pip install -e .[dev]
alembic upgrade head
python -m app.scripts.seed
uvicorn app.main:app --reload --port 8000
```

### 4. Run frontend
```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## URLs
- Frontend: `http://localhost:3000`
- Backend Swagger: `http://localhost:8000/docs`
- Backend health: `http://localhost:8000/api/health`

## Frontend environment variables
`apps/web/.env.example`:
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api`

## Tests and checks
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

Frontend build check:
```bash
cd apps/web
npm run build
```

## Manual demo flow
1. Open `http://localhost:3000/register` and create a user.
2. Login and open `/upload`.
3. Upload TXT/PDF/DOCX.
4. Open `/documents` and verify status becomes `needs_review`.
5. Login as reviewer and open `/reviews` to approve/reject.
6. Open `/documents/{id}` and export JSON for approved record.
7. Login as admin and open `/audit-logs`.

## Security notes
- No real secrets committed.
- Mock AI is default.
- JWT-based protected API access.
- Upload file type and size validation enforced by backend config.

## Current limitations
- Synchronous processing only (no async worker path in active flow yet).
- OCR for images is not implemented.
- No bulk export endpoint yet.
- No multi-tenant organization boundaries yet.

## Employer-facing summary
I built **DocFlow AI**, a full-stack AI-powered document workflow automation platform with FastAPI, PostgreSQL, Next.js, role-based access control, audit logs, human-in-the-loop review, structured extraction, Docker, tests, and CI-ready engineering practices.
