from __future__ import annotations

import io
import json
import urllib.error

import scripts.diagnose_groq as dg


class _Resp:
    def __init__(self, status=200, headers=None, body=b"{}"):
        self.status = status
        self.headers = headers or {}
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_extract_error_fields_json_truncates_and_selects_only_fields():
    body = json.dumps({
        "error": {"message": "x" * 400, "type": "y" * 400, "code": "z" * 400, "secret": "nope"}
    }).encode("utf-8")
    out = dg._extract_error_fields(body)
    assert set(out.keys()) == {"message", "type", "code"}
    assert len(out["message"]) == 300
    assert len(out["type"]) == 300
    assert len(out["code"]) == 300


def test_extract_error_fields_non_json_returns_first_200_chars():
    body = ("A" * 250).encode("utf-8")
    out = dg._extract_error_fields(body)
    assert out == "A" * 200


def test_pick_other_chat_model_skips_current_and_non_chat():
    ids = ["qwen/qwen3.8-27b", "openai/gpt-oss-120b", "whisper-large-v3", "llama-3.1-8b-instant"]
    assert dg._pick_other_chat_model(ids, "qwen/qwen3.8-27b", "openai/gpt-oss-120b") == "llama-3.1-8b-instant"


def test_diagnose_variant_success_reports_only_safe_fields(monkeypatch):
    def opener(req, timeout=30):
        auth = req.get_header("Authorization") or req.headers.get("Authorization")
        assert auth == "Bearer test-key"
        return _Resp(status=200, headers={"server": "cloudflare", "cf-ray": "abc123", "set-cookie": "secret"}, body=b'{"ok":true}')

    res = dg.diagnose_variant("(a)", "m1", {"reasoning_effort": "low"}, "test-key", opener=opener)
    assert res["variant"] == "(a)"
    assert res["http_status"] == 200
    assert res["server"] == "cloudflare"
    assert res["cf_ray"] == "abc123"
    assert res["error"] is None
    assert "Authorization" not in json.dumps(res)
    assert "test-key" not in json.dumps(res)


def test_diagnose_variant_http_error_reports_selected_error_fields(monkeypatch):
    payload = {"error": {"message": "forbidden", "type": "auth_error", "code": "403_code", "extra": "hidden"}}

    def opener(req, timeout=30):
        raise urllib.error.HTTPError(req.full_url, 403, "Forbidden", {"server": "s", "cf-ray": "r"}, io.BytesIO(json.dumps(payload).encode("utf-8")))

    res = dg.diagnose_variant("(a)", "m1", {}, "test-key", opener=opener)
    assert res["http_status"] == 403
    assert res["server"] == "s"
    assert res["cf_ray"] == "r"
    assert res["error"] == {"message": "forbidden", "type": "auth_error", "code": "403_code"}
    assert "hidden" not in json.dumps(res)
    assert "test-key" not in json.dumps(res)
