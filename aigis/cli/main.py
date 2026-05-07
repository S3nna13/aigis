import asyncio
from pathlib import Path

import click

from aigis import __version__


@click.group()
@click.version_option(version=__version__, prog_name="aigis")
def cli():
    """AIGIS — AI Guardrail & Integration System.

    Unified evaluation, safety guardrails, and agent harness.
    """


@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--output", "-o", default="./reports", help="Output directory")
@click.option(
    "--format", "-f", "fmt", default="table", help="Output format: table, json, html, markdown"
)
def eval(config, output, fmt):
    """Run evaluations defined in a YAML config file."""
    from aigis.core.config import load_config
    from aigis.eval.runner import run_eval
    from aigis.reporting.report import format_results

    cfg = load_config(str(config))
    click.echo(f"Running eval: {cfg.name}")

    results = asyncio.run(run_eval(cfg))

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)

    formatted = format_results(results, fmt=fmt)
    if fmt == "json":
        (output_path / "results.json").write_text(formatted)
    elif fmt == "html":
        (output_path / "results.html").write_text(formatted)
    elif fmt == "markdown":
        (output_path / "results.md").write_text(formatted)
    else:
        click.echo(formatted)


@cli.command()
@click.argument("text")
@click.option("--config", "-c", default=None, help="Guardrail config file")
@click.option("--jailbreak/--no-jailbreak", default=True, help="Check jailbreak patterns")
@click.option("--toxicity/--no-toxicity", default=True, help="Check toxicity")
@click.option("--pii/--no-pii", default=False, help="Check for PII")
@click.option("--factual/--no-factual", default=False, help="Check factual consistency")
def guard(text, config, jailbreak, toxicity, pii, factual):
    """Check text against guardrails."""
    from aigis.core.config import load_config
    from aigis.eval.runner import _resolve_model
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail
    from aigis.guardrails.pii import FactualConsistency, PIIDetector

    async def run():
        pipeline = GuardrailPipeline()
        model = None

        if config:
            try:
                cfg = load_config(str(config))
                guard_cfg = cfg.guard
                if guard_cfg:
                    model_cfg = guard_cfg.model or cfg.model
                    if model_cfg:
                        model = _resolve_model(model_cfg)
                    rails = guard_cfg.rails
                    if rails:
                        jailbreak = "jailbreak" in rails.input
                        toxicity = "toxic" in rails.input
                        pii = "pii" in rails.input
                        factual = "factual" in rails.output
            except Exception:
                pass

        if jailbreak:
            pipeline.add_input_rail(JailbreakDetector())
        if toxicity:
            pipeline.add_input_rail(ToxicityGuardrail())
        if pii:
            pipeline.add_input_rail(PIIDetector(redact=True))
        if factual and model:
            pipeline.add_output_rail(FactualConsistency(model_adapter=model))

        results = await pipeline.check_input(text)
        return results

    results = asyncio.run(run())

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        click.echo(f"  [{status}] {r.name}: {r.score:.2f} — {r.reason}")

    if all(r.passed for r in results):
        click.echo("All guardrails passed.")
    else:
        click.echo("Some guardrails triggered! Review output above.", err=True)
        raise click.Abort()


@cli.command()
@click.argument("config", type=click.Path(exists=True))
@click.option("--output", "-o", default="./reports", help="Output directory")
def run(config, output):
    """Run a full pipeline (eval + guardrails) from a config file."""
    from aigis.core.config import load_config
    from aigis.eval.runner import _resolve_model, run_eval
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.hallucination import HallucinationDetector
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail
    from aigis.guardrails.pii import PIIDetector
    from aigis.reporting.report import format_results

    cfg = load_config(str(config))
    click.echo(f"Running pipeline: {cfg.name}")

    eval_results = asyncio.run(run_eval(cfg))

    pipeline = GuardrailPipeline()
    if cfg.guard and cfg.guard.rails:
        rails = cfg.guard.rails
        for rail_name in rails.input:
            match rail_name:
                case "jailbreak":
                    pipeline.add_input_rail(JailbreakDetector())
                case "toxic":
                    pipeline.add_input_rail(ToxicityGuardrail())
                case "pii":
                    pipeline.add_input_rail(PIIDetector(redact=True))
        model_cfg = cfg.guard.model or cfg.model
        model = _resolve_model(model_cfg) if model_cfg else None
        for rail_name in rails.output:
            match rail_name:
                case "hallucination":
                    if model:
                        pipeline.add_output_rail(HallucinationDetector(model))
                case "toxic":
                    pipeline.add_output_rail(ToxicityGuardrail())
    else:
        pipeline.add_input_rail(JailbreakDetector())
        pipeline.add_input_rail(ToxicityGuardrail())

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "eval_results.json").write_text(format_results(eval_results, fmt="json"))

    click.echo(f"Results written to {output_path}/")


@cli.command()
@click.option("--model", default="gpt-4o-mini", help="Model to use")
@click.option("--provider", default="openai", help="Model provider")
def repl(model, provider):
    """Interactive REPL for quick guard checks and eval queries."""
    import asyncio
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail
    from aigis.guardrails.pii import PIIDetector
    from aigis.models.anthropic_adapter import AnthropicAdapter
    from aigis.models.local_adapter import LocalAdapter
    from aigis.models.ollama_adapter import OllamaAdapter
    from aigis.models.openai_adapter import OpenAIAdapter

    def make_adapter():
        match provider:
            case "openai":
                return OpenAIAdapter(model=model)
            case "anthropic":
                return AnthropicAdapter(model=model)
            case "ollama":
                return OllamaAdapter(model=model)
            case "local":
                return LocalAdapter(model=model)
            case _:
                return OpenAIAdapter(model=model)

    click.echo(f"AIGIS Interactive REPL (model={provider}/{model})")
    click.echo("Commands: guard <text> | eval <input> | quit")
    click.echo("-" * 50)

    pipeline = GuardrailPipeline()
    pipeline.add_input_rail(JailbreakDetector())
    pipeline.add_input_rail(ToxicityGuardrail())
    pipeline.add_input_rail(PIIDetector())

    adapter = make_adapter()

    while True:
        try:
            user_input = click.prompt("\naigis> ", prompt_suffix="").strip()
        except (EOFError, KeyboardInterrupt):
            click.echo("\nGoodbye!")
            break

        if not user_input:
            continue

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            click.echo("Goodbye!")
            break

        if cmd == "guard":
            if not arg:
                click.echo("Usage: guard <text>")
                continue

            async def run_guard():
                return await pipeline.check_input(arg)

            results = asyncio.run(run_guard())
            for r in results:
                icon = "PASS" if r.passed else "FAIL"
                click.echo(f"  [{icon}] {r.name}: {r.score:.2f} — {r.reason}")

        elif cmd == "eval":
            if not arg:
                click.echo("Usage: eval <input>")
                continue

            async def run_eval():
                from aigis.models.base import Message

                resp = await adapter.generate([Message(role="user", content=arg)])
                return resp.content

            output = asyncio.run(run_eval())
            click.echo(f"Response: {output}")
            guard_results = asyncio.run(pipeline.check_input(output))
            for r in guard_results:
                icon = "PASS" if r.passed else "FAIL"
                click.echo(f"  [{icon}] {r.name}: {r.score:.2f}")

        elif cmd == "help":
            click.echo("Commands:")
            click.echo("  guard <text>  — Run guardrail checks on text")
            click.echo("  eval <input>  — Generate response and run guardrails")
            click.echo("  quit / exit  — Exit REPL")
        else:
            click.echo(f"Unknown command: {cmd}. Try 'help'.")


@cli.command()
@click.option("--port", "-p", default=8080, help="API server port")
@click.option("--host", default="127.0.0.1", help="API server host")
def serve(port, host):
    """Launch the AIGIS API server for the dashboard."""
    import uvicorn

    click.echo(f"Starting AIGIS API server on http://{host}:{port}")
    uvicorn.run("aigis.api:app", host=host, port=port, reload=True)


@cli.command()
@click.option("--port", "-p", default=5173, help="Dashboard port")
@click.option("--host", default="127.0.0.1", help="Dashboard host")
def dashboard(port, host):
    """Launch the AIGIS interactive dashboard."""
    click.echo("Starting AIGIS Dashboard...")
    click.echo(f"Open http://{host}:{port} in your browser")
    import subprocess
    import sys

    dashboard_dir = str(Path(__file__).parent.parent.parent / "dashboard")
    subprocess.run(
        [sys.executable, "-m", "http.server", str(port), "--bind", host],
        cwd=dashboard_dir,
    )


@cli.command()
@click.argument("path", default=".")
def init(path):
    """Initialize a new AIGIS project with example config."""
    target = Path(path) / "aigis.yaml"
    if target.exists():
        click.echo(f"File exists: {target}", err=True)
        raise click.Abort()
    target.write_text("""# AIGIS configuration
version: "1"
aigis: eval
name: "my-first-eval"
description: "Initial evaluation"

model:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0

eval:
  prompts:
    - "Answer the following: {{input}}"
  tests:
    - input: "What is 2+2?"
      expected: "4"
  assertions:
    - type: contains
      metric: correctness
    - type: exact
""")
    click.echo(f"Created {target}")
