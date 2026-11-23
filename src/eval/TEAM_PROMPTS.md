# Team prompts for model-2 and model-3 NU runs (Role B handoff)

These prompts are for Sudais (model-2, Gemini, `GOOGLE_API_KEY`) and Younas (model-3, OpenRouter, `OPENROUTER_API_KEY`). They are copy-paste prompts for Copilot/assistant use in this repo. **Never print, copy, commit, or ask to see `.env` or any key.** Scripts load keys from the repo-root `.env` themselves. Do not merge PRs, push to `main`, run on non-NU conditions, or create `items_v1.jsonl`/`FROZEN.md`.

## Shared prerequisites and rules

1. Work on your own Role B-safe branch/workflow as agreed; edit only allowed files for your role/task.
2. Ensure repo-root `.env` exists locally, contains your own provider key, and is git-ignored (`git check-ignore .env` must succeed). Do not read or display `.env`.
3. Use `configs/models.yaml` and `configs/config.yaml` as source of truth. Only use a model string that exists in official provider model listings and is configured for your slug.
4. `data/processed/items_nu.jsonl` must be the agreed/final NU file (confirm with Role A/Zia before full run if there is any ambiguity).
5. Run `python -m pytest -q` before claiming a change works.
6. `results/RUN_LOG.md` must be updated only by the runner (`src.eval.run`), never by hand.
7. Smoke test output for real smoke runs must go to a temporary folder outside `results/raw` so failed smoke rows never enter final data. Only the full NU run writes to `results/raw`.
8. If a rate limit or daily quota stops a run, stop cleanly, record it, state when it can resume (next UTC day/provider reset), and do not loop.

## Prompt for Sudais (model-2, Gemini)

```text
ROLE: Sudais Khan's assistant, Role B (Evaluation) tasks for model-2 ONLY. You may edit only scripts/, src/eval/, tests/eval/, configs/, results/raw/, and results/RUN_LOG.md (RUN_LOG only through the runner). Never edit src/data/, data/, docs/RULES.md, src/analysis/, or annotations/. Never read/open/print/copy/commit .env or any API key. Never merge PRs or push to main.

Goal: validate and run Gemini model-2 on NU using MY key (already in environment/.env, loaded by scripts). Do not make real network calls except: (1) provider list-models/model-existence metadata check, (2) a 20-item NU smoke test, (3) the full NU run only if every gate passes.

1) Baseline: read README.md, AGENTS.md, docs/PLAN.md, docs/CONTRACTS.md, src/eval/README.md, configs/models.yaml, configs/config.yaml, scripts/*; run `python -m pytest -q`.
2) Model-existence check (metadata, key from environment): confirm the configured model-2 `model_string` in configs/models.yaml exists in Gemini's official model listing/API response. Print only HTTP status and whether the configured string is present (no keys, no secrets). If not present, STOP and report.
3) Smoke test (20 NU, real, outside results/raw): run model-2 on first 20 NU items writing output to a temporary folder outside results/raw (not --mock for the real smoke). Pass criteria: invalid rate <= 5%, no empty answers, recorded model_string equals configured model_string. On failure STOP and print 3 sample raw outputs (never keys).
4) Full NU run (only if gates pass): gate checks before full run: smoke criteria passed; `data/processed/items_nu.jsonl` hash identical on origin/main and working tree after `git fetch`; no open PR touches `data/processed/`; model-existence check found configured string. Run full NU into `results/raw` (resumable). After run: `python -m src.eval.check_results --results-dir results\raw --items data\processed\items_nu.jsonl --conditions NU` and ensure RUN_LOG updated only by runner.
5) Report: smoke numbers (invalid rate, 3 sample raw outputs if failed else note pass, recorded vs configured model_string), full-run numbers, files written, any stop reason (quota/rate limit with resume time = next UTC day/reset), and what you could not verify.
```

## Prompt for Younas (model-3, OpenRouter)

```text
ROLE: Younas Khan's assistant, Role B (Evaluation) tasks for model-3 ONLY. You may edit only scripts/, src/eval/, tests/eval/, configs/, results/raw/, and results/RUN_LOG.md (RUN_LOG only through the runner). Never edit src/data/, data/, docs/RULES.md, src/analysis/, or annotations/. Never read/open/print/copy/commit .env or any API key. Never merge PRs or push to main.

Goal: validate and run OpenRouter model-3 on NU using MY key (already in environment/.env, loaded by scripts). Do not make real network calls except: (1) provider list-models/model-existence metadata check, (2) a 20-item NU smoke test, (3) the full NU run only if every gate passes.

1) Baseline: read README.md, AGENTS.md, docs/PLAN.md, docs/CONTRACTS.md, src/eval/README.md, configs/models.yaml, configs/config.yaml, scripts/*; run `python -m pytest -q`.
2) Model-existence check (metadata, key from environment): confirm the configured model-3 `model_string` in configs/models.yaml exists in OpenRouter's official models API/listing. Print only HTTP status and whether the configured string is present (no keys, no secrets). If not present, STOP and report.
3) Smoke test (20 NU, real, outside results/raw): run model-3 on first 20 NU items writing output to a temporary folder outside results/raw (not --mock for the real smoke). Pass criteria: invalid rate <= 5%, no empty answers, recorded model_string equals configured model_string. On failure STOP and print 3 sample raw outputs (never keys).
4) Full NU run (only if gates pass): gate checks before full run: smoke criteria passed; `data/processed/items_nu.jsonl` hash identical on origin/main and working tree after `git fetch`; no open PR touches `data/processed/`; model-existence check found configured string. Run full NU into `results/raw` (resumable). After run: `python -m src.eval.check_results --results-dir results\raw --items data\processed\items_nu.jsonl --conditions NU` and ensure RUN_LOG updated only by runner.
5) Report: smoke numbers (invalid rate, 3 sample raw outputs if failed else note pass, recorded vs configured model_string), full-run numbers, files written, any stop reason (quota/rate limit with resume time = next UTC day/reset), and what you could not verify. Confirm the retry rule with Younas/team before treating retry behavior as final.
```

## Candidate free models (official documentation required)

Requested: 3 candidate free models per provider from families different from model-1 (`qwen/qwen3.8-27b`, Qwen family) and the helper (`openai/gpt-oss-120b`, GPT-OSS/OpenAI open-weight helper family as configured). Fields required: exact string, limits, source URL, retrieval date. **Only include values taken from official documentation.**

**Status:** I could not fully confirm exact free-model strings, current free-tier/rate limits, and family suitability from official provider documentation in this session with sufficient certainty to avoid inventing values. The tables below are left as TODO and must be completed from official docs before selection/config changes.

### Gemini (Google AI) candidates

| # | Exact model string | Family (must differ from Qwen and GPT-OSS) | Limits (RPM/RPD/tokens/free tier, as documented) | Official source URL | Retrieval date | Notes |
|---|---|---|---|---|---|---|
| 1 | TODO | TODO | TODO | https://ai.google.dev/gemini-api/docs/models | TODO | Verify free-tier availability and limits in official pricing/docs before use. |
| 2 | TODO | TODO | TODO | https://ai.google.dev/gemini-api/docs/models | TODO | Verify model is not Qwen/GPT-OSS family and supports required API usage. |
| 3 | TODO | TODO | TODO | https://ai.google.dev/pricing | TODO | Confirm exact rate/token limits and any preview/deprecation constraints. |

### OpenRouter candidates

| # | Exact model string | Family (must differ from Qwen and GPT-OSS) | Limits (free tier/RPM/RPD/context/pricing, as documented) | Official source URL | Retrieval date | Notes |
|---|---|---|---|---|---|---|
| 1 | TODO | TODO | TODO | https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties | TODO | Confirm `:free`/free availability, provider limits, and model family from official model listing/docs. |
| 2 | TODO | TODO | TODO | https://openrouter.ai/docs/models | TODO | Verify exact string as accepted by OpenRouter API and current availability. |
| 3 | TODO | TODO | TODO | https://openrouter.ai/models | TODO | Cross-check limits/pricing in official API response/docs before use. |

**Note:** Do not treat catalog snapshots or third-party summaries as sufficient without confirming the exact model string and limits in official provider documentation/API responses. If a candidate is preview-only, deprecated, or family-ambiguous, do not select it until verified.
