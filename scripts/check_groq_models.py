"""Check Groq model availability via the official list-models endpoint.

Loads API key from environment/.env without printing it. Prints only HTTP status
and whether configured model strings are present.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
    except OSError as exc:
        raise SystemExit(f"Cannot read {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"Expected mapping in {path}.")
    return data


def _get_model_strings(models_path: Path) -> tuple[str, str, str]:
    data = _load_yaml(models_path)
    evaluated = data.get("evaluated_models")
    helper = data.get("helper")
    if not isinstance(evaluated, list):
        raise SystemExit(f"Field 'evaluated_models' must be a list in {models_path}.")
    model1 = None
    for entry in evaluated:
        if isinstance(entry, dict) and entry.get("slug") == "model-1":
            model1 = entry
            break
    if model1 is None:
        raise SystemExit(f"Could not find evaluated model slug 'model-1' in {models_path}.")
    if not isinstance(helper, dict):
        raise SystemExit(f"Field 'helper' must be a mapping in {models_path}.")
    model1_string = str(model1.get("model_string", "")).strip()
    helper_string = str(helper.get("model_string", "")).strip()
    key_env = str(model1.get("api_key_env", "")).strip() or str(helper.get("api_key_env", "")).strip()
    if not model1_string or model1_string == "TODO":
        raise SystemExit(f"model-1 model_string is missing or TODO in {models_path}.")
    if not helper_string or helper_string == "TODO":
        raise SystemExit(f"helper model_string is missing or TODO in {models_path}.")
    if not key_env or key_env == "TODO":
        raise SystemExit(f"Groq api_key_env is missing or TODO in {models_path}.")
    return model1_string, helper_string, key_env


def _extract_ids(payload: Any) -> set[str]:
    ids: set[str] = set()
    if isinstance(payload, dict):
        data = payload.get("data")
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    value = item.get("id")
                    if isinstance(value, str):
                        ids.add(value)
        # fallback: some APIs may return models differently
        for key in ("id", "model"):
            value = payload.get(key)
            if isinstance(value, str):
                ids.add(value)
    return ids


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument("--dotenv", default=str(REPO_ROOT / ".env"))
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)

    models_path = (REPO_ROOT / args.models).resolve() if not Path(args.models).is_absolute() else Path(args.models)
    dotenv_path = Path(args.dotenv)
    model1_string, helper_string, key_env = _get_model_strings(models_path)

    if args.mock:
        print(json.dumps({
            "http_status": 200,
            "model_1_present": True,
            "helper_present": True,
            "mock": True,
        }, ensure_ascii=False))
        return 0

    load_dotenv(dotenv_path)
    api_key = os.environ.get(key_env)
    if not api_key:
        print(json.dumps({
            "http_status": None,
            "model_1_present": False,
            "helper_present": False,
            "error": f"missing environment variable: {key_env}",
        }, ensure_ascii=False))
        return 1

    request = urllib.request.Request(
        GROQ_MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "roman-urdu-spelling-robustness/groq-model-check",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", response.getcode())
            body = response.read()
    except urllib.error.HTTPError as exc:
        # do not read/print body to avoid leaking sensitive details
        print(json.dumps({
            "http_status": exc.code,
            "model_1_present": False,
            "helper_present": False,
        }, ensure_ascii=False))
        return 1
    except Exception as exc:
        print(json.dumps({
            "http_status": None,
            "model_1_present": False,
            "helper_present": False,
            "error": exc.__class__.__name__,
        }, ensure_ascii=False))
        return 1

    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        payload = None
    ids = _extract_ids(payload)
    present_model1 = model1_string in ids
    present_helper = helper_string in ids
    print(json.dumps({
        "http_status": status,
        "model_1_present": present_model1,
        "helper_present": present_helper,
    }, ensure_ascii=False))
    return 0 if present_model1 and present_helper else 1


if __name__ == "__main__":
    sys.exit(main())
