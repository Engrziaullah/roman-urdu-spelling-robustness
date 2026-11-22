"""Tests for rule loading and transformation using labelled TOY rules only."""

import csv
import tempfile
import unittest
from pathlib import Path

from src.data.rule_engine import (
    RuleEngineError,
    load_rule_tables,
    transform_field,
    transform_item,
)


def write_rule_files(directory: Path, *, protected_rows=()) -> None:
    """Write labelled TOY rule tables for offline tests."""
    tables = {
        "ru_r_wordmap.csv": (
            ["ru_p", "ru_r", "op_id", "note"],
            [{"ru_p": "alpha", "ru_r": "alfa", "op_id": "TOY_MAP", "note": "TOY"}],
        ),
        "ru_r_rules.csv": (
            ["order", "pattern", "replacement", "op_id", "note"],
            [{"order": "2", "pattern": "beta", "replacement": "bta",
              "op_id": "TOY_R2", "note": "TOY"},
             {"order": "1", "pattern": "gamma", "replacement": "gama",
              "op_id": "TOY_R1", "note": "TOY"}],
        ),
        "ru_x_rules.csv": (
            ["order", "pattern", "replacement", "op_id", "note"],
            [{"order": "1", "pattern": "alpha", "replacement": "alphx",
              "op_id": "TOY_X1", "note": "TOY"}],
        ),
        "protected_patterns.csv": (
            ["pattern_id", "kind", "pattern", "note"],
            list(protected_rows),
        ),
    }
    for filename, (header, rows) in tables.items():
        with (directory / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)


class RuleEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.rule_dir = Path(self.temp.name)
        write_rule_files(
            self.rule_dir,
            protected_rows=[
                {"pattern_id": "TOY_CODE", "kind": "regex",
                 "pattern": r"ID-\d+", "note": "TOY"},
                {"pattern_id": "TOY_NAME", "kind": "literal",
                 "pattern": "SAFE", "note": "TOY"},
            ],
        )
        self.tables = load_rule_tables(self.rule_dir)

    def tearDown(self):
        self.temp.cleanup()

    def test_repository_rule_files_load_and_validate(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        self.assertGreater(len(tables.word_maps), 0)
        self.assertIn("RU-R", tables.regex_rules)
        self.assertIn("RU-X", tables.regex_rules)
        self.assertGreater(len(tables.regex_rules["RU-R"]), 0)
        self.assertGreater(len(tables.regex_rules["RU-X"]), 0)
        self.assertGreater(len(tables.protected_patterns), 0)

    def test_rur_operations_each_have_three_working_examples(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)

        # R1_DROP_VOWEL (Word map)
        for src, expected in [("jawab", "jwab"), ("sawal", "swal"), ("kitab", "ktab")]:
            res = transform_field(src, "item-r1", "question", "RU-R", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("R1_DROP_VOWEL", res.tokens[0].op_ids)

        # R2_SHORTEN_FREQ (Word map)
        for src, expected in [("nahin", "nhi"), ("mein", "mn"), ("bhi", "b")]:
            res = transform_field(src, "item-r2", "question", "RU-R", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("R2_SHORTEN_FREQ", res.tokens[0].op_ids)

        # R3_CASUAL_SHORTEN (Word map)
        for src, expected in [("lekin", "lkn"), ("hoga", "hga"), ("hogi", "hgi")]:
            res = transform_field(src, "item-r3", "question", "RU-R", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("R3_CASUAL_SHORTEN", res.tokens[0].op_ids)

        # R4_DROP_TERMINAL_H (Regex rule 1)
        for src, expected in [("jagah", "jaga"), ("wajah", "waja"), ("gunah", "guna")]:
            res = transform_field(src, "item-r4", "question", "RU-R", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("R4_DROP_TERMINAL_H", res.tokens[0].op_ids)

        # R5_CONTRACTION_IYA (Regex rule 2)
        for src, expected in [("diya", "dya"), ("liya", "lya"), ("jiya", "jya")]:
            res = transform_field(src, "item-r5", "question", "RU-R", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("R5_CONTRACTION_IYA", res.tokens[0].op_ids)

    def test_rux_operations_each_have_three_working_examples(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)

        # X1_X_FOR_KH (Regex rule 1)
        for src, expected in [("khuda", "xuda"), ("khatam", "xatam"), ("khabar", "xabar")]:
            res = transform_field(src, "item-x1", "question", "RU-X", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("X1_X_FOR_KH", res.tokens[0].op_ids)

        # X2_K_FOR_Q (Regex rule 2)
        for src, expected in [("qalam", "kalam"), ("qanoon", "kanoon"), ("nuqta", "nukta")]:
            res = transform_field(src, "item-x2", "question", "RU-X", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("X2_K_FOR_Q", res.tokens[0].op_ids)

        # X3_F_FOR_PH (Regex rule 3)
        for src, expected in [("phool", "fool"), ("phal", "fal"), ("phir", "fir")]:
            res = transform_field(src, "item-x3", "question", "RU-X", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("X3_F_FOR_PH", res.tokens[0].op_ids)

        # X4_V_FOR_W (Regex rule 4)
        for src, expected in [("watan", "vatan"), ("wazir", "vazir"), ("wahan", "vahan")]:
            res = transform_field(src, "item-x4", "question", "RU-X", tables)
            self.assertEqual(res.text, expected)
            self.assertIn("X4_V_FOR_W", res.tokens[0].op_ids)

    def test_repository_protected_patterns_protect_tokens_from_rules(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        # Check that protected tokens are not altered by RU-R or RU-X rules
        text = "A) H2O aur CO2 ki miqdar 15 kg ya 90% hai ____"
        res_r = transform_field(text, "item-prot", "question", "RU-R", tables)
        res_x = transform_field(text, "item-prot", "question", "RU-X", tables)
        for token in ["A)", "H2O", "CO2", "15", "kg", "90", "____"]:
            self.assertIn(token, res_r.text)
            self.assertIn(token, res_x.text)

    def test_ascii_digit_pattern_does_not_protect_urdu_digits(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        ascii_result = transform_field(
            "15 9.25", "item-digits", "question", "RU-R", tables
        )
        urdu_result = transform_field(
            "۱۵", "item-digits", "question", "RU-R", tables
        )
        self.assertEqual(ascii_result.text, "15 9.25")
        self.assertIn("15", ascii_result.text)
        urdu_tokens = tuple(
            span.pattern_ids
            for span in urdu_result.protected_spans
        )
        self.assertTrue(any("DIGIT_URDU" in ids for ids in urdu_tokens))

    def test_ascii_digit_pattern_matches_only_ascii_digits(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        ascii_pattern = next(
            pattern.pattern
            for pattern in tables.protected_patterns
            if pattern.pattern_id == "DIGIT_ASCII"
        )
        self.assertEqual(ascii_pattern, r"\b[0-9]+(?:\.[0-9]+)?\b")
        self.assertNotIn(r"\d", ascii_pattern)

    def test_ru_x_rules_do_not_transform_nonmatching_letter_runs(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        for src in ("alpha", "bravo", "xray", "q", "qwerty"):
            res = transform_field(src, "item-x-boundary", "question", "RU-X", tables)
            if src == "q":
                self.assertEqual(res.text, "k")
            elif src == "qwerty":
                self.assertEqual(res.text, "kwerty")
            else:
                self.assertEqual(res.text, src)

    def test_repository_ru_x_rules_include_x1_through_x4(self):
        repository_rules = Path(__file__).resolve().parents[2] / "src" / "data" / "rules"
        tables = load_rule_tables(repository_rules)
        op_ids = frozenset(rule.op_id for rule in tables.regex_rules["RU-X"])
        self.assertEqual(
            op_ids,
            frozenset({
                "X1_X_FOR_KH",
                "X2_K_FOR_Q",
                "X3_F_FOR_PH",
                "X4_V_FOR_W",
            }),
        )

    def test_map_then_ordered_regex_and_variant_equality_report(self):
        item = {
            "item_id": "toy-1",
            "condition": "RU-P",
            "question": "alpha, beta gamma",
            "options": ["alpha", "beta", "gamma", "delta", "omega"],
            "gold": "E",
        }
        reduced = transform_item(item, "RU-R", self.tables)
        english = transform_item(item, "RU-X", self.tables)

        self.assertEqual(reduced.item["question"], "alfa, bta gama")
        self.assertEqual(english.item["question"], "alphx, beta gamma")
        self.assertFalse(reduced.variant_equals_reference)
        self.assertEqual(reduced.fields["question"].unmatched_words, ())
        self.assertEqual(len(reduced.item["options"]), 5)

    def test_unmatched_words_and_identical_variant_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(directory)
            tables = load_rule_tables(directory)
            item = {
                "item_id": "toy-2",
                "condition": "RU-P",
                "question": "untouched",
                "options": ["same"],
                "gold": "A",
            }
            result = transform_item(item, "RU-X", tables)
            self.assertTrue(result.variant_equals_reference)
            self.assertEqual(result.unmatched_words["question"], ("untouched",))
            self.assertEqual(result.unmatched_words["options[0]"], ("same",))

    def test_protected_literal_regex_overlap_and_per_item_token(self):
        text = "alpha SAFE ID-42 beta"
        result = transform_field(
            text, "toy-3", "question", "RU-R", self.tables, ("alpha",)
        )
        self.assertEqual(result.text, "alpha SAFE ID-42 bta")
        self.assertEqual(len(result.protected_spans), 3)
        self.assertTrue(all(span.source_text == span.output_text
                            for span in result.protected_spans))

    def test_touching_protected_spans_are_merged(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(
                directory,
                protected_rows=[
                    {"pattern_id": "TOY_LEFT", "kind": "literal",
                     "pattern": "ABC", "note": "TOY"},
                    {"pattern_id": "TOY_RIGHT", "kind": "literal",
                     "pattern": "DEF", "note": "TOY"},
                ],
            )
            result = transform_field(
                "ABCDEF alpha", "toy-4", "question", "RU-R",
                load_rule_tables(directory),
            )
        self.assertEqual(result.text, "ABCDEF alfa")
        self.assertEqual(len(result.protected_spans), 1)
        self.assertEqual(
            result.protected_spans[0].pattern_ids,
            ("TOY_LEFT", "TOY_RIGHT"),
        )

    def test_example_rules_are_ignored_and_header_only_files_load(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(directory)
            with (directory / "ru_r_rules.csv").open(
                "a", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow(["3", "untouched", "changed", "TOY_EXAMPLE", "EXAMPLE only"])
            tables = load_rule_tables(directory)
            result = transform_field(
                "untouched", "toy-5", "question", "RU-R", tables
            )
            self.assertEqual(result.text, "untouched")
            self.assertNotIn("TOY_EXAMPLE", tables.op_ids)

    def test_invalid_protected_pattern_names_item_field_and_pattern(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(
                directory,
                protected_rows=[
                    {"pattern_id": "TOY_BAD", "kind": "regex",
                     "pattern": "(", "note": "TOY"},
                ],
            )
            tables = load_rule_tables(directory)
            with self.assertRaisesRegex(
                RuleEngineError, r"toy-6, field options\[2\], pattern_id TOY_BAD"
            ):
                transform_field(
                    "alpha", "toy-6", "options[2]", "RU-R", tables
                )

    def test_private_use_collision_and_empty_match_are_hard_errors(self):
        with self.assertRaisesRegex(RuleEngineError, "toy-7, field question"):
            transform_field("\ue000", "toy-7", "question", "RU-R", self.tables)
        non_reserved = transform_field(
            "\ue200", "toy-7b", "question", "RU-R", self.tables
        )
        self.assertEqual(non_reserved.text, "\ue200")
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(
                directory,
                protected_rows=[
                    {"pattern_id": "TOY_EMPTY", "kind": "regex",
                     "pattern": "a*", "note": "TOY"},
                ],
            )
            with self.assertRaisesRegex(
                RuleEngineError, r"toy-8, field question, pattern_id TOY_EMPTY"
            ):
                transform_field(
                    "alpha", "toy-8", "question", "RU-R",
                    load_rule_tables(directory),
                )

    def test_nonletter_change_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            write_rule_files(directory)
            with (directory / "ru_r_rules.csv").open(
                "w", encoding="utf-8", newline=""
            ) as handle:
                writer = csv.writer(handle)
                writer.writerow(["order", "pattern", "replacement", "op_id", "note"])
                writer.writerow(["1", "alfa", "!", "TOY_BAD", "TOY"])
            with self.assertRaisesRegex(RuleEngineError, "non-letter characters changed"):
                transform_field(
                    "alpha", "toy-9", "question", "RU-R",
                    load_rule_tables(directory),
                )


if __name__ == "__main__":
    unittest.main()
