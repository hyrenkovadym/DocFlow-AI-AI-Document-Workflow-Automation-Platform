# DocFlow AI

AI-powered document intake and workflow automation platform.

## Current phase
Phase 7 adds production-oriented observability and monitoring polish:
- structured JSON logs for API and worker,
- request ID propagation (`X-Request-ID`),
- processing timing metadata (`processing_duration_ms`),
- improved `/api/health`, `/api/ready`, and `/api/system/info`.

Core workflow is unchanged:
upload -> queued -> processing -> needs_review -> approve/reject -> export.

## Tech stack
- Backend: FastAPI, SQLAlchemy 2.x, Alembic, PostgreSQL, Redis, Celery, Pydantic
- Frontend: Next.js, React, TypeScript, Tailwind CSS
- Tooling: pytest, ruff, Docker Compose, GitHub Actions

## AI provider modes
- `AI_PROVIDER=mock` (default): no external API key required.
- `AI_PROVIDER=openai`: OpenAI-compatible endpoint support.
- If openai mode is enabled without key, document processing fails safely per-document; worker remains healthy.

Required vars for openai mode:
- `OPENAI_API_KEY`
- `OPENAI_BASE_URL` (default `https://api.openai.com/v1`)
- `OPENAI_MODEL`
- `OPENAI_TIMEOUT_SECONDS`
- `OPENAI_MAX_RETRIES`

## Observability highlights
- Structured logs include:
  - timestamp, level, logger name,
  - request_id (when available),
  - event/action,
  - document_id/user_id (when safe),
  - status/processing_status,
  - duration_ms (when available).
- Request ID middleware:
  - preserves incoming `X-Request-ID`,
  - generates one when missing,
  - returns it in response header,
  - propagates into audit metadata where possible.
- Processing metadata stored safely on document:
  - `processing_started_at`
  - `processing_finished_at`
  - `processing_duration_ms`

## Safe endpoints
- `GET /api/health`
- `GET /api/ready`
  - reports dependency status (`database`, `redis`),
  - includes `processing_mode`, `ai_provider`,
  - does not require OpenAI.
- `GET /api/system/info`
  - safe runtime config only:
    - `app_name`, `version`, `app_env`,
    - `processing_mode`, `ai_provider`,
    - `redis_configured`, `docs_url`, `openapi_url`.

No secrets are exposed by these endpoints.

## Local setup
```bash
git clone <repo-url>
cd docflow-ai
cp .env.example .env
```

Install backend:
```bash
cd apps/api
pip install -e .[dev]
alembic upgrade head
python -m app.scripts.seed
```

Run API:
```bash
cd apps/api
uvicorn app.main:app --reload --port 8000
```

Run worker:
```bash
cd apps/api
celery -A app.workers.celery_app worker --loglevel=info
```

Run frontend:
```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

## Docker demo
```bash
docker compose -f infra/docker-compose.yml up --build
docker exec docflow-api alembic upgrade head
```

URLs:
- Frontend: `http://localhost:3000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`
- Ready: `http://localhost:8000/api/ready`
- System info: `http://localhost:8000/api/system/info`

Inspect worker logs:
```bash
docker logs -f docflow-worker
```

## Demo checklist
1. Start Docker Compose.
2. Run migrations.
3. Open frontend.
4. Register/login as user.
5. Upload TXT document.
6. Watch status transition `queued -> processing -> needs_review`.
7. Login as reviewer and approve.
8. Export JSON.
9. Login as admin and inspect audit logs.
10. Verify `X-Request-ID`, processing duration, and `/api/system/info`.

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

Frontend lint:
```bash
cd apps/web
npm run lint
```

Frontend build:
```bash
cd apps/web
npm run build
```

Compose validation:
```bash
docker compose -f infra/docker-compose.yml config
```

## Security and logging policy
Intentionally not logged:
- API keys,
- JWT tokens,
- uploaded file content,
- full extracted document text,
- private credentials.

## Known limitations
- No OCR/image pipeline yet.
- Local file storage for uploads in dev mode.
- No bulk export endpoint.
- Frontend session storage is demo-level and documented in `docs/SECURITY.md`.
