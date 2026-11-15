# AGENTS.md: rules for AI coding agents (Antigravity or any other)

Read this file fully at the start of every session. It is the shared rulebook for three people working in parallel.

## Project in three lines
We test whether LLM answers change when only the Roman Urdu spelling of an exam question changes. We sample 500 UrduMMLU items, build five matched
versions (NU, RU-P, RU-R, RU-X, RT), and run 3 to 4 LLMs through free API tiers. Primary outcome: answer flips across spelling variants.

## Read before doing anything
1. `README.md`
2. `docs/PLAN.md` (phases, gates, who does what)
3. `docs/CONTRACTS.md` (the file schemas: the ONLY interface between roles)
4. `docs/RULES.md` (spelling rules and invariants; Role A owns it)
5. The task prompt the user pastes (in `docs/prompts/`)

## Roles and ownership (one owner per folder)
| Role | Person | May edit | Must NOT edit |
|---|---|---|---|
| A: Data | Sudais Khan | `src/data/`, `tests/data/`, `data/`, `docs/RULES.md` | everything else |
| B: Evaluation (repo lead) | Zia Ullah | `src/eval/`, `tests/eval/`, `configs/`, `results/raw/`, `results/RUN_LOG.md` | everything else |
| C: Analysis and validation | Younas Khan | `src/analysis/`, `tests/analysis/`, `annotations/`, `results/tables/`, `results/figures/`, `docs/LITERATURE.md` | everything else |

Shared files (`README.md`, `docs/PLAN.md`, `docs/CONTRACTS.md`, `AGENTS.md`, `requirements.txt`) change only through a small pull request that the other two approve.
At the start of a session the user tells you their role. If a task needs a change outside that role's folders, **stop and tell the user**; do not edit the other folder.
Do not import code across role folders: each module reads and writes files that follow `docs/CONTRACTS.md`.

## Hard rules (scientific integrity)
1. **Never invent results, numbers, citations, model names, rate limits, API endpoints or dataset facts.** Look them up in official documentation or ask the user. If unknown, say so.
2. **Never fabricate model outputs.** Every reported number must trace to a row in `results/raw/`. Mock or synthetic data is for tests only and must be clearly labelled and kept out of `results/raw/`.
3. **Frozen data is read-only.** After `data/processed/FROZEN.md` exists, never modify `data/processed/items_v1.jsonl` or the rule files.
4. **Schemas are fixed** by `docs/CONTRACTS.md`. If you think a schema must change, stop and propose the change in text; all three people must agree before any code changes.
5. **Keep register constant.** Roman Urdu variants differ only in letters (see `docs/RULES.md`, section 3). Never translate, paraphrase, correct or "improve" question content.
6. **Do not tune to the result.** Prompt, rules and analysis plan are fixed before main runs. Do not drop items, models or conditions without logging why.
7. **Report problems, do not hide them.** Invalid answers, failed items and anomalies are counted and reported, never silently dropped.

## Security
- API keys come only from environment variables or a local `.env` (git-ignored). Never print, log, commit or paste a key. Do not read `.env` into the chat.
- Never push to `main`. Work on your branch (`a/<topic>`, `b/<topic>`, `c/<topic>`) and open a pull request.

## Code standards
- Python 3.10+, type hints on public functions, short functions, docstrings stating inputs and outputs.
- Deterministic where randomness exists: take the seed from `configs/config.yaml` (`seed`) or a required `--seed` argument; if the seed is still `TODO`, stop and ask.
- Every script runs from the repo root: `python -m src.<area>.<module> --help`.
- Tests with every module (`tests/<area>/`), runnable with `pytest`. Run them before saying a task is done.
- Do not add heavy dependencies without a reason; add any new package to `requirements.txt` in a PR.
- Commit message style: `data: ...`, `eval: ...`, `analysis: ...`.

## How to work
1. **Plan first.** State a short plan (files to create, functions, tests, open questions) and wait for the user's approval.
2. Implement in small steps. After each step run the tests.
3. When done, report: files changed, how to run, test results, assumptions, and anything you could not decide.
4. Never claim something works unless you ran it. If you cannot run it (no network, no key), say so.
