from typing import Any, Literal
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    provider: Literal["openai", "anthropic", "ollama", "local"]
    model: str
    api_key: str | None = None
    base_url: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = None


class PromptTemplate(BaseModel):
    id: str
    content: str
    variants: list[str] = Field(default_factory=list)
    provider_overrides: dict[str, str] | None = None


class AssertionConfig(BaseModel):
    type: Literal["exact", "contains", "regex", "llm_judge", "factual", "safe", "custom"]
    value: str | float | None = None
    threshold: float | None = None
    metric: str | None = None


class TestCase(BaseModel):
    input: str
    expected: str | None = None
    variants: list[str] | None = None
    tags: list[str] | None = None


class EvalConfig(BaseModel):
    name: str
    description: str | None = None
    model: ModelConfig
    prompts: list[PromptTemplate] | list[str]
    tests: list[TestCase]
    assertions: list[AssertionConfig]
    providers: list[ModelConfig] | None = None


class GuardrailType(BaseModel):
    input: list[str] = Field(default_factory=lambda: ["jailbreak", "toxic", "pii"])
    output: list[str] = Field(default_factory=lambda: ["hallucination", "toxic", "factual"])
    retrieval: list[str] = Field(default_factory=list)
    execution: list[str] = Field(default_factory=list)


class GuardrailConfig(BaseModel):
    name: str
    description: str | None = None
    model: ModelConfig
    rails: GuardrailType
    actions: dict[str, str] | None = None


class ReportConfig(BaseModel):
    format: Literal["json", "markdown", "html", "dashboard"] = "json"
    output_path: str = "./reports"
    include_traces: bool = False
    include_scores: bool = True


class AigisConfig(BaseModel):
    version: str = "1"
    aigis: Literal["eval", "guard", "run"]
    name: str
    description: str | None = None
    eval: EvalConfig | None = None
    guard: GuardrailConfig | None = None
    model: ModelConfig | None = None
    report: ReportConfig = ReportConfig()
