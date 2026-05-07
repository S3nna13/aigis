from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class MetricResult:
    name: str
    score: float
    threshold: float | None = None
    passed: bool | None = None
    reason: str | None = None
    details: dict | None = None

    def __post_init__(self):
        if self.passed is None:
            if self.threshold is not None:
                self.passed = self.score >= self.threshold
            else:
                self.passed = self.score > 0


class Metric(ABC):
    name: str

    @abstractmethod
    async def measure(
        self, input: str, output: str, expected: str | None = None, **kwargs
    ) -> MetricResult: ...


class ExactMatch(Metric):
    name = "exact_match"

    async def measure(
        self, input: str, output: str, expected: str | None = None, **kwargs
    ) -> MetricResult:
        score = 1.0 if output.strip() == (expected or "").strip() else 0.0
        return MetricResult(
            name=self.name,
            score=score,
            reason="Output matches expected exactly" if score else "Output does not match expected",
        )


class Contains(Metric):
    name = "contains"

    async def measure(
        self, input: str, output: str, expected: str | None = None, **kwargs
    ) -> MetricResult:
        if not expected:
            return MetricResult(name=self.name, score=0.0, reason="No expected value provided")
        score = 1.0 if expected.lower() in output.lower() else 0.0
        return MetricResult(
            name=self.name,
            score=score,
            reason=f"Output contains expected text: '{expected}'"
            if score
            else f"Output does not contain: '{expected}'",
        )


class LLMJudge(Metric):
    name = "llm_judge"

    def __init__(self, model_adapter=None, criteria: str = "correctness"):
        self._model = model_adapter
        self._criteria = criteria

    async def measure(
        self, input: str, output: str, expected: str | None = None, **kwargs
    ) -> MetricResult:
        if not self._model:
            return MetricResult(name=self.name, score=0.5, reason="No judge model configured")
        judge_prompt = f"""You are evaluating an AI output. Score 0-1.

Criteria: {self._criteria}

Input: {input}
Expected: {expected or "N/A"}
Output: {output}

Respond with ONLY a number between 0 and 1, and a brief reason."""
        from aigis.models.base import Message

        resp = await self._model.generate([Message(role="user", content=judge_prompt)])
        import re

        scores = re.findall(r"0\.\d+|1\.0|1\.00|[01]", resp.content.strip())
        score = float(scores[0]) if scores else 0.5
        return MetricResult(name=self.name, score=score, reason=resp.content[:200])
