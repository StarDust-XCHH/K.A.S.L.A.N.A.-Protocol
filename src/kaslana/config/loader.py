"""Load .env and YAML configuration files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml

from kaslana.config.schema import AppConfig, ConfigError


def load_config(
    config_path: str | Path | None = None,
    env_path: str | Path | None = None,
) -> AppConfig:
    if env_path is not None:
        load_env_file(Path(env_path))
    else:
        default_env = Path(".env")
        if default_env.exists():
            load_env_file(default_env)

    resolved_path = Path(
        config_path
        or os.environ.get("KASLANA_CONFIG_PATH")
        or "config/config.yaml"
    )
    if not resolved_path.exists():
        raise ConfigError(
            f"Config file not found: {resolved_path}. "
            "Copy config/config.example.yaml to config/config.yaml first."
        )

    with resolved_path.open("r", encoding="utf-8") as stream:
        raw: Any = yaml.safe_load(stream)

    if not isinstance(raw, dict):
        raise ConfigError(f"Config file must contain a YAML mapping: {resolved_path}")

    return AppConfig.from_mapping(raw)


def load_env_file(path: Path) -> None:
    if not path.exists():
        raise ConfigError(f"Env file not found: {path}")

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigError(f"Invalid .env line {line_number}: expected KEY=VALUE")
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            raise ConfigError(f"Invalid .env line {line_number}: empty key")
        os.environ.setdefault(key, value)
