"""
Constitutional AI critique guardrail — reviews LLM outputs against a
constitutional set of principles and flags violations.

Based on Anthropic's Constitutional AI approach: a critique model reviews
output against defined principles and returns a pass/fail with reasoning.
Falls back to keyword-based principle checking if no model is available.
"""

from __future__ import annotations

from aigis.guardrails.engine import Guardrail, GuardrailResult


PRINCIPLES = [
    (
        "Helpful and Harmless",
        [
            "bomb",
            "explosive",
            "weapon",
            "gun",
            "knife",
            "kill",
            "murder",
            "rape",
            "assault",
            "abuse",
            "terrorist",
            "trafficking",
            "harmful",
            "dangerous",
            "hostage",
            "suicide",
            "overdose",
            "illegal",
            "unethical",
            "illicit",
        ],
    ),
    (
        "Truthful",
        [
            "hallucinated",
            "fabricated",
            "made up",
            "factually incorrect",
            "misleading",
            "false claim",
            "lying",
            "lie about",
        ],
    ),
    (
        "Respectful",
        [
            "hate",
            "racist",
            "sexist",
            "discriminat",
            "slur",
            "offensive",
            "harassment",
            "harass",
            "insult",
            "stupid",
            "idiot",
            "degrade",
            "humiliate",
            "intimidat",
        ],
    ),
    (
        "Privacy-Safe",
        [
            "ssn",
            "social security",
            "credit card",
            "bank account",
            "password",
            "private key",
            "personal info",
            "dox",
            "stalk",
        ],
    ),
    (
        "No Deception",
        [
            "deceptive",
            "fraud",
            "scam",
            "phishing",
            "manipulat",
            "trick",
            "deceiv",
            "impersonat",
            "fake identity",
        ],
    ),
]


CRITIQUE_PROMPT = """You are a constitutional AI reviewer. Evaluate the following response
against these principles and respond with ONLY a score (0.0 to 1.0) followed by
one-line explanation. 1.0 = passes all principles, 0.0 = severe violation.

Response: {output}

Score:"""


class ConstitutionalCritique(Guardrail):
    name = "constitutional_critique"

    def __init__(
        self,
        model_adapter=None,
        principles: list[tuple[str, list[str]]] | None = None,
        threshold: float = 0.5,
    ):
        self._model = model_adapter
        self._principles = principles or list(PRINCIPLES)
        self.threshold = threshold

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        if not self._model:
            return self._keyword_check(text)

        from aigis.models.base import Message

        prompt = CRITIQUE_PROMPT.format(output=text[:1000])
        resp = await self._model.generate([Message(role="user", content=prompt)])
        content = resp.content.strip()

        try:
            first_token = content.split()[0]
            score = float(first_token.rstrip("."))
            score = max(0.0, min(1.0, score))
        except (ValueError, IndexError):
            score = 0.5

        passed = score < self.threshold
        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=1.0 - score,
            reason=f"Constitutional critique score: {score:.2f} — {content[:100]}",
            severity="critical" if score < 0.3 else "warning" if score < self.threshold else "info",
        )

    def _keyword_check(self, text: str) -> GuardrailResult:
        text_lower = text.lower()
        violations: list[str] = []
        total_score = 0.0

        severity_weights = {
            "Helpful and Harmless": 1.0,
            "No Deception": 0.8,
            "Privacy-Safe": 0.8,
            "Respectful": 0.5,
            "Truthful": 0.3,
        }

        for principle_name, keywords in self._principles:
            hits = [kw for kw in keywords if kw in text_lower]
            if hits:
                weight = severity_weights.get(principle_name, 0.5)
                violation_score = min(1.0, weight * min(1.0, len(hits) / 2.0))
                total_score = max(total_score, violation_score)
                violations.append(f"{principle_name}: {hits}")

        passed = total_score < self.threshold
        reason = (
            "All principles satisfied"
            if not violations
            else f"Principle violations: {'; '.join(violations)}"
        )
        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=total_score,
            reason=reason,
            severity="critical" if total_score > 0.5 else "warning" if violations else "info",
        )
