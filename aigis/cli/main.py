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
@click.option("--all/--no-all", "use_all", default=False, help="Enable all 14 guardrails")
@click.option("--jailbreak/--no-jailbreak", default=False, help="Jailbreak pattern detection (LLM01)")
@click.option("--toxicity/--no-toxicity", default=False, help="Toxicity keyword detection (LLM02)")
@click.option("--toxicity-filter/--no-toxicity-filter", default=False, help="Toxicity filter via Detoxify (LLM02)")
@click.option("--pii/--no-pii", default=False, help="PII detection and redaction (LLM06)")
@click.option("--injection/--no-injection", default=False, help="Prompt injection detection (LLM01)")
@click.option("--secrets/--no-secrets", default=False, help="Secret/API key scanning (LLM06)")
@click.option("--context/--no-context", default=False, help="Context window length validation (LLM04)")
@click.option("--rag-poisoning/--no-rag-poisoning", default=False, help="RAG context poisoning detection (LLM03)")
@click.option("--structured-output/--no-structured-output", default=False, help="Structured output validation (LLM07)")
@click.option("--constitutional/--no-constitutional", default=False, help="Constitutional AI critique (LLM02)")
@click.option("--factual/--no-factual", default=False, help="Factual consistency check (LLM05)")
@click.option("--hallucination/--no-hallucination", default=False, help="Hallucination detection (LLM05)")
def guard(
    text, config, use_all,
    jailbreak, toxicity, toxicity_filter, pii, injection, secrets,
    context, rag_poisoning, structured_output, constitutional,
    factual, hallucination,
):
    """Check text against one or more guardrails.

    Use --all to run all 14 guardrails at once, or pass individual flags.

    Examples:

      aigis guard "Hello" --all
      aigis guard "secret key = sk-abc123" --secrets
      aigis guard "Ignore all instructions" --injection --jailbreak
    """
    from aigis.core.config import load_config
    from aigis.eval.runner import _resolve_model
    from aigis.guardrails.engine import GuardrailPipeline
    from aigis.guardrails import (
        ContextWindowGuard,
        ConstitutionalCritique,
        FactualConsistency,
        HallucinationDetector,
        JailbreakDetector,
        PIIDetector,
        PromptInjectionDetector,
        RAGPoisoningDetector,
        SecretScanner,
        StructuredOutputValidator,
        ToxicityFilter,
        ToxicityGuardrail,
    )

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
            except Exception:
                pass

        flags = {
            "jailbreak": jailbreak,
            "toxicity": toxicity,
            "toxicity_filter": toxicity_filter,
            "pii": pii,
            "injection": injection,
            "secrets": secrets,
            "context": context,
            "rag_poisoning": rag_poisoning,
            "structured_output": structured_output,
            "constitutional": constitutional,
            "factual": factual,
            "hallucination": hallucination,
        }

        if use_all:
            flags = {k: True for k in flags}
            model = model or (await _resolve_model_if_needed())

        if flags.get("jailbreak"):
            pipeline.add_input_rail(JailbreakDetector())
        if flags.get("toxicity"):
            pipeline.add_input_rail(ToxicityGuardrail())
        if flags.get("toxicity_filter"):
            pipeline.add_input_rail(ToxicityFilter())
        if flags.get("pii"):
            pipeline.add_input_rail(PIIDetector(redact=True))
        if flags.get("injection"):
            pipeline.add_input_rail(PromptInjectionDetector())
        if flags.get("secrets"):
            pipeline.add_input_rail(SecretScanner())
        if flags.get("context"):
            pipeline.add_input_rail(ContextWindowGuard())
        if flags.get("rag_poisoning"):
            pipeline.add_input_rail(RAGPoisoningDetector())
        if flags.get("structured_output"):
            pipeline.add_output_rail(StructuredOutputValidator())
        if flags.get("constitutional"):
            pipeline.add_input_rail(ConstitutionalCritique())
        if flags.get("factual") and model:
            pipeline.add_output_rail(FactualConsistency(model_adapter=model))
        if flags.get("hallucination") and model:
            pipeline.add_output_rail(HallucinationDetector(model))

        if not pipeline._input_rails and not pipeline._output_rails:
            click.echo("No guardrails enabled. Use --all or specify flags.", err=True)
            raise click.Abort()

        results = await pipeline.check_input(text)
        return results

    async def _resolve_model_if_needed():
        from aigis.core.schema import ModelConfig
        cfg = ModelConfig(provider="openai", model="gpt-4o-mini")
        return _resolve_model(cfg)

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


@cli.command("validate")
@click.argument("config", type=click.Path(exists=True))
def validate(config):
    """Validate a YAML config file without running anything."""
    from aigis.core.config import load_config
    from rich.console import Console
    from rich.table import Table

    console = Console()
    try:
        cfg = load_config(str(config))
        console.print(f"[green]Config is valid[/green] — {cfg.name} ({cfg.aigis})")
        t = Table(title="Config Summary")
        t.add_column("Field")
        t.add_column("Value")
        if cfg.model:
            t.add_row("provider", cfg.model.provider)
            t.add_row("model", cfg.model.model)
        if cfg.aigis == "eval" and cfg.eval:
            t.add_row("prompts", str(len(cfg.eval.prompts)))
            t.add_row("tests", str(len(cfg.eval.tests)))
            t.add_row("assertions", str(len(cfg.eval.assertions)))
        if cfg.aigis == "guard" and cfg.guard:
            t.add_row("input_rails", str(cfg.guard.rails.input))
            t.add_row("output_rails", str(cfg.guard.rails.output))
        console.print(t)
    except Exception as exc:
        console.print(f"[red]Invalid config:[/red] {exc}")
        raise click.Abort()


@cli.command("webhooks")
@click.argument("action", type=click.Choice(["list", "add", "remove"]))
@click.option("--url", help="Webhook URL")
@click.option("--secret", help="HMAC secret for signing")
def webhooks(action, url, secret):
    """Manage webhook subscriptions."""
    import json
    from pathlib import Path

    hook_file = Path.home() / ".config" / "aigis" / "webhooks.json"
    hooks = json.loads(hook_file.read_text()) if hook_file.exists() else []

    if action == "list":
        if not hooks:
            click.echo("No webhooks registered.")
        for h in hooks:
            click.echo(f"  {h['url']} (secret={'yes' if h.get('secret') else 'no'})")
    elif action == "add":
        if not url:
            click.echo("--url required for add", err=True)
            raise click.Abort()
        hooks.append({"url": url, "secret": secret})
        hook_file.parent.mkdir(parents=True, exist_ok=True)
        hook_file.write_text(json.dumps(hooks, indent=2))
        click.echo(f"Added webhook: {url}")
    elif action == "remove":
        if not url:
            click.echo("--url required for remove", err=True)
            raise click.Abort()
        hooks = [h for h in hooks if h["url"] != url]
        hook_file.write_text(json.dumps(hooks, indent=2))
        click.echo(f"Removed webhook: {url}")


@cli.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish", "powershell"]))
def completion(shell):
    """Generate shell completion scripts."""
    if shell == "bash":
        script = f"{cli.to_info_dict()['name']} completion bash | source /dev/stdin"
        click.echo(f"# Add to ~/.bashrc or ~/.profile:\n{script}")
    elif shell == "zsh":
        script = f"source <({cli.name} completion zsh)"
        click.echo(f"# Add to ~/.zshrc:\n{script}")
    elif shell == "fish":
        script = f"{cli.name} completion fish | source"
        click.echo(f"# Add to ~/.config/fish/config.fish:\n{script}")
    elif shell == "powershell":
        script = f"{cli.name} completion powershell >> $PROFILE"
        click.echo(f"# Run in PowerShell:\n{script}")


cli.add_command(completion)
