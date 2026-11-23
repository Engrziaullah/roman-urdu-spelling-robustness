"""Provider adapters for official Gemini, Groq, and OpenRouter APIs plus mock."""

from __future__ import annotations

import json
import time
from collections.abc import Sequence
from typing import Any, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.eval.config import ModelConfig, RunSettings


class ProviderError(RuntimeError):
    """A provider failure with an explicit retryability classification."""

    def __init__(self, message: str, *, retryable: bool, status_code: int | None = None):
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code


class Provider(Protocol):
    """One model completion adapter."""

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> tuple[str, float, str | None]:
        """Return response text, elapsed seconds, and provider-returned model string."""


DEFAULT_USER_AGENT = "roman-urdu-spelling-robustness/1.0"


def _post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_s: float,
) -> dict[str, Any]:
    request_headers = {"User-Agent": DEFAULT_USER_AGENT, **headers}
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=request_headers,
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        status = exc.code
        raise ProviderError(
            f"Provider returned HTTP {status}.",
            retryable=status == 429 or 500 <= status <= 599,
            status_code=status,
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
    return decoded


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
    ) -> tuple[str, float, str | None]:
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
        response = _post_json(
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
                "Gemini response did not contain candidate text.", retryable=False
            ) from exc
        if not text:
            raise ProviderError("Gemini returned empty candidate text.", retryable=False)
        elapsed = time.perf_counter() - started
        returned_model = response.get("modelVersion")
        return text, elapsed, returned_model if isinstance(returned_model, str) else None


class OpenAICompatibleProvider:
    """Chat Completions adapter for an explicitly selected compatible provider."""

    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    def complete(
        self,
        prompt: str,
        model_cfg: ModelConfig,
        settings: RunSettings,
    ) -> tuple[str, float, str | None]:
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
        response = _post_json(
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
            ) from exc
        if not isinstance(text, str):
            raise ProviderError(
                f"{model_cfg.provider} response content was not text.", retryable=False
            )
        elapsed = time.perf_counter() - started
        returned_model = response.get("model")
        return text, elapsed, returned_model if isinstance(returned_model, str) else None


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
    ) -> tuple[str, float, str | None]:
        del prompt, settings
        index = min(self._calls, len(self._responses) - 1)
        self._calls += 1
        return self._responses[index], 0.0, model_cfg.model_string


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
