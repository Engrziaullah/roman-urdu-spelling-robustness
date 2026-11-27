import json
import sys
import types
from pathlib import Path

import pandas as pd
import pytest

from src.analysis.tokens import (
    token_comparison_table,
    token_counts,
    token_summary_table,
)

MOCK_ITEMS = Path("tests/fixtures/mock_items_nu.jsonl")


def install_fake_tokenizer(monkeypatch):
    class FakeTokenizer:
        @classmethod
        def from_pretrained(cls, name):
            return cls()

        def encode(self, text, add_special_tokens=False):
            return text.split()

    fake_transformers = types.SimpleNamespace(AutoTokenizer=FakeTokenizer)
    monkeypatch.setitem(sys.modules, "transformers", fake_transformers)


def test_token_counts_with_fake_tokenizer(monkeypatch):
    install_fake_tokenizer(monkeypatch)

    counts = token_counts(MOCK_ITEMS, tokenizer_name="fake-tokenizer")
    items = pd.read_json(MOCK_ITEMS, lines=True)

    assert list(counts.columns) == [
        "item_id",
        "condition",
        "domain",
        "n_tokens_question",
        "n_tokens_options",
        "n_tokens_total",
        "n_chars_total",
    ]
    assert len(counts) == len(items)
    assert counts["condition"].tolist() == items["condition"].tolist()
    assert counts["domain"].tolist() == items["domain"].tolist()
    assert counts.loc[0, "n_tokens_question"] == len(items.loc[0, "question"].split())
    assert counts.loc[0, "n_tokens_options"] == sum(
        len(option.split()) for option in items.loc[0, "options"]
    )
    assert counts.loc[0, "n_tokens_total"] == (
        counts.loc[0, "n_tokens_question"] + counts.loc[0, "n_tokens_options"]
    )
    assert counts.loc[0, "n_chars_total"] == (
        len(items.loc[0, "question"]) + sum(len(option) for option in items.loc[0, "options"])
    )


def test_token_counts_preserves_each_condition(monkeypatch, tmp_path):
    install_fake_tokenizer(monkeypatch)
    items = pd.read_json(MOCK_ITEMS, lines=True).iloc[:2].to_dict("records")
    items[0]["condition"] = "RU-P"
    items[1]["condition"] = "RU-R"
    items_path = tmp_path / "items.jsonl"
    items_path.write_text(
        "\n".join(json.dumps(item) for item in items),
        encoding="utf-8",
    )

    counts = token_counts(items_path, tokenizer_name="fake-tokenizer")

    assert counts["condition"].tolist() == ["RU-P", "RU-R"]


def test_token_counts_reports_missing_transformers(monkeypatch):
    monkeypatch.setitem(sys.modules, "transformers", None)

    with pytest.raises(ImportError, match="pip install transformers"):
        token_counts(MOCK_ITEMS)


def test_token_summaries_and_paired_comparisons_are_domain_aware():
    rows = []
    for item, domain, nu_total, rup_total in [
        ("i1", "d0", 10, 12),
        ("i2", "d0", 20, 23),
        ("i3", "d1", 30, 32),
    ]:
        for condition, total in [("NU", nu_total), ("RU-P", rup_total)]:
            row = {
                "item_id": item,
                "condition": condition,
                "domain": domain,
                "n_tokens_total": total,
                "n_tokens_question": total - 4,
                "n_tokens_options": 4,
                "n_chars_total": total * 2,
            }
            rows.append(row)
    counts = pd.DataFrame(rows)

    summary = token_summary_table(counts, n_boot=100)
    comparison = token_comparison_table(counts, n_boot=100)

    assert set(summary["condition"]) == {"NU", "RU-P"}
    total_difference = comparison.set_index("metric").loc["n_tokens_total"]
    assert total_difference["mean_difference"] == pytest.approx(7 / 3)
    assert set(comparison["condition"]) == {"RU-P"}
