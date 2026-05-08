"""
RAG poisoning detector — detects malicious instructions embedded in
retrieved context chunks from a RAG pipeline.

Addresses OWASP LLM03 (Training Data Poisoning) — specifically
"context poisoning" where an attacker injects instructions into
documents that get retrieved and injected into the LLM context.

Detects:
- Known RAG injection syntax (LlamaIndex, LangChain delimiters)
- Embedded system prompts in retrieved content
- Suspicious XML/JSON structures that could override behavior
"""

from __future__ import annotations

import re

from aigis.guardrails.engine import Guardrail, GuardrailResult


LLAMAINDEX_DELIMITERS = [
    r"<<\s*SYSTEM\s*>>",
    r"<<\s*USER\s*>>",
    r"<<\s*ASSISTANT\s*>>",
    r"<\|system\|>",
    r"<\|user\|>",
    r"<\|assistant\|>",
    r"\\[INST\\]",
    r"<<SYS>>",
    r"<</SYS>>",
]

LANGCHAIN_DELIMITERS = [
    r"```system",
    r"```assistant",
    r"```user",
    r"```instructions",
    r"---\nsystem",
    r"---\nuser",
    r"---\nassistant",
]

INJECTION_IN_DOCS_PATTERNS = [
    "ignore previous instructions",
    "ignore all instructions",
    "disregard your",
    "new system instructions",
    "override your",
    "you are now a",
    "pretend you are",
    "for the purpose of this",
    "roleplay as",
    "act as a different",
    "unrestricted",
    "no content policy",
    "bypass safety",
    "system prompt injection",
]

SUSPICIOUS_XML_PATTERNS = [
    r"<system_prompt>",
    r"<admin>",
    r"<hidden>",
    r"<secret>",
    r"<instruction role",
    r"<role>system</role>",
]


class RAGPoisoningDetector(Guardrail):
    name = "rag_poisoning"

    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self._delimiter_re = re.compile(
            "|".join(LLAMAINDEX_DELIMITERS + LANGCHAIN_DELIMITERS + SUSPICIOUS_XML_PATTERNS),
            re.IGNORECASE | re.MULTILINE,
        )
        self._injection_re = re.compile(
            "|".join(re.escape(p) for p in INJECTION_IN_DOCS_PATTERNS),
            re.IGNORECASE,
        )
        self._xml_re = re.compile(
            "|".join(SUSPICIOUS_XML_PATTERNS),
            re.IGNORECASE,
        )

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        text_lower = text.lower()

        delim_hits = self._delimiter_re.findall(text)
        injection_hits = self._injection_re.findall(text_lower)
        xml_hits = self._xml_re.findall(text_lower)

        delim_score = min(1.0, len(delim_hits) / 2.0)
        injection_score = min(1.0, len(injection_hits) / 3.0)
        xml_score = min(1.0, len(xml_hits) / 2.0)

        score = max(delim_score, injection_score, xml_score)
        passed = score < self.threshold

        reasons = []
        if delim_hits:
            reasons.append(f"delimiter syntax: {len(delim_hits)}")
        if injection_hits:
            reasons.append(f"injection patterns: {len(injection_hits)}")
        if xml_hits:
            reasons.append(f"suspicious XML: {len(xml_hits)}")

        severity = "critical" if score >= 0.7 else "warning" if reasons else "info"

        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason="RAG context clean"
            if not reasons
            else f"Poisoning detected: {', '.join(reasons)}",
            severity=severity,
        )
