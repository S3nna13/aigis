"""
Context window guardrail — validates prompt length before sending to LLM.

Prevents:
- Context length DoS attacks (LLM04)
- Padding/padding attacks to inflate context
- Inputs exceeding model context limits
"""

from __future__ import annotations

import re

from aigis.guardrails.engine import Guardrail, GuardrailResult


MODEL_CONTEXTS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo": 16385,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-2": 100000,
    "llama-3-8b": 8192,
    "llama-3-70b": 8192,
    "llama-3.1-8b": 128000,
    "llama-3.1-70b": 128000,
    "mixtral-8x7b": 32000,
    "mistral-7b": 32000,
}

DEFAULT_SAFETY_MARGIN = 2048


def estimate_tokens(text: str, model: str = "gpt-4o") -> int:
    try:
        import tiktoken as _tiktoken
        enc = _tiktoken.encoding_for_model(_tiktoken_model_name(model))
        return len(enc.encode(text))
    except (KeyError, ImportError):
        return len(text) // 4


def _tiktoken_model_name(model: str) -> str:
    mapping = {
        "gpt-4o": "o200k_base",
        "gpt-4o-mini": "o200k_base",
        "gpt-4-turbo": "o200k_base",
        "gpt-4": "cl100k_base",
        "gpt-3.5-turbo": "cl100k_base",
    }
    return mapping.get(model, "cl100k_base")


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    return estimate_tokens(text, model)


class ContextWindowGuard(Guardrail):
    name = "context_window"

    def __init__(
        self,
        model: str = "gpt-4o",
        safety_margin: int | None = None,
        max_tokens: int | None = None,
    ):
        self.model = model
        self.max_context = MODEL_CONTEXTS.get(model, 128000)
        self.safety_margin = safety_margin if safety_margin is not None else DEFAULT_SAFETY_MARGIN
        self.max_tokens = max_tokens or (self.max_context - self.safety_margin)

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        total_text = text + ("\n" + context if context else "")
        tokens = estimate_tokens(total_text, self.model)

        padding_score = self._detect_padding_attack(text)
        length_score = 0.0
        if tokens > self.max_tokens:
            length_score = min(1.0, (tokens - self.max_tokens) / self.max_tokens)

        score = max(padding_score, length_score)
        passed = score < 0.3

        reasons = []
        if padding_score > 0.1:
            reasons.append("padding pattern detected")
        if tokens > self.max_tokens:
            reasons.append(f"exceeds {self.max_tokens} tokens by {tokens - self.max_tokens}")

        severity = "info"
        if length_score > 0.5:
            severity = "critical"
        elif padding_score >= 0.3:
            severity = "warning"
        elif reasons:
            severity = "warning"

        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason="Context length OK" if not reasons else f"Context issue: {', '.join(reasons)}",
            severity=severity,
        )

    def _detect_padding_attack(self, text: str) -> float:
        stripped = text.strip()
        if not stripped:
            return 0.9

        repeats = re.findall(r"(.)\1{10,}", text)
        if repeats:
            return min(1.0, len(repeats) * 0.3)

        trailing = len(text) - len(text.rstrip())
        trailing_ratio = trailing / max(len(text), 1)
        if trailing_ratio > 0.05:
            return 0.8

        if len(text.strip()) < len(text) * 0.4:
            return 0.9

        return 0.0


class TokenBudget:
    _budgets: dict[str, dict[str, int | float]]

    def __init__(self):
        self._budgets = {}

    def check(self, user_id: str, prompt_tokens: int, completion_tokens: int, limit: int = 10_000_000) -> tuple[bool, str]:
        key = f"user:{user_id}"
        budget = self._budgets.setdefault(key, {"spent": 0, "limit": limit})
        total = prompt_tokens + completion_tokens
        if budget["spent"] + total > budget["limit"]:
            remaining = max(0, budget["limit"] - budget["spent"])
            return False, f"Budget exceeded by {total - remaining}. Remaining: {remaining}"
        budget["spent"] += total
        return True, ""

    def remaining(self, user_id: str) -> int:
        key = f"user:{user_id}"
        budget = self._budgets.get(key, {"spent": 0, "limit": 10_000_000})
        return int(max(0, budget["limit"] - budget["spent"]))

    def reset(self, user_id: str) -> None:
        key = f"user:{user_id}"
        if key in self._budgets:
            self._budgets[key]["spent"] = 0
