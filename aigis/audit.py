"""
Audit logging for AIGIS — immutable append-only log of guard violations,
eval runs, and configuration changes.

Supports structured JSON logs with cryptographic integrity markers.
Logs are written to DATA_DIR/audit_YYYY-MM.json and can be rotated/queryed.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from aigis.guardrails.engine import GuardrailResult


DATA_DIR = Path(os.getenv("AIGIS_DATA_DIR", ".data"))


class AuditEvent(str, Enum):
    GUARD_VIOLATION = "guard.violation"
    GUARD_PASSED = "guard.passed"
    EVAL_RUN_START = "eval.start"
    EVAL_RUN_COMPLETE = "eval.complete"
    EVAL_RUN_FAILED = "eval.failed"
    CONFIG_CHANGED = "config.changed"
    API_KEY_USAGE = "api_key.usage"
    WEBHOOK_DISPATCHED = "webhook.dispatched"
    WEBHOOK_FAILED = "webhook.failed"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"


def _integrity_hash(entry: dict[str, Any]) -> str:
    """SHA-256 digest of the entry JSON (excluding the hash field itself)."""
    content = json.dumps(entry, sort_keys=True, default=str)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def _get_audit_path() -> Path:
    today = datetime.now(timezone.utc).strftime("%Y-%m")
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR / f"audit_{today}.jsonl"


def log_event(
    event: AuditEvent,
    actor: str | None = None,
    resource: str | None = None,
    outcome: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> str:
    """
    Append a structured audit log entry.

    Returns the entry ID (first 16 hex chars of SHA-256 of content).
    """
    entry = {
        "id": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event.value,
        "actor": actor or "system",
        "resource": resource,
        "outcome": outcome,
        "metadata": metadata or {},
    }
    entry["id"] = _integrity_hash(entry)
    entry["integrity"] = _integrity_hash(entry)

    path = _get_audit_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry, default=str) + "\n")

    return entry["id"]  # type: ignore[return-value]


def log_guardrail_result(
    text: str,
    results: list[GuardrailResult],
    passed: bool,
) -> str:
    """Log a guardrail check result."""
    triggered = [r for r in results if not r.passed]
    event = AuditEvent.GUARD_VIOLATION if triggered else AuditEvent.GUARD_PASSED
    return log_event(
        event=event,
        outcome="passed" if passed else "triggered",
        metadata={
            "triggered_rails": [
                {"name": r.name, "score": r.score, "reason": r.reason, "severity": r.severity}
                for r in triggered
            ],
            "total_rails": len(results),
            "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16],
        },
    )


def log_eval_run(
    eval_id: str,
    name: str,
    model: str,
    total: int,
    passed: int,
    failed: int,
    avg_score: float,
    latency_ms: float,
    outcome: str = "completed",
) -> str:
    """Log an eval run summary."""
    return log_event(
        event=AuditEvent.EVAL_RUN_COMPLETE if outcome == "completed" else AuditEvent.EVAL_RUN_FAILED,
        resource=f"eval/{eval_id}",
        outcome=outcome,
        metadata={
            "eval_name": name,
            "model": model,
            "total": total,
            "passed": passed,
            "failed": failed,
            "avg_score": round(avg_score, 3),
            "latency_ms": round(latency_ms, 1),
        },
    )


def query_audit_logs(
    event: AuditEvent | None = None,
    since: datetime | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Query audit logs from the last N files.

    Returns entries sorted newest-first.
    """
    logs: list[dict[str, Any]] = []
    pattern = "audit_*.jsonl"

    for path in sorted(DATA_DIR.glob(pattern), reverse=True):
        try:
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if event and entry.get("event") != event.value:
                        continue
                    if since:
                        entry_ts = datetime.fromisoformat(entry["timestamp"])
                        if entry_ts < since:
                            continue

                    logs.append(entry)
                    if len(logs) >= limit:
                        return logs[:limit]
        except OSError:
            continue

    return logs[:limit]
