from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.eval.config import ConfigError, load_model_config, load_run_settings


def _write_yaml(path: Path, data: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data), encoding="utf-8")
    return path


def _config_data(seed: int = 17) -> dict:
    return {
        "seed": seed,
        "max_output_tokens": 64,
        "temperature": 0,
        "request_timeout_s": 15,
        "max_retries": 2,
        "max_consecutive_failures": 4,
        "backoff_initial_s": 0,
        "paths": {
            "results_raw": "results/raw",
            "run_log": "results/RUN_LOG.md",
            "prompt_template": "configs/prompt.txt",
        },
    }


def _models_data(api_key_env: str = "TEST_EVAL_KEY") -> dict:
    return {
        "helper": "TODO",
        "evaluated_models": [
            {
                "slug": "fixture",
                "provider": "groq",
                "model_string": "fixture-model",
                "api_key_env": api_key_env,
                "requests_per_minute": 30,
                "requests_per_day": 1000,
                "checked_on": "2026-11-16",
            }
        ],
    }


def test_config_loads_from_fixture_and_resolves_paths(tmp_path: Path) -> None:
    config_path = _write_yaml(tmp_path / "configs" / "config.yaml", _config_data())
    settings = load_run_settings(config_path)

    assert settings.seed == 17
    assert settings.max_output_tokens == 64
    assert settings.temperature == 0
    assert settings.paths["results_raw"] == (tmp_path / "results" / "raw").resolve()


def test_config_loads_noise_subset_ids_and_repeats(tmp_path: Path) -> None:
    config_data = _config_data()
    config_data["noise_subset"] = {
        "n_items": 2,
        "repeats": 3,
        "item_ids": ["item-1", "item-2"],
    }
    config_path = _write_yaml(tmp_path / "configs" / "config.yaml", config_data)

    noise_subset = load_run_settings(config_path).noise_subset

    assert noise_subset is not None
    assert noise_subset.n_items == 2
    assert noise_subset.repeats == 3
    assert noise_subset.item_ids == ("item-1", "item-2")


def test_config_rejects_mismatched_noise_subset_ids(tmp_path: Path) -> None:
    config_data = _config_data()
    config_data["noise_subset"] = {
        "n_items": 2,
        "repeats": 3,
        "item_ids": ["item-1"],
    }
    config_path = _write_yaml(tmp_path / "configs" / "config.yaml", config_data)

    with pytest.raises(ConfigError, match="exactly n_items"):
        load_run_settings(config_path)


def test_todo_error_names_field_and_file(tmp_path: Path) -> None:
    config_data = _config_data()
    config_data["seed"] = "TODO"
    config_path = _write_yaml(tmp_path / "configs" / "config.yaml", config_data)

    with pytest.raises(ConfigError, match=r"seed.*config\.yaml"):
        load_run_settings(config_path)


def test_non_finite_backoff_is_rejected(tmp_path: Path) -> None:
    config_data = _config_data()
    config_data["backoff_initial_s"] = float("nan")
    config_path = _write_yaml(tmp_path / "configs" / "config.yaml", config_data)

    with pytest.raises(ConfigError, match="backoff_initial_s"):
        load_run_settings(config_path)


def test_missing_api_key_names_environment_variable_and_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models_path = _write_yaml(
        tmp_path / "configs" / "models.yaml", _models_data("MISSING_EVAL_KEY")
    )
    monkeypatch.delenv("MISSING_EVAL_KEY", raising=False)

    with pytest.raises(ConfigError, match=r"MISSING_EVAL_KEY.*models\.yaml"):
        load_model_config(
            models_path,
            "fixture",
            dotenv_path=tmp_path / "no-local-env",
        )


def test_model_config_loads_key_without_exposing_it_in_repr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    models_path = _write_yaml(tmp_path / "configs" / "models.yaml", _models_data())
    monkeypatch.setenv("TEST_EVAL_KEY", "not-a-real-secret")

    model = load_model_config(models_path, "fixture", dotenv_path=tmp_path / "missing")

    assert model.api_key == "not-a-real-secret"
    assert "not-a-real-secret" not in repr(model)


def test_model_todo_error_names_field_and_file(tmp_path: Path) -> None:
    data = _models_data()
    data["evaluated_models"][0]["requests_per_minute"] = "TODO"
    models_path = _write_yaml(tmp_path / "configs" / "models.yaml", data)

    with pytest.raises(ConfigError, match=r"requests_per_minute.*models\.yaml"):
        load_model_config(models_path, "fixture", load_api_key=False)
