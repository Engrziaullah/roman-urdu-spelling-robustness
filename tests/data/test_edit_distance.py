"""Edit-distance tests with hand-computed TOY strings only."""

import csv
import tempfile
import unittest
from pathlib import Path

from src.data.edit_distance import (
    CSV_HEADER,
    compute_edit_distance,
    levenshtein_distance,
    write_edit_distance,
)


class EditDistanceTests(unittest.TestCase):
    def test_hand_computed_distances(self):
        self.assertEqual(levenshtein_distance("cat", "cat"), 0)
        self.assertEqual(levenshtein_distance("cat", "cot"), 1)
        self.assertEqual(levenshtein_distance("cat", "cart"), 1)
        self.assertEqual(levenshtein_distance("", "x"), 1)
        self.assertEqual(levenshtein_distance("", ""), 0)

    def test_pooled_fields_and_item_identical_share(self):
        rows = [
            {"item_id": "toy-20", "condition": "RU-P",
             "question": "cat", "options": ["one", "bat"], "gold": "A"},
            {"item_id": "toy-20", "condition": "RU-R",
             "question": "cat", "options": ["one", "bet"], "gold": "A"},
            {"item_id": "toy-20", "condition": "RU-X",
             "question": "cot", "options": ["one", "bet"], "gold": "A"},
        ]
        result = compute_edit_distance(rows)
        self.assertEqual([row["variant_pair"] for row in result], [
            "RU-P vs RU-R", "RU-P vs RU-X", "RU-R vs RU-X"
        ])
        self.assertEqual(result[0]["n_items"], 1)
        self.assertEqual(result[0]["n_fields"], 3)
        self.assertAlmostEqual(result[0]["mean_char_edit_distance"], 1 / 3)
        self.assertAlmostEqual(result[0]["mean_normalized_edit_distance"], 1 / 9)
        self.assertEqual(result[0]["share_items_identical"], 0)
        self.assertAlmostEqual(result[0]["share_fields_identical"], 2 / 3)

    def test_exact_csv_header_and_three_rows(self):
        rows = [
            {"item_id": "toy-21", "condition": condition,
             "question": "", "options": ["same", "other", "third", "fourth", "fifth"],
             "gold": "E"}
            for condition in ("RU-P", "RU-R", "RU-X")
        ]
        with tempfile.TemporaryDirectory() as temp:
            output = write_edit_distance(rows, Path(temp) / "toy.csv")
            with output.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                records = list(reader)
        self.assertEqual(tuple(records[0]), CSV_HEADER)
        self.assertEqual(len(records), 4)
        self.assertEqual([record[0] for record in records[1:]], [
            "RU-P vs RU-R", "RU-P vs RU-X", "RU-R vs RU-X"
        ])
        self.assertEqual(records[1][5:], ["1.0", "1.0"])

    def test_normalization_handles_empty_and_nonempty_fields(self):
        rows = [
            {"item_id": "toy-25", "condition": "RU-P",
             "question": "", "options": [""], "gold": "A"},
            {"item_id": "toy-25", "condition": "RU-R",
             "question": "x", "options": [""], "gold": "A"},
            {"item_id": "toy-25", "condition": "RU-X",
             "question": "", "options": [""], "gold": "A"},
        ]
        result = compute_edit_distance(rows)
        self.assertEqual(result[0]["mean_char_edit_distance"], 0.5)
        self.assertEqual(result[0]["mean_normalized_edit_distance"], 0.5)
        self.assertEqual(result[1]["mean_normalized_edit_distance"], 0.0)

    def test_missing_variants_and_failed_drafts_are_not_skipped(self):
        with self.assertRaisesRegex(ValueError, "toy-22.*missing variant"):
            compute_edit_distance([
                {"item_id": "toy-22", "condition": "RU-P",
                 "question": "x", "options": ["a"], "gold": "A"}
            ])
        failed_rows = [
            {"item_id": "toy-23", "condition": condition,
             "question": "x", "options": ["a"], "gold": "A",
             "notes": "DRAFT_FAILED:bad_json" if condition == "RU-P" else ""}
            for condition in ("RU-P", "RU-R", "RU-X")
        ]
        with self.assertRaisesRegex(ValueError, "DRAFT_FAILED"):
            compute_edit_distance(failed_rows)

    def test_results_directory_is_forbidden(self):
        rows = [
            {"item_id": "toy-24", "condition": condition,
             "question": "x", "options": ["a"], "gold": "A"}
            for condition in ("RU-P", "RU-R", "RU-X")
        ]
        with self.assertRaisesRegex(ValueError, "must not be written under results"):
            write_edit_distance(rows, Path("results") / "toy.csv")


if __name__ == "__main__":
    unittest.main()
