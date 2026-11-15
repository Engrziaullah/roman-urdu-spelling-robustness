# Role C: Analysis and validation (Younas Khan): Day 1 tasks

Paste `00_SESSION_START.md` first. Then paste **one task at a time**. Branch names: `c/<topic>`.
You own: `src/analysis/`, `tests/analysis/`, `annotations/`, `results/tables/`, `results/figures/`, `docs/LITERATURE.md`.
Do NOT import code from `src/data/` or `src/eval/`. Read files only through the CONTRACTS formats.

Day 1 goal for Role C (Gate G1): statistics code that passes its tests on **synthetic data** (never presented as results), annotation templates, and the literature table started.

**Important:** Synthetic data exists only to test code. It must live under `tests/` or a clearly named temporary folder and must never be written to `results/raw/` or `results/tables/`.

---

## Task C1: Synthetic data generator that follows CONTRACTS

Context: `docs/CONTRACTS.md` sections 1 to 3.
1. `src/analysis/synthetic.py`: generate (a) a small items table and (b) a results table in the exact formats of CONTRACTS sections 1 and 2,
   for several fake models, all five conditions and the noise subset (3 repeats). Make the generator parameterised: base accuracy, probability that an answer flips between spelling variants,
   probability of an invalid answer, and a planted script gap. Seeded and deterministic.
2. Everything it creates is labelled `synthetic` in `run_id` and in file names. Never write into `results/`.
3. Tests: with flip probability 0 every item has identical answers across RU-P, RU-R and RU-X; with a planted flip rate the measured rate is close to it.

---

## Task C2: Statistics functions (pre-specified; do not choose tests after seeing results)

Context: `docs/CONTRACTS.md` section 3 and the evaluation plan in the research proposal (`docs/*.docx`) and `docs/PLAN.md`.
Implement in `src/analysis/stats.py`, each with a docstring and tests on synthetic data with known answers:
1. Accuracy per model and condition with bootstrap 95% CI (resample items; seed as an argument; 10,000 resamples by default).
2. **Flip definition (state it in the docstring):** an item flips for a model if the chosen letter is not identical across RU-P, RU-R and RU-X. Handle invalid answers explicitly:
   implement two versions, (a) invalid counts as its own answer value, (b) restrict to items valid in all three variants; always report both and the number of items affected.
3. Pairwise flip rates (RU-P vs RU-R, RU-P vs RU-X, RU-R vs RU-X) with bootstrap CI.
4. **Noise baseline** from the noise subset: flip rate between repeats of the same condition (same item, same model). Provide a function that puts the spelling flip rate and the noise baseline side by side on the same items.
5. McNemar test (exact) for NU vs RU-P per model on paired items, with Holm correction across models.
6. Fleiss' kappa across the three spelling variants, and Cohen's kappa for two raters (used for the annotation check).
7. Regression for correctness on condition (and model) with item as the clustering unit. Primary choice: GEE logistic with exchangeable correlation (statsmodels); also try a mixed-effects logistic model with an item random intercept
   and report if it fails to converge. Document the choice and why. I will confirm the choice before any real data is analysed.
8. Tests: planted effects are recovered; identical variants give flip rate 0; Holm gives the expected adjusted values on a known example; kappa matches a hand-computed example.

---

## Task C3: Table writers

Write `src/analysis/tables.py` that reads results files in the CONTRACTS section 2 format and writes the CONTRACTS section 3 tables to an output directory given as an argument:
`accuracy.csv`, `flips.csv`, `flip_rates.csv`, `rt_analysis.csv`, `edit_distance.csv` (reads the edit-distance values produced by Role A), `errors.csv` (header only for now).
Default output directory for tests is a temporary one. Real tables go to `results/tables/` only when real data exists and I say so.
Include `n`, `invalid_rate` and the number of items after exclusions in the tables. Never aggregate across models without showing per-model rows.

---

## Task C4: Annotation templates and kappa script

1. `annotations/verification_template.csv`: columns `item_id, condition, rater, meaning_preserved, words_unchanged, protected_tokens_ok, convention_followed, corrected_text, note` (see `docs/RULES.md` section 9.1).
2. `annotations/kappa_template.csv`: columns `item_id, condition, rater_1, rater_2` with y/n values for meaning preserved.
3. `src/analysis/kappa.py`: read a filled kappa sheet, compute Cohen's kappa and the raw agreement, print both, and warn if kappa is below 0.80 (target in the plan).
   It must report the number of items and never modify the input.
4. `annotations/README.md`: how to use the templates in Google Sheets (import and export as CSV), who rates which items, and the rule that nobody rates items they drafted or generated.

---

## Human tasks for Role C today (not for the agent; the agent must not do these)

- **Literature (`docs/LITERATURE.md`):** read the full text of the P1 papers (L01 to L05) and tick the Opened and Verified boxes only when the details and the claims are confirmed. Re-run the Day 1 searches in section 3.2 and record the exact queries, date, filters and counts. Do not let an AI tool "verify" papers for you.
- **PURUTT:** check the license of the corpus. If unclear, cut the real-usage check (PLAN.md cut list).
- Tell the team immediately if Belebele (L02) contains a Roman Urdu set, because that changes how the novelty is worded.

## Gate G1 checklist (Role C part)
- [ ] Stats code passes its tests on synthetic data; no synthetic file is in `results/`.
- [ ] Annotation templates and kappa script committed.
- [ ] Literature table: P1 papers opened; search log started with real queries and dates.
- [ ] PRs reviewed by someone else.
