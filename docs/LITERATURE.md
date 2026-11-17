# Literature search and verification log

## 3. Literature search log

### 3.1 Search results recorded (November 2026)

| Date | Database | Exact query | Filters | Total hits | Relevant hits | Notes |
|---|---|---|---|---|---|---|
| Nov 2026 | Google Scholar | `"romanized Urdu" "multiple choice"` | none noted | 4 | 0 | Results were unrelated (gender identification, TESOL, loan officers, dissertation) |
| Nov 2026 | Google Scholar | `"Roman Urdu" "spelling variation" LLM` | none noted | about 10 | 0 direct | Hate speech, sentiment, idioms, language identification; none varied spelling for LLM MCQs |
| Nov 2026 | Google Scholar | `"Roman Urdu" MMLU` | none noted | 7 | 1 related | U-MIRAGE appeared; no Roman Urdu MMLU found |
| Nov 2026 | arXiv | `romanized Urdu` | all fields | 36 | 0 direct | Mostly hate speech, sentiment, transliteration, language ID |
| Nov 2026 | arXiv | `Urdu MMLU` | all fields | 2 | 1 | UrduMMLU and IndicMMLU-Pro |
| Nov 2026 | Semantic Scholar | several `"Urdu"`/`"Roman Urdu"` queries | none | counts not informative | n/a | Result counts from loose matching are not evidence of a gap |
| Nov 2026 | AI literature tools (Consensus, Jenni) | gap and novelty prompts | tool defaults | n/a | n/a | **Not reproducible.** Tool summaries; they raised Belebele (L02) as a threat. Never cite the tools' percentages |

### 3.2 Searches to run on Day 1 and again on Day 4 (record date, filters, counts)

| Query | Where | Done (Day 1) | Done (Day 4) |
|---|---|---|---|
| `"Roman Urdu" benchmark transliterated` | Scholar, arXiv | ☐ | ☐ |
| `"romanized Urdu" benchmark` | Scholar, arXiv, Semantic Scholar | ☐ | ☐ |
| `"Urdu" "Latin script" LLM evaluation` | Scholar, arXiv | ☐ | ☐ |
| `"Roman Urdu" "spelling variants" LLM` | Scholar, arXiv | ☐ | ☐ |
| `"Roman Urdu" MCQ LLM` | Scholar, arXiv | ☐ | ☐ |
| `"transliterated Urdu"` LLM benchmark | Scholar, arXiv | ☐ | ☐ |
| `Belebele urd_Latn` | Scholar, Hugging Face, GitHub | ☐ | ☐ |
| `romanized` MMLU benchmark (Hindi, Bengali, Punjabi, Sinhala, any South Asian language) | Scholar, arXiv | ☐ | ☐ |
| `answer flip rate` spelling variants multiple choice LLM | Scholar, arXiv | ☐ | ☐ |

Use at least two phrasings of the language name ("Roman Urdu", "romanized Urdu",
"Urdu written in Latin script", "transliterated Urdu"); a missing hit may only
mean different wording. If a search returns zero results, log it too.

## 4. Claims register: what we may and may not say

| Topic | Allowed wording | Not allowed |
|---|---|---|
| Novelty | "To our knowledge, and as of [date], we did not find a study that ... in our searches (Section X, Appendix Y)." | "No one has done this." "First study ..." (unless the literature table fully supports it) |
| Script effect | "Prior studies report mixed directions across tasks (cite L03, L05, L04 after verification)." | Any direction claimed for exam-style knowledge before our own results |
| Belebele | State exactly what it contains after verification (L02) | Describing it from memory or from a tool summary |
| Spelling | "Prior work normalised spellings (L10) or built variant lists (L09)" **only after those papers are verified** | Claiming that nobody studies spelling variation |
| Contamination | "UrduMMLU is public and may appear in training data; comparisons are within-item." | Claiming the models never saw the data |
| Results | Numbers copied from `results/tables/` only | Any number not traceable to `results/raw/` |
| Novelty rating | Not stated as a percentage in the paper | The tools' or our informal percentages |

## 5. Reference list (fill after verification)

Keep one BibTeX entry per **verified** paper in `paper/references.bib` (key
format: `lastname2026keyword`). Do not add an entry for an unverified paper.

| ID | BibTeX key | Verified date | Verified by |
|---|---|---|---|
| L01 | | | |
| L02 | | | |
| ... | | | |

## 6. Day 4 literature checklist (with the claims audit in `PLAN.md`)

- [ ] All P1 papers opened and verified (L01 to L05).
- [ ] Every paper cited in the draft has its verification box ticked.
- [ ] Section 3.2 searches repeated; dates and counts recorded.
- [ ] Any new closest-prior-work found late is added here and the novelty wording is changed (claims change, data does not).
- [ ] The related-work section uses **only** verified entries.

## 7. Verification notes (one block per verified paper)

### L03 U-MIRAGE (Faheem et al., AbjadNLP 2026, pp. 453–460)

- Opened full text: 2026-11-16 (Younas). Venue: workshop paper (ACL Anthology).
- Dataset: 7,663 English medical MCQs (MIRAGE) translated into Urdu script and one Roman Urdu form (Section 3).
- Roman Urdu: one form only; English medical terms are kept on purpose (code-mixing, Section 3.1). Who translated (human or model) is not stated; validation is back-translation ROUGE-L 0.75 on 500 questions (Table 2).
- Models: 6 configurations (GPT-5-Nano, Gemini 2.0 Flash Lite, quantized Qwen 2.5 0.5B, Gemma 2 2B, LLaMA 3.2 1B in two precisions), zero-shot and chain-of-thought, accuracy only (Table 4).
- Direction of effect (zero-shot, Table 4): all configurations are lower in Urdu variants than English for GPT-5-Nano and Gemma, but not every row (quantized LLaMA 1B Roman Urdu is above English). Roman Urdu is 0.7 to 1.6 points above Urdu script for five configurations; Gemini is the exception (Urdu script 2.26 points higher).
- Text inconsistencies: abstract says 6–10% drop, results say 6–11%; "three proprietary models" but only two are named.
- Our difference: medical only, one Roman Urdu form with English insertions, no spelling variants, no per-item flips.
- Allowed wording: "reports that Roman Urdu was generally slightly ahead of Urdu script for most configurations". Not allowed: "Roman Urdu consistently better", or any number from the abstract.

### L02 Belebele (Bandarkar et al., ACL 2024, pp. 749–775, DOI 10.18653/v1/2024.acl-long.44)

- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed (ACL 2024 Long Papers).
- Task: multiple-choice reading comprehension, 900 questions over 488 FLORES-200 passages, 4 options, answerable from the passage alone (Sections 1, 3.1, Table 1). Not exam-style knowledge items.
- Urdu: both `urd_Arab` and `urd_Latn` exist (Appendix A.1, Table 4).
- How `urd_Latn` was made: annotators transliterated the native-script passages into Latin script with IndicXlit support (Section 3.3); one romanized version per passage.
- Script result: all models except Falcon are stronger in native script (Section 5, Impact of Script; Appendix A.7.3, Table 8). Urdu: GPT-3.5-Turbo 48.3 vs 40.3, LLaMA 2 70B 43.2 vs 38.0, InfoXLM 63.8 vs 42.6; Falcon is the exception (31.7 vs 34.2).
- Models are from 2023 (GPT-3.5-Turbo, LLaMA 1/2, Falcon, XLM-R family), not current models.
- Spelling variation: not studied in the paper (checked by searching the PDF for "spelling"/"variant"; Younas to confirm).
- Our difference: single romanization of reading-comprehension passages; no controlled spelling styles, no per-item answer flips, no exam-style knowledge items.
- Allowed wording: "Belebele includes a romanized Urdu split produced by transliteration, with one romanized version per item; to our knowledge it does not vary spelling styles."
- Not allowed: "Belebele shows Roman Urdu is worse" without naming the task and the models, or any claim about current models.
