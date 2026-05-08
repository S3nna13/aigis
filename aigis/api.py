from __future__ import annotations

import asyncio
import json
import os
import re
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(
    title="AIGIS API",
    description="REST API for the AI Guardrail & Integration System",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
CORS_ORIGINS = os.getenv("AIGIS_CORS_ORIGINS", "https://localhost:5173,https://127.0.0.1:5173")
_cors_origins = [o.strip() for o in CORS_ORIGINS.split(",") if o.strip()]
if not _cors_origins:
    _cors_origins = ["https://localhost:5173", "https://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-API-Key",
        "X-Idempotency-Key",
        "X-AIGIS-Signature",
    ],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
)


class SecurityHeadersMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            response_headers = [
                (b"strict-transport-security", b"max-age=31536000; includeSubDomains"),
                (b"x-content-type-options", b"nosniff"),
                (b"x-frame-options", b"DENY"),
                (b"referrer-policy", b"strict-origin-when-cross-origin"),
                (b"permissions-policy", b"camera=(), microphone=(), geolocation=()"),
                (
                    b"content-security-policy",
                    b"default-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
                ),
            ]

            async def send_with_headers(message):
                if message["type"] == "http.response.start":
                    new_headers = list(message.get("headers", [])) + response_headers
                    await send({**message, "headers": new_headers})
                else:
                    await send(message)

            await self.app(scope, receive, send_with_headers)
        else:
            await self.app(scope, receive, send)


app.add_middleware(SecurityHeadersMiddleware)

# Note: middleware order is reversed — last added runs first on request, last on response.
# SecurityHeadersMiddleware is outermost (runs first), CORSMiddleware is inner.


RATE_LIMIT = int(os.getenv("AIGIS_RATE_LIMIT", "100"))
RATE_WINDOW = int(os.getenv("AIGIS_RATE_WINDOW", "60"))

_rate_hits: dict[str, list[float]] = defaultdict(list)
_rate_lock = asyncio.Lock()


async def rate_limit_middleware(request: Request, call_next):
    if request.url.path in ("/docs", "/redoc", "/openapi.json", "/api/health"):
        return await call_next(request)

    key = request.client.host if request.client else "unknown"
    now = time.monotonic()

    async with _rate_lock:
        window = _rate_hits[key]
        cutoff = now - RATE_WINDOW
        window = [t for t in window if t > cutoff]
        _rate_hits[key] = window

        if len(window) >= RATE_LIMIT:
            return Response(
                content=json.dumps(
                    {"detail": f"Rate limit exceeded: {RATE_LIMIT} req/{RATE_WINDOW}s"}
                ),
                status_code=429,
                media_type="application/json",
            )
        window.append(now)

    return await call_next(request)


app.middleware("http")(rate_limit_middleware)

DATA_DIR = Path(os.getenv("AIGIS_DATA_DIR", "./reports"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

API_KEY = os.getenv("AIGIS_API_KEY", "")


async def verify_api_key(request: Request) -> bool:
    if not API_KEY:
        return False
    key = request.headers.get("X-API-Key") or request.query_params.get("api_key")
    return key == API_KEY


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in ("/docs", "/redoc", "/openapi.json", "/api/health"):
        return await call_next(request)
    if not await verify_api_key(request):
        return Response(
            content=json.dumps({"detail": "Invalid or missing API key"}),
            status_code=401,
            media_type="application/json",
        )
    return await call_next(request)


class EvalRunRequest(BaseModel):
    config_path: str | None = None
    config_yaml: str | None = None
    name: str | None = None
    stream: bool = False


class GuardrailCheckRequest(BaseModel):
    text: str
    rails: list[str] | None = None


class EvalRunResponse(BaseModel):
    id: str
    name: str
    timestamp: str
    results: list[dict[str, Any]]
    summary: dict[str, Any]


class GuardrailCheckResponse(BaseModel):
    id: str
    timestamp: str
    text: str
    results: list[dict[str, Any]]
    passed: bool


def _store_json(filename: str, data: dict) -> Path:
    p = DATA_DIR / filename
    p.write_text(json.dumps(data, indent=2, default=str))
    return p


def _load_json(filename: str) -> dict | None:
    p = DATA_DIR / filename
    if not p.exists():
        return None
    return json.loads(p.read_text())


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.get("/api/evals", response_model=list[dict[str, Any]])
async def list_evals(skip: int = 0, limit: int = 50):
    evals = []
    for p in sorted(DATA_DIR.glob("eval_*.json"), reverse=True):
        data = _load_json(p.name)
        if data:
            evals.append(data)
    return evals[skip : skip + limit]


@app.post("/api/evals", response_model=EvalRunResponse)
async def run_eval(req: EvalRunRequest):
    import yaml
    from aigis.core.config import _merge_top_level, load_config, validate_config
    from aigis.eval.runner import run_eval as _run_eval

    if req.config_path:
        cfg = load_config(req.config_path)
    elif req.config_yaml:
        raw = yaml.safe_load(req.config_yaml)
        _merge_top_level(raw)
        cfg = validate_config(raw)
    else:
        raise HTTPException(status_code=400, detail="Provide config_path or config_yaml")

    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    name = req.name or cfg.name or "unnamed"

    start = time.perf_counter()
    results = await _run_eval(cfg)
    latency_ms = (time.perf_counter() - start) * 1000

    results_dicts = []
    total_score = 0.0
    passed_count = 0
    for r in results:
        rd = {
            "name": r.name,
            "score": r.score,
            "threshold": r.threshold,
            "passed": r.passed,
            "reason": r.reason,
        }
        results_dicts.append(rd)
        total_score += r.score
        if r.passed:
            passed_count += 1

    avg_score = total_score / len(results) if results else 0
    pass_rate = passed_count / len(results) if results else 0

    response = EvalRunResponse(
        id=run_id,
        name=name,
        timestamp=timestamp,
        results=results_dicts,
        summary={
            "total": len(results),
            "passed": passed_count,
            "failed": len(results) - passed_count,
            "avg_score": round(avg_score, 3),
            "pass_rate": round(pass_rate, 3),
            "latency_ms": round(latency_ms, 1),
        },
    )
    _store_json(f"eval_{run_id}.json", response.model_dump())
    return response


@app.post("/api/evals/stream")
async def stream_eval(req: EvalRunRequest):
    import yaml

    from aigis.core.config import _merge_top_level, load_config, validate_config

    if not req.config_path and not req.config_yaml:
        raise HTTPException(status_code=400, detail="Provide config_path or config_yaml")

    if req.config_path:
        cfg = load_config(req.config_path)
    else:
        raw = yaml.safe_load(req.config_yaml)
        _merge_top_level(raw)
        cfg = validate_config(raw)

    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    name = req.name or cfg.name or "unnamed"

    async def event_stream():
        start = time.perf_counter()
        idx = 0
        async for result in _stream_eval(cfg):
            idx += 1
            elapsed = (time.perf_counter() - start) * 1000
            data = {
                "event": "result",
                "id": run_id,
                "name": name,
                "timestamp": timestamp,
                "index": idx,
                "result": result,
                "elapsed_ms": round(elapsed, 1),
            }
            yield f"data: {json.dumps(data, default=str)}\n\n"
        total_ms = (time.perf_counter() - start) * 1000
        yield f"data: {json.dumps({'event': 'done', 'id': run_id, 'total_ms': round(total_ms, 1), 'timestamp': timestamp}, default=str)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


INJECTION_PATTERNS = [
    re.compile(r, re.IGNORECASE)
    for r in [
        r"ignore\s+(all\s+)?previous",
        r"ignore\s+your\s+instructions",
        r"disregard\s+previous",
        r"disregard\s+your",
        r"new\s+instructions:\s*you\s+are",
        r"you\s+are\s+now\s+\w+",
        r"pretend\s+you\s+are",
        r"roleplay\s+as",
        r"<\s*script",
        r"javascript:",
        r"on\s*\w+\s*=",
        r"\{\{.*?\}\}",
    ]
]

DANGEROUS_PROMPT_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _sanitize_prompt(text: str) -> str:
    text = DANGEROUS_PROMPT_CHARS.sub("", text)
    for pattern in INJECTION_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


async def _stream_eval(cfg):
    from aigis.eval.runner import _build_metric, _resolve_model
    from aigis.models.base import Message

    eval_cfg = cfg.eval
    if not eval_cfg:
        return
    model_cfg = eval_cfg.model or cfg.model
    if not model_cfg:
        return
    model = _resolve_model(model_cfg)

    for test in eval_cfg.tests:
        for prompt in eval_cfg.prompts:
            prompt_text = prompt if isinstance(prompt, str) else prompt.content
            safe_input = _sanitize_prompt(test.input)
            filled = prompt_text.replace("{{input}}", safe_input)
            resp = await model.generate([Message(role="user", content=filled)])
            output = resp.content

            for assertion in eval_cfg.assertions:
                metric = _build_metric(assertion, model)
                result = await metric.measure(
                    input=test.input, output=output, expected=test.expected
                )
                yield {
                    "name": result.name,
                    "score": result.score,
                    "passed": result.passed,
                    "reason": result.reason,
                    "input": test.input,
                    "output": output,
                }


@app.get("/api/evals/{eval_id}", response_model=EvalRunResponse)
async def get_eval(eval_id: str):
    data = _load_json(f"eval_{eval_id}.json")
    if not data:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return data


@app.get("/api/guardrails", response_model=list[dict[str, Any]])
async def list_guardrail_logs(skip: int = 0, limit: int = 50):
    logs = []
    for p in sorted(DATA_DIR.glob("guard_*.json"), reverse=True):
        data = _load_json(p.name)
        if data:
            logs.append(data)
    return logs[skip : skip + limit]


@app.post("/api/guardrails/check", response_model=GuardrailCheckResponse)
async def check_guardrails(req: GuardrailCheckRequest):
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail
    from aigis.guardrails.pii import PIIDetector

    pipeline = GuardrailPipeline()
    rails = req.rails or ["jailbreak", "toxic", "pii"]
    for rail in rails:
        match rail:
            case "jailbreak":
                pipeline.add_input_rail(JailbreakDetector())
            case "toxic":
                pipeline.add_input_rail(ToxicityGuardrail())
            case "pii":
                pipeline.add_input_rail(PIIDetector(redact=True))

    start = time.perf_counter()
    results = await pipeline.check_input(req.text)
    (time.perf_counter() - start) * 1000

    check_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()

    response = GuardrailCheckResponse(
        id=check_id,
        timestamp=timestamp,
        text=req.text,
        results=[
            {
                "name": r.name,
                "passed": r.passed,
                "score": r.score,
                "reason": r.reason,
                "severity": r.severity,
                "redacted": r.redacted,
            }
            for r in results
        ],
        passed=all(r.passed for r in results),
    )
    _store_json(f"guard_{check_id}.json", response.model_dump())

    # Audit log guard violation or pass
    try:
        from aigis.audit import log_guardrail_result

        log_guardrail_result(req.text, results, response.passed)
    except Exception:  # noqa: BLE001
        pass  # audit logging should never break API responses

    # Dispatch webhook
    event = "guardrail.passed" if response.passed else "guardrail.triggered"
    asyncio.create_task(
        _dispatch_webhook(
            event,
            f"guard_{check_id}",
            {"check_id": check_id, "text": req.text, "results": response.model_dump()},
        )
    )
    return response


@app.post("/api/webhooks")
async def register_webhook(
    url: str, secret: str | None = None, retries: int = 3, timeout: float = 10.0
):
    from aigis.webhooks import WebhookConfig, get_webhook_manager

    manager = get_webhook_manager()
    config = WebhookConfig(url=url, secret=secret, retries=retries, timeout=timeout)
    manager.register(config)
    return {"registered": url, "total_webhooks": len(manager._hooks)}


@app.get("/api/webhooks")
async def list_webhooks():
    from aigis.webhooks import get_webhook_manager

    manager = get_webhook_manager()
    return [{"url": h.url, "retries": h.retries, "timeout": h.timeout} for h in manager._hooks]


@app.delete("/api/webhooks/{url}")
async def delete_webhook(url: str):
    from aigis.webhooks import get_webhook_manager

    manager = get_webhook_manager()
    count_before = len(manager._hooks)
    manager.unregister(url)
    deleted = len(manager._hooks) < count_before
    if not deleted:
        raise HTTPException(status_code=404, detail="Webhook not found")
    return {"deleted": url}


async def _dispatch_webhook(event: str, source: str, data: dict):
    from aigis.webhooks import WebhookEvent, dispatch_webhook

    try:
        await dispatch_webhook(WebhookEvent(event), source, data)
    except Exception:  # noqa: BLE001
        pass  # webhooks should not block API responses


@app.delete("/api/evals/{eval_id}")
async def delete_eval(eval_id: str):
    p = DATA_DIR / f"eval_{eval_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Eval run not found")
    p.unlink()
    return {"deleted": eval_id}


@app.delete("/api/guardrails/{check_id}")
async def delete_guardrail_log(check_id: str):
    p = DATA_DIR / f"guard_{check_id}.json"
    if not p.exists():
        raise HTTPException(status_code=404, detail="Guardrail log not found")
    p.unlink()
    return {"deleted": check_id}


@app.get("/api/audit", response_model=list[dict[str, Any]])
async def query_audit_logs(
    event: str | None = None,
    since: str | None = None,
    limit: int = 100,
):
    from aigis.audit import AuditEvent, query_audit_logs as _query

    evt = AuditEvent(event) if event else None
    since_dt = None
    if since:
        from datetime import datetime

        since_dt = datetime.fromisoformat(since)
    return _query(event=evt, since=since_dt, limit=limit)


_MODEL_COSTS_PER_1K = {
    "openai:gpt-4o": 0.015,
    "openai:gpt-4o-mini": 0.0006,
    "openai:gpt-4-turbo": 0.01,
    "openai:gpt-3.5-turbo": 0.0015,
    "anthropic:claude-3-opus": 0.015,
    "anthropic:claude-3-sonnet": 0.003,
    "anthropic:claude-3-haiku": 0.00025,
    "ollama:llama-3": 0.0,
    "ollama:mixtral-8x7b": 0.0,
    "local:default": 0.0,
}


class APIMetrics:
    _requests: list[dict[str, Any]] = []
    _lock: asyncio.Lock = asyncio.Lock()

    def record(
        self,
        method: str,
        path: str,
        latency_ms: float,
        tokens_used: int | None = None,
        model: str | None = None,
        status: int = 200,
    ) -> None:
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "method": method,
            "path": path,
            "latency_ms": round(latency_ms, 1),
            "tokens_used": tokens_used,
            "model": model,
            "status": status,
        }
        self._requests.append(entry)
        if len(self._requests) > 10_000:
            self._requests = self._requests[-5000:]

    async def get_stats(
        self,
        window_minutes: int = 60,
    ) -> dict[str, Any]:
        cutoff = datetime.now(timezone.utc).timestamp() - window_minutes * 60
        async with self._lock:
            recent = [
                r
                for r in self._requests
                if datetime.fromisoformat(r["timestamp"]).timestamp() > cutoff
            ]
        total = len(recent)
        latencies = [r["latency_ms"] for r in recent]
        sorted_lat = sorted(latencies) if latencies else [0]
        p50 = sorted_lat[int(len(sorted_lat) * 0.50)] if sorted_lat else 0
        p95 = sorted_lat[int(len(sorted_lat) * 0.95)] if sorted_lat else 0
        p99 = sorted_lat[int(len(sorted_lat) * 0.99)] if sorted_lat else 0
        total_tokens = sum(r["tokens_used"] or 0 for r in recent)
        key = (recent[0]["model"] or "unknown") if recent else "unknown"
        cost = total_tokens / 1000 * _MODEL_COSTS_PER_1K.get(key, 0.0)
        return {
            "requests": total,
            "latency_ms": {"p50": round(p50, 1), "p95": round(p95, 1), "p99": round(p99, 1)},
            "tokens_used": total_tokens,
            "estimated_cost_usd": round(cost, 4),
            "window_minutes": window_minutes,
        }


_metrics = APIMetrics()


@app.middleware("http")  # type: ignore[arg-type]
async def record_metrics(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    latency_ms = (time.perf_counter() - start) * 1000
    _metrics.record(
        method=request.method,
        path=request.url.path,
        latency_ms=latency_ms,
        status=response.status_code if hasattr(response, "status_code") else 200,
    )
    return response


@app.get("/api/metrics", response_model=dict[str, Any])
async def get_metrics(window_minutes: int = 60):
    return await _metrics.get_stats(window_minutes=window_minutes)


@app.post("/api/metrics/reset")
async def reset_metrics():
    async with _metrics._lock:
        _metrics._requests.clear()
    return {"reset": "metrics cleared"}
