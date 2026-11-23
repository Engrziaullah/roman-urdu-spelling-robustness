from __future__ import annotations

from io import BytesIO
from urllib.error import HTTPError

import pytest

from src.eval.config import ModelConfig, RunSettings
from src.eval.providers import (
    GeminiProvider,
    MockProvider,
    OpenAICompatibleProvider,
    ProviderError,
)


def _settings() -> RunSettings:
    return RunSettings(
        seed=1,
        max_output_tokens=24,
        temperature=0.0,
        request_timeout_s=3.0,
        max_retries=1,
        max_consecutive_failures=3,
        backoff_initial_s=0.0,
        paths={},
    )


def _model(provider: str) -> ModelConfig:
    return ModelConfig(
        slug="fixture",
        provider=provider,
        model_string="fixture-model",
        api_key_env="FIXTURE_KEY",
        requests_per_minute=60,
        requests_per_day=1000,
        checked_on="2026-11-16",
        api_key="fixture-secret",
    )


def test_gemini_uses_documented_endpoint_and_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    def fake_post(url, headers, payload, timeout_s):
        captured.update(url=url, headers=headers, payload=payload, timeout_s=timeout_s)
        return {
            "candidates": [{"content": {"parts": [{"text": "A"}]}}],
            "modelVersion": "returned-model",
        }

    monkeypatch.setattr("src.eval.providers._post_json", fake_post)
    text, latency, returned_model = GeminiProvider().complete(
        "test prompt", _model("gemini"), _settings()
    )

    assert captured["url"] == (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        "fixture-model:generateContent"
    )
    assert captured["headers"]["x-goog-api-key"] == "fixture-secret"
    assert captured["payload"]["contents"][0]["parts"][0]["text"] == "test prompt"
    assert captured["payload"]["generationConfig"] == {
        "temperature": 0.0,
        "maxOutputTokens": 24,
    }
    assert (text, returned_model) == ("A", "returned-model")
    assert latency >= 0


@pytest.mark.parametrize(
    ("provider_name", "endpoint", "token_field"),
    [
        (
            "groq",
            "https://api.groq.com/openai/v1/chat/completions",
            "max_completion_tokens",
        ),
        (
            "openrouter",
            "https://openrouter.ai/api/v1/chat/completions",
            "max_tokens",
        ),
    ],
)
def test_openai_compatible_adapters_use_documented_request_shape(
    monkeypatch: pytest.MonkeyPatch,
    provider_name: str,
    endpoint: str,
    token_field: str,
) -> None:
    captured: dict = {}

    def fake_post(url, headers, payload, timeout_s):
        captured.update(url=url, headers=headers, payload=payload, timeout_s=timeout_s)
        return {
            "choices": [{"message": {"content": "B"}}],
            "model": "returned-model",
        }

    monkeypatch.setattr("src.eval.providers._post_json", fake_post)
    text, _, returned_model = OpenAICompatibleProvider(endpoint).complete(
        "test prompt", _model(provider_name), _settings()
    )

    assert captured["url"] == endpoint
    assert captured["headers"]["Authorization"] == "Bearer fixture-secret"
    assert captured["payload"]["model"] == "fixture-model"
    assert captured["payload"]["messages"] == [
        {"role": "user", "content": "test prompt"}
    ]
    assert captured["payload"][token_field] == 24
    assert (text, returned_model) == ("B", "returned-model")


def test_groq_uses_model_generation_overrides(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_post(url, headers, payload, timeout_s):
        captured.update(payload=payload)
        return {
            "choices": [{"message": {"content": "A"}}],
            "model": "qwen/qwen3.8-27b",
        }

    monkeypatch.setattr("src.eval.providers._post_json", fake_post)
    model = _model("groq")
    model = ModelConfig(
        slug=model.slug,
        provider=model.provider,
        model_string=model.model_string,
        api_key_env=model.api_key_env,
        requests_per_minute=model.requests_per_minute,
        requests_per_day=model.requests_per_day,
        checked_on=model.checked_on,
        max_output_tokens=4096,
        reasoning_effort="low",
        api_key=model.api_key,
    )

    OpenAICompatibleProvider("https://provider.invalid").complete(
        "test prompt", model, _settings()
    )

    assert captured["payload"]["max_completion_tokens"] == 4096
    assert captured["payload"]["reasoning_effort"] == "low"


def test_openai_compatible_provider_falls_back_to_global_token_limit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    def fake_post(url, headers, payload, timeout_s):
        captured.update(payload=payload)
        return {
            "choices": [{"message": {"content": "A"}}],
            "model": "returned-model",
        }

    monkeypatch.setattr("src.eval.providers._post_json", fake_post)
    OpenAICompatibleProvider("https://provider.invalid").complete(
        "test prompt", _model("openrouter"), _settings()
    )

    assert captured["payload"]["max_tokens"] == _settings().max_output_tokens


def test_mock_provider_is_deterministic() -> None:
    provider = MockProvider(["B", "C"])
    model = _model("mock")

    results = [provider.complete("ignored", model, _settings())[0] for _ in range(3)]

    assert results == ["B", "C", "C"]


def test_http_rate_limit_is_retryable_and_does_not_expose_response_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_request(*args, **kwargs):
        raise HTTPError(
            "https://provider.invalid",
            429,
            "too many requests",
            {},
            BytesIO(b"private provider response"),
        )

    monkeypatch.setattr("src.eval.providers.urlopen", fail_request)
    with pytest.raises(ProviderError) as caught:
        from src.eval.providers import _post_json

        _post_json("https://provider.invalid", {}, {}, 1.0)

    assert caught.value.retryable
    assert caught.value.status_code == 429
    assert "private provider response" not in str(caught.value)

def test_post_json_sets_fixed_user_agent_for_provider_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict = {}

    class _Resp:
        status = 200
        headers = {}

        def read(self):
            return b'{"ok": true}'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    def fake_urlopen(request, timeout=0):
        captured["user_agent"] = request.get_header("User-agent")
        captured["timeout"] = timeout
        return _Resp()

    monkeypatch.setattr("src.eval.providers.urlopen", fake_urlopen)
    from src.eval.providers import _post_json

    result = _post_json("https://provider.invalid", {"Content-Type": "application/json"}, {"x": 1}, 5.0)

    assert result == {"ok": True}
    assert captured["user_agent"] == "roman-urdu-spelling-robustness/1.0"
    assert captured["timeout"] == 5.0
