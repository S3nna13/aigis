from pathlib import Path

from aigis.core.config import load_config
from aigis.core.schema import AigisConfig, AssertionConfig
from aigis.eval.metrics import (
    Contains,
    CustomMetric,
    ExactMatch,
    FactualCheck,
    LLMJudge,
    Metric,
    MetricResult,
    RegexMatch,
    SafetyCheck,
)
from aigis.models.base import Message, ModelAdapter


def _build_metric(assertion: AssertionConfig, model: ModelAdapter | None = None) -> Metric:
    match assertion.type:
        case "exact":
            return ExactMatch()
        case "contains":
            return Contains()
        case "regex":
            return RegexMatch(pattern=str(assertion.value) if assertion.value else ".*")
        case "llm_judge":
            return LLMJudge(model_adapter=model, criteria=assertion.metric or "correctness")
        case "factual":
            return FactualCheck(model_adapter=model)
        case "safe":
            return SafetyCheck(model_adapter=model)
        case "custom":
            return CustomMetric(
                name=assertion.metric or "custom",
                eval_fn=str(assertion.value) if assertion.value is not None else None,
            )
        case _:
            return ExactMatch()


async def run_eval(
    config: str | Path | AigisConfig, model_override: ModelAdapter | None = None
) -> list[MetricResult]:
    if isinstance(config, (str, Path)):
        parsed = load_config(str(config))
    else:
        parsed = config

    if parsed.aigis not in ("eval", "run"):
        msg = f"Config is not an eval config (type={parsed.aigis})"
        raise ValueError(msg)

    eval_cfg = parsed.eval
    if not eval_cfg:
        msg = "No eval configuration found"
        raise ValueError(msg)

    model_cfg = eval_cfg.model or parsed.model
    if not model_cfg:
        msg = "No model configuration found"
        raise ValueError(msg)
    model = model_override or _resolve_model(model_cfg)
    results: list[MetricResult] = []

    prompt_templates = eval_cfg.prompts
    for test in eval_cfg.tests:
        for prompt in prompt_templates:
            prompt_text = prompt if isinstance(prompt, str) else prompt.content
            filled = prompt_text.replace("{{input}}", test.input)
            resp = await model.generate([Message(role="user", content=filled)])
            output = resp.content

            if isinstance(prompt, str) or not prompt.variants:
                for assertion in eval_cfg.assertions:
                    metric = _build_metric(assertion, model)
                    result = await metric.measure(
                        input=test.input, output=output, expected=test.expected
                    )
                    results.append(result)
            else:
                for variant_text in [prompt.content, *prompt.variants]:
                    filled_v = variant_text.replace("{{input}}", test.input)
                    resp_v = await model.generate([Message(role="user", content=filled_v)])
                    output_v = resp_v.content
                    for assertion in eval_cfg.assertions:
                        metric = _build_metric(assertion, model)
                        result = await metric.measure(
                            input=test.input, output=output_v, expected=test.expected
                        )
                        results.append(result)

    return results


def _resolve_model(cfg) -> ModelAdapter:
    from aigis.models.anthropic_adapter import AnthropicAdapter
    from aigis.models.local_adapter import LocalAdapter
    from aigis.models.ollama_adapter import OllamaAdapter
    from aigis.models.openai_adapter import OpenAIAdapter

    match cfg.provider:
        case "openai":
            return OpenAIAdapter(model=cfg.model, api_key=cfg.api_key, base_url=cfg.base_url)
        case "anthropic":
            return AnthropicAdapter(model=cfg.model, api_key=cfg.api_key, base_url=cfg.base_url)
        case "ollama":
            return OllamaAdapter(model=cfg.model, base_url=cfg.base_url)
        case "local":
            return LocalAdapter(model=cfg.model, api_key=cfg.api_key, base_url=cfg.base_url)
        case _:
            msg = f"Unsupported provider: {cfg.provider}"
            raise ValueError(msg)
