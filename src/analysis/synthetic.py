import json, random
from pathlib import Path

CONDITIONS = ["NU", "RU-P", "RU-R", "RU-X", "RT"]
MODELS = ["model_a", "model_b", "model_c"]
LETTERS = "ABCD"
# Fake accuracies, sirf testing ke liye. Ye asli results nahi hain.
BASE_ACC = {"NU": 0.80, "RU-P": 0.74, "RU-R": 0.68, "RU-X": 0.66, "RT": 0.76}


def make(n_items=500, seed=42, out_dir="src/analysis/synthetic_data"):
    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    items = []
    skill = {}
    for i in range(1, n_items + 1):
        iid = f"umm-{i:04d}"
        gold = rng.choice(LETTERS)
        skill[iid] = rng.gauss(0, 1)  # item ki difficulty
        for cond in CONDITIONS:
            items.append({"item_id": iid, "condition": cond, "gold": gold,
                          "sample_rank": i, "domain": f"d{(i - 1) % 5}"})

    gold_of = {r["item_id"]: r["gold"] for r in items}

    rows = []
    for model in MODELS:
        for i in range(1, n_items + 1):
            iid = f"umm-{i:04d}"
            repeats = [1, 2, 3] if i <= 30 else [1]  # noise subset = pehle 30 items
            for cond in CONDITIONS:
                for rep in repeats:
                    p = min(0.98, max(0.05, BASE_ACC[cond] + 0.10 * skill[iid]))
                    gold = gold_of[iid]
                    if rng.random() < 0.03:
                        ans, valid = None, False  # unparsable answer
                    else:
                        valid = True
                        if rng.random() < p:
                            ans = gold
                        else:
                            ans = rng.choice([x for x in LETTERS if x != gold])
                    rows.append({
                        "run_id": "synthetic", "model_slug": model,
                        "model_string": model, "provider": "fake",
                        "date_utc": "2026-11-16T00:00:00Z",
                        "item_id": iid, "condition": cond, "repeat": rep,
                        "prompt_hash": "x", "raw_output": ans or "???",
                        "parsed_answer": ans, "valid": valid,
                        "latency_s": 1.0, "error": None,
                    })

    with open(out / "items_synth.jsonl", "w", encoding="utf-8") as f:
        for r in items:
            f.write(json.dumps(r) + "\n")
    with open(out / "results_synth.jsonl", "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    print(f"items rows: {len(items)}, result rows: {len(rows)}")


if __name__ == "__main__":
    make()