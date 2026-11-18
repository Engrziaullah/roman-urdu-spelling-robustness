import json
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from src.data.sample import create_sample


class TestFourOptionSample(unittest.TestCase):
    def test_seeded_replacements_use_next_four_option_records_by_domain(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "items_nu.jsonl"
            report_path = Path(temp_dir) / "sampling_report.md"
            create_sample(42, 100, output_path, report_path)

            with output_path.open(encoding="utf-8") as file:
                rows = [json.loads(line) for line in file if line.strip()]

            self.assertEqual(len(rows), 500)
            self.assertEqual(Counter(len(row["options"]) for row in rows), {4: 500})
            self.assertEqual(
                {
                    row["item_id"]: row["source_row"]
                    for row in rows
                    if row["item_id"] in {"umm-0118", "umm-0266", "umm-0401"}
                },
                {
                    "umm-0118": "24754",
                    "umm-0266": "14732",
                    "umm-0401": "21078",
                },
            )
            self.assertIn("Normalized UTF-8 SHA-256", report_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
