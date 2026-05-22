# Roadmap

## Next phase (Phase 7)
- Observability and monitoring foundation for API + worker:
  - structured logging strategy,
  - Celery task metrics and failure dashboards,
  - processing latency/error-rate tracking.
- Confidence calibration and extraction quality analytics.
- Provider failover/health policy automation.

## Short-term improvements
- OCR/image ingestion (PNG/JPEG/TIFF).
- Bulk export endpoint.
- Reviewer assignment and SLA tracking.
- Retry policy/backoff for failed processing tasks.

## Mid-term
- Google Sheets export connector.
- CRM integration connector.
- Webhook notifications for status changes.
- Email intake pipeline.

## Advanced
- Multi-tenant company/workspace boundaries.
- Full-text + vector search over extracted content.
- Background job monitoring UI and task observability.
- SLO stack (metrics, tracing, structured logs).
- Kubernetes deployment templates.
- Rate limiting and abuse prevention.
