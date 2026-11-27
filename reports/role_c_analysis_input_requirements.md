# Role C Analysis Input Requirements

**Audit date:** 2026-11-21
**Scope:** Read-only inspection of current Role C code, tests, contracts, and available inputs. This document does not change the agreed contracts or analysis implementation. No experimental data or statistics were generated.

## 1. Repository and readiness snapshot

- The existing NU sample is `data/processed/items_nu.jsonl` (500 rows, NU only). The final `data/processed/items_v1.jsonl` and `data/processed/FROZEN.md` are absent.
- `results/raw/`, `results/tables/`, and `results/figures/` are absent. `results/RUN_LOG.md` reports no real model runs.
- The assigned kappa sheet, `annotations/kappa_pending_assignment.csv`, has 50 rows for RU-P, but both rater columns are blank. The 300-row verification assignment sheet still uses `PENDING_ASSIGNMENT`.
- Analysis modules and tests already exist. The last analysis-suite run recorded in the prior audit was 64 passed with six expected missing-condition warnings. This documentation task did not rerun tests.
- No analysis notebooks were found.
- The worktree contained pre-existing changes before this task. They were preserved; only this requirements document was added.

This is a summary of the implementation as it exists, not a claim that the inputs are complete or the analysis is release-ready. The shared schemas are in [CONTRACTS.md](../docs/CONTRACTS.md), the execution gates are in [PLAN.md](../docs/PLAN.md), and the previous repository status report is [role_c_readiness_audit.md](./role_c_readiness_audit.md).

## 2. Analysis function inventory

| Analysis | Existing implementation | Purpose and input shape |
|---|---|---|
| Data join / correctness | `load_data` in [accuracy.py](../src/analysis/accuracy.py) | Reads result and item JSONL, joins by item ID and condition, carries gold/domain, derives `correct`. |
| Accuracy and confidence intervals | `accuracy_table`, `accuracy_by_domain_table` in [accuracy.py](../src/analysis/accuracy.py); `bootstrap_mean_ci` in [bootstrap.py](../src/analysis/bootstrap.py) | Model-condition accuracy; optional domain breakdown; seeded percentile bootstrap. |
| Answer Flip Rate (AFR) | `flips_table`, `flip_rates_table`, `dual_flip_rates_table` in [flips.py](../src/analysis/flips.py) | Main-run RU-P/RU-R/RU-X pairwise flips and any-flip rate. Invalid responses are either an `INVALID` category or excluded from the valid-only estimate. |
| Repeated-run variability | `noise_per_item`, `noise_table` in [noise.py](../src/analysis/noise.py) | Within-condition answer disagreement across repeats, summarized by model. |
| Spelling-versus-noise comparison | `compare_to_noise` in [compare.py](../src/analysis/compare.py) | Matched spelling-flip and repeat-noise measures on items with repeated RU conditions; paired bootstrap intervals for excess. |
| Paired condition comparisons | `mcnemar_table`, `mcnemar_all_conditions_table` in [mcnemar.py](../src/analysis/mcnemar.py) | Exact McNemar comparisons of correctness, defaulting to NU versus RU-P; all-condition wrapper compares NU to RU-P, RU-R, RU-X, and RT when available and applies Holm correction. |
| Regression | `mixed_table`, `gee_table` in [mixed.py](../src/analysis/mixed.py) | Per-model item-random-intercept Bayesian logistic mixed model and item-clustered GEE sensitivity model for correctness by condition. |
| Kappa | `evaluate_kappa_sheet`, `cohen_kappa`, `kappa_table`, `fleiss_kappa` in [kappa.py](../src/analysis/kappa.py) | Cohen's kappa for two human ratings; Fleiss' kappa for answer agreement across spelling variants and, separately, across repeats. These are different analyses and must not be conflated. |
| Token lengths | `token_counts`, `token_summary_table`, `token_comparison_table` in [tokens.py](../src/analysis/tokens.py) | Counts with an open-tokenizer proxy and condition-wise paired summaries. |
| Derived table orchestration | `write_all_tables` and `make_*` functions in [tables.py](../src/analysis/tables.py) | Loads results/items and writes the derived CSV set described below. |
| Synthetic-only data | `make` in [synthetic.py](../src/analysis/synthetic.py) | Produces explicitly synthetic items and results for testing. It is not an experimental input and must not be analyzed or reported as real data. |

### Existing tests

Focused tests are present in `tests/analysis/` for accuracy, bootstrap, flips, noise, matched noise comparison, McNemar, regression, kappa, tables, and tokens. The tests cover known-value cases and several input failures, including incomplete/duplicate variants, missing kappa columns/ratings, invalid labels, and missing paired conditions. There is no dedicated `test_synthetic.py`. The previously recorded run was `python -m pytest tests\analysis -q`: 64 passed, six expected warnings. Test fixtures and `src/analysis/synthetic_data/` are synthetic only.

## 3. Canonical input files and schemas

### 3.1 Frozen item file — Role A artifact

**Required path:** `data/processed/items_v1.jsonl`
**Format:** UTF-8 JSON Lines; one object per `(item_id, condition)`.

The shared contract defines these fields:

| Field | Required type/values | Analysis use |
|---|---|---|
| `item_id` | Non-empty string; same ID across all five conditions for one question | Pairing/grouping unit. |
| `source_row` | String or source identifier | Provenance; not used by current analysis functions. |
| `domain` | String from the agreed domain set | Required by domain-wise accuracy; also used for stratified bootstrap when present. |
| `subject` | String | Descriptive/provenance; not used by current analysis functions. |
| `condition` | Exactly `NU`, `RU-P`, `RU-R`, `RU-X`, or `RT` | Analysis condition key. |
| `question` | String | Required by token counts. |
| `options` | Ordered list of strings | Required by token counts; option count must match the source item and parser configuration. |
| `gold` | Valid answer-option label as a string | Correctness comparison; identical across an item's conditions. |
| `verified` | Boolean with meaning agreed by the data owners | Not consumed by current analysis code; must not be treated as proof of completed human review without confirming its semantics. |
| `sample_rank` | Integer, intended range 1–500 | Sampling/fallback provenance; not used by current analysis functions. |
| `notes` | String | Provenance/exception notes; not used by current analysis functions. |

The contract expects 500 distinct item IDs × five conditions = 2,500 rows, one row per item-condition, with stable gold and option order within each item. Current analysis joins on `(item_id, condition)` and will fail on non-unique item keys during its many-to-one merge. The contract still has TBD source mapping and does not resolve option count; the current NU sample contains both four- and five-option items. Those upstream issues must be resolved without forcing all items to four options.

### 3.2 Raw result file — Role B artifact

**Contract path:** `results/raw/<model_slug>/<run_id>.jsonl`
**Format:** UTF-8 JSON Lines; one row per request. `load_data` and `write_all_tables` currently accept a results JSONL file path, not a results directory.

| Field | Required type/values | Analysis use |
|---|---|---|
| `run_id` | String | Contract provenance. Current analysis groups by model/item/condition/repeat, not run ID. |
| `model_slug` | Non-empty string | Model grouping key. |
| `model_string`, `provider` | Strings | Contract provenance; not grouped by current analysis functions. |
| `date_utc` | UTC timestamp string | Contract provenance. |
| `item_id` | String matching the frozen item file | Pairing key. |
| `condition` | One of the five contract condition identifiers | Pairing/filter key. |
| `repeat` | Positive integer; main run is 1 | Selects main rows and identifies repeat observations. |
| `prompt_hash` | String | Contract provenance. |
| `raw_output` | String | Contract provenance; not parsed again by analysis. |
| `parsed_answer` | Valid option label string or null | Flip/noise comparison; joined to `gold` to derive correctness. |
| `valid` | Boolean, consistent with `parsed_answer` and the item's option labels | Invalid-answer accounting and correctness. |
| `latency_s` | Non-negative number | Contract provenance; not used in current statistical functions. |
| `error` | String or null | Evaluation-quality accounting; not used to derive correctness in `load_data`. |

The full contract row has all fields above. The B-owned `src/eval/check_results.py` is the available contract/run-plan validator. Analysis inputs must use canonical rows after retry handling: current statistical code does not deduplicate retries or group by `run_id`, and duplicate `(model_slug, item_id, condition, repeat)` observations can cause failures or ambiguous input. Preserve raw files and use the evaluation validator/run log to reconcile attempts; do not silently drop failures.

### 3.3 Enriched analysis DataFrame

`load_data(results_path, items_path)` reads the two JSONL files, joins on `item_id` and `condition`, selects `gold` and optional `domain`, casts `valid` to Boolean, and creates:

- `correct`: Boolean, true only when `parsed_answer == gold` and `valid` is true.
- Existing result columns, including `model_slug`, `item_id`, `condition`, `repeat`, `parsed_answer`, and `valid`.
- `domain` when present in the item file.

The downstream analysis functions generally accept this in-memory DataFrame rather than files. Their common identifier fields are `model_slug` (string), `item_id` (string), `condition` (string), and `repeat` (positive integer). None uses `run_id` as a statistical unit.

### 3.4 Human kappa sheet

**Required columns:** `item_id`, `condition`, `rater_1`, `rater_2`; CSV or DataFrame.
`item_id` must be non-empty, `condition` must be RU-P/RU-R/RU-X, and each rater value must normalize to `y` or `n`. Each `(item_id, condition)` must be unique.

The current pending assignment has 50 RU-P rows with both ratings blank. The project protocol calls for the same 50 items to be independently rated by two people. The function validates row contents but does **not** enforce exactly 50 rows or that all rows use the same condition; enforce those protocol requirements before reporting a kappa value.

### 3.5 Role A edit-distance CSV

`make_edit_distance_table` accepts an optional CSV with required columns `variant_pair` and `mean_char_edit_distance`; optional columns are `mean_normalized_edit_distance` and `zero_edit_distance_share`. Missing optional columns are filled with NaN. If no path is supplied, the function returns a three-pair schema with NaN values only; these are placeholders, not measured distances.

### 3.6 Token-count DataFrame

`token_counts` reads the frozen item JSONL and needs `item_id`, `condition`, `question` (string), and `options` (list of strings); `domain` is optional. Its output has one row per item-condition with integer-like counts `n_tokens_question`, `n_tokens_options`, `n_tokens_total`, and `n_chars_total`, plus the identifiers and optional domain. It loads `transformers.AutoTokenizer` and defaults to `xlm-roberta-base`; this is explicitly a proxy, not the evaluated API models' tokenizer.

## 4. Function-level inputs, conditions, outputs, and validations

All in-memory DataFrame inputs described below inherit the field types in section 3.3 unless noted. Existing code checks only the validations stated; the readiness checklist includes additional preflight checks required for scientific completeness.

### 4.1 Loading, accuracy, and bootstrap

| Function | Required inputs | Conditions/IDs and checks | Output |
|---|---|---|---|
| `load_data` | Results JSONL plus item JSONL. Result fields include `item_id`, `condition`, `parsed_answer`, `valid`; item fields include `item_id`, `condition`, `gold`, optional `domain`. | Joins on item-condition, validates many-to-one merge and rejects results with missing gold. It does not validate all result-contract types or expected run coverage. | Enriched DataFrame with derived `correct`. |
| `accuracy_table` | Enriched DataFrame with `model_slug`, `item_id`, `condition`, `repeat`, `correct`, `valid`; optional `domain`. | Uses only `repeat == 1`; rejects duplicate item IDs within model-condition. Each available model-condition group is summarized; it does not itself enforce every expected condition or complete item coverage. | DataFrame / `accuracy.csv`: `model_slug, condition, n, accuracy, ci_low, ci_high, invalid_rate`. |
| `accuracy_by_domain_table` | Same as `accuracy_table`, with required `domain`. | Uses main rows and rejects duplicates within model-condition-domain. | `accuracy_by_domain.csv`: model, condition, domain, n, accuracy, CI bounds, invalid rate. |
| `bootstrap_mean_ci` | Non-empty one-dimensional numeric values; optional one-dimensional `strata` of the same length; positive `n_boot`; integer seed. | Rejects empty/non-1D values, `n_boot < 1`, or misaligned strata. Resamples within strata when supplied. | Tuple `(ci_low, ci_high)` of 2.5th/97.5th percentiles. |

### 4.2 AFR / answer flips

| Function | Required inputs | Required conditions and checks | Output |
|---|---|---|---|
| `flips_table` | `model_slug`, `item_id`, `condition`, `repeat`, `parsed_answer`, `valid`; optional `domain`. | Main rows must have exactly one each of `RU-P`, `RU-R`, and `RU-X` per model-item. Rejects duplicate rows and, when provided, conflicting domains. Invalid answers count as `INVALID` by default; `valid_only=True` drops any item not valid in all three variants. | Per model-item wide DataFrame with answer columns `RU-P`, `RU-R`, `RU-X`, three `flip_<condition>_<condition>` indicators, `flip_pairs`, `flip_any`, and optional domain. |
| `flip_rates_table` | Output of `flips_table`, including model and flip indicator columns; optional domain. | Calculates pairwise rates and any-flip rate; domain-stratified bootstrap if domain exists. | `model_slug, variant_pair, n, flip_rate, ci_low, ci_high`; four rows per model (`RU-P vs RU-R`, `RU-P vs RU-X`, `RU-R vs RU-X`, `any`). |
| `dual_flip_rates_table` | Raw result DataFrame fields required by `flips_table`. | Requires complete RU triplets; computes both all-items and valid-only estimates. | Model × subset × pair DataFrame with `n`, `n_total`, `n_excluded`, `invalid_rate`, flip rate, and CI fields. |

Here AFR/any-flip means the fraction of items for which the selected answer is not identical across all three Roman Urdu variants (`flip_any`). Pairwise flip rates are also calculated. `NU` and `RT` are not part of this AFR definition. Invalid handling must be reported using both all-items (`INVALID` as its own category) and valid-only sensitivity results.

### 4.3 Repeated-run variability and matched noise comparison

| Function | Required inputs | Required conditions and checks | Output |
|---|---|---|---|
| `noise_per_item` | `model_slug`, `condition`, `item_id`, `repeat`, `parsed_answer`, `valid`; optional `domain`. | Requires at least two repeats for selected cells; rejects duplicate model-condition-item-repeat keys, incomplete pivot cells, and conflicting item domains. Invalids become `INVALID`. | Per model-item pair-flip and any-flip averages across repeated conditions; optional domain. |
| `noise_table` | Same result DataFrame. | Requires at least one repeated item; uses bootstrap over items, stratified by domain when supplied. | Per model: `n_items`, pair-noise rate and CI, any-noise rate and CI. |
| `compare_to_noise` | Same result DataFrame; `n_boot >= 1`, integer seed. | Main-run RU triplets must be complete (via `flips_table`). Repeats are considered only for RU-P/RU-R/RU-X; incomplete repeat cells and conflicting domains fail. No repeats yields spelling-all-item rates but NaN noise-dependent fields. | Per model: spelling rates over all/noise items, noise rates, excess rates, paired-bootstrap CIs, `n_noise_items`. |

The project run plan expects repeats 1–3 on the fixed 30-item noise subset for every planned model and all five conditions. The functions do not enforce that exact subset or exact repeat IDs; preflight validation must compare raw rows with Role B's config/run plan. `compare_to_noise` uses repeated Roman Urdu conditions for its noise baseline.

**Orchestration caveat:** `make_flip_rates_table` in `tables.py` calls `noise_table` to attach `noise_baseline`. Therefore the current `write_all_tables` path needs repeated-run data; it will fail if no repeated observations exist, even though `compare_to_noise` can represent a no-repeat case with NaN noise fields.

### 4.4 Domain analysis and condition/statistical comparisons

| Function | Required inputs | Conditions and checks | Output |
|---|---|---|---|
| `mcnemar_table` | `model_slug`, `item_id`, `condition`, `repeat`, `correct`; optional `valid` and `domain`. | Requires both requested conditions (default NU and RU-P), main rows, unique item-condition rows, and complete paired items for each model. Rejects conflicting domains. | Per model: paired `n`, both accuracies, discordant counts, accuracy difference and bootstrap CI, exact McNemar `p_raw`, Holm `p_holm`, significance; invalid counts are added if `valid` is present. |
| `mcnemar_all_conditions_table` | Same as `mcnemar_table`; optional condition list. | Compares NU with available RU-P/RU-R/RU-X/RT. Missing conditions are skipped with warnings; incomplete pair data is not silently dropped. Holm is applied over produced comparisons. | Concatenated model-condition comparison DataFrame. |
| `mixed_table` | `model_slug`, `item_id`, `condition`, `repeat`, `correct`; only main rows used. | Intended condition levels are NU, RU-P, RU-R, RU-X, RT; item is random-intercept group. Code has no comprehensive input validation, so preflight must ensure complete paired condition data, no duplicate main rows, non-null binary correctness, and sufficient outcome variation. | Per model-condition-vs-NU estimates: log odds, posterior SD/interval, odds ratio, item SD, convergence and optimizer metadata. |
| `gee_table` | Same enriched fields as `mixed_table`. | Uses main rows, NU reference, item-clustered exchangeable GEE. Preflight must ensure valid condition labels, complete pairing, no duplicates, and binary non-null `correct`. | Per model-condition-vs-NU log odds, SE/interval, odds ratio, p-value, convergence status. |

Accuracy tables and the paired comparisons use `correct` derived from `parsed_answer`, `gold`, and `valid`. Invalid responses therefore count incorrect for accuracy and McNemar correctness, while AFR/noise treat them as the distinct answer `INVALID`.

### 4.5 Kappa analyses

| Function | Required inputs | Conditions and checks | Output |
|---|---|---|---|
| `cohen_kappa` | Two same-length, one-dimensional, non-empty rating arrays for a meaningful result; no missing values. | Checks dimensions/length and missingness. Undefined when expected agreement is 1 (no class variation). | `(cohen_kappa, raw_agreement)` numeric tuple; NaN for undefined kappa. |
| `evaluate_kappa_sheet` | CSV path or DataFrame with `item_id, condition, rater_1, rater_2`. | Rejects empty input, missing columns, blank IDs, conditions outside RU-P/RU-R/RU-X, duplicate item-condition rows, missing ratings, and labels outside y/n. Threshold must be 0–1. Does not enforce the protocol's 50 rows or one fixed condition. | Dict with number of rows, raw agreement, kappa, threshold, pass flag, and status (`PASSED`, `BELOW_THRESHOLD`, or `UNDEFINED_NO_CLASS_VARIATION`). CLI prints this report and does not modify the source CSV. |
| `counts_from_wide` / `fleiss_kappa` | Wide ratings with units as rows and at least two raters as columns; or finite, non-negative count matrix with equal rater count per unit. | Rejects empty/missing or malformed ratings; Fleiss input must have at least two raters per unit. | Count matrix/categories; or scalar Fleiss kappa (NaN if expected agreement is 1). |
| `kappa_with_ci` | Count matrix, aligned item ID for each unit, positive bootstrap count/seed; optional aligned strata. | Checks non-empty dimensions, item alignment and strata length/consistency. Bootstrap resamples at item level. | `(kappa, ci_low, ci_high)`. |
| `kappa_table` | Result DataFrame: `model_slug, item_id, condition, repeat, parsed_answer, valid`; optional domain. | Spelling kappa requires one main answer for every item in all three RU variants. Noise kappa requires repeated RU rows with complete repeat cells. Invalids count as `INVALID`; duplicates/missing cells fail. | Per model: spelling kappa/CI/item count and noise kappa/CI/noise-item count. |

Do not treat `kappa_table` (model answer agreement across variants or repeats) as a substitute for the planned human Cohen's kappa. The latter requires a completed, independently rated annotation sheet.

### 4.6 Tables, RT, edit distance, and errors

`write_all_tables(results_path, items_path, output_dir, edit_distance_path=None, seed=42, n_boot=10000)` requires:

- One canonical results JSONL file satisfying section 3.2.
- The frozen items JSONL satisfying section 3.1.
- Complete main rows for all five conditions for RT and complete RU variant triplets for flips.
- Repeated-run RU data for its current flip-rate/noise table orchestration.
- A Role A edit-distance CSV for measured edit-distance values. If omitted, the edit-distance output is a NaN placeholder only.

It writes CSVs with one header row and no index:

| Output | Expected row unit and key columns |
|---|---|
| `accuracy.csv` | Model × condition; `model_slug, condition, n, accuracy, ci_low, ci_high, invalid_rate`. |
| `accuracy_by_domain.csv` | Model × condition × domain; includes `n, accuracy, ci_low, ci_high, invalid_rate`. |
| `flips.csv` | Model × item; answer columns for RU-P/RU-R/RU-X, pair indicators, `flip_pairs`, `flip_any`. |
| `flip_rates.csv` | Model × three pair comparisons + `any`; includes flip rate/CI and `noise_baseline`. |
| `flip_rates_valid_only.csv` | Valid-only model × comparison; includes total, excluded, and invalid-rate counts. |
| `noise.csv` | Per-model repeated-run pair and any-flip summaries with CIs. |
| `noise_comparison.csv` | Per-model spelling/noise rates and matched excess estimates with CIs. |
| `mcnemar.csv` | Model × available non-NU condition; exact p-values, Holm values, paired counts and CIs. |
| `regression_mixed.csv` | Model × condition effect, random-intercept model estimates and convergence metadata. |
| `regression_gee_sensitivity.csv` | Model × condition effect from GEE, with standard errors, intervals, p-values, convergence status. |
| `rt_analysis.csv` | Model × item; `ans_NU, ans_RT, nu_rt_agree, flips_across_variants, flip_any`. |
| `rt_summary.csv` | Per model; valid/invalid NU/RT counts, answer agreement, accuracy difference, variant flip summary. |
| `edit_distance.csv` | Variant pair; `variant_pair, mean_char_edit_distance, mean_normalized_edit_distance, zero_edit_distance_share`. |
| `errors.csv` | Main-run failing model-item-condition; `model_slug, item_id, condition, parsed_answer, gold, category, note`. Categories/notes are blank for human error annotation. |

The RT builders require NU and RT main rows for each model-item and also call `flips_table`, so all three RU main conditions must be present. The error table is a scaffold for failures; it does not perform error categorization.

### 4.7 Token analysis

| Function | Required inputs | Conditions and checks | Output |
|---|---|---|---|
| `token_counts` | Frozen items JSONL with `item_id, condition, question, options`; optional domain; installed `transformers` and available tokenizer. | Every question/option must be text accepted by the tokenizer. | Per item-condition token/character count DataFrame; CLI writes `token_counts.csv`. |
| `token_summary_table` | Counts DataFrame with item-condition identifiers and four non-missing metrics; optional domain. | Rejects missing columns, duplicate item-condition rows, or missing metrics. Uses domain-stratified bootstrap if domain exists. | `token_summary.csv`: per condition item count and each metric's mean, median, and CI. |
| `token_comparison_table` | Same counts DataFrame; default reference `NU`. | Requires reference condition, unique/non-missing rows, paired reference/target conditions, and stable domain per item if supplied. | `token_comparisons.csv`: condition, reference, metric, paired item count, mean difference, CI. |

## 5. Missing artifacts and responsible role

| Missing or unresolved artifact | Why analysis needs it | Responsible owner |
|---|---|---|
| Complete `data/processed/items_v1.jsonl` with all five conditions and 500 item IDs | Required for result-to-gold joins, RU flip triplets, paired conditions, RT, and token analysis. | **Sudais (Role A)** |
| `data/processed/FROZEN.md` with final dataset hash and freeze evidence | Establishes the approved immutable analysis input and reproducibility boundary. | **Sudais (Role A)** |
| Full RU-P/RU-R/RU-X/RT texts, invariant checks, manual verification and rule decisions | Needed for valid spelling comparisons and for the data freeze. | **Sudais (Role A)**, with human review performed per the team plan |
| Resolved option-count/source mapping, including the sample's five-option items | Gold labels and answer validity must match each item's actual options; current shared contract still presents A–D as typical but unconfirmed. | **Sudais (Role A)** for data/schema inspection; any shared-contract change requires team agreement |
| Measured Role A edit-distance CSV | Needed for a real `edit_distance.csv`; no-path table output is only NaN placeholders. | **Sudais (Role A)** produces measurements; **Role C** incorporates them into derived tables |
| `results/raw/<model_slug>/<run_id>.jsonl` for planned models and conditions | No actual accuracy, AFR, comparison, regression, RT, or error analysis is possible without model outputs. | **Zia (Role B)** leads the evaluation artifacts/run log |
| Main repeat 1 coverage plus configured repeat 1–3 noise-subset rows | Needed for primary analyses and the current combined table writer/noise comparison. | **Zia (Role B)** |
| Validated/canonical result rows and documented missing/error/retry cells | Statistical code does not reconcile retry history or use `run_id` to deduplicate. | **Zia (Role B)** runs the result checker and documents coverage; **Role C** checks analysis-input invariants before calculating |
| Completed human rating sheets; current kappa sheet is blank | Needed for human Cohen's kappa; pending assignment rows are not ratings. | **Role C** owns the kappa workflow/reporting; raters complete their assigned independent reviews under the shared team plan |
| Role C pre-analysis validation and resulting derived tables/figures | Required before reporting any metric; none exist yet. | **Role C** |

`src/eval/check_results.py` is owned by Role B and checks the raw run plan/contract. Role C should consume its documented validation outcome, not modify the evaluation pipeline.

## 6. Required validation before analysis

### Input and linkage

- [ ] Confirm the final item file is frozen and hash-matched to `FROZEN.md`.
- [ ] Validate JSONL parsing and required fields/types before calling `load_data`.
- [ ] Validate unique `(item_id, condition)` item rows; expected 500 IDs × five conditions, unless a documented, approved design change says otherwise.
- [ ] Validate valid condition identifiers; consistent domain, subject, gold answer, option order/count, and sample rank per item.
- [ ] Confirm every gold label exists among that item's answer options, including the three five-option sample cases.
- [ ] Validate result rows against the full result contract, including UTC date, positive repeat, Boolean `valid`, parsed-answer/gold option compatibility, and `valid` consistency.
- [ ] Reconcile retries/errors upstream and ensure one canonical observation per `(model_slug, item_id, condition, repeat)` in the analysis input. Retain the raw attempt history and do not silently drop failed requests.
- [ ] Verify every result item-condition key joins to exactly one frozen item row and no planned model is accidentally mixed with another model string under the same slug.

### Coverage and pairing

- [ ] For every planned model, check expected item-condition coverage and main repeat 1; report missing, duplicate, error, and invalid cells by condition.
- [ ] Require one main RU-P, RU-R, and RU-X answer for each item used in AFR.
- [ ] Require paired NU/condition observations for every planned McNemar comparison and paired NU/RT rows for RT analysis.
- [ ] Compare actual repeated rows with Role B's fixed noise-subset IDs and repeat plan (1–3); check repeat completeness within each model-item-condition.
- [ ] Confirm the outputs from `check_results.py` and preserve its reported problems; it does not replace Role C's pairing/preflight checks.

### Statistical and annotation safeguards

- [ ] Use the pre-specified invalid policy: AFR both with invalids as `INVALID` and valid-only, reporting exclusions; invalid responses count incorrect for accuracy.
- [ ] Use the agreed seed and bootstrap count; keep item-level pairing and domain strata where implemented.
- [ ] Apply Holm correction only to the intended family of paired tests; report the tested conditions and models.
- [ ] Record model-wise regression convergence/status; do not hide failed or unstable fits.
- [ ] For human Cohen's kappa, validate the agreed 50 item IDs, both independent raters, matching rows, one intended condition per assignment, complete `y`/`n` labels, and no duplicates before calling the sheet CLI. Report raw agreement and undefined status if there is no class variation.
- [ ] Do not treat Fleiss kappa over model variants/repeats as human annotation reliability.
- [ ] Label all synthetic inputs/results as synthetic and keep them out of `results/raw/` and empirical result reporting.
- [ ] Write derived CSVs/figures only after their inputs pass checks; preserve failures, exclusions, and denominators in the outputs/report.

## 7. Readiness checklist

### Role A — data readiness

- [ ] Source mapping and variable option-count handling are resolved through the project workflow.
- [ ] Complete RU-P, RU-R, RU-X, RT, and NU item-condition rows exist with stable item IDs, option order, and gold labels.
- [ ] Invariants and manual verification gates are complete and documented; `verified` semantics are unambiguous.
- [ ] Edit-distance measurements are available and documented.
- [ ] The final dataset is frozen and its hash is recorded; no post-freeze edits are used for analysis.

### Role B — evaluation readiness

- [ ] Raw result JSONL exists for each planned model and run, following the full contract.
- [ ] Main repeat coverage and all configured noise-subset repeats are present or explicitly documented as missing.
- [ ] Raw results have been checked for contract errors, duplicates/retry history, invalid answers, and unresolved failures.
- [ ] Run log identifies model strings, providers, run IDs, UTC timestamps, prompt hashes, and run outcomes.

### Role C — analysis readiness

- [ ] The frozen dataset and canonical validated results are available; join and coverage checks pass.
- [ ] Human verification/kappa sheets are completed by assigned raters; kappa is computed only from actual ratings.
- [ ] AFR is calculated on RU-P/RU-R/RU-X with both invalid-answer treatments and clear denominators.
- [ ] Domain, NU comparisons, RT analysis, noise baseline, and regression are run only where their pairing/coverage requirements are satisfied.
- [ ] Edit-distance input is measured (not the NaN placeholder), and token counts use the stated open-tokenizer proxy if included.
- [ ] Derived tables/figures and written claims are reproducible from the frozen items, raw outputs, and recorded analysis settings.

**Overall status:** Not ready for empirical analysis. Existing implementations can be reused, but the frozen item file, raw evaluation outputs, completed human ratings, and measured edit-distance input are still prerequisites. No AFR or kappa value is reported here.
