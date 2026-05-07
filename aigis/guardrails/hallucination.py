from aigis.guardrails.engine import Guardrail, GuardrailResult
from aigis.models.base import Message, ModelAdapter


class HallucinationDetector(Guardrail):
    name = "hallucination_detection"

    def __init__(self, model: ModelAdapter, threshold: float = 0.5):
        self._model = model
        self.threshold = threshold

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        if not context:
            return GuardrailResult(
                name=self.name,
                passed=True,
                score=1.0,
                reason="No context provided for fact-checking",
            )
        prompt = f"""Context: {context}

Statement: {text}

Is the statement factually supported by the context? Answer only: YES or NO, then confidence 0-1."""
        resp = await self._model.generate([Message(role="user", content=prompt)])
        output = resp.content.strip().upper()
        is_supported = output.startswith("YES")
        import re

        scores = re.findall(r"0\.\d+|1\.0", output)
        confidence = float(scores[0]) if scores else 0.5
        score = confidence if is_supported else 1.0 - confidence
        return GuardrailResult(
            name=self.name,
            passed=score >= self.threshold,
            score=score,
            reason=f"Statement is {'supported' if is_supported else 'not supported'} by context (confidence={confidence:.2f})",
            severity="critical" if score < 0.3 else "warning" if score < self.threshold else "info",
        )
