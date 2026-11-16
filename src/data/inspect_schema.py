"""Inspect the local UrduMMLU JSON and write a reproducible schema report.

Run from the repository root:
    python -m src.data.inspect_schema
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

REPO_ID = "MBZUAI/UrduMMLU"
DEFAULT_INPUT = Path("data/raw/urdummlu.json")
DEFAULT_OUTPUT = Path("data/interim/schema_report.md")
CARD_URL = f"https://huggingface.co/datasets/{REPO_ID}/raw/main/README.md"
INFO_URL = f"https://huggingface.co/api/datasets/{REPO_ID}"
SPLITS_URL = f"https://datasets-server.huggingface.co/splits?dataset={REPO_ID}"


def load_dataset_records(local_path: Path) -> tuple[list[dict[str, Any]], str]:
    """Try the required Hugging Face datasets loader, then fall back to local JSON.

    Hugging Face cache is directed into data/raw so downloaded source artefacts
    remain under the repository's ignored raw-data directory.
    """
    try:
        from datasets import load_dataset
        dataset = load_dataset(REPO_ID, split="test", cache_dir="data/raw/hf_cache")
        return [dict(row) for row in dataset], "Loaded from Hugging Face with datasets.load_dataset (test split)."
    except Exception as exc:
        if not local_path.exists():
            raise RuntimeError(
                "Hugging Face datasets loading failed and the local JSON fallback is missing. "
                f"Original error: {type(exc).__name__}: {exc}"
            ) from exc
        records = read_json_records(local_path)
        return records, (
            "FALLBACK: read existing local JSON because datasets.load_dataset failed: "
            f"{type(exc).__name__}: {exc}"
        )


def read_json_records(path: Path) -> list[dict[str, Any]]:
    """Load a JSON array or a dictionary containing a records array."""
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        records = payload
    elif isinstance(payload, dict):
        records = next(
            (payload[key] for key in ("data", "records", "items", "questions")
             if isinstance(payload.get(key), list)),
            None,
        )
        if records is None:
            raise ValueError("JSON root is an object but no data/records/items/questions list was found.")
    else:
        raise ValueError("JSON root must be an array or an object containing a records array.")
    if not all(isinstance(row, dict) for row in records):
        raise ValueError("Every dataset record must be a JSON object.")
    return records


def infer_type(value: Any) -> str:
    """Return a compact JSON-level type label."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, int):
        return "int"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        inner = sorted({infer_type(item) for item in value})
        return "list[" + (", ".join(inner) if inner else "empty") + "]"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def short_value(value: Any, limit: int = 180) -> str:
    """Render one example compactly and truncate long values."""
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    rendered = rendered.replace("\n", " ")
    return rendered if len(rendered) <= limit else rendered[: limit - 3] + "..."


def fetch_text(url: str, timeout: int = 15) -> str:
    """Fetch a UTF-8 web resource; raise a readable error on failure."""
    request = urllib.request.Request(url, headers={"User-Agent": "urdu-mmlu-schema-inspector/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def get_hub_metadata() -> tuple[str, str, str]:
    """Return revision, split summary and license/card text; failures are explicit."""
    revision = "NOT VERIFIED (Hugging Face API unavailable)"
    split_summary = "NOT VERIFIED (Hugging Face dataset-server API unavailable)"
    license_text = "NOT VERIFIED (dataset card could not be fetched)"
    try:
        info = json.loads(fetch_text(INFO_URL))
        revision = str(info.get("sha") or revision)
        card_data = info.get("cardData") or {}
        license_id = card_data.get("license")
        if license_id:
            license_text = f"Dataset-card metadata license identifier: `{license_id}`"
    except Exception as exc:
        revision += f"\n  - Detail: `{type(exc).__name__}: {exc}`"

    try:
        splits = json.loads(fetch_text(SPLITS_URL))
        entries = splits.get("splits", [])
        if entries:
            split_summary = "; ".join(
                f"{item.get('split', 'unknown')} ({item.get('num_examples', 'unknown')} rows; "
                f"config={item.get('config', 'default')})"
                for item in entries
            )
        else:
            split_summary = "No split entries returned by the dataset-server API."
    except Exception as exc:
        split_summary += f"\n  - Detail: `{type(exc).__name__}: {exc}`"

    try:
        card = fetch_text(CARD_URL)
        license_lines = [
            line.strip() for line in card.splitlines()
            if "license" in line.lower() or "cc by" in line.lower()
        ]
        if license_lines:
            license_text += "\n\nRelevant dataset-card lines:\n" + "\n".join(
                f"- `{line}`" for line in license_lines[:12]
            )
        else:
            license_text += "\n\nNo explicit license line was found in the fetched README."
    except Exception as exc:
        license_text += f"\n\nDataset-card fetch detail: `{type(exc).__name__}: {exc}`"

    return revision, split_summary, license_text


def build_report(records: list[dict[str, Any]], revision: str,
                 splits: str, license_text: str, input_path: str = str(DEFAULT_INPUT),
                 loading_method: str = "Not recorded") -> str:
    """Generate a Markdown schema report from records and supplied Hub metadata."""
    if not records:
        raise ValueError("Dataset contains zero records.")

    columns = sorted({key for row in records for key in row})
    lines = [
        "# UrduMMLU Schema Inspection Report",
        "",
        f"- Local source: `{input_path}`",
        f"- Local record count: **{len(records):,}**",
        f"- Hugging Face dataset: `{REPO_ID}`",
        f"- Dataset revision/commit: `{revision}`",
        f"- Available splits and sizes: {splits}",
        f"- Local data loading method: {loading_method}",
        "",
        "## Columns, JSON-level types, and examples",
        "",
    ]

    for column in columns:
        values = [row.get(column) for row in records if column in row]
        types = ", ".join(f"`{kind}` ({count:,})" for kind, count in
                          Counter(infer_type(value) for value in values).most_common())
        lines += [f"### `{column}`", f"- Observed types: {types}", "- Examples:"]
        examples = []
        for row in records:
            if column in row and row[column] not in examples:
                examples.append(row[column])
            if len(examples) == 3:
                break
        for example in examples:
            lines.append(f"  - `{short_value(example)}`")
        lines.append("")

    option_counts = Counter()
    answer_types = Counter()
    answer_values = Counter()
    domains = Counter()
    subjects = Counter()
    empty_counts = Counter()
    ids = []
    questions = []

    for row in records:
        options = row.get("options")
        if isinstance(options, (dict, list, tuple)):
            option_counts[len(options)] += 1
        else:
            option_counts["missing_or_non_collection"] += 1
        answer = row.get("correct_key")
        answer_types[infer_type(answer)] += 1
        answer_values[str(answer)] += 1
        domains[str(row.get("domain"))] += 1
        subjects[str(row.get("subdomain"))] += 1
        for key in ("id", "question", "options", "correct_key", "domain", "subdomain"):
            value = row.get(key)
            if value is None or value == "" or value == [] or value == {}:
                empty_counts[key] += 1
        if "id" in row:
            ids.append(str(row["id"]))
        if isinstance(row.get("question"), str):
            questions.append(row["question"].strip())

    duplicate_ids = len(ids) - len(set(ids))
    duplicate_questions = len(questions) - len(set(questions))
    empty_questions = sum(not q for q in questions)

    lines += [
        "## Answer representation",
        f"- `correct_key` JSON types: {dict(answer_types)}",
        f"- Observed answer values: {dict(answer_values)}",
        "- Interpretation: determine from the values above whether answers are option letters, indices, or text.",
        "",
        "## Number of options per item",
        "",
        "| Option count | Items |",
        "|---:|---:|",
    ]
    for count, number in sorted(option_counts.items(), key=lambda pair: str(pair[0])):
        lines.append(f"| {count} | {number:,} |")

    lines += [
        "",
        "## Domain and subject representation",
        "",
        f"- Unique domains ({len(domains)}): `{', '.join(sorted(domains))}`",
        f"- Exactly five domains? **{'Yes' if len(domains) == 5 else 'No'}**",
        f"- Unique subjects/subdomains ({len(subjects)}): {len(subjects)}",
        "",
        "| Domain | Items |",
        "|---|---:|",
    ]
    for name, number in sorted(domains.items()):
        lines.append(f"| {name} | {number:,} |")
    lines += ["", "| Subdomain | Items |", "|---|---:|"]
    for name, number in sorted(subjects.items()):
        lines.append(f"| {name} | {number:,} |")

    lines += [
        "",
        "## Duplicate and empty-item checks",
        f"- Duplicate IDs: **{duplicate_ids:,}**",
        f"- Duplicate question strings (trimmed exact match): **{duplicate_questions:,}**",
        f"- Empty/whitespace-only questions: **{empty_questions:,}**",
        f"- Empty/missing key-field counts: `{dict(empty_counts)}`",
        "",
        "## Dataset-card license text",
        "",
        license_text,
        "",
        "## Proposed source mapping (text only; not applied to CONTRACTS.md)",
        "",
        "| Project field | Candidate UrduMMLU field | Notes |",
        "|---|---|---|",
        "| `source_row` | `id` | Preserve source identifier as a string in output if required by the contract. |",
        "| `domain` | `domain` | Confirm values and five-domain count above. |",
        "| `subject` | `subdomain` | Source calls this `subdomain`. |",
        "| `question` | `question` | Original Urdu question stem. |",
        "| `options` | `options` | Preserve option order; source may use keyed object A–E. |",
        "| `gold` | `correct_key` | Convert only if required; verify answer key exists in the options keys. |",
        "",
        "## Important compatibility notes",
        "- The contract example shows four options A–D, but the source inspection may show four and five-option items. Do not force all records to four options.",
        "- If any record has option key `E`, the team must agree how the contract's A–D wording is handled before sampling.",
        "- This report describes the local JSON. Hub revision, split and license are marked unverified if the online metadata requests fail.",
        "- No source records were edited.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    records, loading_method = load_dataset_records(args.input)
    revision, splits, license_text = get_hub_metadata()
    report = build_report(records, revision, splits, license_text, str(args.input), loading_method)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(report, encoding="utf-8")
    print(f"Inspected {len(records):,} records from {args.input}")
    print(f"Report saved to {args.out}")
    print(f"Hub revision: {revision}")
    print(f"Splits: {splits}")


if __name__ == "__main__":
    main()
