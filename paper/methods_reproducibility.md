# Methods and Reproducibility (Draft)

> Status: draft based only on repository state as of 2026-11-24. All values that depend on real evaluation runs are marked **[TBD after runs]**.

## 1. Study overview
- Project: Spelling Before Script / orthographic robustness of LLMs on Roman Urdu knowledge MCQs (`README.md`).
- Primary outcome: answer instability (flip rate) across Roman Urdu spelling variants; NU vs Roman Urdu accuracy gap is secondary/confirmatory (`README.md`, `docs/PLAN.md`).
- Conditions: NU, RU-P, RU-R, RU-X, RT (5 matched versions per item; `docs/RULES.md`, `docs/CONTRACTS.md`).
- Planned sample: 500 UrduMMLU items × 5 conditions = 2,500 item-condition rows (target, per `docs/CONTRACTS.md`/`README.md`).
- Current processed NU file: `data/processed/items_nu.jsonl` (500 rows observed on `origin/main` at hash `6ca8f229586a1c5c1c551166e7a6cdd36e66f2f22cf314c0f8a2cb3c4741b74d`, normalized CRLF→LF SHA-256; 100/domain, ranks 1–500 contiguous, first 200 = 40/domain, 4 options each). Final frozen multi-condition file `data/processed/items_v1.jsonl` and `data/processed/FROZEN.md`: **[TBD after freeze/G2]**.

## 2. Source data
- Source dataset: UrduMMLU (MBZUAI/UrduMMLU), as recorded in `README.md` and `data/interim/schema_report.md`.
- License/card metadata noted in repo: CC BY 4.0 listed in schema report (`license: cc-by-4.0`, re-verify on dataset card before release) — **[TBD: release-time verification]**.
- Local raw files present: `data/raw/urdummlu.json`, `data/raw/stats.json` (per `README.md`).
- Schema inspection/mapping basis: `data/interim/schema_report.md` (e.g. `id`→`source_row`, `domain`, `subdomain`→`subject`, `question`, `options`, `correct_key`→`gold`; source may include 4–5 options and answer values A–E observed in source).

## 3. Item/condition format
- Contract: `docs/CONTRACTS.md` (one JSON object per item-condition; fields include `item_id`, `source_row`, `domain`, `subject`, `condition`, `question`, `options`, `gold`, `verified`, `sample_rank`, `notes`).
- Options/gold: option letters shown to model are Latin; order preserved across conditions; both question and options transformed for RU variants with words/order held constant (per contract/rules intent). Exact handling of 4 vs 5 options and parsed answer including `E`: **[TBD pending shared CONTRACTS update/approval]**.

## 4. Evaluation setup
- Models: up to 3–4 from different families via free API tiers (`README.md`, `docs/PLAN.md`). Configured/evaluated entries in `configs/models.yaml`:
  - `model-1` (Groq, `qwen/qwen3.8-27b`, checked 2026-11-19, RPM 20 self-imposed, RPD 1000, `max_output_tokens` 4096, `reasoning_effort` low). Helper (RU-P draft/RT, not evaluated): Groq `openai/gpt-oss-120b`.
  - `model-2` (Gemini): **[TBD]**.
  - `model-3` (OpenRouter): **[TBD]**.
- Prompt: single English template `configs/prompt.txt` for all conditions, zero-shot, temperature 0 (`configs/config.yaml`, `docs/CONTRACTS.md`).
- Key settings (`configs/config.yaml`): `seed: 42`, `temperature: 0`, `max_output_tokens: 16` (global default; per-model overrides supported in config/loader), timeout/retry/backoff/consecutive-failure limits configured. Noise subset: 30 items, 3 repeats, fixed IDs in config.
- Runner implementation: `src/eval/run.py`, providers `src/eval/providers.py`, config loader `src/eval/config.py`, prompt `src/eval/prompt.py`, parser `src/eval/parse.py`, run log `src/eval/runlog.py`.

## 5. Execution protocol (planned/implemented)
- Commands (from repo root): dry-run `python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --max-items 20 --dry-run`; smoke (real) `--max-items 20 --purpose smoke`; full NU `--conditions NU --purpose nu`; full main after freeze `--items data/processed/items_v1.jsonl --conditions NU,RU-P,RU-R,RU-X,RT --purpose main`; noise `--noise-subset` (see `src/eval/README.md`, `scripts/run_nu.ps1`).
- Caching/resume: key `(model_slug, item_id, condition, repeat)`; append-only result rows; latest row authoritative; latest row with non-null error retried on resume; rows with `error: null` not retried (implementation behavior; retry-rule confirmation requested: PR #22 comment https://github.com/Engrziaullah/roman-urdu-spelling-robustness/pull/22#issuecomment-7112322552). **[TBD: team confirmation]**
- Hash guards: items hash sidecar `ITEMS_SHA256.txt` in model output dir (runner); freeze hash line `items_v1.jsonl sha256: <64 hex>` required for non-NU real runs (`src/eval/freeze_hash.py`, `src/eval/run.py`, `src/eval/README.md`).
- Planning/checking: `python -m src.eval.plan_runs ...`, `python -m src.eval.check_results ...` (no network). Current schedule estimate: `src/eval/RUN_SCHEDULE.md` (model-1 2800 requests, ~3 days at configured limits; model-2/3 unknown).

## 6. Results and logging (to be produced)
- Raw results: `results/raw/<model_slug>/*.jsonl` per `docs/CONTRACTS.md` schema. **[TBD after runs]**
- Run log: `results/RUN_LOG.md` updated by runner for real runs. Current state: no real runs recorded. **[TBD after runs]**
- Validation: `src/eval/check_results.py` (Gate G3 checks). **[TBD after runs]**
- Analysis outputs: `results/tables/`, `results/figures/` (owned by Role C). **[TBD]**

## 7. Integrity and limitations
- No invented results/numbers; mock data is for tests only and excluded from `results/raw/`.
- Frozen data treated as read-only after freeze marker; version changes must be recorded (`AGENTS.md`, `docs/CONTRACTS.md`).
- Known limitations as stated in `README.md` (researcher-defined spelling operations, imperfect RT, training-data contamination possibility, sample-size/CI limits, tokenizer proxy for closed models). Effect sizes/CIs/flip rates/invalid rates: **[TBD after runs]**.

## 8. Reproduction checklist (current)
- `python -m pytest -q` (verified in this environment on 2026-11-24: **198 passed, 3 subtests passed, 6 warnings** after merge to `origin/main` state `6b18142`).
- Fresh-clone dry-run procedure documented in `src/eval/README.md`.
- Real-run reproduction requires: final/frozen items, filled model configs, local `.env` keys (never committed), provider availability/quota, and gate compliance. **[TBD after runs]**
