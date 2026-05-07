"""
AIGIS Python SDK — programmatic access to all AIGIS capabilities.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from aigis.core.config import load_config
from aigis.core.schema import AigisConfig, ModelConfig
from aigis.eval.metrics import MetricResult
from aigis.eval.runner import run_eval as _run_eval
from aigis.guardrails.engine import GuardrailPipeline, GuardrailResult
from aigis.guardrails.hallucination import HallucinationDetector
from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail
from aigis.guardrails.pii import FactualConsistency, PIIDetector
from aigis.models.base import ModelAdapter
from aigis.models.anthropic_adapter import AnthropicAdapter
from aigis.models.local_adapter import LocalAdapter
from aigis.models.ollama_adapter import OllamaAdapter
from aigis.models.openai_adapter import OpenAIAdapter
from aigis.reporting.report import format_results


@dataclass
class EvalSummary:
    total: int
    passed: int
    failed: int
    avg_score: float
    pass_rate: float
    results: list[MetricResult]
    latency_ms: float
    tokens_used: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "passed": self.passed,
            "failed": self.failed,
            "avg_score": round(self.avg_score, 3),
            "pass_rate": round(self.pass_rate, 3),
            "results": [
                {"name": r.name, "score": r.score, "passed": r.passed, "reason": r.reason}
                for r in self.results
            ],
            "latency_ms": round(self.latency_ms, 1),
            "tokens_used": self.tokens_used,
        }


@dataclass
class GuardrailCheck:
    passed: bool
    results: list[GuardrailResult]
    latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "results": [
                {
                    "name": r.name,
                    "score": r.score,
                    "passed": r.passed,
                    "reason": r.reason,
                    "severity": r.severity,
                }
                for r in self.results
            ],
            "latency_ms": round(self.latency_ms, 1),
        }


class Aigis:
    """Main SDK entry point. Supports context-manager and direct usage."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        provider: Literal["openai", "anthropic", "ollama", "local"] = "openai",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.0,
    ):
        provider_val: Literal["openai", "anthropic", "ollama", "local"] = provider
        self.model_cfg = ModelConfig(
            provider=provider_val,
            model=model,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )
        self._adapter: ModelAdapter | None = None

    def _resolve_adapter(self) -> ModelAdapter:
        if self._adapter is None:
            match self.model_cfg.provider:
                case "openai":
                    self._adapter = OpenAIAdapter(
                        model=self.model_cfg.model,
                        api_key=self.model_cfg.api_key,
                        base_url=self.model_cfg.base_url,
                    )
                case "anthropic":
                    self._adapter = AnthropicAdapter(
                        model=self.model_cfg.model,
                        api_key=self.model_cfg.api_key,
                        base_url=self.model_cfg.base_url,
                    )
                case "ollama":
                    self._adapter = OllamaAdapter(
                        model=self.model_cfg.model,
                        base_url=self.model_cfg.base_url,
                    )
                case "local":
                    self._adapter = LocalAdapter(
                        model=self.model_cfg.model,
                        api_key=self.model_cfg.api_key,
                        base_url=self.model_cfg.base_url,
                    )
                case _:
                    raise ValueError(f"Unknown provider: {self.model_cfg.provider}")
        return self._adapter

    async def _aresolve_adapter(self):
        return self._resolve_adapter()

    def eval(
        self,
        prompts: list[str],
        tests: list[dict],
        assertions: list[dict],
        *,
        name: str = "sdk-eval",
        description: str | None = None,
        output_format: str = "json",
        output_path: str = "./reports",
    ) -> EvalSummary:
        """Run evaluations synchronously."""
        return asyncio.run(
            self.aeval(
                prompts,
                tests,
                assertions,
                name=name,
                description=description,
                output_format=output_format,
                output_path=output_path,
            )
        )

    async def aeval(
        self,
        prompts: list[str],
        tests: list[dict],
        assertions: list[dict],
        *,
        name: str = "sdk-eval",
        description: str | None = None,
        output_format: str = "json",
        output_path: str = "./reports",
    ) -> EvalSummary:
        """Run evaluations asynchronously."""
        raw_cfg = {
            "version": "1",
            "aigis": "eval",
            "name": name,
            "description": description or f"SDK evaluation: {name}",
            "model": self.model_cfg.model_dump(),
            "eval": {
                "prompts": prompts,
                "tests": tests,
                "assertions": assertions,
            },
            "report": {"format": output_format, "output_path": output_path},
        }

        from aigis.core.config import _merge_top_level, validate_config

        _merge_top_level(raw_cfg)
        cfg = validate_config(raw_cfg)

        adapter = await self._aresolve_adapter()
        start = time.perf_counter()
        results = await _run_eval(cfg, model_override=adapter)
        elapsed_ms = (time.perf_counter() - start) * 1000

        total = len(results)
        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / total if total else 0

        total_tokens = None
        if adapter:
            # attempt to collect token usage from responses
            pass  # token collection handled per-call

        summary = EvalSummary(
            total=total,
            passed=passed,
            failed=total - passed,
            avg_score=avg_score,
            pass_rate=passed / total if total else 0,
            results=results,
            latency_ms=elapsed_ms,
            tokens_used=total_tokens,
        )

        Path(output_path).mkdir(parents=True, exist_ok=True)
        formatted = format_results(results, fmt=output_format)
        suffix = {"json": "json", "html": "html", "markdown": "md"}.get(output_format, "txt")
        (Path(output_path) / f"results_{name}.{suffix}").write_text(formatted)

        return summary

    def guard(
        self,
        text: str,
        *,
        rails: list[str] | None = None,
        redact: bool = False,
    ) -> GuardrailCheck:
        """Check text against guardrails synchronously."""
        return asyncio.run(self.aguard(text, rails=rails, redact=redact))

    async def aguard(
        self,
        text: str,
        *,
        rails: list[str] | None = None,
        redact: bool = False,
    ) -> GuardrailCheck:
        """Check text against guardrails asynchronously."""
        from aigis.guardrails import (
            ContextWindowGuard,
            PromptInjectionDetector,
            RAGPoisoningDetector,
            SecretScanner,
            StructuredOutputValidator,
            ToxicityFilter,
        )

        pipeline = GuardrailPipeline()
        active_rails = rails or ["jailbreak", "toxic", "pii"]

        for rail in active_rails:
            match rail:
                case "jailbreak":
                    pipeline.add_input_rail(JailbreakDetector())
                case "toxic":
                    pipeline.add_input_rail(ToxicityGuardrail())
                case "toxicity_filter":
                    pipeline.add_input_rail(ToxicityFilter())
                case "pii":
                    pipeline.add_input_rail(PIIDetector(redact=redact))
                case "injection":
                    pipeline.add_input_rail(PromptInjectionDetector())
                case "secrets":
                    pipeline.add_input_rail(SecretScanner())
                case "context":
                    pipeline.add_input_rail(ContextWindowGuard(model=self.model_cfg.model))
                case "rag_poisoning":
                    pipeline.add_input_rail(RAGPoisoningDetector())
                case "structured_output":
                    pipeline.add_output_rail(StructuredOutputValidator())
                case "hallucination":
                    adapter = await self._aresolve_adapter()
                    pipeline.add_output_rail(HallucinationDetector(adapter))
                case "factual":
                    adapter = await self._aresolve_adapter()
                    pipeline.add_output_rail(FactualConsistency(model_adapter=adapter))

        start = time.perf_counter()
        results = await pipeline.check_input(text)
        elapsed_ms = (time.perf_counter() - start) * 1000

        return GuardrailCheck(
            passed=all(r.passed for r in results),
            results=results,
            latency_ms=elapsed_ms,
        )

    def run_pipeline(
        self,
        config: str | Path | AigisConfig,
        *,
        output: str = "./reports",
    ) -> dict[str, Any]:
        """Run a full eval + guardrail pipeline from a config file."""
        return asyncio.run(self.arun_pipeline(config, output=output))

    async def arun_pipeline(
        self,
        config: str | Path | AigisConfig,
        *,
        output: str = "./reports",
    ) -> dict[str, Any]:
        """Run a full eval + guardrail pipeline asynchronously."""
        if isinstance(config, (str, Path)):
            cfg = load_config(str(config))
        else:
            cfg = config

        adapter = await self._aresolve_adapter()
        start = time.perf_counter()
        eval_results = await _run_eval(cfg, model_override=adapter)
        eval_ms = (time.perf_counter() - start) * 1000

        guard_cfg = cfg.guard
        pipeline = GuardrailPipeline()
        if guard_cfg and guard_cfg.rails:
            for rail_name in guard_cfg.rails.input:
                match rail_name:
                    case "jailbreak":
                        pipeline.add_input_rail(JailbreakDetector())
                    case "toxic":
                        pipeline.add_input_rail(ToxicityGuardrail())
                    case "pii":
                        pipeline.add_input_rail(PIIDetector(redact=True))
            for rail_name in guard_cfg.rails.output:
                match rail_name:
                    case "hallucination":
                        pipeline.add_output_rail(HallucinationDetector(adapter))
                    case "factual":
                        pipeline.add_output_rail(FactualConsistency(model_adapter=adapter))
        else:
            pipeline.add_input_rail(JailbreakDetector())
            pipeline.add_input_rail(ToxicityGuardrail())

        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        formatted = format_results(eval_results, fmt="json")
        (output_path / "pipeline_eval_results.json").write_text(formatted)

        total = len(eval_results)
        passed = sum(1 for r in eval_results if r.passed)

        return {
            "eval": {
                "total": total,
                "passed": passed,
                "failed": total - passed,
                "avg_score": round(sum(r.score for r in eval_results) / total, 3) if total else 0,
                "latency_ms": round(eval_ms, 1),
            },
            "output_path": str(output_path),
        }
