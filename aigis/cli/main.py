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
@click.option("--format", "-f", "fmt", default="table", help="Output format: table, json, html")
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
    else:
        click.echo(formatted)


@cli.command()
@click.argument("text")
@click.option("--config", "-c", default=None, help="Guardrail config file")
@click.option("--jailbreak/--no-jailbreak", default=True, help="Check jailbreak patterns")
@click.option("--toxicity/--no-toxicity", default=True, help="Check toxicity")
def guard(text, config, jailbreak, toxicity):
    """Check text against guardrails."""
    import asyncio
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail

    async def run():
        pipeline = GuardrailPipeline()
        if jailbreak:
            pipeline.add_input_rail(JailbreakDetector())
        if toxicity:
            pipeline.add_input_rail(ToxicityGuardrail())

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
    from aigis.eval.runner import run_eval
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails.jailbreak import JailbreakDetector, ToxicityGuardrail

    cfg = load_config(str(config))
    click.echo(f"Running pipeline: {cfg.name}")

    eval_results = asyncio.run(run_eval(cfg))

    pipeline = GuardrailPipeline()
    pipeline.add_input_rail(JailbreakDetector())
    pipeline.add_input_rail(ToxicityGuardrail())

    from aigis.reporting.report import format_results

    output_path = Path(output)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "eval_results.json").write_text(format_results(eval_results, fmt="json"))

    click.echo(f"Results written to {output_path}/")


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
