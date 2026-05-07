from dataclasses import dataclass, field

from aigis.models.base import ModelAdapter


@dataclass
class GuardrailResult:
    name: str
    passed: bool
    score: float
    reason: str | None = None
    severity: str = "info"


class GuardrailPipeline:
    def __init__(self, model: ModelAdapter | None = None):
        self._model = model
        self._input_rails: list[Guardrail] = []
        self._output_rails: list[Guardrail] = []

    def add_input_rail(self, rail: "Guardrail"):
        self._input_rails.append(rail)

    def add_output_rail(self, rail: "Guardrail"):
        self._output_rails.append(rail)

    async def check_input(self, text: str) -> list[GuardrailResult]:
        results = []
        for rail in self._input_rails:
            result = await rail.check(text)
            results.append(result)
        return results

    async def check_output(self, text: str, context: str | None = None) -> list[GuardrailResult]:
        results = []
        for rail in self._output_rails:
            result = await rail.check(text, context=context)
            results.append(result)
        return results


class Guardrail:
    name: str

    async def check(self, text: str, context: str | None = None) -> GuardrailResult:
        ...
