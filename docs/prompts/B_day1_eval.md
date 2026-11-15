# Role B: Evaluation and repo lead (Zia Ullah): Day 1 tasks

Paste `00_SESSION_START.md` first. Then paste **one task at a time**. Branch names: `b/<topic>`.
You own: `src/eval/`, `tests/eval/`, `configs/`, `results/raw/`, `results/RUN_LOG.md`.
Do NOT import code from `src/data/` or `src/analysis/`. Read items only through the CONTRACTS file format.

Day 1 goal for Role B (Gate G1): a runner that is tested on mock items and completes NU for at least one real model with parsed answers,
using the real `items_nu.jsonl` as soon as Role A commits it.

---

## Task B1: Config loading and run logging

Context: `docs/CONTRACTS.md` sections 2 and 4, `configs/*.yaml`.
1. `src/eval/config.py`: load `configs/config.yaml` and `configs/models.yaml`; load API keys from environment variables (python-dotenv for a local `.env`) using the variable named in `api_key_env`; never print a key.
2. If a required field is still `TODO`, raise a clear error that names the field and file. Do NOT fill in model names, limits or endpoints yourself.
3. `src/eval/runlog.py`: append one JSON line per request to `results/raw/<model_slug>/<run_id>.jsonl` with exactly the CONTRACTS section 2 fields; append a session summary to `results/RUN_LOG.md`
   (date UTC, run_id, model_slug, model_string, calls made, cache hits, errors).
4. Tests in `tests/eval/`: config loads from a fixture, missing key error, TODO error, log line has all required fields.

---

## Task B2: Prompt builder and answer parser

Context: `configs/prompt.txt` has the placeholders `{letters}`, `{question}`, `{options}`. The number of options per item is NOT assumed to be 4 (Role A is verifying it).
1. `src/eval/prompt.py`: build the prompt from `configs/prompt.txt` for an item and a condition. Options are labelled with Latin letters A, B, C, ... in order (as `A) text`, one per line). `{letters}` lists the valid letters (for example `A, B, C, or D`).
   Return the prompt and its SHA-256 `prompt_hash`. The template text must not be edited by code.
2. `src/eval/parse.py`: parse a model response into `parsed_answer` (A, B, C, D or null) and `valid`.
   Rules (write them in the module docstring and in `src/eval/README.md`): case-insensitive standalone letter that is one of the valid letters; accept forms such as `B`, `B)`, `**B**`, `Answer: B`, `The answer is B.`;
   if the response contains more than one different valid letter, or none, mark it invalid. Invalid answers are kept and counted, never dropped.
3. Tests with at least 25 tricky responses (empty, extra text, multiple letters, lowercase, letter inside a word, "A or B", Urdu text, markdown).

---

## Task B3: Provider adapters and resumable runner

Context: `docs/PLAN.md` (B, Day 1), `docs/CONTRACTS.md` section 2, `docs/RULES.md` is irrelevant here.
1. `src/eval/providers.py`: one interface `complete(prompt, model_cfg) -> text, latency_s, returned_model_string_or_None`. Adapters for the providers named in `configs/models.yaml`
   (e.g. gemini, groq, openrouter). Use the providers' **official, current documentation** for endpoints and request format; if you cannot confirm something, say so and leave a clear TODO.
   Do not hard-code model names. Include a `mock` provider for tests that returns deterministic answers.
2. `src/eval/run.py` with arguments: `--model-slug`, `--items` (path to a CONTRACTS item file), `--conditions` (default `NU`), `--repeats` (default 1), `--purpose` (for example `nu`, `noise`, `main`), `--max-items`, `--mock`, `--dry-run`.
   `run_id` follows `YYYY-MM-DD_<purpose>_r<repeat>`.
3. **Resumable cache:** before each request check whether `(model_slug, item_id, condition, repeat)` already exists in `results/raw/<model_slug>/*.jsonl`; if so skip it. Never overwrite a finished request;
   a repeat is a new row with a different `repeat` value.
4. Respect `requests_per_minute`; exponential backoff on rate limits and server errors; stop after N consecutive failures and report. Log errors in the `error` field and keep going where safe.
5. **Condition guard:** NU may run on `items_nu.jsonl`. Any condition other than NU (RU-P, RU-R, RU-X, RT) must refuse to run unless `data/processed/FROZEN.md` exists
   (real runs on unfrozen variants are not allowed; the `--mock` flag is exempt).
6. Settings from config: temperature 0 and the max output tokens from `configs/config.yaml`. Never print API keys.
7. Tests with the mock provider: resume after interruption does not repeat requests, rows follow the schema, the condition guard blocks non-NU runs, invalid answers are recorded.

---

## Task B4: Mock end-to-end test on 10 items

Create `tests/fixtures/mock_items_nu.jsonl` (10 invented items clearly marked as mock, in the CONTRACTS format) and run the whole pipeline with `--mock`.
Mock output must never be written to `results/raw/`: use a temporary directory. Report the invalid rate, latency fields and any schema problem. Mock data is for tests only.

---

## Task B5: First real NU run (only after Role A commits `items_nu.jsonl` and `configs/models.yaml` is filled)

1. Smoke test first: 20 items, the NU condition, one model. Check the parse rate and the rate-limit behaviour. Stop and report if the invalid rate is above 5%.
2. Then run NU for the whole file, one model at a time, in the background with the resumable cache. Report calls made, errors, invalid rate and the `model_string` actually used.
3. Update `results/RUN_LOG.md`. Do not retry selectively or hide failures.

---

## Human tasks for Role B today (not for the agent)

- Repo hygiene at G0: add `AGENTS.md`, real `.gitignore` (with the dot), `.env.example`, `requirements.txt`, `configs/`; fix the README clone URL (`robustness`); protect `main`; create Issues per task.
- Fill `configs/models.yaml` from each provider's current free-tier page (model strings, per-minute and per-day limits, the date checked, who runs which model).
- Fill `configs/config.yaml`: seed, `max_output_tokens`.
- Help check that every person's API key works.

## Gate G1 checklist (Role B part)
- [ ] Runner, prompt builder, parser and cache pass tests on mock items.
- [ ] NU completed for at least one real model with parsed answers and an invalid rate below 5%.
- [ ] `results/RUN_LOG.md` has the model string and UTC date for each run.
- [ ] PRs reviewed by someone else.
