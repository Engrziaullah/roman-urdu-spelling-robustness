# Spelling Before Script
### Orthographic Robustness of LLMs on Roman Urdu Knowledge MCQs

> **Status:** active development (4-day execution sprint). Results are not yet available; nothing in this repository should be cited as a finding until the release tag `v1.0` exists.

---

## 1. What this project is

Roman Urdu (Urdu written in Latin letters) has no standard spelling: one word may appear as `kya`, `kia` or `kiya`. Prior work compares Nastaliq and Roman Urdu on single tasks, with mixed results. This project asks a narrower question:

> **If only the spelling of a Roman Urdu exam question changes (same words, same word order, same formality), how often does an LLM's answer change?**

We sample 500 questions from [UrduMMLU](https://huggingface.co/datasets/MBZUAI/UrduMMLU), build five matched versions of each, and evaluate 3–4 LLMs from different families with one fixed prompt. No training and no paid compute.

The primary outcome is **answer instability (flip rate) across spelling variants**. The Nastaliq-vs-Roman-Urdu accuracy gap is a secondary, confirmatory result and is **not** claimed as the discovery.

## 2. Conditions (five matched versions per item)

| Code | Condition | Rule |
|---|---|---|
| `NU` | Original Nastaliq | No change |
| `RU-P` | Phonetic Roman Urdu | One letter pattern per sound, fixed vowel conventions (e.g. `nahin`, `jawab`) |
| `RU-R` | Reduced Roman Urdu | Vowel elision and common shortenings (e.g. `nhi`, `jwab`); same words as RU-P |
| `RU-X` | English-orthography Roman Urdu | English letter habits (e.g. `x` for kh, `k` for q); same words as RU-P |
| `RT` | Round-trip | RU-P transliterated back to Nastaliq automatically; exposes conversion artefacts |

**Register control:** all variants keep the same words and word order. No slang, no English insertions, no formality changes. Full operation rules live in `docs/RULES.md` (written in Phase 1).

## 3. Research questions

| ID | Question |
|---|---|
| **RQ1 (primary)** | How often does a model's answer change across RU-P, RU-R and RU-X versions of the same item? |
| RQ2 | How large is the NU vs Roman Urdu accuracy gap on exam-style knowledge items? (no direction assumed) |
| RQ3 | How much of the apparent effect comes from the conversion itself (RT control)? |
| RQ4 | Which items break (numerals, named entities, unit symbols?) and does token length add explanatory power? |

Hypotheses, metrics and success criteria are in the research proposal; the plan for executing them is in [`docs/PLAN.md`](docs/PLAN.md).

## 4. Team and ownership

Three contributors work in parallel, in every phase and at the same time. Each owns one folder, to avoid merge conflicts. The assignment below is provisional: swap roles on Day 1 (before G0) if someone's skills fit another role better.

| Role | Owner | Owns | Main responsibility |
|---|---|---|---|
| **A — Data** | **Sudais Khan** | `src/data/`, `data/`, `docs/RULES.md` | Sampling, RU-P draft, RU-R/RU-X rule engines, RT, edit distances |
| **B — Evaluation (and repo lead)** | **Zia Ullah** | `src/eval/`, `configs/`, `results/raw/` | API clients, prompt, parser, caching/logging, all model runs |
| **C — Analysis & validation** | **Younas Khan** | `src/analysis/`, `annotations/`, `results/tables/`, `results/figures/` | Statistics, annotation and kappa, literature table, paper skeleton |

Roles rotate in Phase 3, where everyone writes a paper section. Shared files (`README.md`, `docs/`) are changed only through small pull requests.

## 5. Repository layout

```
roman-urdu-spelling-robustness/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── configs/
│   ├── config.yaml
│   ├── models.yaml
│   └── prompt.txt
├── docs/
├── AGENTS.md
│   ├── CONTRACTS.md
│   ├── LITERATURE.md
│   ├── PLAN.md
│   ├── RULES.md
│   └── prompts/
├── data/
│   ├── raw/
│   │   ├── stats.json
│   │   └── urdummlu.json
│   ├── interim/
│   └── processed/
│       └── items_nu.jsonl
├── src/
│   ├── analysis/
│   ├── data/
│   └── eval/
├── tests/
│   ├── analysis/
│   ├── data/
│   ├── eval/
│   └── fixtures/
├── results/
│   └── RUN_LOG.md
```

`data/raw/` currently contains committed UrduMMLU files (`urdummlu.json` and
`stats.json`); the earlier "not committed" note was inaccurate. The team still
needs to decide how these source files should be handled. `data/processed/`
currently contains `items_nu.jsonl`; `FROZEN.md` is not present yet.
`src/data/rules/`, `annotations/`, `paper/`, and the `results/raw/`,
`results/tables/`, and `results/figures/` output directories are not present in
the current tree.

## 6. Setup

```bash
git clone https://github.com/Engrziaullah/roman-urdu-spelling-robustness.git
cd roman-urdu-spelling-robustness
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env    # then add YOUR OWN API keys; never commit .env
```

Entry-point commands will be added to this section by each owner when their module is merged (Phase 1–2). Until then, see `docs/PLAN.md` for what is expected from each module.

## 7. Working rules (important for parallel work)

1. **Branches:** `a/<topic>`, `b/<topic>`, `c/<topic>`. Never push directly to `main`; open a PR, one teammate reviews.
2. **Stay in your folder.** If you need a change in someone else's folder, ask them or open an issue.
3. **Schemas are fixed in `docs/CONTRACTS.md`.** Changing a schema needs agreement from all three.
4. **Frozen data is read-only.** After gate G2, `data/processed/` is not edited. A fix means a new version (`v2`) with a recorded reason.
5. **Secrets:** API keys only in `.env` (gitignored). Never paste keys into code, notebooks or prompts to an AI assistant.
6. **Log everything that affects results:** model string, provider, UTC date, prompt hash, seed, run id.
7. **AI-assisted code (Antigravity or otherwise) must be reviewed by a human** before merge, especially the spelling-rule engine and the statistics code. Rule outputs must be checked by someone who reads Urdu.
8. **Do not tune to the result.** The rules, prompt and analysis plan are fixed before the main runs.

## 8. Reproducibility and integrity

- Sampling uses a fixed seed; the item IDs are committed.
- Models are evaluated zero-shot, temperature 0, one English instruction template for all conditions, answer-letter output.
- Invalid or unparsable answers are counted per condition and reported (target < 5% per condition).
- Run-to-run noise is estimated on a 30-item subset with three repeats; spelling effects are read against it.
- A null result (models are robust to these spelling changes) is a valid, reportable outcome.
- Free API tiers change without notice; model strings and dates are logged for every run.

## 9. Known limitations (stated up front)

- Spelling styles are researcher-defined operations, not a sample of real writers.
- Automatic transliteration for `RT` is imperfect, so `RT` is a diagnostic, not ground truth.
- UrduMMLU is public and may be in training data; comparisons are kept within-item.
- With 500 items, 95% intervals on accuracy are still about ±4–5 points, so small accuracy gaps will not be resolved; flip rate is the primary outcome. (The original proposal text assumes 200 items and ±7 points; it must be updated to match.)
- Token-length analysis uses an open tokenizer as a proxy, because closed API models do not expose their tokenizers (to be stated in the paper).

## 10. Data, license and citation

- Source data: **UrduMMLU**, Tabassum, Ahmad, Iqbal, Aijaz, Ahsan, Nakov, arXiv:2606.07167, Hugging Face `MBZUAI/UrduMMLU` (listed as CC BY 4.0; re-verify on the dataset card before release).
- Derived data in this repo must carry attribution to the source under its license.
- Code license: _to be decided by the team before release_ (MIT is a common choice).
- Citation entry for this repository will be added at release.

## 11. Progress

Evidence-based status (updated 2026-11-24; no gate marked complete without team agreement/artifacts).

| Gate | Date/time | Condition | Status |
|---|---|---|---|
| G0 | Day 1, hour 2 | Contracts, repo skeleton, seed, prompt and model list agreed | ⬜ Not complete. Evidence: repo skeleton, `configs/prompt.txt`, `configs/config.yaml` seed 42, and `configs/models.yaml` exist; model-1/helper configured, model-2/model-3 TODO; contracts shared-update proposed in PR #25 (pending agreement/merge). |
| G1 | End Day 1 | Sample committed, RU-P draft done, harness runs on NU | ⬜ Not complete. Evidence: `data/processed/items_nu.jsonl` committed on `origin/main` (500 items, hash `2b3b4c9dfd12d97a5df285019ada4206d89e8d83fc2bd9004c1836d7b33cad73`, normalized CRLF→LF); eval harness/scripts present (PR #22 merged, https://github.com/Engrziaullah/roman-urdu-spelling-robustness/pull/22) and NU dry-run/mock verified; RU-P draft completion and real NU run pending/blocked (issue #23). |
| G2 | End Day 2 | Dataset verified and **frozen**, kappa computed | ⬜ Not complete. Evidence: `data/processed/FROZEN.md` and `items_v1.jsonl` not present; kappa artifacts not verified complete. |
| G3 | End Day 3 | All raw model outputs collected, invalid rate checked | ⬜ Not complete. Evidence: `results/RUN_LOG.md` shows no real runs recorded; no complete NU/all-condition raw outputs collected. |
| G4 | End Day 4 | Analysis, draft, code and data released (`v1.0`) | ⬜ Not complete. |
