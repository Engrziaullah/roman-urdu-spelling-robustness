from __future__ import annotations

import json
from pathlib import Path

import scripts.probe_limits as probe_limits


def test_probe_limits_reports_status_headers_and_usage_without_secret(monkeypatch, tmp_path, capsys):
    models = {
        "helper": {"slug": "helper", "provider": "groq", "model_string": "openai/gpt-oss-120b"},
        "evaluated_models": [
            {
                "slug": "model-1",
                "provider": "groq",
                "model_string": "qwen/qwen3.8-27b",
                "api_key_env": "GROQ_API_KEY",
            }
        ],
    }
    models_path = tmp_path / "models.yaml"
    models_path.write_text(
        "helper:\n"
        "  slug: helper\n  provider: groq\n  model_string: openai/gpt-oss-120b\n"
        "evaluated_models:\n"
        "  - slug: model-1\n    provider: groq\n    model_string: qwen/qwen3.8-27b\n    api_key_env: GROQ_API_KEY\n",
        encoding="utf-8",
    )
    dotenv = tmp_path / ".env"
    dotenv.write_text("GROQ_API_KEY=secret-test-key\n", encoding="utf-8")

    calls = []

    def fake_http_json(method, url, api_key, payload=None, timeout_s=30.0):
        calls.append((method, url, payload))
        assert api_key == "secret-test-key"
        if method == "GET":
            body = json.dumps({"data": [{"id": "qwen/qwen3.8-27b"}, {"id": "openai/gpt-oss-120b"}, {"id": "openai/gpt-oss-20b"}, {"id": "allam-2-7b"}]}).encode()
            return 200, {}, body
        model = payload["model"]
        if model == "allam-2-7b":
            headers = {
                "x-ratelimit-limit-requests": "7000",
                "x-ratelimit-remaining-requests": "6999",
                "x-ratelimit-reset-requests": "12.342s",
                "x-ratelimit-limit-tokens": "6000",
                "x-ratelimit-remaining-tokens": "5978",
                "x-ratelimit-reset-tokens": "220ms",
            }
            usage = {"prompt_tokens": 14, "completion_tokens": 3}
        else:
            headers = {
                "x-ratelimit-limit-requests": "1000",
                "x-ratelimit-remaining-requests": "999",
                "x-ratelimit-reset-requests": "1m26.4s",
                "x-ratelimit-limit-tokens": "8000",
                "x-ratelimit-remaining-tokens": "7945",
                "x-ratelimit-reset-tokens": "412ms",
            }
            usage = {"prompt_tokens": 47, "completion_tokens": 8}
        body = json.dumps({"usage": usage}).encode()
        return 200, headers, body

    monkeypatch.setattr(probe_limits, "http_json", fake_http_json)

    rc = probe_limits.main(["--models", str(models_path), "--dotenv", str(dotenv), "--max-others", "3"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "secret-test-key" not in out
    assert "Authorization" not in out
    data = json.loads(out)
    assert data["models_list_http_status"] == 200
    assert len(data["probes"]) == 4
    m1 = next(r for r in data["probes"] if r["model"] == "qwen/qwen3.8-27b")
    assert m1["http_status"] == 200
    assert m1["x-ratelimit-limit-tokens"] == "8000"
    assert m1["prompt_tokens"] == 47
    assert m1["completion_tokens"] == 8
    assert m1.get("retry-after") is None
