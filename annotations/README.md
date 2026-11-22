# Manual Verification & Inter-Rater Reliability (Gate G2)

This directory contains the templates, guidelines, and instructions for Phase 2 manual validation of Roman Urdu orthographic variants (`RU-P`, `RU-R`, `RU-X`).

---

## 1. Files in this Directory

- `verification_template.csv`: Schema-only template for full 100-item verification across all three Roman Urdu conditions.
- `verification_pending_assignment.csv`: Prepared 300-row file covering the 100 items from the nested 200 fallback subset (`umm-0001` through `umm-0100`) across `RU-P`, `RU-R`, and `RU-X`, with raters flagged as `PENDING_ASSIGNMENT` awaiting Gate G0/G1 formal designation.
- `kappa_template.csv`: Schema-only template for the 50-item double-rated inter-annotator agreement check.
- `kappa_pending_assignment.csv`: Prepared 50-item double-rating template covering items `umm-0001` through `umm-0050` across `RU-P`.
- `GUIDELINES.md`: Comprehensive human verification manual covering all four criteria, edge cases, examples, and the Kappa calculation workflow.
- `README.md`: Protocol overview, instructions for Google Sheets, and verification workflow.

---

## 2. Verification Protocol & Work Split (Day 2)

Per `PLAN.md` (Gate G2) and `RULES.md` (Section 9):

1. **Full Check of 100 Items:**
   - 100 items are fully verified across conditions (`RU-P`, `RU-R`, `RU-X`), prioritizing the nested 200-item fallback subset first.
   - The workload is divided equally among the three team members (~33 items per person).
   - **Cardinal Rule:** Nobody checks an item they drafted or generated themselves.

2. **Inter-Rater Agreement (Kappa Check):**
   - Two different team members independently rate the **same 50 items** for `meaning_preserved` (`y`/`n`).
   - Agreement is evaluated using Cohen's kappa ($\kappa$).
   - **Quality Criterion:** Target Cohen's $\kappa \ge 0.80$.
   - **Handling Lower Values:** If $\kappa < 0.80$, do NOT adjust the ratings. Revise the spelling rules (`docs/RULES.md`), regenerate the variants, re-rate, and report the initial $\kappa$ honestly in the paper.

3. **Spot-Check of Remaining 400 Items:**
   - Sample at random across domains.
   - The error rate must remain **below 10%**. Any systematic error found must be logged, added to the deterministic rule engine, and re-tested.

---

## 3. Annotation Columns & Criteria

### Full Verification Sheet (`verification_template.csv`)

| Column | Allowed Values | Description |
|---|---|---|
| `item_id` | e.g. `umm-0001` | Unique question identifier from UrduMMLU sample. |
| `condition` | `RU-P`, `RU-R`, `RU-X` | The Roman Urdu variant being checked. |
| `rater` | e.g. `Zia`, `Sudais`, `Younas` | Name / handle of the reviewer. |
| `meaning_preserved` | `y` / `n` | Is the semantic meaning identical to the original Nastaliq (`NU`) item? |
| `words_unchanged` | `y` / `n` | Are the exact same words and word order preserved? No slang, no paraphrasing, no register changes. |
| `protected_tokens_ok` | `y` / `n` | Are digits, math symbols, units, English terms, and option labels untouched? |
| `convention_followed` | `y` / `n` | Does the spelling adhere to the rules in `docs/RULES.md`? |
| `corrected_text` | Text | Suggested correction if any invariant was violated. |
| `note` | Text | Optional notes on ambiguity, dialect, or tokenization quirks. |

### Kappa Sheet (`kappa_template.csv`)

| Column | Allowed Values | Description |
|---|---|---|
| `item_id` | e.g. `umm-0001` | Unique question identifier. |
| `condition` | `RU-P`, `RU-R`, `RU-X` | Condition evaluated. |
| `rater_1` | `y` / `n` | Independent rating for meaning preservation by Rater 1. |
| `rater_2` | `y` / `n` | Independent rating for meaning preservation by Rater 2. |

### Annotation validity checks

- Use exactly one row per `item_id` and `condition`. The same item may appear once for each of `RU-P`, `RU-R`, and `RU-X`.
- Enter only `y` or `n` in both rater columns. Blank cells and other values are not scored; correct the source sheet before calculating agreement.
- Do not delete incomplete or disputed rows to improve agreement. Resolve them with the project lead and retain the original ratings for audit.
- If all ratings have no class variation, Cohen's kappa is undefined even when raw agreement is 100%. Report that status and do not treat it as a pass.
- Calculate agreement only from an actually completed sheet. The template's example rows are not human annotations and are not evidence of agreement.
- Both CSV templates contain headers only; add approved item assignments before collecting ratings.

---

## 4. Google Sheets Workflow

To avoid formatting or encoding issues when collaborating:

### Importing into Google Sheets
1. Create a new Google Spreadsheet or open the shared team drive sheet.
2. Go to **File -> Import -> Upload** and select `verification_template.csv` or `kappa_template.csv`.
3. Set **Import location** to *"Replace current sheet"*.
4. Set **Separator type** to *"Detect automatically"* or *"Comma"*.
5. Set **Convert text to numbers, dates, and formulas** to **"No"** (keeps IDs like `umm-0001` as text strings).

### Rating Process
- Fill in columns `y` or `n` (lowercase).
- Do not add or delete columns.
- Raters work independently on the 50 kappa items before comparing results.

### Exporting Back to Repository
1. In Google Sheets, navigate to **File -> Download -> Comma-separated values (.csv, current sheet)**.
2. Save the exported CSV directly into `annotations/` (e.g. `annotations/kappa_50_checked.csv`).
3. Ensure the exported file is encoded in UTF-8 without byte order marks (BOM).

---

## 5. Running the Kappa Check Script

To compute raw agreement and Cohen's kappa from a completed kappa sheet:

```bash
python -m src.analysis.kappa --sheet annotations/kappa_50_checked.csv
```

The script will output:
- Total items evaluated ($N$)
- Observed raw agreement ($P_o$)
- Cohen's kappa score ($\kappa$)
- A `PASSED`, `BELOW_THRESHOLD`, or `UNDEFINED_NO_CLASS_VARIATION` status.
- An automatic alert if $\kappa < 0.80$, advising rule revision per Gate G2 requirements.
- An explicit error for duplicate item-condition rows, missing ratings, or labels outside `y`/`n`.
