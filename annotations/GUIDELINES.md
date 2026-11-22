# Human Verification Guidelines: Roman Urdu Spelling Instability Study

**Document Version:** 1.0  
**Phase:** Gate G2 Preparation  
**Applicability:** Reviewers validating Roman Urdu orthographic variants (`RU-P`, `RU-R`, `RU-X`) against source Nastaliq (`NU`) items from UrduMMLU.

---

## 1. Overview and Core Objective

The primary scientific objective of this study is to measure whether LLMs change their answers solely due to spelling variations of the same exam question. This measurement is **scientifically valid only if all Roman Urdu variants differ exclusively in orthography (letters)**.

The questions must never change in:
- Meaning, semantics, or scope.
- Word choice, vocabulary, or phrasing.
- Grammatical register, tone, or formality.
- Numerical, mathematical, or scientific values.

As a human verifier, your role is to strictly audit candidate items and identify any deviation from these invariants before data is frozen at Gate G2.

---

## 2. Verification Protocol & Cardinal Invariants

1. **Independent Evaluation:** Reviewers must work independently without discussing individual ratings until sheets are submitted.
2. **Drafting Segregation Rule:** *No person may verify an item they drafted, generated, or transliterated themselves.*
3. **Double-Rating Subset (Cohen's Kappa):** 50 items are independently double-rated by two reviewers to compute inter-rater reliability.
   - Target agreement: **Cohen's $\kappa \ge 0.80$**.
   - If $\kappa < 0.80$, ratings must **never be altered or dropped**. The initial value must be reported, rules in `docs/RULES.md` revised, variants regenerated, and items re-rated.
4. **Pass/Fail Threshold:** The overall error rate across verified items must remain **below 10%**.

---

## 3. The Four Verification Criteria

For each assigned row in the verification sheet, evaluate the item across these four mandatory criteria:

### Criterion 1: Meaning Preserved (`meaning_preserved` = `y`/`n`)
* **Definition:** Does the transliterated Roman Urdu question and every option convey the exact same semantic question and truth conditions as the original Nastaliq (`NU`) source text?
* **Mark `y` if:**
  - A native Urdu speaker reading the Roman Urdu text would understand the identical exam question and options as the Nastaliq text.
* **Mark `n` if:**
  - Negation is lost or added (e.g. `nahin` omitted or inserted).
  - Scope or quantifiers are altered (e.g. "تمام" (all) transliterated as "kuch" (some)).
  - A technical term or concept is distorted into an unrelated word.
  - Tense, modality, or conditional logic is altered.

### Criterion 2: Words Unchanged (`words_unchanged` = `y`/`n`)
* **Definition:** Are the exact same lexical words preserved in the exact same word order?
* **Mark `y` if:**
  - Word-for-word alignment with the source Urdu is maintained.
  - Only spelling changes between letters (e.g., `jawab` vs `jwab`).
* **Mark `n` if:**
  - English translations are substituted for Urdu words (e.g. translating "درست" to "correct" instead of transliterating as `durust`).
  - Synonyms or colloquial paraphrasing are introduced (e.g. replacing "والدین" with `ammi abbu`).
  - Words are added, deleted, or reordered.

### Criterion 3: Protected Tokens OK (`protected_tokens_ok` = `y`/`n`)
* **Definition:** Are all protected tokens preserved exactly as they appeared in the source text without alteration?
* **Protected Tokens Include:**
  - **Digits & Numerals:** ASCII digits (`15`, `90`, `3.14`) and Urdu-script numerals (`۱۵`).
  - **Option Labels:** Latin labels `A)`, `B)`, `C)`, `D)`.
  - **Scientific Notation & Units:** e.g. `10^-34`, `kg`, `cm`, `Js`, `Hz`, `mol`, `pH`.
  - **Chemical Formulas & Math Symbols:** e.g. `H2O`, `CO2`, `+`, `=`, `%`.
  - **URLs & Latin Technical Terms:** Any pre-existing English terms in Latin script.
  - **Fill-in-the-Blank Lines:** Underscore sequences (e.g. `____`).
* **Mark `y` if:** All protected tokens match the source text character-for-character.
* **Mark `n` if:** Any digit, formula, unit, or option label was translated, modified, or omitted.

### Criterion 4: Convention Followed (`convention_followed` = `y`/`n`)
* **Definition:** Does the spelling adhere to the approved project rules in `docs/RULES.md`?
* **Condition-Specific Standards:**
  - **RU-P (Primary / Standardized Roman Urdu):**
    - Adheres to standard function word spellings (`mein`, `se`, `ke`, `ka`, `ki`, `hai`, `hain`, `nahin`, `kya`, `yeh`, `woh`, `aur`).
    - Negative particle is spelled `nahin` (never `nahi`, `nhi`, or `nehn`).
    - Vowel representation follows C1 (short/long "a" as `a`).
    - Consults `src/data/rules/ru_p_lexicon.csv`.
  - **RU-R (Reduced Roman Urdu):**
    - Exhibits casual/speed-typing shortenings per `ru_r_wordmap.csv` and `ru_r_rules.csv` (e.g. `nahin` -> `nhi`, `jawab` -> `jwab`, `jagah` -> `jaga`).
    - Preserves token counts (1 token maps to 1 token).
  - **RU-X (English-Orthography Roman Urdu):**
    - Uses English orthographic habits per `ru_x_rules.csv` (e.g. `x` for `kh`, `k` for `q`, `f` for `ph`, `v` for `w`).
    - Preserves token counts and protected tokens.
* **Mark `y` if:** The spelling conforms to the targeted condition's conventions.
* **Mark `n` if:** The spelling introduces unapproved conventions or breaks token alignment.

---

## 4. How to Record Annotations

### Verification Sheet Format (`verification_pending_assignment.csv`)

| Column | Allowed Values | Action / Guideline |
|---|---|---|
| `item_id` | e.g. `umm-0001` | Pre-populated item identifier. Do not modify. |
| `condition` | `RU-P`, `RU-R`, `RU-X` | Pre-populated condition variant. Do not modify. |
| `rater` | Reviewer Name | Replace `PENDING_ASSIGNMENT` with your name (e.g. `Younas` or `Zia`). |
| `meaning_preserved` | `y` or `n` | Enter lowercase `y` or `n`. |
| `words_unchanged` | `y` or `n` | Enter lowercase `y` or `n`. |
| `protected_tokens_ok` | `y` or `n` | Enter lowercase `y` or `n`. |
| `convention_followed` | `y` or `n` | Enter lowercase `y` or `n`. |
| `corrected_text` | Free text | If any criterion is `n`, enter your proposed corrected text. Leave blank if all are `y`. |
| `note` | Free text | Explain the issue or note any dialectal ambiguity. |

---

## 5. Cohen's Kappa Workflow (50 Double-Rated Items)

1. Two independent raters receive `annotations/kappa_pending_assignment.csv`.
2. Each rater fills in their designated column (`rater_1` or `rater_2`) with `y` or `n` evaluating `meaning_preserved`.
3. Neither rater may inspect or discuss the other's ratings until both have completed the sheet.
4. Save the completed sheet as `annotations/kappa_50_checked.csv` (encoded in UTF-8 without BOM).
5. Run the validation CLI:
   ```powershell
   python -m src.analysis.kappa --sheet annotations/kappa_50_checked.csv
   ```
6. The CLI reports observed raw agreement $P_o$ and Cohen's $\kappa$. Target: $\kappa \ge 0.80$.

---

## 6. Logging Invariant Violations and Rule Updates

When candidate text fails verification:
1. Record `n` in the corresponding criterion column and specify the recommended fix in `corrected_text`.
2. Report systematic or recurring errors to the team.
3. Recurring errors become formal rule additions:
   - Lexical additions go into `src/data/rules/ru_p_lexicon.csv`.
   - Transformation fixes go into `ru_r_wordmap.csv`, `ru_r_rules.csv`, or `ru_x_rules.csv`.
   - Update `docs/RULES.md §11` (Rule Version Log) and bump rule version.
   - Regenerate affected candidate items and re-verify.
