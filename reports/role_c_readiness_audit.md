# Role C Readiness Audit

**Audit date:** 2026-11-21

**Scope:** Repository inspection and Role C readiness only. No datasets, configurations, evaluation pipelines, or annotation assignments were changed. No experimental data was generated.

## Current repository status

- The checked-out branch is `a/engine-scaffold-younas` (the project guidance recommends `c/<topic>` for Role C work).
- The worktree was already dirty before this audit, with changes across `annotations/`, `configs/`, `data/interim/`, `docs/`, `src/analysis/`, `src/data/`, and tests. These changes were left untouched; this report is the only file created for the audit.
- `reports/`, `results/raw/`, `results/tables/`, `results/figures/`, and `notebooks/` were absent during inspection. `results/` contains only `RUN_LOG.md`.
- The required project guidance and the Role C task prompt were read: [README.md](../README.md), [PLAN.md](../docs/PLAN.md), [CONTRACTS.md](../docs/CONTRACTS.md), [RULES.md](../docs/RULES.md), and [C_day1_analysis.md](../docs/prompts/C_day1_analysis.md).

## Available data and evaluation outputs

### Data

- Source files exist: `data/raw/urdummlu.json` (26,431 records) and `data/raw/stats.json`.
- The existing [schema report](../data/interim/schema_report.md) describes the local source fields and reports five domains and 26 subdomains. The official Hugging Face card has now been checked and records 26,431 Urdu MCQs, CC BY 4.0, and `urdummlu.json`; the downloadable dataset archive has not been independently downloaded and inspected.
- `data/processed/items_nu.jsonl` contains 500 unique items, condition `NU` only, ranks 1–500, with 100 items per domain. It has 497 four-option items and 3 five-option items. The current schema therefore includes a small number of five-option cases, not only A–D cases.
- All 500 NU rows contain `verified: true`; this field value is not evidence that Roman Urdu variants have undergone manual verification. The interim RU-P records inspected have `verified: false`.
- `data/interim/` contains a 30-row RU-P draft, a 30-row pilot file, a 30-row cache file, prompt files, an exclusion-filter CSV, and sampling/schema reports. The RU-P rows inspected are marked unverified. No complete RU-P set or RU-R, RU-X, and RT variants were found.
- `data/processed/FROZEN.md` and `data/processed/items_v1.jsonl` are absent; the complete five-condition, 2,500-row frozen dataset is not available.
- The [sampling report](../data/interim/sampling_report.md) records seed 42, 500 selected records, 100 per domain, and a nested 200-item subset. Its counts are recorded project metadata, not independently recalculated in this audit.

### Evaluation outputs

- No `results/raw/` directory or model result JSONL files exist. The [run log](../results/RUN_LOG.md) says no real runs have been recorded.
- `configs/config.yaml` and `configs/models.yaml` exist and include a seed, noise-subset settings, and three evaluated-model entries. These are Role B-owned configuration files; their values are reported as repository contents, not independently validated provider/model facts.
- `src/eval/` exists (the requested `src/evaluation/` path does not). Its `check_results.py` provides a read-only result-contract and run-plan checker, but it expects the final items file and saved results, neither of which is currently present.

## Existing analysis functionality

The `src/analysis/` package already contains:

- `accuracy.py` and `bootstrap.py`: main-run accuracy, domain summaries, and seeded bootstrap intervals.
- `flips.py`: pairwise and any-variant flips, with invalid answers treated as a distinct value or excluded through a valid-only view.
- `noise.py` and `compare.py`: repeat variability and matched spelling-flip versus noise comparisons.
- `mcnemar.py`: exact paired McNemar tests with Holm correction.
- `mixed.py`: item-intercept Bayesian logistic mixed-model output and GEE sensitivity output.
- `kappa.py`: Fleiss' kappa for variant/repeat comparisons and a Cohen's kappa CSV-sheet CLI with validation, raw agreement, and threshold status.
- `tables.py`: table builders/writer for accuracy, flips, noise, McNemar, regression, NU/RT comparisons, edit distance, and error categorization.
- `tokens.py`: open-tokenizer proxy counts and paired summaries.
- `synthetic.py`: a synthetic-data generator, with clearly named files under `src/analysis/synthetic_data/`.

No analysis notebooks or generated real-data tables were found. The current `synthetic.py` generator uses fixed internal conditions and defaults; it does not expose all of the parameterized accuracy, flip probability, invalid probability, and script-gap controls described in the Role C Day 1 prompt. No dedicated `tests/analysis/test_synthetic.py` was found.

## Existing validation functions and tests

- Analysis tests exist in `tests/analysis/` for the main analysis modules.
- Command run: `python -m pytest tests\analysis -q` — **64 passed**, with **6 warnings**. The warnings are expected warnings from tests exercising absent paired conditions in McNemar comparisons.
- This was a unit-test run on the current checkout (including pre-existing uncommitted changes); it is not validation of real experimental data or analysis outputs.
- Data-side invariant/rule/sample tests and evaluation-side tests also exist, but were not run as part of this Role C audit.
- Annotation files are not completed ratings:
  - `verification_pending_assignment.csv` has 300 rows for the 100-item/three-condition workflow, with raters still `PENDING_ASSIGNMENT`.
  - `kappa_pending_assignment.csv` has 50 rows with no completed ratings.
  - `rup_pilot_verification.csv` has 30 rows with raters still pending.
  - `kappa_template.csv` is header-only. `verification_template.csv` contains three illustrative rows, including `y` values and a sample note; these are examples, not human verification evidence.
- [LITERATURE.md](../docs/LITERATURE.md) exists. Its own status notes say some entries remain unverified; the audit does not independently validate checked papers or claims. Unchecked sources must not be cited as verified.

## Completed Role C work

- Analysis implementations and focused unit tests are present for AFR/flip rates, bootstrap intervals, paired comparisons, noise variability, McNemar/Holm, regression, kappa, tables, and token proxies.
- Annotation templates and pending-assignment sheets are present.
- The literature table exists.
- The analysis test suite passes on the current checkout as noted above.

These are present in the working tree; many Role C files are uncommitted, so this audit does not describe them as merged or release-ready. No real-data AFR, condition comparison, repeat-variability estimate, kappa result, or derived table can yet be reported.

## Missing Role C prerequisites

- A complete, frozen, contract-compliant five-condition dataset with resolved option-count handling.
- Real evaluation output files with sufficient coverage to calculate AFR and compare conditions.
- Human verification assignments and completed ratings, including an actual Cohen's kappa calculation. Pending sheets and illustrative template rows are not evidence of verification.
- Repeated-run results for the configured noise subset; without them, spelling instability cannot be compared against observed run-to-run variability.
- A decision on whether to complete the synthetic generator's prompt-specified parameter controls and tests before relying on it for additional statistical test cases.
- After upstream inputs are available: run the analysis against those inputs, validate missing/duplicate/invalid rows, and produce the contract tables under `results/tables/`. None are currently present.

## Dependencies belonging to Sudais (Role A)

- Resolve the source/contract option-count issue: the selected NU sample includes three five-option items.
- Produce and validate the complete RU-P, RU-R, RU-X, and RT data while preserving the spelling invariants.
- Complete the outstanding rules/verification decisions, manual verification workflow, and edit-distance outputs.
- Create the final frozen dataset and its recorded hash only after the required verification gates are actually satisfied.
- Clarify the intended meaning of the `verified` field on the NU-only sample so it is not mistaken for completed Roman Urdu verification.

## Dependencies belonging to Zia (Role B)

- Complete real model runs and save outputs under `results/raw/` using the contract format; maintain the run log.
- Validate the completeness, duplicates, errors, and invalid-answer rates against the final items file and run plan.
- Confirm Role B-owned model/configuration decisions through the project workflow before interpreting any model results. No such configuration changes were made in this audit.

## Recommended next steps

1. Role A resolves the option-count and verification-status questions, completes the required variants and checks, and freezes the data only when the documented gates are met.
2. Role B runs and validates the planned evaluation against the frozen dataset, preserving all failures and invalid answers in the raw outputs and log.
3. Role C completes the assigned human rating workflow and computes kappa only from a completed sheet; do not use pending sheets or template examples as ratings.
4. Once the frozen dataset and real result files are available, Role C runs the existing analysis, checks output completeness and invalid handling, and produces the derived tables/figures. Any synthetic-generator gap can be addressed separately in Role C-owned code and tests.
5. Keep existing uncommitted work intact and coordinate ownership through the project's branch/PR workflow; do not modify Role A/B-owned files as part of Role C follow-up.
