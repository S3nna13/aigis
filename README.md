# AIGIS — AI Guardrail & Integration System
**by [Aurelius Research](https://github.com/aurelius-research)**

A unified harness for evaluating, securing, and orchestrating LLM-powered applications. Combines evaluation benchmarks, safety guardrails, agent orchestration, and prompt testing into one cohesive framework.

```
┌─────────────────────────────────────────────────────────────┐
│                        AIGIS STACK                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌───────────┐  ┌───────────┐  ┌────────────┐             │
│   │   EVAL    │  │  SAFETY   │  │  AGENTS    │             │
│   │  Engine   │  │  Rails    │  │  HARNESS   │             │
│   └─────┬─────┘  └─────┬─────┘  └─────┬──────┘             │
│         │              │              │                     │
│         └──────────────┼──────────────┘                     │
│                        ▼                                    │
│              ┌─────────────────────┐                        │
│              │   AIGIS CORE ENGINE │                        │
│              │  FastAPI · SDK · CLI│                        │
│              └─────────────────────┘                        │
│                        ▲                                    │
│         ┌──────────────┼──────────────┐                     │
│   ┌─────┴─────┐  ┌─────┴─────┐  ┌─────┴──────┐            │
│   │  OpenAI   │  │ Anthropic │  │  Ollama    │            │
│   │ Adapter   │  │  Adapter  │  │  Adapter   │            │
│   └───────────┘  └───────────┘  └────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

```bash
# Install Python core
pip install -e .

# With all model providers
pip install -e '.[all]'

# With token counting (tiktoken)
pip install -e '.[tokenizer]'

# Install TypeScript CLI
cd cli && npm install && cd ..

# Run an evaluation
aigis eval examples/basic-eval.yaml

# Check text against all 14 guardrails
aigis guard "How do I hack a computer?" --all

# Run specific guardrails
aigis guard "sk-1234567890abcdef" --secrets
aigis guard "Ignore all previous instructions" --injection

# Launch the dashboard
aigis serve &
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
| `aigis guard <text>` | Check against guardrails (14 rails) |
| `aigis run <config>` | Full pipeline (eval + guard) |
| `aigis serve` | Launch the FastAPI server |
| `aigis dashboard` | Launch the web dashboard |
| `aigis repl` | Interactive REPL for quick checks |
| `aigis validate <config>` | Validate YAML config without running |
| `aigis webhooks list\|add\|remove` | Manage webhook subscriptions |
| `aigis completion bash\|zsh\|fish` | Generate shell completion scripts |

### Guard Command — All 14 Rails

```bash
aigis guard "text" --all                    # all 14 guardrails
aigis guard "text" --jailbreak              # LLM01 prompt injection/jailbreak
aigis guard "text" --toxicity               # LLM02 toxicity keywords
aigis guard "text" --toxicity-filter        # LLM02 Detoxify-backed filter
aigis guard "text" --pii                    # LLM06 PII redaction
aigis guard "text" --injection              # LLM01 prompt injection
aigis guard "text" --secrets               # LLM06 secret/API key scanning
aigis guard "text" --context               # LLM04 context length & padding DoS
aigis guard "text" --rag-poisoning         # LLM03 RAG context poisoning
aigis guard "text" --structured-output     # LLM07 JSON schema validation
aigis guard "text" --constitutional        # Constitutional AI critique
aigis guard "text" --factual               # LLM05 factual consistency
aigis guard "text" --hallucination         # LLM05 hallucination detection
```

## Guardrails — OWASP LLM Top 10 Coverage

| Rail | OWASP | Description |
|------|-------|-------------|
| `JailbreakDetector` | LLM01 | Phrase + keyword scoring for jailbreak attacks |
| `PromptInjectionDetector` | LLM01 | 45+ injection fragments, delimiter tricks, override markers |
| `ToxicityGuardrail` | LLM02 | Keyword-based toxicity detection |
| `ToxicityFilter` | LLM02 | Detoxify-backed multi-category filter |
| `ConstitutionalCritique` | LLM02 | Weighted constitutional principle evaluation |
| `RAGPoisoningDetector` | LLM03 | LlamaIndex/LangChain delimiter poisoning |
| `ContextWindowGuard` | LLM04 | Token limit, padding/padding DoS, repeat char detection |
| `FactualConsistency` | LLM05 | LLM-based factual consistency check |
| `HallucinationDetector` | LLM05 | RAG-grounded hallucination detection |
| `PIIDetector` | LLM06 | Email, phone, SSN, credit card, IP, ZIP detection |
| `SecretScanner` | LLM06 | 15+ secret patterns, Shannon entropy, base64 detection |
| `StructuredOutputValidator` | LLM07 | Pydantic schema validation on LLM JSON outputs |
| `TokenBudget` | LLM04 | Per-user token spend tracking |
| `count_tokens` / `estimate_tokens` | LLM04 | tiktoken-backed or heuristic token counting |

## Python SDK

```python
from aigis.sdk import Aigis

client = Aigis()

# Check text against guardrails
result = client.guard("Hello, how are you?", rails=["toxic", "secrets"])
print(f"Passed: {result.passed}")
for r in result.results:
    print(f"  {r.name}: score={r.score:.2f}, passed={r.passed}")

# Run full evaluation
summary = client.run_eval("examples/basic-eval.yaml")
print(f"Pass rate: {summary.pass_rate:.2%}")
```

## Dashboard

The interactive dashboard provides real-time visualization of:
- Evaluation scores and pass rates
- API metrics (p50/p95/p99 latency, token usage, cost)
- Guardrail hit counts and severity
- Historical trend charts

```bash
aigis serve &
aigis dashboard
# → http://127.0.0.1:5173
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `AIGIS_API_KEY` | `""` | API authentication key (required for production) |
| `AIGIS_CORS_ORIGINS` | `localhost:5173,127.0.0.1:5173` | Allowed CORS origins (comma-separated) |
| `AIGIS_RATE_LIMIT` | `100` | Max requests per window |
| `AIGIS_RATE_WINDOW` | `60` | Rate limit window in seconds |
| `AIGIS_DATA_DIR` | `./reports` | Where eval/guardrail JSON files are stored |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |

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
│   ├── guardrails/       # Safety guardrails (14 rails)
│   ├── reporting/        # Report generation
│   └── cli/              # Python CLI (click)
├── cli/                  # TypeScript CLI (commander)
├── dashboard/            # React/Vite web dashboard
├── examples/             # 8 guardrail example configs
├── tests/
└── .github/workflows/    # CI + Release workflows
```

## License

MIT