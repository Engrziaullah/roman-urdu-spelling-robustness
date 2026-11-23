# NU and full-condition run schedule (planned, probe-informed)

Generated from `python -m src.eval.plan_runs --items data\processed\items_nu.jsonl --conditions NU,RU-P,RU-R,RU-X,RT` on 2026-11-24 (local). This is an estimate only (no full provider benchmark).

## Probe evidence (Groq, 2026-11-24, `scripts/probe_limits.py`, 1 tiny chat request/model, max 8 completion tokens)

Headers observed (official names per Groq rate-limits docs: `retry-after` on 429; `x-ratelimit-limit-requests`/`x-ratelimit-remaining-requests`/`x-ratelimit-reset-requests` as RPD; `x-ratelimit-limit-tokens`/`x-ratelimit-remaining-tokens`/`x-ratelimit-reset-tokens` as TPM). Source: live probe headers on 2026-11-24.

| model | http_status | RPD limit/remain/reset | TPM limit/remain/reset | retry-after | prompt_tokens | completion_tokens | total_tokens (probe) |
|---|---:|---|---|---:|---:|---:|---:|
| `qwen/qwen3.8-27b` (model-1) | 200 | 1000 / 999 / 1m26.4s | 8000 / 7945 / 412ms | - | 47 | 8 | 55 |
| `openai/gpt-oss-120b` (helper) | 200 | 1000 / 999 / 1m26.4s | 8000 / 7914 / 644ms | - | 78 | 8 | 86 |
| `openai/gpt-oss-20b` | 200 | 1000 / 999 / 1m26.4s | 8000 / 7914 / 644ms | - | 78 | 8 | 86 |
| `allam-2-7b` | 200 | 7000 / 6999 / 12.342s | 6000 / 5978 / 220ms | - | 14 | 3 | 17 |

`models_list_http_status`: 200. Selected other chat models from list-models (excluding model-1/helper): `openai/gpt-oss-20b`, `allam-2-7b` (only 2 matched filter).

## Model-1 effective rate and 2,800-request estimate

- Configured (`configs/models.yaml`, checked 2026-11-19): `requests_per_minute: 20` (self-imposed throttle), `requests_per_day: 1000`. Probe-verified header limits (2026-11-24): RPD 1000 (`x-ratelimit-limit-requests`), TPM 8000 (`x-ratelimit-limit-tokens`).
- Effective sustainable RPM (formula): `min(configured RPM, TPM_limit / avg_total_tokens_per_request)`.
- Probe tiny-request usage for model-1: 55 total tokens (47 prompt + 8 completion). **Real NU per-request token usage is unknown** (result schema has no token fields; NU prompts/answers are longer and `qwen/qwen3.8-27b` is a reasoning-capable model), so the TPM term cannot be concluded from the probe alone. Prior real smoke on 2026-11-23 stopped with HTTP 429 after 4 answered requests + 1 error in the old runner semantics, consistent with short-window/token pressure, but not a measured tokens/request value.
- Request-count estimate (RPD only): full pass 2,500 + noise extra 300 = **2,800 requests**. At 1,000 RPD this requires **>= 3 days** (e.g. 1,000 + 1,000 + 800), independent of TPM if TPM were sufficient.
- Practical implication: TPM/short-window limits may further constrain throughput or cause waits/stops; runner now retries short 429/503 waits (<=120s, up to 5/request) and stops with UTC resume time on daily/long waits.

## Planner table

| model_slug | requests_per_minute | requests_per_day | full_pass_requests | noise_extra_requests | estimated_days |
|---|---:|---:|---:|---:|---:|
| model-1 | 20 (configured) | 1000 (probe/header-verified RPD) | 2500 | 300 | >= 3 (RPD-bound; TPM/real usage unknown) |
| model-2 | unknown | unknown | 2500 | 300 | unknown |
| model-3 | unknown | unknown | 2500 | 300 | unknown |

Notes:
- Full pass: 500 unique items × 5 conditions = 2500 requests per model.
- Noise extra: 30 items × 5 conditions × (3 repeats - 1) = 300 additional requests per model.
- Model-2 and model-3 remain **unknown** until their official limits/strings are filled in `configs/models.yaml`.
- Actual runs must use the agreed items file and respect gate checks (items hash sidecar, FROZEN.md for non-NU real runs, quotas/rate limits, and clean resume handling).
