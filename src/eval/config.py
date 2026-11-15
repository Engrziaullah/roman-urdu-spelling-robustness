"""Load evaluation settings and model credentials without exposing secrets."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from math import isfinite
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


class ConfigError(ValueError):
    """Raised when an evaluation configuration is missing or invalid."""


@dataclass(frozen=True)
class RunSettings:
    seed: int
    max_output_tokens: int
    temperature: float
    request_timeout_s: float
    max_retries: int
    max_consecutive_failures: int
    backoff_initial_s: float
    paths: dict[str, Path]


@dataclass(frozen=True)
class ModelConfig:
    slug: str
    provider: str
    model_string: str
    api_key_env: str
    requests_per_minute: int
    requests_per_day: int
    checked_on: str
    api_key: str | None = field(default=None, repr=False)


def _read_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except OSError as exc:
        raise ConfigError(f"Cannot read configuration file {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration in {path} must be a YAML mapping.")
    return data


def _required(data: dict[str, Any], key: str, path: Path) -> Any:
    value = data.get(key)
    if value is None or (isinstance(value, str) and value.strip().upper() == "TODO"):
        raise ConfigError(f"Required field '{key}' is TODO or missing in {path}.")
    return value


def _positive_int(value: Any, field_name: str, path: Path) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ConfigError(f"Field '{field_name}' must be a positive integer in {path}.")
    return value


def _positive_number(value: Any, field_name: str, path: Path) -> float:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not isfinite(value)
        or value <= 0
    ):
        raise ConfigError(f"Field '{field_name}' must be a positive number in {path}.")
    return float(value)


def load_run_settings(config_path: str | Path) -> RunSettings:
    """Load validated run settings and resolve configured paths from the repo root."""
    path = Path(config_path).resolve()
    data = _read_yaml(path)
    seed = _required(data, "seed", path)
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ConfigError(f"Field 'seed' must be an integer in {path}.")

    max_output_tokens = _positive_int(
        _required(data, "max_output_tokens", path), "max_output_tokens", path
    )
    temperature = data.get("temperature")
    if isinstance(temperature, bool) or temperature != 0:
        raise ConfigError(f"Field 'temperature' must be 0 in {path}.")

    request_timeout_s = _positive_number(
        _required(data, "request_timeout_s", path), "request_timeout_s", path
    )
    max_retries_value = _required(data, "max_retries", path)
    if (
        isinstance(max_retries_value, bool)
        or not isinstance(max_retries_value, int)
        or max_retries_value < 0
    ):
        raise ConfigError(f"Field 'max_retries' must be a non-negative integer in {path}.")
    max_consecutive_failures = _positive_int(
        _required(data, "max_consecutive_failures", path),
        "max_consecutive_failures",
        path,
    )
    backoff_initial_s = data.get("backoff_initial_s")
    if (
        isinstance(backoff_initial_s, bool)
        or not isinstance(backoff_initial_s, (int, float))
        or not isfinite(backoff_initial_s)
        or backoff_initial_s < 0
    ):
        raise ConfigError(f"Field 'backoff_initial_s' must be non-negative in {path}.")

    root = path.parent.parent
    configured_paths = _required(data, "paths", path)
    if not isinstance(configured_paths, dict):
        raise ConfigError(f"Field 'paths' must be a mapping in {path}.")
    resolved_paths: dict[str, Path] = {}
    for key in ("results_raw", "run_log", "prompt_template"):
        value = _required(configured_paths, key, path)
        if not isinstance(value, str):
            raise ConfigError(f"Field 'paths.{key}' must be a path string in {path}.")
        resolved_paths[key] = (root / value).resolve()

    return RunSettings(
        seed=seed,
        max_output_tokens=max_output_tokens,
        temperature=0.0,
        request_timeout_s=request_timeout_s,
        max_retries=max_retries_value,
        max_consecutive_failures=max_consecutive_failures,
        backoff_initial_s=float(backoff_initial_s),
        paths=resolved_paths,
    )


def load_model_config(
    models_path: str | Path,
    model_slug: str,
    *,
    load_api_key: bool = True,
    dotenv_path: str | Path | None = None,
) -> ModelConfig:
    """Load one evaluated model and optionally resolve its key from the environment."""
    path = Path(models_path).resolve()
    data = _read_yaml(path)
    models = data.get("evaluated_models")
    if not isinstance(models, list):
        raise ConfigError(f"Field 'evaluated_models' must be a list in {path}.")
    matches = [
        model for model in models
        if isinstance(model, dict) and model.get("slug") == model_slug
    ]
    if len(matches) != 1:
        raise ConfigError(
            f"Model slug '{model_slug}' must match exactly one entry in {path}."
        )
    model = matches[0]
    required_strings: dict[str, str] = {}
    for key in ("slug", "provider", "model_string", "api_key_env", "checked_on"):
        value = _required(model, key, path)
        if not isinstance(value, str) or not value.strip():
            raise ConfigError(f"Field 'evaluated_models.{key}' must be text in {path}.")
        required_strings[key] = value.strip()
    try:
        date.fromisoformat(required_strings["checked_on"])
    except ValueError as exc:
        raise ConfigError(
            f"Field 'checked_on' must use YYYY-MM-DD in {path}."
        ) from exc

    api_key_env = required_strings["api_key_env"]
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", api_key_env):
        raise ConfigError(
            f"Field 'evaluated_models.api_key_env' must be an environment variable "
            f"name in {path}."
        )
    requests_per_minute = _positive_int(
        _required(model, "requests_per_minute", path), "requests_per_minute", path
    )
    requests_per_day = _positive_int(
        _required(model, "requests_per_day", path), "requests_per_day", path
    )

    api_key: str | None = None
    if load_api_key:
        env_file = Path(dotenv_path).resolve() if dotenv_path else path.parent.parent / ".env"
        load_dotenv(dotenv_path=env_file, override=False)
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ConfigError(
                f"Required environment variable '{api_key_env}' is not set "
                f"(configured in {path})."
            )

    return ModelConfig(
        slug=required_strings["slug"],
        provider=required_strings["provider"].lower(),
        model_string=required_strings["model_string"],
        api_key_env=api_key_env,
        requests_per_minute=requests_per_minute,
        requests_per_day=requests_per_day,
        checked_on=required_strings["checked_on"],
        api_key=api_key,
    )
