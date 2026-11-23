"""Diagnose Groq HTTP 403/access issues without exposing secrets.

Sends one tiny chat-completion request per variant (max 8 output tokens),
reads the configured model strings from configs/models.yaml, loads the API
key from the environment/.env, and prints only non-secret diagnostics:
variant name, HTTP status, selected error-body fields (message/type/code,
each truncated to 300 chars) or the first 200 chars of a non-JSON body, and
response headers `server`/`cf-ray` when present.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

import yaml
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"
GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"
RUNNER_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "roman-urdu-spelling-robustness/1.0",
}
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
NON_CHAT_MARKERS = ("whisper", "embed", "tts", "guard", "moderation", "tool-use")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected mapping in {path}.")
    return data


def _get_config(models_path: Path) -> tuple[str, str, str, dict[str, Any], dict[str, Any]]:
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
    if model1 is None or not isinstance(helper, dict):
        raise SystemExit(f"Could not find model-1/helper in {models_path}.")
    model1_string = str(model1.get("model_string", "")).strip()
    helper_string = str(helper.get("model_string", "")).strip()
    key_env = str(model1.get("api_key_env", "")).strip() or str(helper.get("api_key_env", "")).strip()
    if not model1_string or model1_string == "TODO" or not helper_string or helper_string == "TODO":
        raise SystemExit(f"model-1/helper model_string missing in {models_path}.")
    if not key_env or key_env == "TODO":
        raise SystemExit(f"Groq api_key_env missing in {models_path}.")
    return model1_string, helper_string, key_env, model1, helper


def _extract_ids(payload: Any) -> list[str]:
    ids: list[str] = []
    if isinstance(payload, dict) and isinstance(payload.get("data"), list):
        for item in payload["data"]:
            if isinstance(item, dict) and isinstance(item.get("id"), str):
                ids.append(item["id"])
    return ids


def _pick_other_chat_model(ids: list[str], model1: str, helper: str) -> str | None:
    for model_id in ids:
        if model_id in {model1, helper}:
            continue
        lowered = model_id.lower()
        if any(marker in lowered for marker in NON_CHAT_MARKERS):
            continue
        return model_id
    for model_id in ids:
        if model_id not in {model1, helper}:
            return model_id
    return None


def _fetch_model_ids(api_key: str, opener: Callable[..., Any]) -> tuple[int | None, list[str]]:
    request = urllib.request.Request(
        GROQ_MODELS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "roman-urdu-spelling-robustness/1.0",
        },
        method="GET",
    )
    try:
        with opener(request, timeout=30) as response:
            status = getattr(response, "status", response.getcode())
            body = response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, []
    except Exception:
        return None, []
    try:
        payload = json.loads(body.decode("utf-8", errors="replace"))
    except Exception:
        return status, []
    return status, _extract_ids(payload)


def _truncate_text(value: Any, limit: int) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text[:limit]


def _extract_error_fields(body: bytes) -> dict[str, str | None] | str:
    text = body.decode("utf-8", errors="replace")
    try:
        payload = json.loads(text)
    except Exception:
        return text[:200]
    err = payload.get("error") if isinstance(payload, dict) else None
    if not isinstance(err, dict):
        # some APIs put fields at top level
        err = payload if isinstance(payload, dict) else {}
    return {
        "message": _truncate_text(err.get("message"), 300),
        "type": _truncate_text(err.get("type"), 300),
        "code": _truncate_text(err.get("code"), 300),
    }


def _build_payload(model_string: str, model_cfg: dict[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": model_string,
        "messages": [{"role": "user", "content": "Reply with the single letter A."}],
        "temperature": 0,
        "max_completion_tokens": 8,
    }
    effort = model_cfg.get("reasoning_effort")
    if isinstance(effort, str) and effort.strip():
        payload["reasoning_effort"] = effort.strip()
    return payload


def _get_header(hdrs: Any, name: str) -> str | None:
    if hdrs is None:
        return None
    getter = getattr(hdrs, "get", None)
    if getter is None:
        return None
    value = getter(name)
    if value is None:
        value = getter(name.lower())
    if value is None:
        value = getter(name.title())
    return value if isinstance(value, str) else (str(value) if value is not None else None)


def diagnose_variant(
    variant: str,
    model_string: str,
    model_cfg: dict[str, Any],
    api_key: str,
    extra_headers: dict[str, str] | None = None,
    opener: Callable[..., Any] | None = None,
) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {api_key}", **RUNNER_HEADERS}
    if extra_headers:
        headers.update(extra_headers)
    request = urllib.request.Request(
        GROQ_CHAT_URL,
        data=json.dumps(_build_payload(model_string, model_cfg)).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    open_fn = opener or urllib.request.urlopen
    result: dict[str, Any] = {"variant": variant, "http_status": None, "server": None, "cf_ray": None}
    try:
        with open_fn(request, timeout=30) as response:
            result["http_status"] = getattr(response, "status", None)
            if result["http_status"] is None and hasattr(response, "getcode"):
                result["http_status"] = response.getcode()
            hdrs = getattr(response, "headers", {}) or {}
            result["server"] = _get_header(hdrs, "server")
            result["cf_ray"] = _get_header(hdrs, "cf-ray")
            # success: do not print body
            result["error"] = None
            return result
    except urllib.error.HTTPError as exc:
        result["http_status"] = exc.code
        hdrs = getattr(exc, "headers", None)
        result["server"] = _get_header(hdrs, "server")
        result["cf_ray"] = _get_header(hdrs, "cf-ray")
        try:
            body = exc.read() or b""
        except Exception:
            body = b""
        result["error"] = _extract_error_fields(body)
        return result
    except Exception as exc:
        result["error"] = {"message": exc.__class__.__name__, "type": None, "code": None}
        return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="configs/models.yaml")
    parser.add_argument("--dotenv", default=str(REPO_ROOT / ".env"))
    args = parser.parse_args(argv)

    models_path = (REPO_ROOT / args.models).resolve() if not Path(args.models).is_absolute() else Path(args.models)
    dotenv_path = Path(args.dotenv)
    model1_string, helper_string, key_env, model1_cfg, helper_cfg = _get_config(models_path)
    load_dotenv(dotenv_path)
    api_key = os.environ.get(key_env)
    if not api_key:
        print(json.dumps({"error": f"missing environment variable: {key_env}"}, ensure_ascii=False))
        return 1

    models_status, ids = _fetch_model_ids(api_key, urllib.request.urlopen)
    other = _pick_other_chat_model(ids, model1_string, helper_string)
    results = []
    results.append(diagnose_variant("(a) model-1 runner headers", model1_string, model1_cfg, api_key))
    results.append(diagnose_variant("(b) model-1 + browser User-Agent", model1_string, model1_cfg, api_key, {"User-Agent": BROWSER_USER_AGENT}))
    results.append(diagnose_variant("(c) helper runner headers", helper_string, helper_cfg, api_key))
    if other:
        results.append(diagnose_variant(f"(d) other model ({other}) runner headers", other, {}, api_key))
    else:
        results.append({"variant": "(d) other model (none found)", "http_status": None, "server": None, "cf_ray": None, "error": None})
    print(json.dumps({"models_list_http_status": models_status, "results": results}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
