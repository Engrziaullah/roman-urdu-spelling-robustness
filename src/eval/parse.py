"""Parse exactly one unambiguous standalone option letter from model output.

Letters are case-insensitive and must be standalone Unicode word tokens.
Formatting punctuation around a letter is accepted (for example ``B)``,
``**B**``, and ``Answer: B``). Repeated occurrences of the same valid letter
remain valid. More than one distinct valid letter, or no valid letter, is
invalid; invalid answers are retained in run results rather than dropped.
"""

from __future__ import annotations

import re
from collections.abc import Iterable


_STANDALONE_ASCII_LETTER = re.compile(r"(?<!\w)([A-Za-z])(?!\w)", re.UNICODE)


def parse_answer(
    response: str,
    valid_letters: Iterable[str],
) -> tuple[str | None, bool]:
    """Return the sole distinct valid letter and validity for a model response."""
    allowed = {letter.upper() for letter in valid_letters}
    if not allowed or any(
        len(letter) != 1 or letter < "A" or letter > "Z" for letter in allowed
    ):
        raise ValueError("valid_letters must contain one or more ASCII letters A-Z.")
    if not isinstance(response, str):
        raise TypeError("response must be text.")

    found = {
        match.group(1).upper()
        for match in _STANDALONE_ASCII_LETTER.finditer(response)
        if match.group(1).upper() in allowed
    }
    if len(found) != 1:
        return None, False
    return next(iter(found)), True
