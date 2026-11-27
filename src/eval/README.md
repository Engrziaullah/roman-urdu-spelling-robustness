# Evaluation runner

Run commands from the repository root with the project's Python 3.10 environment.
The runner reads JSONL items and writes one result row per request to the configured
`results/raw/<model_slug>/` directory. Every input and output file is UTF-8; JSONL
keeps Urdu readable. Mock output must use a temporary directory and never belongs
in `results/raw/`.

## Freeze hash (FROZEN.md line)

For non-NU real runs, `data/processed/FROZEN.md` must contain the exact hash line
for the frozen items file (UTF-8 text, CRLF normalized to LF, same as the runner):

```powershell
python -m src.eval.freeze_hash data/processed/items_v1.jsonl
```

To hash a committed git object without relying on working-tree line endings or
PowerShell text pipelines, read bytes in binary mode via git (no shell pipe):

```powershell
python -m src.eval.freeze_hash --git-ref origin/main data/processed/items_v1.jsonl
```

Output format (exact): `items_v1.jsonl sha256: <64 hex chars>`.

**PowerShell pitfall (hashing):** do not compute/compare hashes through PowerShell
pipes such as `git show ... | python ...` or by capturing output with `Out-String`,
because Windows PowerShell 5.1 can re-encode UTF-8/Urdu bytes and produce a wrong
hash. Compute hashes in Python using binary reads
(`Path.read_bytes()` / `open(..., 'rb')`) or `subprocess.run(..., capture_output=True).stdout`,
or use `python -m src.eval.freeze_hash [--git-ref <ref>] <file>`.

## Dry-run

A dry-run validates the selected items and prints the planned request count. It
does not read `.env`, require completed model strings/limits, contact a provider,
or write results:

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --max-items 20 --dry-run
```

`configs/models.yaml` must contain the selected slug. `TODO` values remain for the
human owner to fill from official provider pages before a real run.

## Twenty-item smoke test

This is a **real provider run** and consumes API quota. After filling the model's
official settings and adding its key to the local `.env`, run:

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --max-items 20 --purpose smoke
```

`scripts/run_nu.ps1` performs the recommended gate automatically: it checks that
`.env` is git-ignored, runs the Groq model-existence check, executes the smoke in
a temporary folder outside `results/raw/`, and stops before the full NU run if
the gate fails. Smoke gate (after retries): all 20 requests must end with an
answer (`error_count == 0`, no provider-error rows), invalid-answer rate among
answered requests must be <= 5%, no answer may be empty, and every recorded
`model_string` must equal the configured one. Provider-error rows are excluded
from the invalid-answer rate and reported separately.

The 20 saved rows use the normal cache key. A subsequent full NU run skips these
same item/condition/repeat keys; they remain valid part of the full results.
If the smoke gate fails, diagnose from the smoke JSONL rows: for
reasoning-capable models (including `qwen/qwen3.8-27b`), a common cause is
truncated answers from an insufficient output-token budget. Raise **only
model-1** `max_output_tokens` in `configs/models.yaml` (and use a
`reasoning_effort` option only when the provider's official documentation
confirms it). Retry at most 3 smoke attempts, each in a fresh temporary folder,
then stop and report if the gate still fails.

## Full NU run, per model

Run the command once for each configured model slug:

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
python -m src.eval.run --model-slug model-2 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
python -m src.eval.run --model-slug model-3 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
```

Rows go to `results/raw/<model_slug>/<run_id>.jsonl`. Real runs append a summary
to `results/RUN_LOG.md`; mock and dry runs do not.

## Full main run (all conditions, after freeze)

After `data/processed/items_v1.jsonl` and `data/processed/FROZEN.md` exist and the
FROZEN hash matches, run per model (exact command pattern):

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_v1.jsonl --conditions NU,RU-P,RU-R,RU-X,RT --purpose main
```

Repeat for `model-2` and `model-3` when their configs/keys are ready. `--noise-subset`
cannot be combined with `--max-items`.

## Resume after interruption

Rerun the same command with the same model slug, input, conditions, and repeat
number. The cache key is `(model_slug, item_id, condition, repeat)`, independent
of `purpose` and `run_id`. Existing rows are appended, never overwritten; a new
repeat creates a separate row. The latest appended row for a key is authoritative.
A latest row with an error is retried on resume and appended as another row; a
latest row with `error: null` is skipped. Older attempts are retained, and result
checking distinguishes retry history from duplicate successful requests.

Rate-limit handling (real runs): on HTTP 429/503 the runner reads `retry-after`
and rate-limit headers when present. If the wait is short (<= 120 seconds), it
sleeps `wait + 1` second and retries the same request (up to 5 wait-retries per
request). If daily limits are exhausted (e.g. request-remaining indicates RPD
exhaustion), or the required wait is longer than 120 seconds, the run stops
cleanly, computes/writes the earliest UTC resume time in the run summary, and
does not loop. Consecutive non-rate-limit final failures still stop at
`max_consecutive_failures`. Stopped runs write completed rows and a run-log
summary. Provider-error rows are counted as `error_count` and excluded from the
invalid-answer rate (invalid-answer rate is computed over answered requests
only).

## Noise-subset repeats

After confirming the data/config seed, create the 30-item list once:

```powershell
python -m src.eval.make_noise_subset --items data/processed/items_nu.jsonl
```

The selector stores six IDs per domain from `sample_rank <= 200` in
`configs/config.yaml`. It refuses to replace a non-empty ID list unless `--force`
is supplied.

Configured noise subset (`configs/config.yaml`): 30 item IDs, `repeats: 3`. To run
the noise repeats for one model (all 5 conditions), use the same command; the cache
skips completed keys, so rerunning resumes and fills any missing repeats (including
repeats 2 and 3 on the 30 noise IDs if repeat 1 is already present). `--noise-subset`
sets repeats from config (CLI `--repeats` is not used in this mode):

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_v1.jsonl --conditions NU,RU-P,RU-R,RU-X,RT --noise-subset
```

Non-NU real runs require `data/processed/FROZEN.md` to contain a case-insensitive
line of this form (other text in the file is allowed):

```text
items_v1.jsonl sha256: <64 hex chars>
```

The runner hashes the UTF-8 text supplied by `--items` after replacing CRLF with
LF and refuses to run if the line is missing or the hash differs. NU runs and
mock runs are exempt. Mock runs do not contact providers.

## Planning and checking

The planner makes no network calls and prints `unknown` for unresolved rate
limits:

```powershell
python -m src.eval.plan_runs --items data/processed/items_nu.jsonl --conditions NU,RU-P,RU-R,RU-X,RT
```

After collection, inspect Gate G3 results without modifying any result files:

```powershell
python -m src.eval.check_results --results-dir results/raw --items data/processed/items_v1.jsonl
```

The checker reports all attempt rows and duplicate keys. A duplicate is treated
as retry history only when each earlier row for that key has an error and the
latest row succeeds; it remains visible in the report but is not a Gate G3
failure. Missing combinations and invalid rates use the latest row per key.
Unresolved errors, other duplicate keys, schema/answer problems, multiple model
strings, and invalid rates above 5 percent make the checker exit nonzero.


## Rate-limit probing

`scripts/probe_limits.py` (reads the Groq key from environment/`.env`, never
prints keys or Authorization/request headers) performs one `GET /openai/v1/models`
and one tiny chat-completion request per target (model-1, helper, and up to 3
other chat-capable models from the list). It prints only: model string, HTTP
status, `retry-after` (if present), numeric rate-limit headers (limit/remaining/
reset for requests and tokens, if present), and prompt/completion token counts
from response `usage`. Use it to collect header-verified limits and estimate
effective rate/days; real per-request token usage for NU prompts may differ from
the tiny probe.

## 403 troubleshooting (Groq/provider access)

If a real Groq smoke/run fails with HTTP 403 while list-models/auth checks look
healthy, run the diagnosis script (reads key from environment/`.env`, never prints
keys or Authorization headers). It sends one tiny chat-completion request per
variant (max 8 output tokens) and prints only variant name, HTTP status, selected
error-body fields (`message`/`type`/`code`, truncated) or a short non-JSON prefix,
and `server`/`cf-ray` headers when present:

```powershell
python scripts/diagnose_groq.py --models configs/models.yaml
```

Variants: (a) model-1 with runner headers, (b) model-1 with an explicit
browser-like `User-Agent`, (c) helper with runner headers, (d) one other
chat-capable model from Groq list-models (not model-1/helper).

Outcome guide:
- **(b) 200 and (a) 403** (e.g. Cloudflare `error code: 1010`): default Python
  `User-Agent` is blocked at the edge. Fix: send a fixed, honest `User-Agent`
  (for example `roman-urdu-spelling-robustness/1.0`) on all provider requests in
  `src/eval/providers.py`, rerun diagnosis to confirm 200, then continue.
- **Model/terms/access-specific 403** (message indicates terms not accepted or
  model/org access blocked on specific models): human action in Groq console may
  be required. Test a few other listed chat models (one tiny request each) and
  report statuses/families; do not change `configs/models.yaml` without explicit
  approval.
- **Every variant 403 with same key/org/region message**: stop and report exact
  message fields; requires human fix (key, org, or region). Never print keys.


## Fresh-clone test procedure (dry-run, no API keys/results)

Run from a clean clone in a temporary location (Windows PowerShell example):

```powershell
git clone <repo-url> roman-urdu-spelling-robustness-fresh
cd roman-urdu-spelling-robustness-fresh
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m pytest -q
python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --max-items 20 --dry-run
python -m src.eval.plan_runs --items data/processed/items_nu.jsonl --conditions NU,RU-P,RU-R,RU-X,RT
python -m src.eval.check_results --results-dir results/raw --items data/processed/items_nu.jsonl --conditions NU
```

Notes: dry-run and planner make no network calls. `check_results` on an empty/missing
results set will report missing combinations (expected before real runs). Real provider
runs require filled model configs, keys in local `.env` (never committed), and gate/freeze
conditions described above.

## Answer parsing and provider references

The parser accepts a case-insensitive, standalone valid option letter. Formatting
punctuation is allowed (`B`, `B)`, `**B**`, `Answer: B`, or `The answer is B.`).
If the response contains no valid letter or more than one distinct valid letter,
it is invalid. Repeated occurrences of the same valid letter are accepted.
Invalid answers remain in the JSONL results and count toward the invalid rate.
Prompt letters are generated from each item's option count, including `E` for a
five-option item.

Provider adapters are based on these provider request references:

- Gemini `generateContent`: <https://ai.google.dev/api/generate-content/generate-content>
- Groq Chat Completions: <https://console.groq.com/docs/api-reference#chat-create>
- OpenRouter API reference: <https://openrouter.ai/docs/api-reference/overview>
