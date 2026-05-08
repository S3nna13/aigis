# Changelog

All notable changes to AIGIS are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.2] — 2026-05-08

### Security

- **Stored XSS in dashboard**: Added `sanitize()` utility to escape HTML entities in eval and report names before rendering in React components (`Evals.tsx`, `Reports.tsx`, `Overview.tsx`).
- **Prompt injection in eval inputs**: Added `_sanitize_prompt()` to strip control characters and injection patterns before `{{input}}` substitution in streaming eval.

### Added

- **`SECURITY.md`**: Responsible disclosure policy, OWASP LLM Top 10 coverage table, production deployment best practices.
- **`.github/CODEOWNERS`**: Route Python/dashboard/CLI to maintainers.
- **`.github/dependabot.yml`**: Weekly pip, npm/dashboard, npm/cli dependency updates.

### Changed

- Pin `ruff==0.15.12` explicitly in CI and release workflows to prevent version drift.
- Bump `ruff-pre-commit` to `v0.15.12` in `.pre-commit-config.yaml`.
- Pin npm dependencies in dashboard and CLI to prevent Dependabot from proposing breaking major version bumps (e.g., `vite ~6.4.0`, `typescript ~5.4.0`).

## [0.2.1] — 2026-05-08

### Security

- **Auth bypass**: `verify_api_key()` now returns `False` when `AIGIS_API_KEY` is empty (was returning `True`, allowing unauthenticated access).
- **CORS misconfiguration**: Empty `AIGIS_CORS_ORIGINS` env var no longer produces `[""]` which browsers treat as wildcard. Now falls back to `localhost:5173` and `127.0.0.1:5173`.
- **API information disclosure**: `/api/health` no longer returns `"authenticated": bool` field.
- **CSP hardening**: Add `script-src 'self'`, `base-uri 'self'`, `form-action 'self'`. Remove deprecated `X-XSS-Protection` header.

### Fixed

- SDK `aguard()`: add missing `constitutional` rail routing.
- Ruff formatting applied across all 18 files.

## [0.2.0] — 2025-05-07

### Added

- **14 guardrails** (up from 5 in v0.1.0):

  | Guardrail | OWASP | Description |
  |-----------|-------|-------------|
  | `JailbreakDetector` | LLM01 | Phrase + keyword scoring for jailbreak attacks |
  | `ToxicityGuardrail` | LLM02 | Keyword-based toxicity detection |
  | `ToxicityFilter` | LLM02 | Detoxify-backed multi-category toxicity filter (with keyword fallback) |
  | `PIIDetector` | LLM06 | Email, phone, SSN, credit card, IP, ZIP detection + redaction |
  | `FactualConsistency` | LLM05 | LLM-based factual consistency check |
  | `HallucinationDetector` | LLM05 | RAG-grounded hallucination detection |
  | `PromptInjectionDetector` | LLM01 | 45+ injection fragment patterns + delimiter tricks |
  | `SecretScanner` | LLM06 | 15+ secret patterns + Shannon entropy + base64 detection |
  | `ContextWindowGuard` | LLM04 | Context length validation, padding/padding DoS detection |
  | `RAGPoisoningDetector` | LLM03 | LlamaIndex/LangChain delimiter poisoning in retrieved context |
  | `StructuredOutputValidator` | LLM07 | Pydantic schema validation on LLM JSON outputs |
  | `ConstitutionalCritique` | LLM02 | Weighted constitutional principle evaluation |

- **Python SDK** (`aigis.sdk.Aigis`): sync + async APIs for eval and guardrail checks, 12-rail pipeline support
- **FastAPI server**: 19 routes — health, evals CRUD, SSE streaming, guardrails, webhooks, audit, metrics
- **API metrics** (`GET /api/metrics`): p50/p95/p99 latency, token usage, estimated cost per time window
- **Webhook system**: HMAC-SHA256 signatures, timing-safe verification, retry with exponential backoff
- **Audit logging**: immutable append-only JSONL logs, monthly rotation, SHA-256 integrity markers
- **SecurityHeadersMiddleware**: HSTS, X-Frame-Options: DENY, X-Content-Type-Options, X-XSS-Protection, CSP, Referrer-Policy, Permissions-Policy
- **CLI `guard --all`**: runs all 14 guardrails; individual `--jailbreak`, `--toxicity`, `--secrets`, `--injection`, `--context`, etc. flags
- **CLI `validate`**: config schema validation with rich table output
- **CLI `webhooks`**: list/add/remove webhook subscriptions
- **Dashboard Overview**: live API metrics (latency, tokens, cost) fetched from `/api/metrics`
- **4 model adapters**: OpenAI, Anthropic, Ollama, Local — all with circuit breaker + retry
- **10 eval metrics**: ExactMatch, Contains, RegexMatch, LLMJudge, FactualCheck, SafetyCheck, CustomMetric, LatencyMetric, TokenUsageMetric
- **Security regression tests**: OWASP LLM01/LLM06 attack vector coverage

### Changed

- CORS narrowed to explicit origins via `AIGIS_CORS_ORIGINS` env var
- Rate limiting middleware configurable via `AIGIS_RATE_LIMIT` / `AIGIS_RATE_WINDOW`
- JailbreakDetector uses keyword fallback scoring for obfuscated attacks

### Fixed

- Dashboard `EvalRun` type mismatch: `avgScore`/`passRate` → `summary.avg_score`/`summary.pass_rate`
- JailbreakDetector phrase matching now supplemented with keyword scoring

## [0.1.0] — 2025-05-07

- Initial release
