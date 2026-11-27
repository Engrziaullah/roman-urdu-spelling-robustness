"""Probe Gemini API reachability and rate-limit headers without exposing secrets.

Reads the configured Gemini model entry and loads the repo-root .env with an
explicit path. Prints only HTTP status, model IDs, and numeric rate-limit
headers. Never prints API keys or response bodies.

Examples (no network calls made by this assistant):
  python scripts/probe_gemini.py --model-slug model-2 --dry-run
  python scripts/probe_gemini.py --model-slug model-2 --mock
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.eval.config import ConfigError, load_model_config  # noqa: E402


GEMINI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)


def _numeric_rate_limit_headers(headers: Any) -> dict[str, str]:
    numeric: dict[str, str] = {}
    for key, value in headers.items():
        lower = str(key).lower()
        text = str(value).strip()
        if "ratelimit" in lower or "retry-after" in lower:
            if text.lstrip("-").isdigit():
                numeric[str(key)] = text
    return dict(sorted(numeric.items()))


def _print_report(
    *,
    http_status: int | str,
    model_slug: str,
    model_string: str,
    provider_model_id: str | None,
    numeric_headers: dict[str, str],
    mode: str,
) -> None:
    payload = {
        "mode": mode,
        "http_status": http_status,
        "model_ids": {
            "slug": model_slug,
            "configured_model_string": model_string,
            "provider_model_id": provider_model_id,
        },
        "numeric_rate_limit_headers": numeric_headers,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


def _mock_probe(model_slug: str, model_string: str) -> int:
    _print_report(
        http_status=200,
        model_slug=model_slug,
        model_string=model_string,
        provider_model_id=model_string if model_string != "TODO" else "mock-gemini-model",
        numeric_headers={
            "x-ratelimit-limit-requests": "60",
            "x-ratelimit-remaining-requests": "59",
        },
        mode="mock",
    )
    return 0


def _dry_run(model_slug: str, models_path: Path) -> int:
    load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)
    try:
        model = load_model_config(models_path, model_slug, load_api_key=False)
    except ConfigError as exc:
        _print_report(
            http_status="dry-run",
            model_slug=model_slug,
            model_string="unavailable (config incomplete)",
            provider_model_id=None,
            numeric_headers={},
            mode="dry-run",
        )
        print(
            json.dumps({"mode": "dry-run", "config_status": "incomplete", "config_error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 0
    if model.provider != "gemini":
        print(
            json.dumps(
                {
                    "mode": "dry-run",
                    "error": f"Model slug '{model_slug}' is provider '{model.provider}', expected 'gemini'.",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    _print_report(
        http_status="dry-run",
        model_slug=model.slug,
        model_string=model.model_string,
        provider_model_id=None,
        numeric_headers={},
        mode="dry-run",
    )
    return 0


def _real_probe(model_slug: str, models_path: Path) -> int:
    load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)
    try:
        model = load_model_config(models_path, model_slug, load_api_key=True)
    except ConfigError as exc:
        print(json.dumps({"mode": "real", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if model.provider != "gemini":
        print(
            json.dumps(
                {
                    "mode": "real",
                    "error": f"Model slug '{model_slug}' is provider '{model.provider}', expected 'gemini'.",
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2
    if not model.api_key:
        print(json.dumps({"mode": "real", "error": "API key is not available."}, ensure_ascii=False), file=sys.stderr)
        return 2
    url = GEMINI_ENDPOINT.format(model=quote(model.model_string, safe=""))
    payload = {
        "contents": [{"parts": [{"text": "Reply with only the letter: A.\n\nAnswer:"}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 1},
    }
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": model.api_key},
        method="POST",
    )
    provider_model_id: str | None = None
    try:
        with urlopen(request, timeout=30) as response:
            status = response.status
            headers = response.headers
            body = response.read().decode("utf-8", errors="replace")
        try:
            decoded = json.loads(body)
            if isinstance(decoded, dict) and isinstance(decoded.get("modelVersion"), str):
                provider_model_id = decoded["modelVersion"]
        except json.JSONDecodeError:
            provider_model_id = None
        numeric_headers = _numeric_rate_limit_headers(headers)
    except HTTPError as exc:
        status = exc.code
        numeric_headers = _numeric_rate_limit_headers(exc.headers)
        provider_model_id = None
    except (URLError, TimeoutError, OSError) as exc:
        print(json.dumps({"mode": "real", "error": f"Network error: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 1
    _print_report(
        http_status=status,
        model_slug=model.slug,
        model_string=model.model_string,
        provider_model_id=provider_model_id,
        numeric_headers=numeric_headers,
        mode="real",
    )
    return 0 if 200 <= int(status) < 300 else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-slug", default="model-2")
    parser.add_argument("--models", default=str(REPO_ROOT / "configs" / "models.yaml"))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Load config and print planned probe; no network call.")
    mode.add_argument("--mock", action="store_true", help="Print a simulated successful probe; no network call.")
    args = parser.parse_args(argv)
    models_path = Path(args.models)
    if not models_path.is_absolute():
        models_path = (REPO_ROOT / models_path).resolve()
    if args.mock:
        model_string = "TODO"
        try:
            load_dotenv(dotenv_path=REPO_ROOT / ".env", override=False)
            model = load_model_config(models_path, args.model_slug, load_api_key=False)
            model_string = model.model_string
        except ConfigError:
            pass
        return _mock_probe(args.model_slug, model_string)
    if args.dry_run:
        return _dry_run(args.model_slug, models_path)
    return _real_probe(args.model_slug, models_path)


if __name__ == "__main__":
    raise SystemExit(main())
