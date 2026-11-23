from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.eval.config import ModelConfig, RunSettings
from src.eval.providers import CompletionResult, MockProvider, ProviderError, RateLimitInfo
from src.eval.run import RunInputError, main, read_items, run_pipeline
from src.eval.runlog import RESULT_FIELDS


REPO_ROOT = Path(__file__).resolve().parents[2]
MOCK_ITEMS = REPO_ROOT / "tests" / "fixtures" / "mock_items_nu.jsonl"
MOCK_PROMPT = REPO_ROOT / "tests" / "fixtures" / "mock_prompt.txt"


def _settings(**overrides) -> RunSettings:
    settings = RunSettings(
        seed=11,
        max_output_tokens=16,
        temperature=0.0,
        request_timeout_s=2.0,
        max_retries=0,
        max_consecutive_failures=5,
        backoff_initial_s=0.0,
        paths={
            "results_raw": REPO_ROOT / "results" / "raw",
            "run_log": REPO_ROOT / "results" / "RUN_LOG.md",
            "prompt_template": MOCK_PROMPT,
        },
    )
    return replace(settings, **overrides)


def _model(provider: str = "mock") -> ModelConfig:
    return ModelConfig(
        slug="fixture",
        provider=provider,
        model_string="fixture-model",
        api_key_env="FIXTURE_KEY",
        requests_per_minute=60,
        requests_per_day=1000,
        checked_on="2026-11-16",
    )


def _run(tmp_path: Path, **overrides):
    kwargs = {
        "items_path": MOCK_ITEMS,
        "model_config": _model(),
        "settings": _settings(),
        "provider": MockProvider(),
        "output_dir": tmp_path / "temporary-results",
        "conditions": ("NU",),
        "mock": True,
        "run_log_path": tmp_path / "RUN_LOG.md",
        "run_date": "2026-11-16",
        "sleep": lambda _seconds: None,
    }
    kwargs.update(overrides)
    return run_pipeline(**kwargs)


def test_mock_end_to_end_on_ten_items_reports_metrics_and_schema(
    tmp_path: Path,
) -> None:
    summary = _run(tmp_path)
    output = (
        tmp_path
        / "temporary-results"
        / "fixture"
        / "2026-11-16_nu_r1.jsonl"
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert summary.processed_requests == 10
    assert summary.calls_made == 10
    assert summary.invalid_rate == 0
    assert summary.latency_mean_s == 0
    assert summary.latency_min_s == 0
    assert summary.latency_max_s == 0
    assert summary.schema_problems == ()
    assert len(rows) == 10
    assert all(set(row) == set(RESULT_FIELDS) for row in rows)
    assert not (tmp_path / "RUN_LOG.md").exists()
    assert not (REPO_ROOT / "results" / "raw" / "fixture").exists()


def test_invalid_answer_is_recorded_not_dropped(tmp_path: Path) -> None:
    summary = _run(
        tmp_path,
        provider=MockProvider(["no answer"]),
        max_items=1,
    )
    row_path = (
        tmp_path
        / "temporary-results"
        / "fixture"
        / "2026-11-16_nu_r1.jsonl"
    )
    row = json.loads(row_path.read_text(encoding="utf-8").strip())

    assert summary.invalid_count == 1
    assert summary.invalid_rate == 1
    assert row["parsed_answer"] is None
    assert row["valid"] is False
    assert row["error"] is None


def test_resume_skips_already_recorded_request(tmp_path: Path) -> None:
    class CountingProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            return CompletionResult(text="A", latency_s=0.01, model_string=None)

    provider = CountingProvider()
    first = _run(tmp_path, provider=provider, max_items=1)
    second = _run(tmp_path, provider=provider, max_items=1)

    assert first.calls_made == 1
    assert second.calls_made == 0
    assert second.cache_hits == 1
    assert provider.calls == 1


def test_resume_retries_failed_rows_and_latest_attempt_becomes_authoritative(
    tmp_path: Path,
) -> None:
    class FailOnceProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            if self.calls == 1:
                raise ProviderError("temporary failure", retryable=False)
            return CompletionResult(text="A", latency_s=0.01, model_string=None)

    provider = FailOnceProvider()
    first = _run(tmp_path, provider=provider, max_items=1)
    second = _run(tmp_path, provider=provider, max_items=1)
    third = _run(tmp_path, provider=provider, max_items=1)
    output = (
        tmp_path
        / "temporary-results"
        / "fixture"
        / "2026-11-16_nu_r1.jsonl"
    )
    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]

    assert first.errors == 1
    assert second.calls_made == 1
    assert second.cache_hits == 0
    assert third.calls_made == 0
    assert third.cache_hits == 1
    assert provider.calls == 2
    assert len(rows) == 2
    assert rows[0]["error"] == "temporary failure"
    assert rows[1]["error"] is None


def test_non_nu_real_run_requires_frozen_marker(tmp_path: Path) -> None:
    with pytest.raises(RunInputError, match="FROZEN.md"):
        run_pipeline(
            items_path=MOCK_ITEMS,
            model_config=_model("groq"),
            settings=_settings(),
            provider=MockProvider(),
            output_dir=tmp_path / "real-results",
            conditions=("RU-P",),
            mock=False,
            frozen_marker=tmp_path / "data" / "processed" / "FROZEN.md",
            run_log_path=tmp_path / "RUN_LOG.md",
        )


def test_non_nu_frozen_hash_normalizes_crlf_and_utf8(tmp_path: Path) -> None:
    item = read_items(MOCK_ITEMS)[0]
    item["condition"] = "RU-P"
    serialized = json.dumps(item, ensure_ascii=False) + "\n"
    items_path = tmp_path / "items_v1.jsonl"
    items_path.write_bytes(serialized.replace("\n", "\r\n").encode("utf-8"))
    expected_hash = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    marker = tmp_path / "FROZEN.md"
    marker.write_text(
        f"Freeze approved.\nITEMS_V1.JSONL SHA256: {expected_hash.upper()}\n",
        encoding="utf-8",
    )

    summary = run_pipeline(
        items_path=items_path,
        model_config=_model("groq"),
        settings=_settings(),
        provider=MockProvider(),
        output_dir=tmp_path / "real-results",
        conditions=("RU-P",),
        mock=False,
        frozen_marker=marker,
        run_log_path=tmp_path / "RUN_LOG.md",
        run_date="2026-11-16",
        max_items=1,
        sleep=lambda _seconds: None,
    )

    assert summary.calls_made == 1


def test_non_nu_frozen_hash_mismatch_reports_expected_and_actual(
    tmp_path: Path,
) -> None:
    item = read_items(MOCK_ITEMS)[0]
    item["condition"] = "RU-P"
    items_path = tmp_path / "items_v1.jsonl"
    items_path.write_text(json.dumps(item) + "\n", encoding="utf-8")
    marker = tmp_path / "FROZEN.md"
    expected_hash = "0" * 64
    marker.write_text(f"items_v1.jsonl sha256: {expected_hash}\n", encoding="utf-8")
    normalized = items_path.read_bytes().replace(b"\r\n", b"\n")
    actual_hash = hashlib.sha256(normalized).hexdigest()

    with pytest.raises(
        RunInputError,
        match=f"expected hash: {expected_hash}, actual hash: {actual_hash}",
    ):
        run_pipeline(
            items_path=items_path,
            model_config=_model("groq"),
            settings=_settings(),
            provider=MockProvider(),
            output_dir=tmp_path / "real-results",
            conditions=("RU-P",),
            mock=False,
            frozen_marker=marker,
            run_log_path=tmp_path / "RUN_LOG.md",
        )


def test_mock_run_is_exempt_from_frozen_guard(tmp_path: Path) -> None:
    item = read_items(MOCK_ITEMS, mock=True)[0]
    item["condition"] = "RU-P"
    items_path = tmp_path / "mock_ru_p.jsonl"
    items_path.write_text(json.dumps(item) + "\n", encoding="utf-8")

    summary = _run(
        tmp_path,
        items_path=items_path,
        conditions=("RU-P",),
        max_items=1,
    )

    assert summary.processed_requests == 1


def test_mock_output_cannot_be_written_under_results_raw(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="temporary directory"):
        _run(
            tmp_path,
            output_dir=REPO_ROOT / "results" / "raw",
            max_items=1,
        )


def test_mock_output_must_be_under_system_temp(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="system temporary directory"):
        _run(
            tmp_path,
            output_dir=Path("D:/Orthographic Robustness of LLMs on Roman Urdu/mock-output"),
            max_items=1,
        )


def test_retryable_failure_uses_exponential_retry(tmp_path: Path) -> None:
    class FlakyProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            if self.calls == 1:
                raise ProviderError("temporary", retryable=True, status_code=503)
            return CompletionResult(text="A", latency_s=0.02, model_string=None)

    provider = FlakyProvider()
    settings = _settings(max_retries=1)
    summary = _run(
        tmp_path,
        provider=provider,
        settings=settings,
        mock=False,
        model_config=_model("groq"),
        output_dir=tmp_path / "real-results",
        run_log_path=tmp_path / "real-RUN_LOG.md",
        max_items=1,
    )

    assert provider.calls == 2
    assert summary.calls_made == 2
    assert summary.errors == 0
    assert summary.processed_requests == 1
    assert (tmp_path / "real-RUN_LOG.md").is_file()


def test_runner_stops_after_consecutive_final_failures(tmp_path: Path) -> None:
    class FailedProvider:
        def complete(self, prompt, model_cfg, settings):
            raise ProviderError("unavailable", retryable=False)

    summary = _run(
        tmp_path,
        provider=FailedProvider(),
        settings=_settings(max_consecutive_failures=2),
        mock=False,
        model_config=_model("groq"),
        output_dir=tmp_path / "real-results",
        run_log_path=tmp_path / "real-RUN_LOG.md",
    )

    assert summary.calls_made == 2
    assert summary.errors == 2
    assert summary.error_count == 2
    assert summary.answered_requests == 0
    assert summary.processed_requests == 2
    assert summary.invalid_answer_rate == 0.0
    assert summary.invalid_rate == 0.0
    assert summary.stopped_after_consecutive_failures is True


def test_daily_quota_stops_before_an_unattempted_request_and_resumes(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class CountingProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            return CompletionResult(text="A", latency_s=0.01, model_string=None)

    provider = CountingProvider()
    model = replace(_model("groq"), requests_per_day=1)
    output_dir = tmp_path / "real-results"
    run_log_path = tmp_path / "real-RUN_LOG.md"
    run_date = datetime.now(timezone.utc).date().isoformat()
    first = _run(
        tmp_path,
        provider=provider,
        model_config=model,
        mock=False,
        output_dir=output_dir,
        run_log_path=run_log_path,
        run_date=run_date,
        max_items=2,
    )
    second = _run(
        tmp_path,
        provider=provider,
        model_config=model,
        mock=False,
        output_dir=output_dir,
        run_log_path=run_log_path,
        run_date=run_date,
        max_items=2,
    )
    next_day = (
        datetime.now(timezone.utc).date() + timedelta(days=1)
    ).isoformat()
    monkeypatch.setattr(
        "src.eval.run._utc_now",
        lambda: f"{next_day}T00:00:00Z",
    )
    third = _run(
        tmp_path,
        provider=provider,
        model_config=model,
        mock=False,
        output_dir=output_dir,
        run_log_path=run_log_path,
        run_date=next_day,
        max_items=2,
    )

    assert first.calls_made == 1
    assert first.stopped_after_daily_quota is True
    assert second.calls_made == 0
    assert second.cache_hits == 1
    assert second.stopped_after_daily_quota is True
    assert third.calls_made == 1
    assert third.cache_hits == 1
    assert third.stopped_after_daily_quota is False
    assert provider.calls == 2


def test_http_429_stops_the_run_without_retrying_or_looping(tmp_path: Path) -> None:
    class RateLimitedProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            raise ProviderError("rate limited", retryable=True, status_code=429)

    provider = RateLimitedProvider()
    summary = _run(
        tmp_path,
        provider=provider,
        settings=_settings(max_retries=3),
        mock=False,
        model_config=_model("groq"),
        output_dir=tmp_path / "real-results",
        run_log_path=tmp_path / "real-RUN_LOG.md",
    )

    assert provider.calls == 1
    assert summary.calls_made == 1
    assert summary.errors == 1
    assert summary.error_count == 1
    assert summary.answered_requests == 0
    assert summary.invalid_answer_rate == 0.0
    assert summary.stopped_after_rate_limit is True


def test_cli_mock_run_uses_fixture_and_requires_temporary_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    exit_code = main(
        [
            "--model-slug",
            "mock",
            "--items",
            str(MOCK_ITEMS),
            "--mock",
            "--max-items",
            "1",
            "--output-dir",
            str(tmp_path / "cli-output"),
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["processed_requests"] == 1
    assert output["invalid_rate"] == 0
    assert not (REPO_ROOT / "results" / "raw" / "mock").exists()


def test_short_429_wait_then_success_retries_same_request(tmp_path: Path, monkeypatch) -> None:
    sleeps: list[float] = []

    class ShortRateLimitedProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            if self.calls == 1:
                raise ProviderError(
                    "rate limited",
                    retryable=True,
                    status_code=429,
                    headers={"retry-after": "2"},
                    rate_limit=RateLimitInfo(retry_after_s=2.0),
                )
            return CompletionResult(
                text="A",
                latency_s=0.01,
                model_string=model_cfg.model_string,
                headers={"x-ratelimit-remaining-requests": "999", "x-ratelimit-reset-requests": "1m0s"},
                rate_limit=RateLimitInfo(remaining_requests="999", reset_requests="1m0s"),
            )

    provider = ShortRateLimitedProvider()
    summary = run_pipeline(
        items_path=MOCK_ITEMS,
        model_config=_model("groq"),
        settings=_settings(),
        provider=provider,
        output_dir=tmp_path / "real-results",
        conditions=("NU",),
        mock=False,
        run_log_path=tmp_path / "RUN_LOG.md",
        run_date="2026-11-16",
        max_items=1,
        sleep=lambda seconds: sleeps.append(seconds),
    )

    assert provider.calls == 2
    assert sleeps == [3.0]
    assert summary.calls_made == 2
    assert summary.error_count == 0
    assert summary.answered_requests == 1
    assert summary.invalid_answer_rate == 0.0
    assert summary.stopped_after_rate_limit is False
    assert summary.resume_time_utc is None


def test_long_429_stops_with_resume_time(tmp_path: Path, monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("src.eval.run._resume_time_utc", lambda s: "2099-01-01T00:02:01Z")

    class LongRateLimitedProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            raise ProviderError(
                "rate limited",
                retryable=True,
                status_code=429,
                headers={"retry-after": "121"},
                rate_limit=RateLimitInfo(retry_after_s=121.0),
            )

    provider = LongRateLimitedProvider()
    summary = run_pipeline(
        items_path=MOCK_ITEMS,
        model_config=_model("groq"),
        settings=_settings(),
        provider=provider,
        output_dir=tmp_path / "real-results",
        conditions=("NU",),
        mock=False,
        run_log_path=tmp_path / "RUN_LOG.md",
        run_date="2026-11-16",
        max_items=1,
        sleep=lambda seconds: sleeps.append(seconds),
    )

    assert provider.calls == 1
    assert sleeps == []
    assert summary.error_count == 1
    assert summary.answered_requests == 0
    assert summary.invalid_answer_rate == 0.0
    assert summary.stopped_after_rate_limit is True
    assert summary.stopped_after_daily_quota is False
    assert summary.resume_time_utc == "2099-01-01T00:02:01Z"


def test_daily_limit_exhausted_stops_with_resume_time(tmp_path: Path, monkeypatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("src.eval.run._resume_time_utc", lambda s: "2099-01-02T00:00:00Z")

    class DailyLimitedProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            raise ProviderError(
                "daily limit",
                retryable=True,
                status_code=429,
                headers={
                    "x-ratelimit-remaining-requests": "0",
                    "x-ratelimit-reset-requests": "24h0m0s",
                },
                rate_limit=RateLimitInfo(
                    remaining_requests="0",
                    reset_requests="24h0m0s",
                ),
            )

    provider = DailyLimitedProvider()
    summary = run_pipeline(
        items_path=MOCK_ITEMS,
        model_config=_model("groq"),
        settings=_settings(),
        provider=provider,
        output_dir=tmp_path / "real-results",
        conditions=("NU",),
        mock=False,
        run_log_path=tmp_path / "RUN_LOG.md",
        run_date="2026-11-16",
        max_items=1,
        sleep=lambda seconds: sleeps.append(seconds),
    )

    assert provider.calls == 1
    assert sleeps == []
    assert summary.error_count == 1
    assert summary.answered_requests == 0
    assert summary.invalid_answer_rate == 0.0
    assert summary.stopped_after_rate_limit is True
    assert summary.stopped_after_daily_quota is True
    assert summary.resume_time_utc == "2099-01-02T00:00:00Z"


def test_error_rows_excluded_from_invalid_answer_rate(tmp_path: Path) -> None:
    class MixedProvider:
        calls = 0

        def complete(self, prompt, model_cfg, settings):
            self.calls += 1
            if self.calls == 1:
                return CompletionResult(text="no answer", latency_s=0.01, model_string=model_cfg.model_string)
            raise ProviderError("temporary failure", retryable=False)

    provider = MixedProvider()
    summary = run_pipeline(
        items_path=MOCK_ITEMS,
        model_config=_model("groq"),
        settings=_settings(max_consecutive_failures=5),
        provider=provider,
        output_dir=tmp_path / "real-results",
        conditions=("NU",),
        mock=False,
        run_log_path=tmp_path / "RUN_LOG.md",
        run_date="2026-11-16",
        max_items=2,
        sleep=lambda seconds: None,
    )

    assert summary.processed_requests == 2
    assert summary.answered_requests == 1
    assert summary.error_count == 1
    assert summary.invalid_answer_count == 1
    assert summary.invalid_answer_rate == 1.0
