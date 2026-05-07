from pathlib import Path


from aigis.core.config import load_config
from aigis.core.schema import AigisConfig, AssertionConfig
from aigis.eval.metrics import Contains, ExactMatch, LLMJudge, Metric, MetricResult
from aigis.models.base import Message, ModelAdapter


def _build_metric(assertion: AssertionConfig, model: ModelAdapter | None = None) -> Metric:
    match assertion.type:
        case "exact":
            return ExactMatch()
        case "contains":
            return Contains()
        case "llm_judge":
            return LLMJudge(model_adapter=model, criteria=assertion.metric or "correctness")
        case _:
            return ExactMatch()


async def run_eval(
    config: str | Path | AigisConfig, model_override: ModelAdapter | None = None
) -> list[MetricResult]:
    if isinstance(config, (str, Path)):
        parsed = load_config(str(config))
    else:
        parsed = config

    if parsed.aigis != "eval":
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

    for test in eval_cfg.tests:
        for prompt in eval_cfg.prompts:
            prompt_text = prompt if isinstance(prompt, str) else prompt.content
            filled = prompt_text.replace("{{input}}", test.input)
            resp = await model.generate([Message(role="user", content=filled)])
            output = resp.content

            for assertion in eval_cfg.assertions:
                metric = _build_metric(assertion, model)
                result = await metric.measure(
                    input=test.input, output=output, expected=test.expected
                )
                results.append(result)

    return results


def _resolve_model(cfg) -> ModelAdapter:
    from aigis.models.openai_adapter import OpenAIAdapter

    match cfg.provider:
        case "openai":
            return OpenAIAdapter(model=cfg.model, api_key=cfg.api_key, base_url=cfg.base_url)
        case _:
            msg = f"Unsupported provider: {cfg.provider}"
            raise ValueError(msg)
