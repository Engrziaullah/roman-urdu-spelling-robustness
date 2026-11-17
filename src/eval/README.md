# Evaluation runner

Run commands from the repository root with the project's Python 3.10 environment.
The runner reads JSONL items and writes one result row per request to the configured
`results/raw/<model_slug>/` directory. Every input and output file is UTF-8; JSONL
keeps Urdu readable. Mock output must use a temporary directory and never belongs
in `results/raw/`.

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

The 20 saved rows use the normal cache key. A subsequent full NU run skips these
same item/condition/repeat keys; they remain valid part of the full results.

## Full NU run, per model

Run the command once for each configured model slug:

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
python -m src.eval.run --model-slug model-2 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
python -m src.eval.run --model-slug model-3 --items data/processed/items_nu.jsonl --conditions NU --purpose nu
```

Rows go to `results/raw/<model_slug>/<run_id>.jsonl`. Real runs append a summary
to `results/RUN_LOG.md`; mock and dry runs do not.

## Resume after interruption

Rerun the same command with the same model slug, input, conditions, and repeat
number. The cache key is `(model_slug, item_id, condition, repeat)`, independent
of `purpose` and `run_id`. Existing rows are appended, never overwritten; a new
repeat creates a separate row. **Current behavior:** any matching row, including
one with a non-null `error`, is treated as cached and skipped. If the run contains
errors, review them before resuming; failed-row retry and duplicate-row selection
are pending agreement with the analysis owner because the result schema has no
attempt field.

HTTP 429 and the configured daily quota stop a real run cleanly. Consecutive
non-429 final failures also stop at `max_consecutive_failures`. A stopped run
writes its completed rows and a run-log summary. Under the current cache rule, a
saved error row is not retried on resume.

## Noise-subset repeats

After confirming the data/config seed, create the 30-item list once:

```powershell
python -m src.eval.make_noise_subset --items data/processed/items_nu.jsonl
```

The selector stores six IDs per domain from `sample_rank <= 200` in
`configs/config.yaml`. It refuses to replace a non-empty ID list unless `--force`
is supplied. Run the three repeats for one model with:

```powershell
python -m src.eval.run --model-slug model-1 --items data/processed/items_v1.jsonl --conditions NU,RU-P,RU-R,RU-X,RT --noise-subset
```

Non-NU real runs require `data/processed/FROZEN.md`. Mock runs do not contact
providers and are exempt from the guard.

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

The checker exits nonzero for schema/answer problems, missing or duplicate
combinations, request errors, multiple model strings, or an invalid rate above
5 percent.

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
