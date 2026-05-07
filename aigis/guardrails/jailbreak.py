from aigis.guardrails.engine import Guardrail, GuardrailResult


class JailbreakDetector(Guardrail):
    name = "jailbreak_detection"

    JAILBREAK_PATTERNS = [
        "ignore previous instructions",
        "ignore all instructions",
        "you are now",
        "DAN",
        "do anything now",
        "you must act as",
        "pretend you are",
        "bypass your",
        "override your",
        "forget your",
        "you have been",
        "new personality",
        "jailbreak",
        "no restrictions",
        "you don't need to follow",
        "you're free from",
        "act as a human",
        "roleplay as",
        "developer mode",
        "jailbroken",
        "chatgpt is dead",
        "character.ai style",
    ]

    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        text_lower = text.lower()
        matches = [p for p in self.JAILBREAK_PATTERNS if p.lower() in text_lower]
        score = min(1.0, len(matches) / 5.0)
        return GuardrailResult(
            name=self.name,
            passed=score < self.threshold,
            score=score,
            reason=f"Found {len(matches)} jailbreak pattern(s): {matches}"
            if matches
            else "No jailbreak patterns detected",
            severity="critical"
            if score >= 0.7
            else "warning"
            if score >= self.threshold
            else "info",
        )


class ToxicityGuardrail(Guardrail):
    name = "toxicity"

    TOXIC_PATTERNS = [
        "hate",
        "kill",
        "destroy",
        "stupid",
        "idiot",
        "racist",
        "sexist",
        "violence",
        "attack",
    ]

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        text_lower = text.lower()
        matches = [p for p in self.TOXIC_PATTERNS if p.lower() in text_lower]
        score = min(1.0, len(matches) / 3.0)
        return GuardrailResult(
            name=self.name,
            passed=score < self.threshold,
            score=score,
            reason=f"Toxic content detected: {matches}" if matches else "No toxic content detected",
            severity="critical"
            if score >= 0.7
            else "warning"
            if score >= self.threshold
            else "info",
        )
