# Security Notes

## Secrets
- All secrets come from environment variables.
- Never commit `.env` files.

## Authentication and authorization
- Passwords hashed with Passlib (`pbkdf2_sha256`).
- JWT bearer tokens with configurable secret/expiry.
- Role-based access control for user/reviewer/admin privileges.

## File upload safety
- Only allowed extensions are accepted.
- File size limit enforced by server-side validation.
- Uploaded files are treated as untrusted content.

## AI safety
- AI output is schema-validated before storage.
- Human review is built in before operational export.

## Production recommendations
- Enforce HTTPS and secure cookies/session boundaries.
- Store files in object storage with malware scanning.
- Add rate limiting and abuse detection.
- Rotate JWT secret and API keys regularly.
