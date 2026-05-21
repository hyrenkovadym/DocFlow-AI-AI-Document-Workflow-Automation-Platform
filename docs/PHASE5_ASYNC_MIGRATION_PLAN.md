# Phase 5 Async Worker Migration Plan

## Goal
Activate asynchronous document processing using Redis + Celery without breaking the current Phase 4 synchronous MVP behavior.

## Non-goals
- No real OpenAI rollout in this phase.
- No major frontend redesign.
- No schema-breaking migration for existing documents.

## Safety Principles
1. Keep synchronous pipeline as fallback path.
2. Roll out async behind an explicit config flag.
3. Make status transitions idempotent and retry-safe.
4. Preserve API contract for upload/reprocess endpoints.
5. Enable fast rollback to synchronous mode.

## Proposed Runtime Toggle
Add a backend config switch:
- `PROCESSING_MODE=sync|async` (default `sync` initially).

Behavior:
- `sync`: current Phase 4 behavior (process inline).
- `async`: upload/reprocess enqueue Celery task and return quickly with `queued` status.

## Incremental Delivery Plan

### Step 1: Queue mode scaffolding (no default behavior change)
- Wire upload/reprocess service methods to choose sync/async by `PROCESSING_MODE`.
- In async mode:
  - set status `queued`,
  - enqueue `process_document_task(document_id)`.
- Keep existing sync code path untouched.

### Step 2: Worker correctness and idempotency
- Ensure task is safe to retry:
  - read current status and allow re-entry from `queued`/`processing`,
  - avoid duplicate extraction/review task corruption,
  - always write deterministic status transitions.
- Keep audit events consistent and avoid noisy duplicates where possible.

### Step 3: API and frontend compatibility
- Upload/reprocess responses remain stable schema-wise.
- Frontend handles queued/processing states (already has status badges).
- Add polling or manual refresh guidance for demo flow.

### Step 4: Test coverage expansion
- Add tests for `PROCESSING_MODE=async`:
  - upload returns `queued`,
  - task transitions to `needs_review` on success,
  - failure transitions to `failed` + `processing_error` + audit event,
  - reprocess in async mode works and respects permissions.
- Keep existing sync-mode test suite green.

### Step 5: Docker/dev workflow validation
- Validate local stack with:
  - API + worker + Redis + Postgres,
  - migrations and seed,
  - end-to-end upload -> review queue flow.

## Rollback Plan
If async mode causes regressions:
1. Set `PROCESSING_MODE=sync`.
2. Restart API only (worker may stay idle).
3. Continue processing inline without data migration.

## Observability Checklist (minimum)
- Log enqueue events with document ID.
- Log worker task start/end/failure with document ID.
- Track queued->processing->needs_review/failed transitions in audit logs.

## Acceptance Criteria
- Sync mode remains fully functional (Phase 4 parity).
- Async mode is opt-in and demo-stable.
- No permission regressions.
- Export/reprocess behaviors from Phase 4 remain intact.
- Backend tests and frontend build/lint still pass.
