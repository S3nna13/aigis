import asyncio

from aigis.guardrails.pii import PIIDetector, FactualConsistency


def test_pii_detects_email():
    det = PIIDetector()
    result = asyncio.run(det.check("Contact me at john@example.com for details"))
    assert result.passed is False
    assert "email" in result.reason.lower()


def test_pii_detects_phone():
    det = PIIDetector()
    result = asyncio.run(det.check("Call 555-123-4567 now"))
    assert result.passed is False


def test_pii_detects_ssn():
    det = PIIDetector()
    result = asyncio.run(det.check("SSN: 123-45-6789"))
    assert result.passed is False


def test_pii_redact():
    det = PIIDetector(redact=True)
    result = asyncio.run(det.check("Email: test@test.com and phone: 555-111-2222"))
    assert result.redacted is not None
    assert "[EMAIL]" in result.redacted
    assert "[PHONE]" in result.redacted
    assert "test@test.com" not in result.redacted


def test_pii_clean_text():
    det = PIIDetector()
    result = asyncio.run(det.check("The quick brown fox jumps over the lazy dog"))
    assert result.passed is True
    assert result.score == 0.0


def test_factual_consistency_no_model():
    fc = FactualConsistency()
    result = asyncio.run(fc.check("The sky is blue"))
    assert result.passed is True
    assert "No model configured" in result.reason


def test_pii_credit_card():
    det = PIIDetector()
    result = asyncio.run(det.check("Card: 4111 1111 1111 1111"))
    assert result.passed is False
    assert "credit_card" in result.reason.lower()
