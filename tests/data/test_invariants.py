"""Invariant tests using explicitly labelled TOY rules and strings only."""

import unittest
from dataclasses import replace

from src.data.invariants import (
    InvariantViolation,
    reject_draft_failures,
    validate_field_result,
    validate_rup_proxy,
    validate_variant_group,
)
from src.data.rule_engine import (
    FieldResult,
    ProtectedSpanResult,
    RegexRule,
    RuleTables,
    TokenProvenance,
    WordMapRule,
    transform_item,
)


def toy_tables(*, expanding: bool = False) -> RuleTables:
    """Build deterministic TOY-only transformations."""
    return RuleTables(
        word_maps={
            "alpha": WordMapRule("alpha", "alfa", "TOY_MAP"),
        },
        regex_rules={
            "RU-R": (
                RegexRule(1, "beta", "bta", "TOY_R"),
            ) if not expanding else (
                RegexRule(1, r".+", r"\g<0>x", "TOY_EXPAND"),
            ),
            "RU-X": (
                RegexRule(1, "gamma", "gama", "TOY_X"),
            ),
        },
        protected_patterns=(),
    )


def toy_rup_item():
    return {
        "item_id": "toy-10",
        "condition": "RU-P",
        "question": "alpha beta, gamma 9",
        "options": ["alpha", "beta", "gamma", "delta", "omega"],
        "gold": "E",
        "notes": "",
    }


class InvariantTests(unittest.TestCase):
    def test_generated_variants_preserve_five_option_item_structure(self):
        tables = toy_tables()
        reference = toy_rup_item()
        reduced = transform_item(reference, "RU-R", tables).item
        english = transform_item(reference, "RU-X", tables).item
        validate_variant_group(
            reference, {"RU-R": reduced, "RU-X": english}, tables
        )

    def test_changed_option_position_is_rejected(self):
        tables = toy_tables()
        reference = toy_rup_item()
        reduced = transform_item(reference, "RU-R", tables).item
        english = transform_item(reference, "RU-X", tables).item
        english["options"][0], english["options"][1] = (
            english["options"][1], english["options"][0]
        )
        with self.assertRaisesRegex(
            InvariantViolation, r"toy-10, field options\[0\].*engine output"
        ):
            validate_variant_group(
                reference, {"RU-R": reduced, "RU-X": english}, tables
            )

    def test_gold_and_option_count_are_hard_failures(self):
        tables = toy_tables()
        reference = toy_rup_item()
        reduced = transform_item(reference, "RU-R", tables).item
        english = transform_item(reference, "RU-X", tables).item
        english["gold"] = "A"
        with self.assertRaisesRegex(InvariantViolation, "gold unchanged"):
            validate_variant_group(
                reference, {"RU-R": reduced, "RU-X": english}, tables
            )
        english["gold"] = "E"
        english["options"].pop()
        with self.assertRaisesRegex(InvariantViolation, "option count and order"):
            validate_variant_group(
                reference, {"RU-R": reduced, "RU-X": english}, tables
            )

    def test_idempotence_violation_is_named(self):
        tables = toy_tables(expanding=True)
        reference = {
            "item_id": "toy-11",
            "condition": "RU-P",
            "question": "a",
            "options": ["one"],
            "gold": "A",
        }
        reduced = transform_item(reference, "RU-R", tables).item
        english = transform_item(reference, "RU-X", tables).item
        with self.assertRaisesRegex(InvariantViolation, "idempotence"):
            validate_variant_group(
                reference, {"RU-R": reduced, "RU-X": english}, tables
            )

    def test_unknown_operation_and_invalid_provenance_are_rejected(self):
        result = FieldResult(
            "toy",
            "toys",
            (TokenProvenance(0, "toy", "toys", ("TOY_UNKNOWN",)),),
            (),
        )
        with self.assertRaisesRegex(InvariantViolation, "unknown op_id"):
            validate_field_result("toy", result, "toy-12", "question", frozenset())
        wrong_index = replace(
            result,
            tokens=(TokenProvenance(1, "toy", "toys", ("TOY",)),),
        )
        with self.assertRaisesRegex(InvariantViolation, "positional provenance"):
            validate_field_result("toy", wrong_index, "toy-12", "question", frozenset({"TOY"}))

    def test_protected_span_mismatch_is_rejected(self):
        result = FieldResult(
            "SAFE",
            "SAFE",
            (TokenProvenance(0, "SAFE", "SAFE", ()),),
            (ProtectedSpanResult(0, "SAFE", "NOT_SAFE", ("TOY_PROTECTED",)),),
        )
        with self.assertRaisesRegex(InvariantViolation, "protected token unchanged"):
            validate_field_result("SAFE", result, "toy-13", "question", frozenset())

    def test_failed_draft_rows_are_rejected(self):
        failed = {
            "item_id": "toy-14",
            "condition": "RU-P",
            "notes": "DRAFT_FAILED:bad_json",
        }
        with self.assertRaisesRegex(InvariantViolation, "toy-14.*DRAFT_FAILED"):
            reject_draft_failures([failed])
        with self.assertRaisesRegex(InvariantViolation, "DRAFT_FAILED"):
            validate_rup_proxy(
                {"item_id": "toy-14"},
                {**failed, "question": "toy", "options": ["a"]},
            )
        reference = toy_rup_item()
        reduced = transform_item(reference, "RU-R", toy_tables()).item
        english = transform_item(reference, "RU-X", toy_tables()).item
        failed_variant = {**reduced, "notes": "DRAFT_FAILED:bad_json"}
        with self.assertRaisesRegex(InvariantViolation, "DRAFT_FAILED"):
            validate_variant_group(
                reference,
                {"RU-R": failed_variant, "RU-X": english},
                toy_tables(),
            )

    def test_rup_diagnostics_are_labelled_proxy_not_pass(self):
        diagnostics = validate_rup_proxy(
            {
                "item_id": "toy-15",
                "condition": "NU",
                "question": "toy 12",
                "options": ["one", "two"],
                "gold": "A",
            },
            {
                "item_id": "toy-15",
                "condition": "RU-P",
                "question": "toy",
                "options": ["one", "two"],
                "gold": "A",
                "notes": "",
            },
            protected_tokens=("one",),
        )
        self.assertEqual(diagnostics["status"], "proxy")
        self.assertTrue(any("token count" in item for item in diagnostics["diagnostics"]))
        self.assertTrue(any("order assumed" in item for item in diagnostics["diagnostics"]))


if __name__ == "__main__":
    unittest.main()
