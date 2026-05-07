"""
Prompt injection guardrail — detects attempts to manipulate the model by
injecting instructions into user prompts that override system behavior.

Addresses OWASP LLM01 (Prompt Injection) by detecting known injection
patterns, delimiter-based overrides, and role-play attacks.
"""

from __future__ import annotations

import re

from aigis.guardrails.engine import Guardrail, GuardrailResult


INJECT_FRAGMENTS = [
    "ignore previous",
    "ignore all instructions",
    "ignore your instructions",
    "disregard previous",
    "disregard all",
    "forget your instructions",
    "forget your rules",
    "you are now",
    "you must now",
    "you now have",
    "new instructions",
    "new system instructions",
    "override your",
    "bypass your",
    "ignore your",
    "no restrictions",
    "not bound by",
    "without any rules",
    "free from your",
    "escape your",
    "no ethical",
    "ignore the rules",
    "disregard the rules",
    "override the rules",
    "ignore system",
    "system prompt",
    "reveal your system",
    "print your system",
    "repeat your system",
    "show me your prompt",
    "what are your instructions",
    "what are your rules",
    "tell me your system",
    "what rules do you follow",
    "you are just a",
    "you are an ai",
    "you are a language model",
    "you are a chatbot",
    "just pretend",
    "for the purposes of",
    "act as a different",
    "role-play as",
    "pretend you are",
    "imagine you are",
    "you can do anything",
    "do anything now",
    "anything goes",
    "no content policy",
    "bypass content",
    "overcome limitation",
    "ignore content policy",
    "your guidelines",
    "your safety guidelines",
    "your policy",
    "your restrictions",
    "your terms",
    "conditions of use",
    "remove your",
    "strip your",
    "bypass safety",
    "safety filter",
    "bypass filter",
    "harmful content",
    "malicious instructions",
    "injected instructions",
    "adversarial prompt",
    "special word",
    "trigger word",
    "magic word",
    "master key",
    "universal override",
]

DELIMITER_TRICK = [
    r'"""\s*system',
    r'"""\s*instruction',
    r'"""\s*admin',
    r'```\s*system',
    r'```\s*instruction',
    r'<\|\s*system',
    r'<\|\s*instruction',
    r'<\|\s*user',
    r'{{.*}}',
    r'\{\{.*\}\}',
    r'<<\s*',
    r'>>\s*',
    r'<<<',
    r'>>>',
    r'\[\[.*\]\]',
]

OVERRIDE_MARKERS = [
    "sudoron",
    "dan",
    "sticker",
    "developer mode",
    "jailbroken",
    "jailbreak",
    "am i allowed",
    "can you",
    "will you",
    "you should allow",
    "you must allow",
    "i am a researcher",
    "red team",
]


class PromptInjectionDetector(Guardrail):
    name = "prompt_injection"

    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self._fragment_re = re.compile(
            "|".join(re.escape(f) for f in INJECT_FRAGMENTS),
            re.IGNORECASE,
        )
        self._delimiter_re = re.compile(
            "|".join(DELIMITER_TRICK),
            re.IGNORECASE,
        )
        self._override_re = re.compile(
            "|".join(re.escape(o) for o in OVERRIDE_MARKERS),
            re.IGNORECASE,
        )

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        text_lower = text.lower()

        frag_matches = self._fragment_re.findall(text_lower)
        delim_matches = self._delimiter_re.findall(text)
        override_matches = self._override_re.findall(text_lower)

        fragment_score = min(1.0, len(frag_matches) / 3.0)
        delimiter_score = min(1.0, len(delim_matches) / 2.0)
        override_score = min(1.0, len(override_matches) / 2.0)

        score = max(fragment_score, delimiter_score, override_score)

        reasons = []
        if frag_matches:
            reasons.append(f"injection fragments: {len(frag_matches)}")
        if delim_matches:
            reasons.append(f"delimiter tricks: {len(delim_matches)}")
        if override_matches:
            reasons.append(f"override markers: {len(override_matches)}")

        passed = score < self.threshold
        reason = "No prompt injection detected" if not reasons else (
            f"Potential injection detected — {', '.join(reasons)}"
        )
        severity = "critical" if score >= 0.7 else "warning" if score >= self.threshold else "info"

        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            severity=severity,
        )
