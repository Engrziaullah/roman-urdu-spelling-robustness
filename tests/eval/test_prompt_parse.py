from __future__ import annotations

from pathlib import Path

import pytest

from src.eval.parse import parse_answer
from src.eval.prompt import PromptTemplateError, build_prompt, letters_for_options


def _item(options: list[str] | None = None) -> dict:
    return {
        "item_id": "mock-prompt-01",
        "condition": "NU",
        "question": "What is 2 + 2? {keep this literal}",
        "options": options or ["3", "4", "5", "6"],
    }


def test_prompt_builder_labels_variable_option_counts_and_hashes(
    tmp_path: Path,
) -> None:
    template = tmp_path / "prompt.txt"
    template.write_text(
        "Choose from {letters}\n{question}\n{options}\n",
        encoding="utf-8",
    )
    prompt, prompt_hash = build_prompt(
        _item(["one", "two", "three", "four", "five"]),
        "NU",
        template,
    )

    assert "Choose from A, B, C, D, or E" in prompt
    assert "A) one\nB) two\nC) three\nD) four\nE) five" in prompt
    assert "{keep this literal}" in prompt
    assert len(prompt_hash) == 64


def test_prompt_builder_rejects_todo_and_condition_mismatch(tmp_path: Path) -> None:
    template = tmp_path / "prompt.txt"
    template.write_text("TODO {letters} {question} {options}", encoding="utf-8")
    with pytest.raises(PromptTemplateError, match="TODO"):
        build_prompt(_item(), "NU", template)

    template.write_text("{letters} {question} {options}", encoding="utf-8")
    with pytest.raises(ValueError, match="condition"):
        build_prompt(_item(), "RU-P", template)


def test_letters_for_options_does_not_assume_four() -> None:
    assert letters_for_options(5) == ["A", "B", "C", "D", "E"]
    with pytest.raises(ValueError, match="1 and 26"):
        letters_for_options(27)


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        ("B", ("B", True)),
        ("b", ("B", True)),
        ("B)", ("B", True)),
        ("**B**", ("B", True)),
        ("Answer: B", ("B", True)),
        ("The answer is B.", ("B", True)),
        ("(B)", ("B", True)),
        ("[B]", ("B", True)),
        ("Answer:\nB", ("B", True)),
        ("جواب: B", ("B", True)),
        ("Option B is correct", ("B", True)),
        (" B ", ("B", True)),
        ("B, B", ("B", True)),
        ("B and b", ("B", True)),
        ("Answer: E", ("E", True)),
        ("", (None, False)),
        ("   ", (None, False)),
        ("AB", (None, False)),
        ("Alphabet", (None, False)),
        ("B2", (None, False)),
        ("2B", (None, False)),
        ("A or B", (None, False)),
        ("A, C", (None, False)),
        ("Answer: B, not C", (None, False)),
        ("None", (None, False)),
        ("F", (None, False)),
        ("جواب اردو", (None, False)),
        ("** **", (None, False)),
        ("the answer", (None, False)),
        ("B C", (None, False)),
        ("XBZ", (None, False)),
        ("foo_B_", (None, False)),
    ],
)
def test_parser_handles_tricky_responses(
    response: str,
    expected: tuple[str | None, bool],
) -> None:
    assert parse_answer(response, ["A", "B", "C", "D", "E"]) == expected


def test_parser_accepts_only_supplied_valid_letters() -> None:
    assert parse_answer("E", ["A", "B", "C", "D", "E"]) == ("E", True)
    assert parse_answer("E", ["A", "B", "C", "D"]) == (None, False)


def test_parser_rejects_invalid_letter_configuration() -> None:
    with pytest.raises(ValueError, match="ASCII letters"):
        parse_answer("A", ["AA"])
