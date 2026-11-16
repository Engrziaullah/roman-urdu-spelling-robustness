
import json
import csv
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "data" / "raw" / "urdummlu.json"
OUTPUT_FILE = ROOT / "data" / "interim" / "exclusion_filter_full.csv"

ENGLISH_THRESHOLD = 30.0
FORMULA_THRESHOLD = 15.0

MATH_SYMBOLS = set("=+-*/^%<>√∫∑∏≈≠≤≥±×÷∞∂∆∇")


def calculate_ratios(question):
    letters = [
        c for c in question
        if unicodedata.category(c).startswith("L")
    ]

    latin_letters = [
        c for c in letters
        if ("A" <= c <= "Z") or ("a" <= c <= "z")
    ]

    english_char_ratio = (
        len(latin_letters) / len(letters) * 100
        if letters else 0.0
    )

    # Count English words instead of individual English letters.
    words = re.findall(r"[^\W\d_]+", question, flags=re.UNICODE)

    english_words = [
        word for word in words
        if re.search(r"[A-Za-z]", word)
    ]

    english_word_ratio = (
        len(english_words) / len(words) * 100
        if words else 0.0
    )

    visible_chars = [c for c in question if not c.isspace()]

    math_chars = [
        c for c in visible_chars
        if unicodedata.category(c) == "Sm" or c in MATH_SYMBOLS
    ]

    formula_ratio = (
        len(math_chars) / len(visible_chars) * 100
        if visible_chars else 0.0
    )

    return english_char_ratio, english_word_ratio, formula_ratio


def main():
    with open(INPUT_FILE, encoding="utf-8") as f:
        records = json.load(f)

    sample = records
    results = []

    for record in sample:
        question = record.get("question") or ""

        char_ratio, word_ratio, formula_ratio = calculate_ratios(question)

        reasons = []

        if word_ratio > ENGLISH_THRESHOLD:
            reasons.append("English-dominated")

        if formula_ratio > FORMULA_THRESHOLD:
            reasons.append("Formula-dominated")

        results.append({
            "id": record.get("id"),
            "english_char_ratio_percent": round(char_ratio, 2),
            "english_word_ratio_percent": round(word_ratio, 2),
            "formula_ratio_percent": round(formula_ratio, 2),
            "flagged": bool(reasons),
            "reason": "; ".join(reasons) if reasons else "None",
            "question": question
        })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    flagged = sum(row["flagged"] for row in results)

    print("Total records checked:", len(results))
    print("Excluded records:", flagged)
    print("Eligible records:", len(results) - flagged)
    print("Original dataset modified: NO")
    print("Output:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
