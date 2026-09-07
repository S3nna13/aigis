# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability within AIGIS, please report it responsibly.

**Please do NOT file a public GitHub issue for security vulnerabilities.**

Instead, please report them via one of the following:

1. **Email**: Send details to the maintainers via the [repository's security advisories](https://github.com/Aurelien033/aigis/security/advisories/new).
2. **GitHub Private Vulnerability Reporting**: Use the "Security" tab → "Advisories" → "New draft security advisory".

When reporting, please include:

- A description of the vulnerability
- Steps to reproduce the issue
- Potential impact of the vulnerability
- If possible, a suggested fix or mitigation

## Response Timeline

- **Acknowledgement**: Within 48 hours, we will acknowledge receipt of your report.
- **Initial Assessment**: Within 7 days, we will perform an initial assessment and provide an expected timeline for a fix.
- **Fix Release**: We aim to release a patched version within 30 days of confirmation, depending on severity and complexity.

## Security Categories We Monitor

AIGIS is built to defend against the [OWASP Top 10 for LLM Applications](https://owasp.org/llms/):

- **LLM01** — Prompt Injection
- **LLM02** — Insecure Output Handling
- **LLM03** — Training Data Poisoning (RAG poisoning)
- **LLM04** — Model Denial of Service
- **LLM05** — Supply Chain Vulnerabilities
- **LLM06** — Sensitive Information Disclosure
- **LLM07** — Insecure Plugin Design
- **LLM08** — Excessive Agency
- **LLM09** — Overreliance
- **LLM10** — Model Theft

## Security Best Practices for Deployment

When deploying AIGIS in production:

1. **Always set `AIGIS_API_KEY`** — the API defaults to open access if unset.
2. **Use TLS** — terminate TLS before `aigis serve` or use a reverse proxy with TLS.
3. **Limit CORS origins** — set `AIGIS_CORS_ORIGINS` to specific domains, never `*` in production.
4. **Enable rate limiting** — configure `AIGIS_RATE_LIMIT` and `AIGIS_RATE_WINDOW` for your expected load.
5. **Audit log retention** — regularly back up and rotate audit logs (see `aigis/audit.py`).
6. **Webhook secrets** — use the `secret` parameter when registering webhooks for HMAC verification.