# RULES: Spelling Operation Rules for RU-P, RU-R, RU-X and RT

**Owner:** Role A (Sudais Khan). **Reviewers:** Zia Ullah, Younas Khan (a different person reviews every change).
**Status:** `v2 DRAFT`. Everything marked *PROPOSED* or *CANDIDATE* is a starting point, **not a decision**.
A native Urdu reader must confirm each item before the data freeze (Gate G2). Nothing in this file may be changed after G2.

Related files: `CONTRACTS.md` (data schema), `PLAN.md` (schedule and gates), `LITERATURE.md` (evidence for the operations).

---

## 0. Why this file matters

The primary outcome of the study is **answer instability across Roman Urdu spellings of the same question**. That result is only valid if the three Roman Urdu versions (RU-P, RU-R, RU-X) differ **only in letters**: not in words, word order, formality or register. These rules define exactly what is allowed to change. If they are vague, the result cannot be interpreted.

## 1. Decisions to record at Gate G0 (fill in; do not leave blank)

| # | Decision | Value | Decided by / date |
|---|---|---|---|
| 1 | Non-evaluated LLM used to draft RU-P (must NOT be one of the evaluated models) | PENDING (model string and provider) | |
| 2 | Tool/model used for RT (RU-P back to Nastaliq) | PENDING (name, version, settings) | |
| 3 | Random seed for sampling | 42 | Zia Ullah, covering for Sudais, 2026-11-19 |
| 4 | Size of the spot-check sample on the 400 items not fully verified | 60 items, 12 per domain, sampled from outside the 100 fully verified items with seed 42 | Zia Ullah, covering for Sudais, 2026-11-19 |
| 5 | Punctuation policy (section 3.4) confirmed | Confirmed as written in section 3.4 | Zia Ullah, covering for Sudais, 2026-11-19 |
| 6 | Number of options per item (from the real UrduMMLU schema) | Both 4-option and 5-option items are allowed. Preserve original option order; for 5-option items, E is a valid answer. Do not replace 5-option items. | Team-agreed policy; confirmed by Roles A, B and C |
| 7 | Who verifies which item ranges (section 9.1) | PENDING; do not assign Zia to RU-R/RU-X or items with rules authored by Zia | |

## 2. What is transformed

Following `CONTRACTS.md`:

- The **question stem** and **every option text** are transformed in RU-P, RU-R, RU-X (and RT is derived from RU-P).
- The **option letters** shown to the model (A, B, C, D, E as applicable) are always Latin and never change.
- `gold` (the correct letter) and the **order of options** never change.
- Both 4-option and 5-option items are retained in the dataset. No five-option item is replaced merely to force a four-option format.
- NU is the original UrduMMLU text, untouched.

## 3. Invariants (must hold for every item; the code tests them)

These are the register-control rules. Violating any of them makes the item invalid.

1. **Same words.** RU-P, RU-R and RU-X contain exactly the same words as one another, in the same order. Only the spelling of those words may differ.
2. **Same token count.** The number of whitespace-separated tokens is identical across RU-P, RU-R and RU-X for the question and for each option.
   (If a source text contains joiners or spacing quirks that make this check unreliable, record the exception in the item's `notes`, do not silence the test.)
3. **No additions, no deletions.** No slang, no English insertions, no filler words, no change of formality, no paraphrase, no "fixing" of the source text.
4. **Protected tokens are unchanged** (section 3.3).
5. **One word, one spelling per condition.** Within a condition, the same Urdu word is spelled the same way everywhere in the dataset (enforced through the RU-P lexicon, section 4.3). Variation exists **between** conditions, not within one.
6. **Determinism.** The same input always produces the same output (no randomness, no model calls in RU-R/RU-X).

### 3.3 Protected tokens (never altered by RU-R or RU-X)

- Digits and numbers: kept exactly as in the source, including Urdu-script digits, unless the team decides otherwise at G0 and logs it in section 11.
- Option labels A, B, C, D and E, where applicable.
- Formulas, chemical symbols, units and mathematical notation.
- URLs, email addresses, code-like strings.
- English words already written in Latin script in the source.
- Proper names whose spelling the question depends on (flag them in `notes` during drafting).

### 3.4 Punctuation (PROPOSED; confirm at G0)

Convert Urdu punctuation to its Latin counterpart **identically in RU-P, RU-R and RU-X**, so punctuation is never a hidden difference between the variants:
`ØŸ` to `?`, `ØŒ` to `,`, `Û”` to `.`. Quotation marks and brackets are kept as they are. Record any change to this policy in section 11.

## 4. RU-P: phonetic Roman Urdu (the reference spelling)

**Purpose:** a single, consistent, phonetic Roman spelling per Urdu word. RU-R and RU-X are derived from RU-P by rule.

### 4.1 Principles

- One fixed spelling per word, used everywhere (lexicon-driven, section 4.3).
- Phonetic, consistent conventions, not "creative" spellings.
- Transliterate only. **Do not translate, summarise, correct or reword.**

### 4.2 Convention decisions (PROPOSED defaults; a native reader confirms each on Day 1)

Examples are taken from common function words and the illustrative forms in the proposal. They are meant to anchor the conventions, not to be exhaustive.

| # | Decision | PROPOSED default | Examples | Confirmed? |
|---|---|---|---|---|
| C1 | Short and long "a" sounds | Written as `a` | `nahin`, `jawab`, `sawal` | â˜ |
| C2 | The negative word | `nahin` | | â˜ |
| C3 | Common function words | Fixed forms | `kya`, `yeh`, `woh`, `aur`, `ke`, `ki`, `ko`, `se`, `mein`, `hai`, `hain` | â˜ |
| C4 | Aspirated consonants | Consonant + `h` | to be listed from real items | â˜ |
| C5 | Digraphs for single Urdu sounds | `kh`, `gh`, `sh`, `ch`, `zh`, `q` | | â˜ |
| C6 | Distinctions Roman letters cannot express (e.g. retroflex vs dental, several "s/z/t/h" letters) | Not distinguished in RU-P | | â˜ |
| C7 | Nasalisation | Written with `n` | | â˜ |
| C8 | Izafat and compound words | Decide one convention; document examples | | â˜ |
| C9 | Hamza and ain | Decide one convention; document examples | | â˜ |

**Procedure:** apply the defaults to a **pilot of 30 items**, have native readers review them, correct the table, and only then run the drafting step on all 500.
Every correction made later is logged and, if it recurs, becomes a rule (section 9.4).

### 4.3 RU-P lexicon (keeps spelling consistent)

`src/data/rules/ru_p_lexicon.csv`: columns `urdu_word, ru_p, note`. It starts small (high-frequency words) and **grows from review corrections**.
The draft step must look up the lexicon first, so the same word is never spelled two ways within RU-P.

### 4.4 Drafting and review

1. A non-evaluated LLM (decision 1) drafts RU-P for the question and options of each item. The prompt must say: transliterate only; do not translate or correct; keep protected tokens unchanged; follow the conventions in section 4.2; return structured output.
2. The draft is **never trusted**. It enters manual verification (section 9).
3. Record the exact prompt text and model string used, in this file or in `data/interim/`.

## 5. RU-R: reduced Roman Urdu

**Idea:** how people type fast. Shortened forms, dropped vowels. **Same words as RU-P**, only fewer letters.

### 5.1 Operations (CANDIDATES; each must be confirmed and tested before use)

| ID | Operation | Scope | Example (illustrative) | Evidence of use | Status |
|---|---|---|---|---|---|
| R1 | Drop a non-initial vowel in listed words | Word map only | `jawab` to `jwab`, `sawal` to `swal` | Check Soomro et al. list / real text | CANDIDATE |
| R2 | Shortened forms of very frequent words | Word map only | `nahin` to `nhi` | Check Soomro et al. list / real text | CANDIDATE |
| R3 | Further common casual shortenings | Word map only | add only if attested | | CANDIDATE |

### 5.2 Rules for adding an operation

An operation may enter RU-R only if (a) it is attested in a real spelling-variant source (e.g. the spelling-variant list in Soomro et al. 2024, or real text such as PURUTT if its license allows use), **or** (b) it is explicitly documented as a *synthetic* operation and reported as such in the paper.
Each operation needs at least 3 unit-test examples.

### 5.3 Machine-readable form

`src/data/rules/ru_r_wordmap.csv`: columns `ru_p, ru_r, op_id, note` (exact whole-word replacements).
`src/data/rules/ru_r_rules.csv`: ordered regex rules, columns `order, pattern, replacement, op_id, note` (applied after the word map, whole words only).

## 6. RU-X: English-orthography Roman Urdu

**Idea:** spelling habits borrowed from English orthography. **Same words as RU-P**, only different letter choices.

### 6.1 Operations (CANDIDATES; confirm before use)

| ID | Operation | Example (illustrative) | Evidence of use | Status |
|---|---|---|---|---|
| X1 | `x` for the sound `kh` | `xuda` | **Not yet shown to be attested; the proposal calls it illustrative** | CANDIDATE (verify or replace) |
| X2 | `k` for `q` | `kalam` | Verify | CANDIDATE (verify or replace) |
| X3 | English digraph habits (e.g. doubled vowels reduced or expanded, `f` for `ph`) | to be listed | Verify | CANDIDATE |

If X1 or X2 cannot be shown to occur in real Roman Urdu text, replace them with attested English-orthography habits and record the replacement in section 11.
This is a validity point for the paper: RU-X must represent a plausible spelling style, not an arbitrary code.

### 6.2 Machine-readable form

`src/data/rules/ru_x_rules.csv`: ordered regex rules, columns `order, pattern, replacement, op_id, note`. Applied whole-word, never inside protected tokens.

## 7. Rule engine specification (for `src/data/`)

1. **Order of operations:** mask protected tokens, then apply word map (exact whole words), then ordered regex rules, then unmask.
2. **Rules are data.** Rule tables are CSV files; changing a rule must not require changing code.
3. **Deterministic and idempotent:** the same input gives the same output; applying the engine to its own output changes nothing.
4. **Hard failures, not silent fixes:** if an invariant in section 3 is violated, the engine raises an error that names the item and the invariant.
5. **Unit tests** (in `tests/` or next to the module): each operation (3+ examples), protected-token preservation, token-count equality, determinism, idempotence.
6. **Report unmatched words:** list words that no rule touched, so reviewers can see where the variants are identical to RU-P (a variant equal to RU-P is flagged, not hidden).

## 8. Edit distance (shows the manipulation is real)

- Metric: character-level Levenshtein distance, computed per field (question and each option) between each pair: RU-P vs RU-R, RU-P vs RU-X, RU-R vs RU-X.
- Report **both** the mean raw distance and the mean length-normalised distance (distance divided by the longer string).
- Output `results/tables/edit_distance.csv` (`variant pair, mean_char_edit_distance`, plus the normalised column). Also report the share of items where a variant equals RU-P.
- Use the same normalisation of text (the same punctuation policy and no extra whitespace differences) before measuring.

## 9. Verification protocol (Day 2; never cut)

### 9.1 Full check of 100 items

- 100 items fully checked, **nested 200-item subset first**, split about 33 per person.
- **Nobody checks an item they drafted or generated themselves.**
- For each item and each Roman Urdu condition the checker records (columns for `annotations/` sheets): `item_id, condition, rater, meaning_preserved (y/n), words_unchanged (y/n), protected_tokens_ok (y/n), convention_followed (y/n), corrected_text, note`.

### 9.2 Kappa check

- Two different people independently rate the **same 50 items** for meaning preservation (y/n).
- Compute Cohen's kappa. Target is at least 0.80.
- **If kappa is below 0.80:** do not adjust the numbers. Revise the rules, re-rate, and **report the initial value** in the paper.

### 9.3 Spot-check of the remaining items

- The size is fixed at G0 (decision 4). Guidance: with a spot-check of n items and **zero** errors found, the 95% upper bound on the true error rate is roughly 3/n (for n = 60, about 5%). The pass criterion from the proposal is an error rate **below 10%**; choose n so that this is meaningful.
- Sample at random, stratified by domain, with the seed recorded.
- If the error rate is 10% or more: fix the rules, regenerate the affected variants, re-check, and report this honestly.

### 9.4 Corrections log

Every manual correction is logged. A correction type that recurs becomes a rule (word-map entry or regex), the rule version is bumped (section 11), the variants are regenerated and the affected items are re-checked.

## 10. RT: round-trip (diagnostic only)

- RT is RU-P transliterated back to Nastaliq with the tool recorded in decision 2.
- **Transliterate only:** no translation, no corrections, protected tokens unchanged.
- For every item compute a character-level similarity between RT and the original NU text and keep it in the item's notes or in a side table.
- RT is a **diagnostic, not ground truth**: automatic back-transliteration is imperfect. If RT and NU differ, that difference may come from the tool, not from the model.
- `gold` and option order are unchanged. RT items follow the same `CONTRACTS.md` schema.

## 11. Rule version log (append only; newest first)

| Version | Date | Author | Change | Why | Items affected / re-checked |
|---|---|---|---|---|---|
| v2 | 2026-11-28 | Role A (team-agreed policy) | Superseded the v1 four-option-only decision; retain all original 4-option and 5-option items without replacement | Keep the dataset faithful to the source schema and the agreed 4/5-option policy | 500 items: 497 with 4 options and 3 with 5 options |
| v1 | 2026-11-19 | Zia Ullah (covering for Sudais) | Recorded decisions 3â€“6; replaced the three selected five-option records with next-ranked four-option records in the same domains | Keep the 500-item sample at four options per item while preserving the seed-42 stratified order | `umm-0118`, `umm-0266`, `umm-0401`; no Roman Urdu variants exist yet |
| v0 | (start) | A | Initial draft created | Kick-off | none |

## 12. Acceptance checklist before the freeze (Gate G2)

- [ ] All G0 decisions in section 1 are filled in.
- [ ] Every convention in section 4.2 is confirmed by a native reader (or its change is logged).
- [ ] Every operation used in RU-R and RU-X is confirmed, attested or documented as synthetic, and tested.
- [ ] Invariants (section 3) hold for all 500 items; no unexplained exceptions.
- [ ] Edit-distance report produced; variants differ measurably and the share of unchanged variants is reported.
- [ ] 100 items fully verified; kappa on 50 items computed (initial value kept).
- [ ] Spot-check done; error rate below 10%, or the fix-and-recheck cycle is documented.
- [ ] RU-P lexicon, rule CSVs and this file are committed; their SHA-256 hashes go into `data/processed/FROZEN.md` with the dataset hash.
