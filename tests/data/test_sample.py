
import json
import unittest
import tempfile
from collections import Counter
from pathlib import Path

from src.data.sample import create_sample

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_FILE = ROOT / "data" / "processed" / "items_nu.jsonl"

EXPECTED_FIELDS = {
    "item_id",
    "source_row",
    "domain",
    "subject",
    "condition",
    "question",
    "options",
    "gold",
    "verified",
    "sample_rank",
    "notes",
}


class TestSample(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(SAMPLE_FILE, encoding="utf-8") as f:
            cls.rows = [json.loads(line) for line in f if line.strip()]

    def test_total_records(self):
        self.assertEqual(len(self.rows), 500)

    def test_unique_item_ids(self):
        ids = [r["item_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields(self):
        for row in self.rows:
            self.assertEqual(set(row.keys()), EXPECTED_FIELDS)

    def test_100_records_per_domain(self):
        counts = Counter(r["domain"] for r in self.rows)
        self.assertEqual(len(counts), 5)
        for count in counts.values():
            self.assertEqual(count, 100)

    def test_first_200_have_40_per_domain(self):
        first_200 = [
            r for r in self.rows
            if r["sample_rank"] <= 200
        ]
        counts = Counter(r["domain"] for r in first_200)

        self.assertEqual(len(first_200), 200)
        for count in counts.values():
            self.assertEqual(count, 40)

    def test_gold_is_valid(self):
        for row in self.rows:
            valid_keys = "ABCDE"[:len(row["options"])]
            self.assertIn(row["gold"], valid_keys)

    def test_no_empty_text(self):
        for row in self.rows:
            self.assertTrue(row["question"].strip())
            self.assertTrue(row["options"])
            for option in row["options"]:
                self.assertTrue(str(option).strip())

    def test_condition_and_verified(self):
        for row in self.rows:
            self.assertEqual(row["condition"], "NU")
            self.assertIs(row["verified"], True)

    def test_sample_ranks(self):
        ranks = sorted(r["sample_rank"] for r in self.rows)
        self.assertEqual(ranks, list(range(1, 501)))

    def test_same_seed_produces_same_output(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.jsonl"
            second = Path(temp) / "second.jsonl"

            create_sample(42, 100, first, Path(temp) / "first_report.md")
            create_sample(42, 100, second, Path(temp) / "second_report.md")

            self.assertEqual(
                first.read_bytes(),
                second.read_bytes()
            )


if __name__ == "__main__":
    unittest.main()

import json
import unittest
import tempfile
from collections import Counter
from pathlib import Path

from src.data.sample import create_sample

ROOT = Path(__file__).resolve().parents[2]
SAMPLE_FILE = ROOT / "data" / "processed" / "items_nu.jsonl"

EXPECTED_FIELDS = {
    "item_id",
    "source_row",
    "domain",
    "subject",
    "condition",
    "question",
    "options",
    "gold",
    "verified",
    "sample_rank",
    "notes",
}


class TestSample(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        with open(SAMPLE_FILE, encoding="utf-8") as f:
            cls.rows = [json.loads(line) for line in f if line.strip()]

    def test_total_records(self):
        self.assertEqual(len(self.rows), 500)

    def test_unique_item_ids(self):
        ids = [r["item_id"] for r in self.rows]
        self.assertEqual(len(ids), len(set(ids)))

    def test_required_fields(self):
        for row in self.rows:
            self.assertEqual(set(row.keys()), EXPECTED_FIELDS)

    def test_100_records_per_domain(self):
        counts = Counter(r["domain"] for r in self.rows)
        self.assertEqual(len(counts), 5)
        for count in counts.values():
            self.assertEqual(count, 100)

    def test_first_200_have_40_per_domain(self):
        first_200 = [
            r for r in self.rows
            if r["sample_rank"] <= 200
        ]
        counts = Counter(r["domain"] for r in first_200)

        self.assertEqual(len(first_200), 200)
        for count in counts.values():
            self.assertEqual(count, 40)

    def test_gold_is_valid(self):
        for row in self.rows:
            valid_keys = "ABCDE"[:len(row["options"])]
            self.assertIn(row["gold"], valid_keys)

    def test_no_empty_text(self):
        for row in self.rows:
            self.assertTrue(row["question"].strip())
            self.assertTrue(row["options"])
            for option in row["options"]:
                self.assertTrue(str(option).strip())

    def test_condition_and_verified(self):
        for row in self.rows:
            self.assertEqual(row["condition"], "NU")
            self.assertIs(row["verified"], True)

    def test_sample_ranks(self):
        ranks = sorted(r["sample_rank"] for r in self.rows)
        self.assertEqual(ranks, list(range(1, 501)))

    def test_same_seed_produces_same_output(self):
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / "first.jsonl"
            second = Path(temp) / "second.jsonl"

            create_sample(42, 100, first, Path(temp) / "first_report.md")
            create_sample(42, 100, second, Path(temp) / "second_report.md")

            self.assertEqual(
                first.read_bytes(),
                second.read_bytes()
            )


if __name__ == "__main__":
    unittest.main()
