# Interface Contracts

These schemas are the agreement between A (data), B (evaluation) and C (analysis). Agree on them at Gate G0. Change them only with all three people's consent.

> **Status (Day 1 inspection complete in `data/interim/schema_report.md`):** UrduMMLU field names and option counts have been inspected on the local source (`data/raw/urdummlu.json`, 26,431 records). Source has 4-option and 5-option items; answer values include `E` (42 records). Update/application to the frozen project dataset requires team agreement and Role A ownership where applicable.

## 1. Dataset file (long format, frozen at G2)

`data/processed/items_v1.jsonl`: one JSON object per **(item, condition)**.

```json
{
  "item_id": "umm-0001",
  "source_row": "<identifier of the row in UrduMMLU, preserved as a string>",
  "domain": "<one of the 5 UrduMMLU domains>",
  "subject": "<UrduMMLU subdomain/subject>",
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
- `options` keep their order across conditions. Option letters shown to the model (A, B, C, D, E as applicable) are always Latin.
- Both `question` and every `options` entry are transformed; the words and word order stay the same across RU-P, RU-R and RU-X.
- Number of options: **4 or 5** per item (do not force all records to 4 options). If an item has option `E`, `gold` and valid parsed answers may be `E`.

### Source mapping (from `data/interim/schema_report.md`)

| Our field | UrduMMLU field | Notes |
|---|---|---|
| `source_row` | `id` | Preserve source identifier as a string in output if required by the contract. |
| `domain` | `domain` | Source inspection shows 5 domains. |
| `subject` | `subdomain` | Source calls this `subdomain` (26 unique values observed). |
| `question` | `question` | Original Urdu question stem. |
| `options` | `options` | Preserve option order; source may use keyed object A–E. |
| `gold` | `correct_key` | Verify answer key exists in the item's options; values observed include A–E. |

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
  "parsed_answer": "A | B | C | D | E | null",
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
- Retry rule: a row with a non-null `error` is retried on resume; the **last row for a key** `(model_slug, item_id, condition, repeat)` is authoritative; invalid answers with no error (`error: null`, `valid: false`) are never retried.
- `results/RUN_LOG.md` is updated only by the runner for real runs.

### Frozen items marker (G2 / non-NU real runs)

`data/processed/FROZEN.md` must contain a case-insensitive line of the form:

```text
items_v1.jsonl sha256: <64 hex chars>
```

The hash is computed from the UTF-8 text of `items_v1.jsonl` after normalizing CRLF line endings to LF (same normalization as the runner/freeze-hash helper). Other text in `FROZEN.md` is allowed. Non-NU real runs require the marker/hash to match; NU runs and mock runs are exempt as documented by the runner.

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
