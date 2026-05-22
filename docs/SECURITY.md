# Security Notes

## Secrets
- Secrets are loaded from environment variables.
- `.env` files are never committed.
- Demo credentials in docs are local-only development accounts.
- OpenAI API keys are optional and must be provided only via environment variables.
- API keys are never returned by API endpoints and must never be written to logs.

## Authentication and authorization
- Passwords are hashed with Passlib (`pbkdf2_sha256`).
- JWT bearer tokens protect API routes.
- Role-based access control is enforced server-side.

## Role permissions
- `user`:
  - can upload and view only own documents,
  - can export/reprocess only own documents,
  - cannot access review queue,
  - cannot approve/reject,
  - cannot access audit logs.
- `reviewer`:
  - can access review queue,
  - can approve/reject and patch extraction fields,
  - can access documents needed for review flow.
- `admin`:
  - has reviewer capabilities,
  - can read audit logs.

## File upload safety
- Allowlist-based extension checks.
- Server-side file size limit.
- Empty file uploads are rejected.
- Uploaded files are treated as untrusted content.

## AI/output safety
- Mock AI is default in MVP.
- Structured output is validated through Pydantic models.
- Human review is required before operational export decisions.
- OpenAI-compatible provider output is treated as untrusted input until schema validation passes.
- Invalid JSON/schema failures are handled safely per document (status -> `failed`), without crashing workers.

## Auditability
- Important lifecycle events are logged:
  - upload,
  - processing start/failure,
  - extraction completion,
  - review actions,
  - export events,
  - reprocess requests.

## Production recommendations
- Enforce HTTPS everywhere.
- Move token storage/session strategy from demo mode to hardened auth/session policy.
- Store uploads in object storage with malware scanning.
- Add rate limiting, abuse controls, and security monitoring.
- Rotate JWT/API secrets and tighten key management.
- Use secret managers for AI provider credentials and enable least-privilege key scopes.
