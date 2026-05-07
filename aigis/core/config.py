from pathlib import Path

import yaml
from pydantic import ValidationError

from aigis.core.schema import AigisConfig


def load_config(path: str | Path) -> AigisConfig:
    path = Path(path)
    if not path.exists():
        msg = f"Config not found: {path}"
        raise FileNotFoundError(msg)
    raw = yaml.safe_load(path.read_text())
    try:
        return AigisConfig.model_validate(raw)
    except ValidationError as e:
        msg = f"Invalid config in {path}:\n{e}"
        raise ValueError(msg) from e


def validate_config(raw: dict) -> AigisConfig:
    try:
        return AigisConfig.model_validate(raw)
    except ValidationError as e:
        msg = f"Invalid config:\n{e}"
        raise ValueError(msg) from e
