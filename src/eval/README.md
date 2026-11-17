# Evaluation module

`python -m src.eval.run --help` shows the runner options. Real runs require completed
values in `configs/config.yaml` and `configs/models.yaml`; unresolved `TODO` values
are errors, not defaults.

## Answer parsing

The parser accepts a case-insensitive, standalone valid option letter. Formatting
punctuation is allowed (`B`, `B)`, `**B**`, `Answer: B`, or `The answer is B.`).
If the response contains no valid letter or more than one distinct valid letter,
it is invalid. Repeated occurrences of the same valid letter are accepted.
Invalid answers remain in the JSONL results and count toward the invalid rate.

## Mock runs

Mock items and outputs are for tests only. Run them with `--mock` and an explicit
temporary `--output-dir`; mock rows must never be written to `results/raw/`.
Mock runs do not append to `results/RUN_LOG.md`.

## Provider references

Adapters follow the providers' documented request formats:

- Gemini `generateContent`: <https://ai.google.dev/api/generate-content/generate-content>
- Groq Chat Completions: <https://console.groq.com/docs/api-reference#chat-create>
- OpenRouter API reference: <https://openrouter.ai/docs/api-reference/overview>
