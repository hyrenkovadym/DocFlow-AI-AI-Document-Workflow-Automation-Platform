# Security Policy

## Supported versions
This repository is a portfolio project and does not currently publish release branches. Security fixes are applied on `main`.

## Reporting a vulnerability
- Do not post secrets or exploit details in public issues.
- Open a private report through GitHub Security Advisories if available.
- Include reproduction steps, affected endpoints, and impact summary.

## Secure development notes
- Never commit real API keys, JWT secrets, or private customer documents.
- Use `.env` for all secrets and keep `.env` untracked.
- Mock AI provider is the default in local and CI flows.
- Uploaded files are treated as untrusted input and validated by extension and size.
- AI output is validated with Pydantic before persistence.
- Production deployment should enforce HTTPS, object-storage malware scanning, and secret rotation.
