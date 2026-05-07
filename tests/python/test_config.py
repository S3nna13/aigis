import pytest

from aigis.core.config import load_config, validate_config
from aigis.core.schema import ModelConfig


def test_model_config_defaults():
    cfg = ModelConfig(provider="openai", model="gpt-4o-mini")
    assert cfg.provider == "openai"
    assert cfg.temperature == 0.0
    assert cfg.api_key is None


def test_validate_config_minimal_eval():
    raw = {
        "version": "1",
        "aigis": "eval",
        "name": "test-eval",
        "model": {"provider": "openai", "model": "gpt-4o-mini"},
        "eval": {
            "prompts": ["Hello {{input}}"],
            "tests": [{"input": "hi", "expected": "hello"}],
            "assertions": [{"type": "contains"}],
        },
    }
    cfg = validate_config(raw)
    assert cfg.name == "test-eval"
    assert cfg.aigis == "eval"
    assert cfg.eval is not None
    assert len(cfg.eval.tests) == 1


def test_load_config_file_not_found():
    with pytest.raises(FileNotFoundError, match="Config not found"):
        load_config("/nonexistent/path.yaml")


def test_load_config_example(tmp_path):
    yaml_content = """
version: "1"
aigis: eval
name: "inline-test"
model:
  provider: openai
  model: gpt-4o-mini
eval:
  prompts:
    - "Answer: {{input}}"
  tests:
    - input: "2+2"
      expected: "4"
  assertions:
    - type: exact
"""
    p = tmp_path / "test.yaml"
    p.write_text(yaml_content)
    cfg = load_config(str(p))
    assert cfg.name == "inline-test"
    assert cfg.eval.model.model == "gpt-4o-mini"


def test_merge_top_level_into_eval(tmp_path):
    yaml_content = """
version: "1"
aigis: eval
name: "merge-test"
model:
  provider: openai
  model: gpt-4o
eval:
  prompts:
    - "{{input}}"
  tests:
    - input: "hello"
  assertions:
    - type: contains
"""
    p = tmp_path / "merge.yaml"
    p.write_text(yaml_content)
    cfg = load_config(str(p))
    assert cfg.eval.name == "merge-test"
    assert cfg.eval.model.model == "gpt-4o"
