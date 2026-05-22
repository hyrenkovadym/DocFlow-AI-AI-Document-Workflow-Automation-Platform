# Demo Checklist (v1.0.0)

Use this checklist to run and validate the local end-to-end demo.

## Setup
1. Start Docker services:
   - `docker compose -f infra/docker-compose.yml up --build`
2. Run database migrations:
   - `docker exec docflow-api alembic upgrade head`
3. Seed demo data:
   - `docker exec docflow-api python -m app.scripts.seed`

## URLs
1. Frontend: `http://localhost:3000`
2. Backend API docs: `http://localhost:8000/docs`
3. Health: `http://localhost:8000/api/health`
4. Ready: `http://localhost:8000/api/ready`
5. System info: `http://localhost:8000/api/system/info`

## Demo credentials (local-only)
1. Admin: `admin@example.com` / `Password123!`
2. Reviewer: `reviewer@example.com` / `Password123!`
3. User: `user@example.com` / `Password123!`

## Workflow validation
1. Login as `user@example.com`.
2. Upload a TXT document from `/upload`.
3. Confirm status transitions:
   - `queued` -> `processing` -> `needs_review`
4. Login as `reviewer@example.com`.
5. Open review queue and approve the document.
6. Export JSON from document detail.
7. Login as `admin@example.com`.
8. Open `/audit-logs` and confirm lifecycle events.

## Operational validation
1. Call `/api/ready` and confirm dependency status payload.
2. Call `/api/system/info` and confirm safe config output.
3. Verify request ID behavior:
   - send `X-Request-ID` header manually in a request,
   - confirm same value is returned in response header.

## Observability validation
1. Inspect worker logs:
   - `docker logs -f docflow-worker`
2. Confirm logs include safe structured events with:
   - request/document IDs,
   - status transitions,
   - processing duration.

## Security sanity checks
1. Confirm no `.env` or credentials files are committed.
2. Confirm no API keys are present in logs or endpoint responses.
