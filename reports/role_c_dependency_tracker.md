# Role C Dependency Tracker

Status checked 2026-11-21 against the [readiness audit](./role_c_readiness_audit.md), [analysis input requirements](./role_c_analysis_input_requirements.md), and current repository files. `Complete` is used only where repository evidence exists; pending sheets and templates are not evidence of completed review.

## Five-condition dataset

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Resolve source mapping and option-count treatment; update the shared contract only with team agreement | Sudais | Confirm all source fields, gold labels and four-/five-option handling; preserve each item's actual options | Local UrduMMLU schema and team agreement for any contract change | Pending |
| Complete `data/processed/items_v1.jsonl` | Sudais | 500 item IDs × five conditions; unique item-condition keys; stable gold, options and rank; all spelling invariants and verification metadata valid | Source mapping, RU-P/RU-R/RU-X/RT variants, human verification and kappa gates | In Progress |
| Freeze record `data/processed/FROZEN.md` with final dataset hash | Sudais | Hash matches final item/rule artifacts; freeze only after Gate G2 criteria pass | Completed variants, verification/spot-check, kappa, edit-distance checks | Pending |
| Measured edit-distance CSV for RU variant pairs | Sudais | Raw and normalized distance plus unchanged-variant share; values trace to final variants | Complete candidate variants | Pending |

Evidence: only the 500-row NU file and a 30-row unverified RU-P pilot are present; the final five-condition file and freeze record are absent.

## Model evaluation outputs

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Per-model request results under `results/raw/<model_slug>/<run_id>.jsonl` | Zia | Full result contract; planned model/item/condition coverage; valid repeat IDs; preserve invalids, errors, retries and provenance | Frozen dataset, approved model/prompt/configuration | Pending |
| Noise-subset repeats in the raw results | Zia | Match fixed configured item IDs; include planned repeats 1–3 for each required model, condition and item, or document missing cells | Frozen dataset and run plan | Pending |
| Real run entries in `results/RUN_LOG.md` | Zia | Run IDs, model strings/provider, UTC dates, prompt hash, calls/errors, invalid rate and stop reason reconcile with raw results | Actual model runs | Pending |
| Result-checker validation outcome | Zia | Run `src/eval/check_results.py`; resolve or explicitly document missing, duplicate, invalid and error rows before handoff | Raw results plus final frozen item file and configuration | Pending |

Evidence: `results/RUN_LOG.md` says no real runs are recorded; `results/raw/` is absent.

## Human verification

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Completed 100-item verification sheet (300 item-condition rows) and corrections record | Role C coordinates; assigned team raters perform independent reviews | Rate RU-P/RU-R/RU-X on the four required criteria; no one reviews their own generated items; preserve corrections and notes | Complete candidate variants and named reviewer assignments | In Progress |
| Spot-check record for remaining items | Role C coordinates with assigned reviewers | Follow agreed stratified sample/seed; report error rate; if ≥10%, record fixes and rechecks without hiding initial findings | Candidate variants and agreed spot-check plan | Pending |

Evidence: `annotations/verification_pending_assignment.csv` has 300 rows, but raters remain `PENDING_ASSIGNMENT`; the pilot sheet is also pending. No completed verification or corrections record was found.

## Kappa agreement

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Completed `annotations/kappa_50_checked.csv` | Role C coordinates; two assigned raters rate independently | Same 50 assigned items; both ratings present and `y`/`n`; unique item-condition rows; preserve original ratings | Candidate variants and assigned independent raters | In Progress |
| Cohen's kappa and raw-agreement record | Role C | Run the existing kappa CLI on the completed sheet; report N, raw agreement, kappa, and undefined/below-threshold status; retain initial result if rules are revised | Completed, validated kappa sheet | Pending |

Evidence: `annotations/kappa_pending_assignment.csv` has 50 RU-P rows, but both rating columns are blank; no completed sheet or kappa result exists.

## AFR and statistical analysis

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Existing analysis implementation and unit tests in `src/analysis/` and `tests/analysis/` | Role C | Repository contains the modules/tests; prior audit recorded 64 analysis tests passing (six expected warnings) | None for code/test existence; this does not establish empirical readiness | Complete |
| Pre-analysis validation record (checklist in the input-requirements document; result location to be recorded with the analysis run) | Role C | Confirm frozen hash, schema/types, unique keys, complete pairings, canonical retry handling, invalid denominators, and noise-repeat coverage | Validated Role A dataset and Role B result-checker outcome | Pending |
| Empirical AFR, condition/domain comparisons, noise, McNemar/Holm, regression, and NU/RT tables under `results/tables/` | Role C | Use only real validated inputs; report per-model denominators, invalid treatment, missingness and model-fit status; no synthetic rows | Frozen dataset; raw main runs; required repeat data; verified edit-distance input | Pending |
| Analysis figures under `results/figures/` | Role C | Figures reproduce from validated tables and state uncertainty/denominators | Completed empirical tables | Pending |

## Final research reporting

| Deliverable / expected file | Owner | Required validation | Depends on | Status |
|---|---|---|---|---|
| Results and limitations section in the project manuscript | Role C | Every numerical claim traces to validated tables/raw rows; report exclusions, invalids, missing runs and null results | Completed analyses and tables | Pending |
| Final claims/literature audit using `docs/LITERATURE.md` | Role C, with assigned paper readers | Cite only sources whose full text and claims have been checked; reconcile every result claim with a table | Verified sources and completed analyses | In Progress |
| Reproducible final tables/figures and analysis settings | Role C | A teammate can reproduce outputs from frozen items, raw results, edit-distance input and recorded seed/settings | All upstream gates and final analysis | Pending |

## Readiness gates

- **Dataset:** In Progress — partial NU/RU-P artifacts exist; no frozen five-condition dataset.
- **Evaluation:** Pending — no real raw outputs or run-log entries.
- **Human verification:** In Progress — assignment sheet exists, but assignments/ratings are incomplete.
- **Kappa:** In Progress — 50-row sheet exists, but ratings are blank.
- **Empirical analysis:** Pending — do not calculate or report AFR/Kappa until required inputs and gates pass.
- **Final reporting:** Pending — depends on validated empirical outputs and source checks.

**Next handoff:** Sudais completes and freezes the validated dataset; Zia supplies checked raw results and run records; Role C then validates the analysis inputs, completes the assigned review/kappa workflow, and runs the existing analyses. No role should bypass its listed gates.
