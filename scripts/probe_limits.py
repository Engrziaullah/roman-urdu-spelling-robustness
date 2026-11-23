"""Probe Groq model limits/headers for model-1, helper, and a few other chat models.

This script is intentionally narrow and safe:
- reads the API key from environment/.env (never prints keys or Authorization/request headers)
- sends one tiny chat-completion request per selected model (max 8 tokens)
- prints only: model string, HTTP status, retry-after (if present), numeric rate-limit
  headers (limit/remaining/reset for requests and tokens, if present), and prompt/completion
  token counts from the response usage field when available

Run from repository root, for example:
    python scripts/probe_limits.py --models configs/models.yaml
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml
from dotenv import load_dotenv

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
FIXED_USER_AGENT = "roman-urdu-spelling-robustness/1.0"
RATE_LIMIT_HEADER_NAMES = (
    "retry-after",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
)


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file {path} must contain a mapping.")
    return data


def load_groq_targets(models_path: Path) -> tuple[str, str, str, dict[str, Any] | None, dict[str, Any] | None]:
    data = _read_yaml(models_path)
    evaluated = data.get("evaluated_models")
    if not isinstance(evaluated, list):
        raise ValueError(f"Field 'evaluated_models' must be a list in {models_path}.")
    model_1_entry: dict[str, Any] | None = None
    for entry in evaluated:
        if isinstance(entry, dict) and entry.get("slug") == "model-1":
            model_1_entry = entry
            break
    if model_1_entry is None:
        raise ValueError(f"Model slug 'model-1' not found in {models_path}.")
    if str(model_1_entry.get("provider", "")).lower() != "groq":
        raise ValueError("model-1 provider must be 'groq' for this probe.")
    model_1 = str(model_1_entry.get("model_string", "")).strip()
    api_key_env = str(model_1_entry.get("api_key_env", "")).strip()
    if not model_1 or not api_key_env:
        raise ValueError(f"model-1 must define model_string and api_key_env in {models_path}.")

    helper = data.get("helper")
    helper_entry = helper if isinstance(helper, dict) else None
    helper_string = ""
    if helper_entry and str(helper_entry.get("provider", "")).lower() == "groq":
        helper_string = str(helper_entry.get("model_string", "")).strip()
    return model_1, helper_string, api_key_env, model_1_entry, helper_entry


def resolve_api_key(api_key_env: str, dotenv_path: Path) -> str:
    load_dotenv(dotenv_path=dotenv_path, override=False)
    value = os.environ.get(api_key_env)
    if not value:
        raise ValueError(
            f"Required environment variable '{api_key_env}' is not set "
            f"(checked environment and {dotenv_path})."
        )
    return value


def _headers_dict(headers: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        items = headers.items()
    except Exception:
        return result
    for key, value in items:
        if isinstance(key, str) and isinstance(value, str):
            result[key.lower()] = value
    return result


def http_json(method: str, url: str, api_key: str, payload: dict[str, Any] | None = None, timeout_s: float = 30.0) -> tuple[int, dict[str, str], bytes]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": FIXED_USER_AGENT,
        },
        method=method,
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:
            return int(getattr(response, "status", response.getcode())), _headers_dict(response.headers), response.read()
    except HTTPError as exc:
        body = b""
        try:
            body = exc.read() or b""
        except Exception:
            body = b""
        return int(exc.code), _headers_dict(getattr(exc, "headers", {}) or {}), body
    except (URLError, TimeoutError, OSError) as exc:
        return 0, {}, str(exc).encode("utf-8", errors="replace")


def _usage_counts(body: bytes) -> tuple[int | str | None, int | str | None]:
    try:
        decoded = json.loads(body.decode("utf-8"))
    except Exception:
        return None, None
    if not isinstance(decoded, dict):
        return None, None
    usage = decoded.get("usage")
    if not isinstance(usage, dict):
        return None, None
    prompt = usage.get("prompt_tokens")
    completion = usage.get("completion_tokens")
    p = prompt if isinstance(prompt, int) and not isinstance(prompt, bool) else None
    c = completion if isinstance(completion, int) and not isinstance(completion, bool) else None
    return p, c


def _extract_rate_headers(headers: dict[str, str]) -> dict[str, str | None]:
    return {name: headers.get(name) for name in RATE_LIMIT_HEADER_NAMES}


def pick_other_chat_models(model_ids: list[str], exclude: set[str], limit: int = 3) -> list[str]:
    excluded_markers = ("whisper", "embed", "tts", "guard", "moderation", "tool-use", "orpheus")
    selected: list[str] = []
    for model_id in model_ids:
        if model_id in exclude:
            continue
        lowered = model_id.lower()
        if any(marker in lowered for marker in excluded_markers):
            continue
        selected.append(model_id)
        if len(selected) >= limit:
            break
    return selected


def _chat_payload(model_string: str, entry: dict[str, Any] | None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model_string,
        "messages": [{"role": "user", "content": "Reply with the single letter A."}],
        "temperature": 0,
        "max_completion_tokens": 8,
    }
    if entry and entry.get("reasoning_effort"):
        payload["reasoning_effort"] = entry["reasoning_effort"]
    return payload


def probe_model(model_string: str, api_key: str, entry: dict[str, Any] | None) -> dict[str, Any]:
    status, headers, body = http_json("POST", GROQ_CHAT_URL, api_key, _chat_payload(model_string, entry))
    prompt_tokens, completion_tokens = _usage_counts(body)
    result = {
        "model": model_string,
        "http_status": status,
        **_extract_rate_headers(headers),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument("--dotenv", default=".env")
    parser.add_argument("--max-others", type=int, default=3)
    args = parser.parse_args(argv)

    models_path = Path(args.models)
    dotenv_path = Path(args.dotenv)
    model_1, helper, api_key_env, model_1_entry, helper_entry = load_groq_targets(models_path)
    api_key = resolve_api_key(api_key_env, dotenv_path)

    list_status, _headers, body = http_json("GET", GROQ_MODELS_URL, api_key, None)
    model_ids: list[str] = []
    if list_status == 200:
        try:
            decoded = json.loads(body.decode("utf-8"))
            data = decoded.get("data", []) if isinstance(decoded, dict) else []
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and isinstance(item.get("id"), str):
                        model_ids.append(item["id"])
        except Exception:
            model_ids = []

    others = pick_other_chat_models(model_ids, {model_1, helper}, limit=max(0, args.max_others))
    targets: list[tuple[str, dict[str, Any] | None]] = [(model_1, model_1_entry)]
    if helper:
        targets.append((helper, helper_entry))
    for other in others:
        targets.append((other, None))

    rows = []
    for model_string, entry in targets:
        rows.append(probe_model(model_string, api_key, entry))

    output = {
        "models_list_http_status": list_status,
        "selected_other_models": others,
        "probes": rows,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
