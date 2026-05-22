# Security Notes

## Secrets handling
- Secrets are loaded from environment variables.
- `.env` files are not committed.
- OpenAI key is optional and never required for tests.

Never expose:
- `OPENAI_API_KEY`
- JWT secret
- database/redis passwords

## Authentication and RBAC
- Passwords are hashed with Passlib.
- JWT protects API routes.
- Role checks are enforced server-side.

## Upload safety
- Extension allowlist.
- Size limits.
- Empty-file rejection.
- Uploaded files treated as untrusted.

## AI safety
- Mock provider is default.
- All provider outputs are schema-validated.
- AI output is advisory; human review remains required.

## Observability safety
Structured logs and audit metadata intentionally exclude:
- API keys/tokens
- uploaded file contents
- full extracted text
- private credentials

Request IDs are safe to expose and used for traceability.

## Operational endpoint safety
`/api/health`, `/api/ready`, `/api/system/info` only return safe runtime state.
They do not expose raw credentials.

## Production recommendations
- Enforce HTTPS end-to-end.
- Use secret manager for runtime keys.
- Rotate JWT and provider credentials regularly.
- Add rate limiting and abuse controls.
- Add centralized log retention and alerting with access controls.
