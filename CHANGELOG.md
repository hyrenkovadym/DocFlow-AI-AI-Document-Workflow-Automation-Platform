# Changelog

All notable changes to this project are documented in this file.

## v1.0.0
- Full-stack document workflow MVP
- Async Celery processing
- Mock/OpenAI-compatible AI providers
- Human review workflow
- Export system
- Audit logs
- Observability and request tracing
- Frontend dashboard
- Dockerized local development
- Tests and CI-ready structure

## 0.2.0 - 2026-05-21
- Built DocFlow AI MVP full-stack architecture from scratch.
- Added FastAPI backend with JWT auth, RBAC, document lifecycle, review workflow, audit logs, exports.
- Added Celery worker pipeline with Redis and AI provider abstraction (mock + OpenAI-compatible).
- Added SQLAlchemy models, Alembic migration, seed script, and backend tests.
- Added Next.js frontend dashboard with auth, upload flow, status tables, review queue, and audit screen.
- Added Docker Compose stack, API/worker/web Dockerfiles, and GitHub Actions CI.
- Added professional docs for architecture, API, workflows, AI pipeline, database, security, and roadmap.
