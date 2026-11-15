# Execution Plan: 3 Phases, 4 Days, 3 People in Parallel

This plan compresses an 8-week single-researcher proposal into 4 days for three people. That is only possible if the work is split along **interfaces** (see `CONTRACTS.md`) so nobody waits for anybody, and if quality gates are respected. Read the "What is cut, and what is never cut" section before starting.

## 0. Principles

1. **Contracts first.** Agree on file schemas in the first 2 hours; after that, A, B and C can build against the schema, using mock data, without waiting for each other.
2. **One owner per folder.** A: data. B: evaluation. C: analysis and validation.
3. **Start the free-API clock early.** Free-tier rate limits are the main schedule risk. B starts Nastaliq (NU) runs as soon as the sample exists, because NU needs no manual verification.
4. **Human gates cannot be skipped.** Manual verification and the kappa check decide whether the data is valid.
5. **Freeze before running.** Main runs happen only on frozen data.

## 0b. Who does what (by name, all three working at the same time)

Provisional assignment (swap before G0 if needed): **Zia Ullah = B (Evaluation, repo lead, PR reviewer)**, **Sudais Khan = A (Data)**, **Younas Khan = C (Analysis & validation)**.

| | **Zia Ullah (B)** | **Sudais Khan (A)** | **Younas Khan (C)** |
|---|---|---|---|
| **Phase 1, Day 1** | Repo skeleton and rules; runner, prompt, parser, cache, mock test; starts NU runs when the sample is committed | UrduMMLU schema check; 500-item sample; RU-P draft; `RULES.md` v0 | Stats code on synthetic data; annotation templates; literature table; PURUTT license check |
| **Phase 2a, Day 2** | Finish NU runs; dry-run pipeline; noise-subset config; verify own third of the 100 items; review PRs | RU-R and RU-X rule engines with tests; RT; edit distances; verify own third | Kappa script; token counts; verify own third; check edit-distance report |
| **Phase 2b, Day 3** | Runs model 1 and the noise subset on own keys; monitors invalid rate and the run log | Runs model 2 on own keys; prepares the error-analysis sheet | Runs model 3 (and 4 if used) on own keys; analysis on partial results |
| **Phase 3, Day 4** | Methods and reproducibility section; clean repo, fresh-clone test, tag `v1.0` | RQ4 error categorisation and token covariate; introduction and related work; dataset card | RQ1–RQ3 statistics, tables and figures; results and limitations section |

How the parallel work stays unblocked:
- **No one waits for anyone on Day 1.** Zia tests the runner on mock items, Younas tests stats on synthetic data, and Sudais produces the real sample; all three follow `CONTRACTS.md`.
- **If you finish early,** pick up the next unassigned item from the cut-list order in section 6 or review a teammate's open PR; do not start editing another person's folder.
- **Verification is split three ways on Day 2** (about 33 items each, none of it your own generated output). For the kappa check, two different people independently rate the same 50 items.

## 1. Request budget (to plan API usage)

| Run | Calculation | Requests |
|---|---|---|
| Main | 500 items × 5 conditions × 4 models | 10,000 |
| Noise subset (2 extra repeats) | 30 items × 5 conditions × 4 models × 2 | 1,200 |
| **Total** | | **≈ 11,200** |

**Decision: 500 items** (confirmed by the team; the proposal's work-plan table says 500, while its abstract, power note and feasibility section still say 200 and must be updated to match). At 500 items, 95% intervals on accuracy are about ±4–5 points. The cost is volume: ~11,200 requests in a 4-day sprint is the main schedule risk. Per-day and per-minute limits of each free tier must be checked on the provider's page on Day 1 and written into `configs/models.yaml`; they change, so do not rely on memory.

---

## 2. Phase 1: Foundation (Day 1)

**Goal:** contracts agreed, sample drawn, first RU-P draft, harness works end-to-end on NU.

### Day 1, hours 0–2: all three together (Gate G0)

- [ ] Create repo skeleton and folder ownership (see README); add `.gitignore` and `.env.example`.
- [ ] Review and agree `CONTRACTS.md` (any change now is cheap; after G0 it is expensive).
- [ ] Fix: random seed, the prompt template text, the 3–4 models and providers, and the decision on what is transformed (**question stem and all option texts**; option letters A–D stay Latin).
- [ ] Each person creates their own API keys and confirms they work.
- [ ] Choose the RT transliteration tool and the non-evaluated LLM for the RU-P draft. Record both in `docs/RULES.md`. The drafting LLM must not be one of the evaluated models.

### Day 1, hours 2–10: parallel work

| | Tasks | Output |
|---|---|---|
| **A: Data** | Download UrduMMLU; inspect the real schema (fields, number of options, answer format) and update `CONTRACTS.md` if needed. Write `sample.py`: stratified 500 items (100 per domain, fixed seed), ordered by `sample_rank` so that the first 40 per domain form a **nested 200-item fallback subset**, exclusion filter for formula/symbol/English-term-dominated items (count what is excluded). Commit `items_nu.jsonl`. Draft RU-P with the non-evaluated LLM. Start `docs/RULES.md`. | `data/processed/items_nu.jsonl`, RU-P draft in `data/interim/`, rules v0 |
| **B: Evaluation** | `src/eval/`: provider clients with retry and rate-limit handling, prompt builder, answer-letter parser, **resumable cache** (never repeat a finished request), run logger. Test on 10 mock items. When A commits `items_nu.jsonl`, **start NU runs** on every model. | Working runner, first NU outputs in `results/raw/` |
| **C: Analysis & validation** | Write analysis functions on **synthetic data** that follows the results schema: flip rate across variants, bootstrap 95% CI, McNemar with Holm correction, Fleiss' kappa, logistic mixed-effects (item random intercept). Build annotation sheet templates (verification and kappa). Start `docs/LITERATURE.md`: re-run the searches and **read the full text** of the closest papers listed in the proposal; check the PURUTT license. | Tested stats code, annotation templates, literature table |

### Gate G1 (end of Day 1)

- [ ] `items_nu.jsonl` committed, 500 items, seed recorded, nested 200-item subset marked.
- [ ] RU-P draft exists for all 500 items.
- [ ] Runner completes NU for at least one model with parsed answers.
- [ ] Stats code passes its tests on synthetic data.

---

## 3. Phase 2: Build, verify, freeze, run (Days 2–3)

**Goal:** a verified, frozen dataset by end of Day 2; all model outputs by end of Day 3.

### Day 2 (verify and freeze)

| | Tasks | Output |
|---|---|---|
| **A** | Implement **deterministic rule engines** for RU-R and RU-X from RU-P, with unit tests (the same input always gives the same output). Implement RT (RU-P back to Nastaliq). Compute mean character edit distances between variants. | `src/data/`, `data/interim/` variants, edit-distance table |
| **B** | Finish NU runs for all models. Dry-run the full pipeline on the RU-P *draft* **only to test code** (these outputs are discarded, not results). Prepare the noise-subset configuration (30 items, fixed IDs). | NU baseline complete, pipeline verified |
| **C** | Prepare the kappa script and the verification workflow. Compute token-length per item with an open tokenizer as proxy (state this as a limitation). | `annotations/`, kappa script, token counts |
| **All** | **Manual verification:** 100 items fully checked (prioritise the nested 200 subset first), split about 33 per person, and each person checks items they did **not** draft or generate. For the kappa check, two different people independently rate the same 50 items for meaning preservation. Spot-check the remaining 400 items (decide the spot-check sample size at G0; the < 10% error criterion applies to it). Log every correction. | Verified sheets, corrections log |

### Gate G2 (end of Day 2): freeze

- [ ] Spot-check error rate < 10% (otherwise fix the rules, re-check, and report this honestly).
- [ ] Cohen's kappa on 50 items computed. Target ≥ 0.80. **If it is lower, do not adjust the numbers; revise the rules, re-rate, and report the initial value in the paper.**
- [ ] Final `items_v1.jsonl` written; SHA-256 recorded in `data/processed/FROZEN.md`. **No edits after this point.**

### Day 3 (run everything)

Each person runs a different model/provider **on their own machine and keys** using the same code, so rate limits are used in parallel. Outputs go to `results/raw/<model>/`, one file per run, matching `CONTRACTS.md`.

| | Tasks |
|---|---|
| **B** | Lead the runs; monitor errors, retries, and invalid-answer rate per condition; maintain the run log. |
| **A** | Run their share of models; in parallel, prepare the error-analysis sheet (40–50 failing items) once outputs appear. |
| **C** | Run their share of models; run noise-subset analysis first (3 repeats), then run the analysis scripts on partial results as they arrive. |

Order of runs: (1) noise subset, (2) main run per model, (3) retries for failures.

### Gate G3 (end of Day 3)

- [ ] All planned model × condition × item results present (or the missing ones documented, with a reason).
- [ ] Invalid/unparsable rate < 5% per condition, or handled explicitly.
- [ ] `results/raw/` committed with model strings and UTC dates in the logs.

---

## 4. Phase 3: Analysis, writing, release (Day 4)

**Goal:** all analyses done, a complete draft, and a reproducible release.

| | Analysis task | Writing task | Release task |
|---|---|---|---|
| **A** | RQ4: categorize 40–50 errors (numerals, named entities, unit symbols, other); token length as a covariate | Introduction, related work (from the verified `LITERATURE.md` only) | Dataset card, edit-distance table, attribution/license |
| **B** | Check invalid rates, noise baseline across models; sanity checks (e.g., flip counts reproduced by a second script) | Methods and reproducibility | Clean repo, pinned `requirements.txt`, script that regenerates tables from `results/raw/`, tag `v1.0` |
| **C** | RQ1–RQ3: flip rates, CIs against noise, McNemar + Holm, mixed-effects, NU vs RT analysis; tables and figures | Results and limitations | Final figures and tables in `results/` |

Final steps (all three together, last 3 hours):

- [ ] Claims audit: every sentence in the draft is checked against a table or a verified source. Use conservative wording; do not claim state-of-the-art or novelty beyond what the literature table supports.
- [ ] Every cited paper has been opened and checked against its full text (the proposal itself warns that its related-work entries came from search snippets).
- [ ] Repeat the "closest prior work" searches (e.g., "Roman Urdu" spelling variants LLM; "romanized" MMLU) and record the date and result.
- [ ] Fresh-clone test: a teammate who did not write the code reproduces one table from the repository.

### Gate G4 (end of Day 4)

- [ ] Draft complete; code, frozen data, rules, logs released under `v1.0`.

Note: submitting to a venue is outside this 4-day scope. The deadline and format of the target workshop (AbjadNLP, LoResLM, or another) have to be checked separately. The proposal itself marks these CFPs as "to be verified".

---

## 5. Git workflow for three people on Antigravity

- Branch names: `a/…`, `b/…`, `c/…`. Small PRs (aim for several per day), reviewed by one other person, merged quickly. Rebase on `main` at least twice per day.
- Commit messages: `data: add RU-R rule for vowel elision`, `eval: resume from cache`, `analysis: add Holm correction`.
- **Each Antigravity agent has its own session; the repository is the only shared memory.** At the start of every session, give the agent: `README.md`, `docs/PLAN.md`, `docs/CONTRACTS.md`, and your role/folder, and tell it not to touch other owners' folders.
- Ask agents for tests with every module, and review diffs yourself. AI-generated spelling rules and statistics code are the two places where silent mistakes cost the most.
- Use GitHub Issues (one per task, labelled A/B/C and phase). Keep the README progress table updated only at gates, to avoid conflicts.
- Never commit `.env` or API keys.

## 6. What is cut, and what is never cut

**Cut in this order if time runs out:**
0. **Fall back from 500 to the nested 200-item subset** if free-tier limits or verification time make 500 infeasible (decide by the middle of Day 2, and report the final N honestly; do not mix partially run items).
1. PURUTT real-usage check (optional here; also needs a license check).
2. The 4th model (3 models from different families are enough for the primary analysis).
3. RQ4 failure categorization reduced from 40–50 to about 30 errors.
4. Tokenizer analysis (it is only a covariate, with low novelty).

**Never cut:**
- Manual verification and the kappa check.
- The noise-subset baseline (without it, flips cannot be interpreted).
- Frozen data and run logs.
- Reporting null or unfavourable results.

## 7. Main risks for this schedule

| Risk | Mitigation |
|---|---|
| Free-tier daily limits stop the runs (10,000+ main requests) | Start NU on Day 1–2; resumable cache; run models in parallel on three keys; fall back to 3 models |
| Verification takes longer than expected | Start manual checks as soon as RU-P draft exists (Day 1 evening); cut PURUTT first |
| Kappa < 0.80 | Revise rules and re-rate; report the initial value honestly |
| A provider changes or removes a model mid-run | Log model strings and dates; re-run the affected cells only |
| Merge conflicts | Folder ownership, small PRs, schemas fixed at G0 |
| A closer prior study is found late | Repeat searches on Day 1 and Day 4; adjust claims, not data |
