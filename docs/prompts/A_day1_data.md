# Role A: Data (Sudais Khan): Day 1 tasks

Paste `00_SESSION_START.md` first. Then paste **one task at a time** from this file. Branch names: `a/<topic>`.
You own: `src/data/`, `tests/data/`, `data/`, `docs/RULES.md`.
Do NOT import code from `src/eval/` or `src/analysis/`. Read `configs/*.yaml` directly with PyYAML if you need settings.

Day 1 goal for Role A (Gate G1): `data/processed/items_nu.jsonl` committed (500 items, seed recorded, nested 200-item subset marked)
and an RU-P draft for all 500 items.

---

## Task A1: Inspect the real UrduMMLU schema

Context: `docs/CONTRACTS.md` has a "Source mapping" table marked TBD. Field names and the number of options per item have NOT been verified.

Do:
1. Write `src/data/inspect_schema.py` that loads the dataset `MBZUAI/UrduMMLU` from Hugging Face (use the `datasets` library; save any download under `data/raw/`, which is git-ignored).
2. Print and save to `data/interim/schema_report.md`: dataset revision/commit, available splits and sizes, every column with dtype and 3 example values (truncate long text),
   how the answer is stored (letter, index, or text), the number of options per item (distribution), how domain and subject are represented (are there exactly 5 domains?),
   any duplicate or empty items, and the license text on the dataset card.
3. Do NOT guess. If the dataset is not what the docs assume (not 4 options, no domain field, answer stored as text, etc.), say so clearly and propose how to map it.
4. Propose, as text only, the completed "Source mapping" table for `docs/CONTRACTS.md`. Do not edit `docs/CONTRACTS.md` yourself; I will raise a PR so all three people can agree.

Tests: a small test that the report generator works on a tiny local fixture (no network).
Stop after this task and report. Wait for my approval before A2.

---

## Task A2: Stratified sample of 500 items with nested 200-item subset

Context: `docs/PLAN.md` (A, Day 1), `docs/CONTRACTS.md` section 1, `docs/RULES.md` section 2. Use the real schema found in A1.

Requirements:
1. `src/data/sample.py`, arguments: `--seed` (or read `seed` from `configs/config.yaml`; if it is `TODO`, stop and ask), `--per-domain 100`, `--out data/processed/items_nu.jsonl`.
2. **Exclusion filter** (documented and measurable): exclude items dominated by formulas, symbols or English terms. Propose a concrete rule (for example the share of characters that are not Urdu letters
   or spaces above a threshold, plus detection of math notation) and show me the proposal and threshold before applying it. Log the count excluded by each reason.
3. Stratify by domain: exactly 100 items per domain after exclusions. Shuffle within each domain with the seed.
   **If any domain has fewer than 100 eligible items, STOP and tell me; do not silently relax the filter or take items from another domain.**
4. `sample_rank` (1 to 500): within each domain give `domain_rank` 1..100 from the shuffled order; then sort by (`domain_rank`, domain name) and number 1..500.
   Result: ranks 1 to 200 contain exactly 40 items per domain (the nested 200-item fallback subset). Verify this with a test.
5. `item_id` is `umm-` plus the zero-padded `sample_rank` (for example `umm-0001`). `gold` is a letter and options keep their order.
6. Output `data/processed/items_nu.jsonl`: one object per item with exactly the CONTRACTS fields, `condition: "NU"`, `verified: true` (untouched source text), `notes: ""`.
   (The 2,500-row `items_v1.jsonl` is built later at the freeze, not now.)
7. Write `data/interim/sampling_report.md`: seed, dataset revision, counts per domain and subject, exclusions by reason, the final rank structure, the date.
8. Never modify question or option text.

Tests: same seed gives the same file; 500 unique `item_id`; 100 per domain; first 200 ranks have 40 per domain; `gold` in the option range; no empty text.
Report and wait for approval.

---

## Task A3: RU-P draft with a non-evaluated LLM (pilot first)

Context: `docs/RULES.md` sections 3, 4 and 9. **The RU-P conventions (section 4.2) are PROPOSED defaults and still need native confirmation: run a 30-item pilot first.**

Requirements:
1. `src/data/draft_rup.py`, arguments: `--pilot N` (default off), `--in data/processed/items_nu.jsonl`, `--out data/interim/rup_draft.jsonl`.
2. The drafting model comes from `configs/models.yaml` under `helper:`. **Refuse to run** if it is `TODO`, or if its `model_string` or provider/model matches any entry in `evaluated_models`. Read the API key from the environment only.
3. Transliterate the question and **every option** into Roman Urdu following RU-P conventions. The prompt to the model must state: transliterate only; do not translate, correct, summarise or reword;
   keep digits, option labels, formulas, units, URLs and Latin-script words unchanged; use the spelling in the lexicon when a word is listed; return structured JSON only.
4. Look up `src/data/rules/ru_p_lexicon.csv` (columns `urdu_word, ru_p, note`) before calling the model so the same word gets the same spelling. Create the file with headers and no invented entries.
5. Cache every call so reruns do not repeat requests; use retries with backoff; validate the JSON; flag malformed outputs instead of dropping them.
6. After drafting, run invariant checks from `docs/RULES.md` section 3 as far as they can be checked at this stage: protected tokens preserved, token count of each field unchanged compared with NU (flag mismatches, do not fix), no empty fields.
7. Output `data/interim/rup_draft.jsonl` in the CONTRACTS item format with `condition: "RU-P"`, `verified: false`, and a `notes` field for any flag. The model's output is a DRAFT: never mark it verified.
8. Print a short summary: items drafted, flagged items, cache hits, failures. Record the exact prompt text and model string used in `data/interim/rup_prompt.md`.

Tests: JSON validation, refusal when the helper equals an evaluated model, lexicon lookup, protected-token check (all with a mock model; no network).
Run the pilot on 30 items only, show me the results, and **stop**. I will have native readers review them and correct the conventions before the full run.

---

## Task A4: Rule files skeleton (no invented rules)

Create (headers only, plus at most clearly marked `EXAMPLE` rows copied from `docs/RULES.md`): `src/data/rules/ru_r_wordmap.csv`, `src/data/rules/ru_r_rules.csv`, `src/data/rules/ru_x_rules.csv`, `src/data/rules/protected_patterns.csv`.
Column formats are in `docs/RULES.md` sections 5.3 and 6.2. Do not add rules from your own knowledge: rules are decided by humans after review.
Add a short `src/data/rules/README.md` explaining the format. This prepares Day 2 (rule engines).

---

## Human tasks for Role A today (not for the agent)

- Fill the G0 decisions in `docs/RULES.md` section 1 with the team.
- Native review of the 30-item RU-P pilot; update conventions C1 to C9 (section 4.2) and the lexicon.
- Commit `items_nu.jsonl` early so Role B can start NU runs.

## Gate G1 checklist (Role A part)
- [ ] `items_nu.jsonl`: 500 items, seed and dataset revision recorded, nested 200 subset verified by a test.
- [ ] `schema_report.md` and `sampling_report.md` committed; Source mapping proposed to the team.
- [ ] RU-P draft exists for all 500 items (every item flagged `verified: false`).
- [ ] Tests pass; PR opened and reviewed by someone else.
