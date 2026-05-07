import re

from aigis.guardrails.engine import Guardrail, GuardrailResult


class PIIDetector(Guardrail):
    name = "pii_detection"

    PATTERNS: dict[str, str] = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone_us": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
        "ip_address": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "date_of_birth": r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        "zipcode": r"\b\d{5}(?:-\d{4})?\b",
    }

    REDACT_LABELS: dict[str, str] = {
        "email": "[EMAIL]",
        "phone_us": "[PHONE]",
        "ssn": "[SSN]",
        "credit_card": "[CREDIT_CARD]",
        "ip_address": "[IP]",
        "date_of_birth": "[DOB]",
        "zipcode": "[ZIP]",
    }

    def __init__(self, threshold: float = 0.2, redact: bool = False):
        self.threshold = threshold
        self.redact = redact

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        findings: dict[str, list[str]] = {}
        for pii_type, pattern in self.PATTERNS.items():
            matches = re.findall(pattern, text)
            if matches:
                findings[pii_type] = matches

        total_findings = sum(len(v) for v in findings.values())
        score = min(1.0, total_findings / 3.0)
        found_types = list(findings.keys())

        redacted = text
        if self.redact and findings:
            for pii_type, matches in findings.items():
                for m in matches:
                    redacted = redacted.replace(m, self.REDACT_LABELS[pii_type])

        return GuardrailResult(
            name=self.name,
            passed=score < self.threshold,
            score=score,
            reason=f"PII detected: {found_types} ({total_findings} instances)"
            if findings
            else "No PII detected",
            severity="critical"
            if score >= 0.5
            else "warning"
            if score >= self.threshold
            else "info",
            redacted=redacted if self.redact and findings else None,
        )


class FactualConsistency(Guardrail):
    name = "factual_consistency"

    def __init__(self, model_adapter=None, threshold: float = 0.5):
        self._model = model_adapter
        self.threshold = threshold

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        if not self._model:
            return GuardrailResult(
                name=self.name,
                passed=True,
                score=0.0,
                reason="No model configured for factual consistency check",
                severity="info",
            )

        from aigis.models.base import Message

        prompt = (
            "You are a factual consistency checker. Given a statement and optional context, "
            "determine if the statement is factually consistent.\n\n"
            f"{'Context: ' + context + chr(10) + chr(10) if context else ''}"
            f"Statement: {text}\n\n"
            "Respond with ONLY a number between 0 (inconsistent) and 1 (consistent), "
            "then a brief explanation."
        )
        import re as _re

        resp = await self._model.generate([Message(role="user", content=prompt)])
        scores = _re.findall(r"0\.\d+|1\.0|1\.00|[01]", resp.content.strip())
        score = 1.0 - (float(scores[0]) if scores else 0.5)
        return GuardrailResult(
            name=self.name,
            passed=score < self.threshold,
            score=score,
            reason=resp.content[:200],
            severity="critical"
            if score >= 0.7
            else "warning"
            if score >= self.threshold
            else "info",
        )
