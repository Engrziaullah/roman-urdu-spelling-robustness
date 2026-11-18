"""RU-P draft tests with labelled TOY data and a fake client; no network calls."""

import csv
import json
import tempfile
import unittest
from pathlib import Path

from src.data.draft_rup import (
    DraftClientError,
    DraftConfigurationError,
    build_prompt,
    draft_items,
    load_lexicon,
    validate_helper_config,
)


def toy_config(*, helper_model="TOY_HELPER", helper_provider="toy-provider"):
    """Return a fully local config containing only TOY model identifiers."""
    return {
        "helper": {
            "provider": helper_provider,
            "model_string": helper_model,
            "api_key_env": "TOY_KEY",
        },
        "evaluated_models": [
            {"provider": "toy-eval-provider", "model_string": "TOY_EVALUATED"}
        ],
    }


def toy_item(item_id="toy-30", *, question="TOY 123", options=None):
    """Return a contract-shaped source row with clearly labelled toy strings."""
    return {
        "item_id": item_id,
        "source_row": "TOY_SOURCE",
        "domain": "TOY_DOMAIN",
        "subject": "TOY_SUBJECT",
        "condition": "NU",
        "question": question,
        "options": list(options if options is not None else ["TOY_ONE", "TOY_TWO"]),
        "gold": "A",
        "verified": True,
        "sample_rank": 1,
        "notes": "",
    }


class FakeClient:
    """Return canned TOY responses or raise configured retryable failures."""

    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete(self, prompt, model_string):
        self.calls.append((prompt, model_string))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class DraftRupTests(unittest.TestCase):
    def test_repository_lexicon_is_header_only(self):
        lexicon_path = (
            Path(__file__).resolve().parents[2]
            / "src" / "data" / "rules" / "ru_p_lexicon.csv"
        )
        self.assertEqual(load_lexicon(lexicon_path), {})

    def test_refuses_unresolved_or_evaluated_helper(self):
        client = FakeClient(['{"question":"toy","options":["a","b"]}'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(DraftConfigurationError, "TODO/TBD"):
                draft_items(
                    [toy_item()], client, toy_config(helper_model="TODO"), {},
                    cache_path=Path(temp) / "cache.jsonl",
                    failures_path=Path(temp) / "failures.jsonl",
                )
            self.assertEqual(client.calls, [])
            with self.assertRaisesRegex(DraftConfigurationError, "must not match"):
                draft_items(
                    [toy_item()], client,
                    toy_config(helper_model="TOY_EVALUATED"), {},
                    cache_path=Path(temp) / "cache2.jsonl",
                    failures_path=Path(temp) / "failures2.jsonl",
                )
            self.assertEqual(client.calls, [])

    def test_lexicon_is_in_prompt_before_fake_client_call(self):
        with tempfile.TemporaryDirectory() as temp:
            lexicon_path = Path(temp) / "lexicon.csv"
            with lexicon_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.writer(handle)
                writer.writerow(["urdu_word", "ru_p", "note"])
                writer.writerow(["TOY_WORD", "toy_spelling", "TOY entry"])
            lexicon = load_lexicon(lexicon_path)
            prompt = build_prompt(toy_item(), lexicon)
            self.assertIn("TOY_WORD", prompt)
            self.assertIn("toy_spelling", prompt)
            client = FakeClient([
                json.dumps({"question": "TOY 123", "options": ["TOY_ONE", "TOY_TWO"]})
            ])
            result = draft_items(
                [toy_item()],
                client,
                toy_config(),
                lexicon,
                cache_path=Path(temp) / "cache.jsonl",
                failures_path=Path(temp) / "failures.jsonl",
                output_path=Path(temp) / "draft.jsonl",
                prompt_record_path=Path(temp) / "rup_prompt.md",
            )
            self.assertEqual(len(client.calls), 1)
            self.assertIn("TOY_WORD", client.calls[0][0])
            self.assertEqual(result.rows[0]["condition"], "RU-P")
            self.assertIs(result.rows[0]["verified"], False)
            saved_row = json.loads(
                (Path(temp) / "draft.jsonl").read_text(encoding="utf-8")
            )
            self.assertEqual(saved_row, result.rows[0])
            prompt_record = (Path(temp) / "rup_prompt.md").read_text(encoding="utf-8")
            record = json.loads(prompt_record.splitlines()[2])
            self.assertEqual(record["prompt"], client.calls[0][0])
            self.assertEqual(record["model_string"], "TOY_HELPER")

    def test_malformed_outputs_are_retained_and_raw_text_is_saved(self):
        cases = [
            ("{TOY malformed", "bad_json"),
            (json.dumps({"question": "TOY", "options": ["TOY_ONLY"]}),
             "wrong_option_count"),
            (json.dumps({"question": "", "options": ["TOY_ONE", "TOY_TWO"]}),
             "empty_field"),
        ]
        for index, (raw, reason) in enumerate(cases):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                client = FakeClient([raw])
                source = toy_item(f"toy-fail-{index}")
                result = draft_items(
                    [source],
                    client,
                    toy_config(),
                    {},
                    cache_path=root / "cache.jsonl",
                    failures_path=root / "failures.jsonl",
                )
                self.assertEqual(len(result.rows), 1)
                row = result.rows[0]
                self.assertEqual(row["question"], source["question"])
                self.assertEqual(row["options"], source["options"])
                self.assertEqual(row["notes"], f"DRAFT_FAILED:{reason}")
                self.assertIs(row["verified"], False)
                failure = json.loads((root / "failures.jsonl").read_text(encoding="utf-8"))
                self.assertEqual(failure["raw_output"], raw)
                self.assertEqual(failure["reason_code"], reason)

    def test_malformed_response_is_cached_and_rerun_does_not_repeat_call(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient(["TOY not-json"])
            kwargs = {
                "cache_path": root / "cache.jsonl",
                "failures_path": root / "failures.jsonl",
            }
            first = draft_items([toy_item()], client, toy_config(), {}, **kwargs)
            second = draft_items([toy_item()], client, toy_config(), {}, **kwargs)
            self.assertEqual(first.rows[0]["notes"], "DRAFT_FAILED:bad_json")
            self.assertEqual(second.rows[0]["notes"], "DRAFT_FAILED:bad_json")
            self.assertEqual(len(client.calls), 1)
            self.assertEqual(second.cache_hits, 1)

    def test_retries_with_backoff_and_accepts_five_options(self):
        response = json.dumps({
            "question": "TOY 123",
            "options": ["TOY_ONE", "TOY_TWO", "TOY_THREE", "TOY_FOUR", "TOY_FIVE"],
        })
        client = FakeClient([DraftClientError("TOY transient"), response])
        delays = []
        with tempfile.TemporaryDirectory() as temp:
            result = draft_items(
                [toy_item(options=["TOY_ONE", "TOY_TWO", "TOY_THREE", "TOY_FOUR", "TOY_FIVE"])],
                client,
                toy_config(),
                {},
                cache_path=Path(temp) / "cache.jsonl",
                failures_path=Path(temp) / "failures.jsonl",
                max_attempts=3,
                backoff_initial_s=0.25,
                sleep=delays.append,
            )
        self.assertEqual(len(client.calls), 2)
        self.assertEqual(delays, [0.25])
        self.assertEqual(len(result.rows[0]["options"]), 5)
        self.assertEqual(result.failures, 0)

    def test_proxy_flags_protected_token_mismatch(self):
        response = json.dumps({
            "question": "TOY_CHANGED 123",
            "options": ["TOY_ONE", "TOY_TWO"],
        })
        with tempfile.TemporaryDirectory() as temp:
            result = draft_items(
                [toy_item(question="TOY_SAFE 123")],
                FakeClient([response]),
                toy_config(),
                {},
                cache_path=Path(temp) / "cache.jsonl",
                failures_path=Path(temp) / "failures.jsonl",
                protected_tokens_by_item={"toy-30": ["TOY_SAFE"]},
            )
        self.assertEqual(result.rows[0]["condition"], "RU-P")
        self.assertIn("DRAFT_FLAG:protected_token_mismatch", result.rows[0]["notes"])
        self.assertEqual(result.failures, 0)

    def test_request_failures_are_retained_after_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            client = FakeClient([
                DraftClientError("TOY fail"),
                DraftClientError("TOY fail"),
            ])
            result = draft_items(
                [toy_item()],
                client,
                toy_config(),
                {},
                cache_path=root / "cache.jsonl",
                failures_path=root / "failures.jsonl",
                max_attempts=2,
                backoff_initial_s=0,
                sleep=lambda _: None,
            )
            self.assertEqual(result.rows[0]["notes"], "DRAFT_FAILED:request_failed")
            self.assertEqual(result.failures, 1)
            failure = json.loads((root / "failures.jsonl").read_text(encoding="utf-8"))
            self.assertIsNone(failure["raw_output"])


if __name__ == "__main__":
    unittest.main()
