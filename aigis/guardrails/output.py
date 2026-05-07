"""
Structured output validation guardrail — validates that LLM outputs conform
to expected schemas using Pydantic.

Prevents:
- Malformed JSON responses
- Schema violations in structured data
- Type mismatches in API-style responses
"""

from __future__ import annotations

import json
import re
from typing import Any, get_origin

from aigis.guardrails.engine import Guardrail, GuardrailResult


class OutputValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__(f"Validation errors: {errors}")


class StructuredOutputValidator(Guardrail):
    name = "structured_output"

    def __init__(
        self,
        schema: dict[str, Any] | None = None,
        json_strict: bool = False,
    ):
        self.schema = schema or {}
        self.json_strict = json_strict

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        errors: list[str] = []

        json_text = self._extract_json(text)
        if json_text is None:
            errors.append("No JSON object found in output")
            score = 0.9
            return GuardrailResult(
                name=self.name, passed=False, score=score,
                reason=f"Validation errors: {errors}", severity="critical",
            )

        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            return GuardrailResult(
                name=self.name, passed=False, score=1.0,
                reason=f"Invalid JSON: {e}", severity="critical",
            )

        if self.schema:
            errors = self._validate_schema(data, self.schema, path="")
            score = min(1.0, len(errors) / 3.0)
        else:
            score = 0.0

        passed = score < 0.3
        return GuardrailResult(
            name=self.name,
            passed=passed,
            score=score,
            reason="Output valid" if not errors else f"Validation errors: {errors}",
            severity="critical" if score > 0.7 else "warning" if errors else "info",
        )

    def _extract_json(self, text: str) -> str | None:
        text = text.strip()
        if text.startswith("{"):
            end = text.rfind("}") + 1
            if end > 0:
                return text[:end]
        matches = list(re.finditer(r"\{[^}]+\}", text))
        if matches:
            return matches[-1].group()
        return None

    def _validate_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
        path: str,
    ) -> list[str]:
        errors = []
        for field, expected_type in schema.items():
            field_path = f"{path}.{field}" if path else field
            if field not in data:
                errors.append(f"Missing field: {field_path}")
                continue
            actual = data[field]
            if not self._check_type(actual, expected_type):
                errors.append(
                    f"Type mismatch at {field_path}: "
                    f"expected {expected_type}, got {type(actual).__name__}"
                )
        return errors

    def _check_type(self, value: Any, expected: Any) -> bool:
        if expected is None:
            return value is None
        if isinstance(expected, type):
            return isinstance(value, expected)
        origin = get_origin(expected)
        if origin is list:
            return isinstance(value, list)
        if origin is dict:
            return isinstance(value, dict)
        return isinstance(value, expected)
