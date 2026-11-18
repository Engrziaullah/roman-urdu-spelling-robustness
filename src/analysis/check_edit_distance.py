"""Validate Role A's edit-distance CSV without modifying it."""

import argparse
import csv
import math
from pathlib import Path

EXPECTED_VARIANT_PAIRS = (
    "RU-P vs RU-R",
    "RU-P vs RU-X",
    "RU-R vs RU-X",
)
REQUIRED_COLUMNS = (
    "variant_pair",
    "mean_char_edit_distance",
    "mean_normalized_edit_distance",
)


def check_edit_distance_csv(path: str | Path) -> list[str]:
    """Return validation problems for an edit-distance CSV, or an empty list.

    The CSV uses the derived-table columns produced by ``tables.py`` and one
    row for each of the three Roman Urdu variant pairs. The file is read-only.
    """
    problems = []
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            columns = reader.fieldnames
            if not columns:
                return ["CSV is empty or has no header."]
            missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
            if missing_columns:
                return [f"Missing required column: {column}" for column in missing_columns]
            rows = list(reader)
    except (OSError, UnicodeError, csv.Error) as exc:
        return [f"Could not read CSV: {exc}"]

    seen_pairs = {}
    for row_number, row in enumerate(rows, start=2):
        if None in row:
            problems.append(f"Row {row_number}: more values than header columns.")
            continue
        missing_values = [
            column for column in columns if row.get(column) is None or not row[column].strip()
        ]
        if missing_values:
            problems.append(
                f"Row {row_number}: missing value in column(s): {', '.join(missing_values)}."
            )
            continue

        pair = row["variant_pair"].strip()
        if pair not in EXPECTED_VARIANT_PAIRS:
            problems.append(f"Row {row_number}: unexpected variant_pair {pair!r}.")
        else:
            seen_pairs[pair] = seen_pairs.get(pair, 0) + 1

        for column in REQUIRED_COLUMNS[1:]:
            try:
                value = float(row[column])
            except ValueError:
                problems.append(f"Row {row_number}: {column} must be numeric.")
                continue
            if not math.isfinite(value):
                problems.append(f"Row {row_number}: {column} must be finite.")
            elif column == "mean_char_edit_distance" and value < 0:
                problems.append(f"Row {row_number}: {column} must be non-negative.")
            elif column == "mean_normalized_edit_distance" and not 0 <= value <= 1:
                problems.append(f"Row {row_number}: {column} must be between 0 and 1.")

    for pair in EXPECTED_VARIANT_PAIRS:
        count = seen_pairs.get(pair, 0)
        if count == 0:
            problems.append(f"Missing expected variant_pair: {pair}.")
        elif count > 1:
            problems.append(f"Expected variant_pair {pair} exactly once; found {count} rows.")
    return problems


def main(argv: list[str] | None = None) -> int:
    """Print validation results for the CSV path provided on the command line."""
    parser = argparse.ArgumentParser(description="Validate an edit-distance CSV.")
    parser.add_argument("path", help="Path to Role A's edit-distance CSV.")
    args = parser.parse_args(argv)

    problems = check_edit_distance_csv(args.path)
    if problems:
        for problem in problems:
            print(problem)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
