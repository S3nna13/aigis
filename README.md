# AIGIS — AI Guardrail & Integration System

A unified harness for evaluating, securing, and orchestrating LLM-powered applications. Combines evaluation benchmarks, safety guardrails, agent orchestration, and prompt testing into one cohesive framework.

```
            ▲
           ╱ ╲
          ╱   ╲
         ╱     ╲
        ╱ EVAL  ╲
       ╱─────────╲
      ╱  SAFETY   ╲
     ╱─────────────╲
    ╱    AGENTS     ╲
   ╱─────────────────╲
  ╱  PROMPT TESTING   ╲
 ╱─────────────────────╲
╱   AIGIS CORE ENGINE   ╲
───────────────────────────
```

## Quick Start

```bash
# Install Python core
pip install -e .

# Install TypeScript CLI
cd cli && npm install && cd ..

# Initialize a project
aigis init my-project

# Run an evaluation
aigis eval examples/basic-eval.yaml

# Check text against guardrails
aigis guard "How do I hack a computer?"

# Launch the dashboard
aigis dashboard
```

## Architecture

```yaml
# aigis.yaml — single config for everything
version: "1"
aigis: eval                # mode: eval | guard | run
name: "my-eval"

model:
  provider: openai         # openai, anthropic, ollama, local
  model: gpt-4o-mini

eval:                      # evaluation config
  prompts:
    - "Answer: {{input}}"
  tests:
    - input: "What is 2+2?"
      expected: "4"
  assertions:
    - type: contains
    - type: llm_judge
      metric: factual_correctness

guard:                     # optional guardrails
  rails:
    input: [jailbreak, toxic]
    output: [hallucination, factual]

report:
  format: html
  output_path: ./reports
```

## CLI Commands

| Command | Description |
|---------|-------------|
| `aigis init [dir]` | Scaffold a new project |
| `aigis eval <config>` | Run evaluations |
| `aigis guard <text>` | Check against guardrails |
| `aigis run <config>` | Full pipeline (eval + guard) |
| `aigis dashboard` | Launch web dashboard |

## Dashboard

The interactive dashboard provides real-time visualization of:
- Evaluation scores and pass rates
- Guardrail hit counts and severity
- Pipeline execution traces
- Historical trend charts

```bash
aigis dashboard
# → http://127.0.0.1:5173
```

## Extending

### Custom Metrics

```python
from aigis.eval.metrics import Metric, MetricResult

class MyMetric(Metric):
    name = "my_metric"

    async def measure(self, input, output, expected=None, **kwargs):
        score = 1.0 if "keyword" in output else 0.0
        return MetricResult(name=self.name, score=score)
```

### Custom Guardrails

```python
from aigis.guardrails.engine import Guardrail, GuardrailResult

class MyGuardrail(Guardrail):
    name = "my_guard"

    async def check(self, text, context=None):
        score = 0.0 if "bad" in text else 1.0
        return GuardrailResult(name=self.name, passed=score > 0.5, score=score)
```

## Project Structure

```
aigis/
├── aigis/                # Python core
│   ├── core/             # Config, schema, validation
│   ├── models/           # Model adapters (OpenAI, Anthropic, Ollama)
│   ├── eval/             # Evaluation engine, metrics
│   ├── guardrails/       # Safety guardrails
│   ├── reporting/        # Report generation
│   └── cli/              # Python CLI (click)
├── cli/                  # TypeScript CLI (commander)
├── dashboard/            # React/Vite web dashboard
├── examples/             # Example configs
└── tests/
```

## License

MIT
