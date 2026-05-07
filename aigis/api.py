from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="AIGIS API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = Path("./reports")
DATA_DIR.mkdir(parents=True, exist_ok=True)


class EvalRunRequest(BaseModel):
    config_path: str | None = None
    config_yaml: str | None = None
    name: str | None = None


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
    return {"status": "ok", "version": "0.1.0"}


@app.get("/api/evals", response_model=list[dict[str, Any]])
async def list_evals():
    evals = []
    for p in sorted(DATA_DIR.glob("eval_*.json")):
        data = _load_json(p.name)
        if data:
            evals.append(data)
    return evals


@app.post("/api/evals", response_model=EvalRunResponse)
async def run_eval(req: EvalRunRequest):
    from aigis.core.config import load_config, validate_config
    from aigis.eval.runner import run_eval as _run_eval

    if req.config_path:
        cfg = load_config(req.config_path)
    elif req.config_yaml:
        import yaml

        raw = yaml.safe_load(req.config_yaml)
        from aigis.core.config import _merge_top_level

        _merge_top_level(raw)
        cfg = validate_config(raw)
    else:
        raise HTTPException(status_code=400, detail="Provide config_path or config_yaml")

    run_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now(timezone.utc).isoformat()
    name = req.name or cfg.name or "unnamed"

    results = await _run_eval(cfg)

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
        },
    )
    _store_json(f"eval_{run_id}.json", response.model_dump())
    return response


@app.get("/api/evals/{eval_id}", response_model=EvalRunResponse)
async def get_eval(eval_id: str):
    data = _load_json(f"eval_{eval_id}.json")
    if not data:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return data


@app.get("/api/guardrails", response_model=list[dict[str, Any]])
async def list_guardrail_logs():
    logs = []
    for p in sorted(DATA_DIR.glob("guard_*.json")):
        data = _load_json(p.name)
        if data:
            logs.append(data)
    return logs


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

    results = await pipeline.check_input(req.text)

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
            }
            for r in results
        ],
        passed=all(r.passed for r in results),
    )
    _store_json(f"guard_{check_id}.json", response.model_dump())
    return response
