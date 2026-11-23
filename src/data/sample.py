
import argparse
import csv
import json
import random
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

INPUT_FILE = ROOT / "data" / "raw" / "urdummlu.json"
EXCLUSION_FILE = ROOT / "data" / "interim" / "exclusion_filter_full.csv"
REPORT_FILE = ROOT / "data" / "interim" / "sampling_report.md"

DATASET_REVISION = "aae060a8564c261393de206c94a4557c850e7f2f"


def load_exclusions():
    excluded_ids = set()
    reasons = Counter()

    with open(EXCLUSION_FILE, encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if row["flagged"] == "True":
                excluded_ids.add(str(row["id"]))
                for reason in row["reason"].split("; "):
                    reasons[reason] += 1

    return excluded_ids, reasons


def normalize_options(options):
    if isinstance(options, dict):
        return list(options.values())
    if isinstance(options, list):
        return options
    raise ValueError("Unsupported options format")


def create_sample(seed, per_domain, output_file, report_file=None):
    with open(INPUT_FILE, encoding="utf-8") as f:
        records = json.load(f)

    excluded_ids, exclusion_reasons = load_exclusions()

    groups = defaultdict(list)

    for record in records:
        if str(record["id"]) in excluded_ids:
            continue

        domain = str(record["domain"])
        groups[domain].append(record)

    domains = sorted(groups)

    for domain in domains:
        if len(groups[domain]) < per_domain:
            raise ValueError(
                f"STOP: {domain} has only {len(groups[domain])} "
                f"eligible records; {per_domain} required."
            )

    rng = random.Random(seed)
    selected = []

    for domain in domains:
        items = list(groups[domain])
        rng.shuffle(items)

        for domain_rank, record in enumerate(items[:per_domain], start=1):
            options = normalize_options(record["options"])
            gold = str(record["correct_key"]).upper()

            if not options or not record.get("question"):
                raise ValueError(f"Empty question/options in source ID {record['id']}")

            if isinstance(record["options"], dict):
                option_keys = [str(k).upper() for k in record["options"]]
                if gold not in option_keys:
                    raise ValueError(f"Gold key mismatch in source ID {record['id']}")
            else:
                if gold not in "ABCDE"[:len(options)]:
                    raise ValueError(f"Invalid gold key in source ID {record['id']}")

            if any(not str(option).strip() for option in options):
                raise ValueError(f"Empty option in source ID {record['id']}")

            selected.append({
                "domain_rank": domain_rank,
                "domain": domain,
                "source_row": str(record["id"]),
                "subject": str(record["subdomain"]),
                "question": str(record["question"]),
                "options": [str(option) for option in options],
                "gold": gold,
            })

    selected.sort(key=lambda x: (x["domain_rank"], x["domain"]))

    output_file.parent.mkdir(parents=True, exist_ok=True)

    final_rows = []

    for sample_rank, item in enumerate(selected, start=1):
        final_rows.append({
            "item_id": f"umm-{sample_rank:04d}",
            "source_row": item["source_row"],
            "domain": item["domain"],
            "subject": item["subject"],
            "condition": "NU",
            "question": item["question"],
            "options": item["options"],
            "gold": item["gold"],
            "verified": True,
            "sample_rank": sample_rank,
            "notes": "",
        })

    with open(output_file, "w", encoding="utf-8") as f:
        for row in final_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    domain_counts = Counter(row["domain"] for row in final_rows)
    subject_counts = Counter(
        (row["domain"], row["subject"]) for row in final_rows
    )

    first_200 = Counter(row["domain"] for row in final_rows[:200])

    if len(final_rows) != per_domain * len(domains):
        raise ValueError("Incorrect total sample size")

    if any(count != per_domain for count in domain_counts.values()):
        raise ValueError("Domain sample count verification failed")

    if any(count != 40 for count in first_200.values()):
        raise ValueError("First 200 rank verification failed")

    if len({row["item_id"] for row in final_rows}) != len(final_rows):
        raise ValueError("Duplicate item IDs found")

    report_file = Path(report_file) if report_file else REPORT_FILE
    report_file.parent.mkdir(parents=True, exist_ok=True)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("# Sampling Report\n\n")
        f.write(f"- Date: {date.today().isoformat()}\n")
        f.write(f"- Seed: {seed}\n")
        f.write(f"- Dataset revision: `{DATASET_REVISION}`\n")
        f.write(f"- Total source records: {len(records)}\n")
        f.write(f"- Total excluded: {len(excluded_ids)}\n")
        f.write(f"- Total selected: {len(final_rows)}\n\n")

        f.write("## Eligible records by domain\n\n")
        for domain in domains:
            f.write(f"- {domain}: {len(groups[domain])}\n")

        f.write("\n## Selected records by domain\n\n")
        for domain, count in sorted(domain_counts.items()):
            f.write(f"- {domain}: {count}\n")

        f.write("\n## Selected records by subject\n\n")
        for (domain, subject), count in sorted(subject_counts.items()):
            f.write(f"- {domain} / {subject}: {count}\n")

        f.write("\n## Exclusions by reason\n\n")
        for reason, count in sorted(exclusion_reasons.items()):
            f.write(f"- {reason}: {count}\n")

        f.write("\n## Rank verification\n\n")
        f.write("- Total ranks: 1–500\n")
        f.write("- First 200 ranks: 40 records per domain\n")
        f.write("- All domain counts: 100\n")

    print("Sampling completed successfully.")
    print("Seed:", seed)
    print("Total selected:", len(final_rows))
    print("Records by domain:")
    for domain, count in sorted(domain_counts.items()):
        print(f"{domain}: {count}")
    print("First 200 rank counts:", dict(sorted(first_200.items())))
    print("Output:", output_file)
    print("Report:", report_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--per-domain", type=int, default=100)
    parser.add_argument(
        "--out",
        default="data/processed/items_nu.jsonl"
    )
    args = parser.parse_args()

    output_file = ROOT / args.out
    create_sample(args.seed, args.per_domain, output_file)


if __name__ == "__main__":
    main()
