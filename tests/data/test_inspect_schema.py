"""Offline tests for the UrduMMLU schema report generator."""
import unittest

from src.data.inspect_schema import build_report, read_json_records


class SchemaReportTests(unittest.TestCase):
    def test_report_generator_on_tiny_fixture(self):
        fixture = [
            {
                "id": 1,
                "question": "سوال اول؟",
                "options": {"A": "الف", "B": "ب"},
                "correct_key": "A",
                "domain": "STEM",
                "subdomain": "physics",
            },
            {
                "id": 2,
                "question": "سوال دوم؟",
                "options": {"A": "ج", "B": "د", "C": "ہ"},
                "correct_key": "C",
                "domain": "Humanities",
                "subdomain": "urdu",
            },
        ]
        report = build_report(
            fixture,
            revision="test-sha",
            splits="test (2 rows)",
            license_text="CC BY 4.0 (test fixture)",
            input_path="fixture.json",
        )
        self.assertIn("Local record count: **2**", report)
        self.assertIn("Exactly five domains? **No**", report)
        self.assertIn("Duplicate IDs: **0**", report)
        self.assertIn("test-sha", report)
        self.assertIn("CC BY 4.0", report)
        self.assertIn("| 2 | 1 |", report)
        self.assertIn("| 3 | 1 |", report)

    def test_read_json_records_accepts_array(self):
        import json
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "fixture.json"
            path.write_text(json.dumps([{"id": 1}], ensure_ascii=False), encoding="utf-8")
            self.assertEqual(read_json_records(path), [{"id": 1}])


if __name__ == "__main__":
    unittest.main()
