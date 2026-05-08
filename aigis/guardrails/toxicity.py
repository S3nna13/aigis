"""
Toxicity filter guardrail — uses Detoxify for multi-category toxicity classification.

Falls back to keyword-based detection if Detoxify is not installed.

Supports categories matching the Detoxify taxonomy:
toxic, severe_toxic, obscene, threat, insult, identity_attack
"""

from __future__ import annotations

from aigis.guardrails.engine import Guardrail, GuardrailResult

_TOXICITY_KEYWORD_PATTERNS = [
    "hate",
    "kill",
    "murder",
    "rape",
    "terrorist",
    "extremist",
    "bomb",
    "weapon",
    "attack",
    "harmful",
    "violent",
    "abuse",
    "assault",
    "molest",
    "racist",
    "sexist",
    "discriminate",
    "slur",
    "threat",
]


class ToxicityFilter(Guardrail):
    name = "toxicity_filter"

    CATEGORIES = [
        "toxic",
        "severe_toxic",
        "obscene",
        "threat",
        "insult",
        "identity_attack",
    ]

    def __init__(
        self,
        threshold: float = 0.5,
        categories: list[str] | None = None,
        use_detoxify: bool = True,
    ):
        self.threshold = threshold
        self.categories = categories or self.CATEGORIES
        self.use_detoxify = use_detoxify
        self._model = None

    def _load_detoxify(self):
        if self._model is not None:
            return self._model
        try:
            from detoxify import Detoxify

            self._model = Detoxify("unbiased")
            return self._model
        except ImportError:
            return None

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        model = self._load_detoxify()

        if model is not None:
            scores = model.predict(text)
            violations = {
                cat: scores.get(cat, 0.0)
                for cat in self.categories
                if scores.get(cat, 0.0) > self.threshold
            }
            max_score = max(violations.values()) if violations else 0.0
            score = max_score
            passed = score < self.threshold
            reason = (
                f"Detoxify flagged: {list(violations.keys())}"
                if violations
                else "No toxic content detected"
            )
            severity = "critical" if max_score > 0.8 else "warning" if violations else "info"
        else:
            text_lower = text.lower()
            matches = [kw for kw in _TOXICITY_KEYWORD_PATTERNS if kw in text_lower]
            score = min(1.0, len(matches) / 3.0)
            passed = score < self.threshold
            reason = f"Keyword match: {matches}" if matches else "No toxic content detected"
            severity = "critical" if score > 0.7 else "warning" if matches else "info"

        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            severity=severity,
        )
