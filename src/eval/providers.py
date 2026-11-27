"""Provider adapters for official Gemini, Groq, and OpenRouter APIs plus mock."""

from __future__ import annotations

import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.eval.config import ModelConfig, RunSettings


@dataclass(frozen=True)
class RateLimitInfo:
    retry_after_s: float | None = None
    limit_requests: str | None = None
    remaining_requests: str | None = None
    reset_requests: str | None = None
    limit_tokens: str | None = None
    remaining_tokens: str | None = None
    reset_tokens: str | None = None


class ProviderError(RuntimeError):
    """A provider failure with an explicit retryability classification."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
        rate_limit: RateLimitInfo | None = None,
    ):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code
        self.headers = headers or {}
        self.rate_limit = rate_limit


@dataclass(frozen=True)
class CompletionResult:
    text: str
    latency_s: float
    model_string: str | None
    headers: dict[str, str] = field(default_factory=dict)
    usage: dict[str, Any] | None = None
    rate_limit: RateLimitInfo | None = None


class Provider(Protocol):
    """One model completion adapter."""

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> CompletionResult:
        """Return response text, elapsed seconds, provider model string, and metadata."""


DEFAULT_USER_AGENT = "roman-urdu-spelling-robustness/1.0"
_RATE_LIMIT_HEADER_NAMES = (
    "retry-after",
    "x-ratelimit-limit-requests",
    "x-ratelimit-remaining-requests",
    "x-ratelimit-reset-requests",
    "x-ratelimit-limit-tokens",
    "x-ratelimit-remaining-tokens",
    "x-ratelimit-reset-tokens",
)


def _headers_to_dict(headers: Any) -> dict[str, str]:
    result: dict[str, str] = {}
    try:
        items = headers.items()
    except Exception:
        return result
    for key, value in items:
        if isinstance(key, str) and isinstance(value, str):
            result[key.lower()] = value
    return result


def _parse_retry_after_seconds(value: str | None) -> float | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    try:
        seconds = float(text)
    except ValueError:
        return None
    return seconds if seconds >= 0 else None


def parse_rate_limit_info(headers: Mapping[str, str] | None) -> RateLimitInfo | None:
    if not headers:
        return None
    lowered = {str(k).lower(): str(v) for k, v in headers.items()}
    if not any(name in lowered for name in _RATE_LIMIT_HEADER_NAMES):
        return None
    return RateLimitInfo(
        retry_after_s=_parse_retry_after_seconds(lowered.get("retry-after")),
        limit_requests=lowered.get("x-ratelimit-limit-requests"),
        remaining_requests=lowered.get("x-ratelimit-remaining-requests"),
        reset_requests=lowered.get("x-ratelimit-reset-requests"),
        limit_tokens=lowered.get("x-ratelimit-limit-tokens"),
        remaining_tokens=lowered.get("x-ratelimit-remaining-tokens"),
        reset_tokens=lowered.get("x-ratelimit-reset-tokens"),
    )


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_s: float,
) -> tuple[dict[str, Any], dict[str, str]]:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT, **headers}
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:
            resp_headers = _headers_to_dict(getattr(response, "headers", {}) or {})
            decoded = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = exc.code
        resp_headers = _headers_to_dict(getattr(exc, "headers", {}) or {})
        try:
            exc.read()
        except Exception:
            pass
        raise ProviderError(
            f"Provider returned HTTP {status}.",
            retryable=status in {429, 503} or 500 <= status <= 599,
            status_code=status,
            headers=resp_headers,
            rate_limit=parse_rate_limit_info(resp_headers),
        ) from exc
    except URLError as exc:
        raise ProviderError(
            "Network error while contacting provider.", retryable=True
        ) from exc
    except TimeoutError as exc:
        raise ProviderError("Provider request timed out.", retryable=True) from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ProviderError(
            "Provider returned an invalid JSON response.", retryable=False
        ) from exc
    if not isinstance(decoded, dict):
        raise ProviderError("Provider response must be a JSON object.", retryable=False)
    return decoded, resp_headers


def _required_api_key(model_cfg: ModelConfig) -> str:
    if not model_cfg.api_key:
        raise ProviderError(
            f"API key is unavailable for environment variable '{model_cfg.api_key_env}'.",
            retryable=False,
        )
    return model_cfg.api_key


class GeminiProvider:
    """Gemini generateContent adapter using Google's documented REST format."""

    endpoint = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> CompletionResult:
        key = _required_api_key(model_cfg)
        url = self.endpoint.format(model=quote(model_cfg.model_string, safe=""))
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": settings.temperature,
                "maxOutputTokens": settings.max_output_tokens,
            },
        }
        started = time.perf_counter()
        response, headers = _post_json(
            url,
            {"Content-Type": "application/json", "x-goog-api-key": key},
            payload,
            settings.request_timeout_s,
        )
        try:
            parts = response["candidates"][0]["content"]["parts"]
            if not isinstance(parts, list):
                raise TypeError("Gemini parts must be a list.")
            text = "".join(
                part["text"]
                for part in parts
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                "Gemini response did not contain candidate text.",
                retryable=False,
                headers=headers,
                rate_limit=parse_rate_limit_info(headers),
            ) from exc
        if not text:
            raise ProviderError(
                "Gemini returned empty candidate text.",
                retryable=False,
                headers=headers,
                rate_limit=parse_rate_limit_info(headers),
            )
        elapsed = time.perf_counter() - started
        returned_model = response.get("modelVersion")
        usage = response.get("usageMetadata") if isinstance(response.get("usageMetadata"), dict) else None
        return CompletionResult(
            text=text,
            latency_s=elapsed,
            model_string=returned_model if isinstance(returned_model, str) else None,
            headers=headers,
            usage=usage,
            rate_limit=parse_rate_limit_info(headers),
        )


class OpenAICompatibleProvider:
    """Chat Completions adapter for an explicitly selected compatible provider."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> CompletionResult:
        key = _required_api_key(model_cfg)
        payload: dict[str, Any] = {
            "model": model_cfg.model_string,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": settings.temperature,
        }
        max_output_tokens = (
            model_cfg.max_output_tokens
            if model_cfg.max_output_tokens is not None
            else settings.max_output_tokens
        )
        if model_cfg.provider == "groq":
            payload["max_completion_tokens"] = max_output_tokens
            if model_cfg.reasoning_effort is not None:
                payload["reasoning_effort"] = model_cfg.reasoning_effort
        else:
            payload["max_tokens"] = max_output_tokens
        started = time.perf_counter()
        response, headers = _post_json(
            self.endpoint,
            {"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            payload,
            settings.request_timeout_s,
        )
        try:
            text = response["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(
                f"{model_cfg.provider} response did not contain chat text.",
                retryable=False,
                headers=headers,
                rate_limit=parse_rate_limit_info(headers),
            ) from exc
        if not isinstance(text, str):
            raise ProviderError(
                f"{model_cfg.provider} response content was not text.",
                retryable=False,
                headers=headers,
                rate_limit=parse_rate_limit_info(headers),
            )
        elapsed = time.perf_counter() - started
        returned_model = response.get("model")
        usage = response.get("usage") if isinstance(response.get("usage"), dict) else None
        return CompletionResult(
            text=text,
            latency_s=elapsed,
            model_string=returned_model if isinstance(returned_model, str) else None,
            headers=headers,
            usage=usage,
            rate_limit=parse_rate_limit_info(headers),
        )


class MockProvider:
    """Deterministic mock provider; responses repeat the final configured value."""

    def __init__(self, responses: Sequence[str] = ("A",)):
        if not responses:
            raise ValueError("MockProvider requires at least one response.")
        self._responses = tuple(responses)
        self._calls = 0

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> CompletionResult:
        del prompt, settings
        index = min(self._calls, len(self._responses) - 1)
        self._calls += 1
        return CompletionResult(
            text=self._responses[index],
            latency_s=0.0,
            model_string=model_cfg.model_string,
            headers={},
            usage=None,
            rate_limit=None,
        )


def create_provider(provider_name: str) -> Provider:
    """Create an adapter for a configured, documented provider."""
    providers: dict[str, Provider] = {
        "gemini": GeminiProvider(),
        "groq": OpenAICompatibleProvider(
            "https://api.groq.com/openai/v1/chat/completions"
        ),
        "openrouter": OpenAICompatibleProvider(
            "https://openrouter.ai/api/v1/chat/completions"
        ),
        "mock": MockProvider(),
    }
    try:
        return providers[provider_name.lower()]
    except KeyError as exc:
        raise ValueError(
            f"Unsupported provider '{provider_name}'. Configure one of: "
            f"{', '.join(sorted(providers))}."
        ) from exc
