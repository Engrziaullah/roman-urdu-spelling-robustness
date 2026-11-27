import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.data.sample import create_sample


class TestOptionPolicy(unittest.TestCase):

    def test_seeded_sample_preserves_four_and_five_options(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "items_nu.jsonl"
            report_path = Path(temp_dir) / "sampling_report.md"

            create_sample(42, 100, output_path, report_path)

            with output_path.open(encoding="utf-8") as file:
                rows = [
                    json.loads(line)
                    for line in file
                    if line.strip()
                ]

            self.assertEqual(len(rows), 500)

            option_counts = Counter(
                len(row["options"]) for row in rows
            )
            self.assertEqual(option_counts, {4: 497, 5: 3})

            for row in rows:
                valid_keys = "ABCDE"[:len(row["options"])]
                self.assertIn(row["gold"], valid_keys)

            five_option_rows = [
                row for row in rows
                if len(row["options"]) == 5
            ]
            self.assertEqual(len(five_option_rows), 3)

            report = report_path.read_text(encoding="utf-8")
            self.assertIn(
                "Normalized UTF-8 SHA-256", report
            )
            self.assertIn("no replacement", report.lower())


if __name__ == "__main__":
    unittest.main()
