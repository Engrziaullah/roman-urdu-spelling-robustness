# Interface Contracts

These schemas are the agreement between A (data), B (evaluation) and C (analysis). Agree on them at Gate G0. Change them only with all three people's consent.

> **Open item for Day 1 (Role A):** the UrduMMLU field names and the number of answer options have not been verified from the actual files yet. Inspect the downloaded data and update the "Source mapping" below before G0 is closed.

## 1. Dataset file (long format, frozen at G2)

`data/processed/items_v1.jsonl`: one JSON object per **(item, condition)**.

```json
{
  "item_id": "umm-0001",
  "source_row": "<identifier of the row in UrduMMLU, filled from the real schema>",
  "domain": "<one of the 5 UrduMMLU domains>",
  "subject": "<UrduMMLU subject>",
  "condition": "NU | RU-P | RU-R | RU-X | RT",
  "question": "<question stem in this condition's script/spelling>",
  "options": ["<option 1>", "<option 2>", "<option 3>", "<option 4>"],
  "gold": "A",
  "verified": true,
  "sample_rank": 1,
  "notes": ""
}
```

Rules:
- Exactly 500 distinct `item_id` values × 5 conditions = 2,500 rows.
- Items carry a `sample_rank` (1–500) so that nested subsets can be cut cleanly (see PLAN.md, fallback subset).
- `gold` is a letter and is **identical across all five conditions** of one item.
- `options` keep their order across conditions. Option letters shown to the model (A, B, C, D) are always Latin.
- Both `question` and every `options` entry are transformed; the words and word order stay the same across RU-P, RU-R and RU-X.
- Number of options: verify on Day 1 (4 is typical for MMLU-style sets but is **not** confirmed here).

### Source mapping (Role A fills in on Day 1)

| Our field | UrduMMLU field | Notes |
|---|---|---|
| `source_row` | _TBD_ | |
| `domain` | _TBD_ | |
| `subject` | _TBD_ | |
| `question` | _TBD_ | |
| `options` | _TBD_ | |
| `gold` | _TBD_ | |

## 2. Run result file

`results/raw/<model_slug>/<run_id>.jsonl`: one JSON object per request.

```json
{
  "run_id": "2026-11-16_noise_r1",
  "model_slug": "<short name>",
  "model_string": "<exact string sent to the provider>",
  "provider": "<provider name>",
  "date_utc": "2026-11-16T10:21:05Z",
  "item_id": "umm-0001",
  "condition": "RU-P",
  "repeat": 1,
  "prompt_hash": "<sha256 of the full prompt text>",
  "raw_output": "<model response as returned>",
  "parsed_answer": "A | B | C | D | null",
  "valid": true,
  "latency_s": 1.84,
  "error": null
}
```

Rules:
- Zero-shot, temperature 0, one English instruction template for all conditions (`configs/prompt.txt`).
- `valid=false` when the answer cannot be parsed to a letter; these are counted, not dropped.
- Never overwrite a finished request. A repeat is a new row with a different `repeat` value.
- `repeat` is 1 for main runs; the noise subset uses repeats 1–3.

## 3. Derived tables (written by C into `results/tables/`)

| File | One row per | Key columns |
|---|---|---|
| `accuracy.csv` | model × condition | n, accuracy, ci_low, ci_high, invalid_rate |
| `flips.csv` | model × item | answers per condition, flip_any, flip_pairs |
| `flip_rates.csv` | model × variant pair | flip_rate, ci_low, ci_high, noise_baseline |
| `rt_analysis.csv` | model × item | nu_rt_agree, flips_across_variants |
| `edit_distance.csv` | variant pair | mean_char_edit_distance |
| `errors.csv` | failing item | model, condition, category (RQ4) |

## 4. Config files (owned by B)

- `configs/models.yaml`: provider, `model_string`, rate limits (checked on the provider page on Day 1, with the date).
- `configs/prompt.txt`: the single prompt template.
- `configs/config.yaml`: seed, paths, repeat counts, noise-subset item IDs.
