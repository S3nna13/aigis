"""
Secret scanner guardrail — detects API keys, tokens, credentials, and high-entropy
strings in prompts before they are sent to the model.

Supports common secret formats: AWS keys, GCP tokens, Azure keys, OpenAI keys,
GitHub tokens, SSH keys, credit cards, and generic high-entropy strings.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from aigis.guardrails.engine import Guardrail, GuardrailResult


@dataclass
class SecretPattern:
    name: str
    pattern: re.Pattern
    entropy_aware: bool = False


_SHARED_SECRET_PATTERNS = (
    SecretPattern(
        name="aws_access_key",
        pattern=re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
    SecretPattern(
        name="aws_secret_key",
        pattern=re.compile(r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{40}['\"]?"),
    ),
    SecretPattern(
        name="openai_api_key",
        pattern=re.compile(r"sk-[A-Za-z0-9]{48}"),
    ),
    SecretPattern(
        name="github_token",
        pattern=re.compile(r"(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,255}"),
    ),
    SecretPattern(
        name="slack_token",
        pattern=re.compile(r"xox[baprs]-[0-9]{10,13}-[0-9]{10,13}[a-zA-Z0-9-]*"),
    ),
    SecretPattern(
        name="stripe_key",
        pattern=re.compile(r"(sk|pk)_(test|live)_[0-9a-zA-Z]{24,255}"),
    ),
    SecretPattern(
        name="gcp_service_account",
        pattern=re.compile(r'"type": "service_account"'),
    ),
    SecretPattern(
        name="gcp_api_key",
        pattern=re.compile(r"AIza[0-9A-Za-z_-]{35,255}"),
    ),
    SecretPattern(
        name="azure_subscription_key",
        pattern=re.compile(r"(?i)azure_[a-z_]+key\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{32,}['\"]?"),
    ),
    SecretPattern(
        name="ssh_private_key",
        pattern=re.compile(r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----"),
    ),
    SecretPattern(
        name="pgp_private_key",
        pattern=re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----"),
    ),
    SecretPattern(
        name="generic_api_key",
        pattern=re.compile(r"(?i)(api[_-]?key|apikey|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9_=-]{20,128}['\"]?"),
    ),
    SecretPattern(
        name="authorization_header",
        pattern=re.compile(r"(?i)authorization\s*:\s*Bearer\s+[A-Za-z0-9_=-]+\.?[A-Za-z0-9_=-]*"),
    ),
    SecretPattern(
        name="base64_encoded_secret",
        pattern=re.compile(r"(?i)(secret|password|token|credential)\s*[:=]\s*['\"]?[A-Za-z0-9+/=]{40,100}['\"]?"),
    ),
    SecretPattern(
        name="connection_string",
        pattern=re.compile(r"(?i)(mongodb|mysql|postgres|postgresql|redis|amqp|rabbitmq)://[^@]+@"),
    ),
    SecretPattern(
        name="dotenv_assignment",
        pattern=re.compile(r"^[A-Z_0-9]+=(sk-|AKIA|ghp_|xoxb|AIza)"),
    ),
)


def _shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    length = len(text)
    freq: dict[str, float] = {}
    for ch in text:
        freq[ch] = freq.get(ch, 0) + 1
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _find_high_entropy_strings(text: str, threshold: float = 4.5, min_length: int = 20) -> list[str]:
    """Find long high-entropy strings that may be secrets."""
    results = []
    candidates = re.findall(r"[A-Za-z0-9+/=]{20,200}", text)
    for candidate in candidates:
        if "=" in candidate and len(candidate) > 30:
            try:
                import base64
                base64.b64decode(candidate)
                results.append(candidate)
                continue
            except Exception:
                pass
        if _shannon_entropy(candidate) > threshold:
            results.append(candidate)
    return results


class SecretScanner(Guardrail):
    name = "secret_scanner"

    def __init__(
        self,
        threshold: float = 0.3,
        block_on_high_entropy: bool = True,
        entropy_threshold: float = 4.5,
    ):
        self.threshold = threshold
        self.block_on_high_entropy = block_on_high_entropy
        self.entropy_threshold = entropy_threshold
        self._patterns = _SHARED_SECRET_PATTERNS

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        found: list[str] = []
        for sp in self._patterns:
            if sp.pattern.search(text):
                found.append(sp.name)

        high_entropy = _find_high_entropy_strings(text, threshold=self.entropy_threshold)
        score = min(1.0, len(found) / 3.0)
        if high_entropy and self.block_on_high_entropy:
            score = max(score, 0.8)
        passed = score < self.threshold

        reason = "No secrets detected" if not found and not high_entropy else (
            f"Detected secret types: {found}" +
            (f"; high-entropy strings found: {len(high_entropy)}" if high_entropy else "")
        )
        severity = "critical" if found else "warning" if high_entropy else "info"

        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason=reason,
            severity=severity,
        )
