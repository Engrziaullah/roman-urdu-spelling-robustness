# LITERATURE: Verified Literature Table and Search Log

**Owner:** Role C (Younas Khan), with reading shared across the team. **Status:** `v0 STARTER`.

> **Nothing in this file is verified yet.** Every entry below comes from search results, snippets and tool summaries gathered while planning the project
> (Google Scholar, arXiv, Semantic Scholar, and AI literature tools). These can be wrong or incomplete (titles, authors, years, venues, and above all the *claims*).
> **Do not cite a paper in the draft until it has been opened and its details checked against the full text and the verification box is ticked.**

---

## 1. How to verify a paper (about 15 minutes per paper)

1. Open the full text (publisher page, ACL Anthology, arXiv). A snippet or an AI summary does not count.
2. Check: exact title, authors, year, venue/status (peer-reviewed, preprint, workshop, GitHub project), and DOI or arXiv id.
3. Find the passage that supports the claim in the "What our notes say" column. Copy the section/table number into the notes. If the passage is not there, correct or delete the claim.
4. Fill in the three right-hand columns. A paper is **verified** only when all of these hold: full text opened, bibliographic details checked, claim confirmed or corrected.
5. Preprints and GitHub projects are marked as such in the paper. Do not describe them as peer-reviewed.

**Priority:** P1 = could change our novelty claim (read first, today). P2 = needed for related work and method justification. P3 = background, read if time allows.

## 2. Literature table

Column "Reader" = who reads it first (swap freely). "Opened" and "Verified" are tick boxes.

| ID | Priority | Paper as we know it (unverified) | What our notes say (from snippets/tool summaries) | Why it matters / what to check in the full text | Reader | Opened | Verified |
|---|---|---|---|---|---|---|---|
| L01 | P1 | UrduMMLU. Tabassum, Ahmad, Iqbal, Aijaz, Ahsan, Nakov. EMNLP 2026. arXiv:2606.07167. HF: `MBZUAI/UrduMMLU` | Large benchmark of Urdu exam-style MCQs (about 26k items, 26 subjects, 5 domains); Nastaliq only | **Our source data.** Check: schema, number of options, domain and subject fields, answer format, license on the dataset card (CC BY 4.0?), whether any Roman Urdu version exists | Sudais | ☐ | ☐ |
| L02 | P1 | Belebele. Bandarkar et al. ACL 2024 | Parallel reading-comprehension MCQs in 122 language variants; **reported to include Urdu in Nastaliq (urd_Arab) and Latin script (urd_Latn)** | **Biggest novelty threat.** Check: does `urd_Latn` exist, how was it produced (transliteration tool? one romanization?), what do the results say about Urdu script vs Latin, any spelling variation. If it only has one romanization and reading comprehension, our spelling manipulation is still open | Younas | ☑ | ☑ |
| L03 | P1 | U-MIRAGE. Faheem et al. AbjadNLP 2026 | Urdu and Roman Urdu medical QA benchmark with chain-of-thought; Roman Urdu reported better than Nastaliq | Closest design (script comparison on QA). Check: how Roman Urdu was produced, how many forms, models, the direction and size of the effect, domain | Zia | ☐ | ☐ |
| L04 | P1 | Script Gap. Khullar et al. arXiv 2025 (arXiv:2512.10780) | Native vs romanized scripts for LLM triage in Indian languages; romanized inputs performed worse; models often grasp intent but still misclassify | Mechanism and effect-size reference. Check: languages, task, whether Urdu is included, how romanization was produced, exact gap and flip-related results. Preprint? | Sudais | ☐ | ☐ |
| L05 | P1 | Evaluating LLMs on Urdu Idioms. Khan and Akter. arXiv 2510.17460; Findings of EMNLP 2026 | Native Urdu vs Roman Urdu idiom translation; native script reported better | Script effect with opposite sign to U-MIRAGE. Check: venue status, number of Roman Urdu forms, metrics | Younas | ☐ | ☐ |
| L06 | P2 | Robustness of LLMs to transliteration perturbations in Bangla. Haider et al. 2025 (BanglaLP workshop) | Transliteration-based perturbations of Bangla data to test LLM robustness | Method precedent in a neighbouring language. Check: how perturbations were built, tasks (MCQ?), whether spelling styles were controlled | Zia | ☐ | ☐ |
| L07 | P2 | Language Models are not Equally Robust to Non-Canonical Tokenization across Languages. Ghosh and Jyothi. arXiv 2026 | Tokenization perturbations across many languages, including MMLU-style tasks | Tokenization is not orthography. Check: what exactly was perturbed and whether the surface string stays fixed | Younas | ☐ | ☐ |
| L08 | P2 | Formality is Favored. Li et al. EMNLP 2024 | LLMs reported to prefer formal text with fewer spelling errors | Justifies **register control** in RULES.md. Check the exact claim and scope | Zia | ☐ | ☐ |
| L09 | P2 | A dataset of Roman Urdu text with spelling variations for sentence-level sentiment analysis. Soomro et al. 2024 (Data in Brief) | 5,244 Roman Urdu words with spelling variants (one to five variants) plus about 28k reviews | **Evidence for RU-R/RU-X operations.** Check: the variant list format, license, which variation patterns are attested | Sudais | ☐ | ☐ |
| L10 | P2 | Roman Urdu Adversarial Benchmark (RUAB). Jamil and Rafi. AbjadNLP 2026 | Safety evaluation across English, mixed and transliterated Roman Urdu; spellings reportedly normalised before testing | Supports "spelling is usually normalised away". Check the exact normalisation statement | Younas | ☐ | ☐ |
| L11 | P2 | Does Script Matter? Evaluating LLMs for Urdu Sentiment across Nastaliq, Roman Urdu and Code-Switched Text. Zenodo preprint 2026 | Sentiment across three forms; Roman Urdu reported best | Preprint. Check: peer-review status, forms compared, spelling handling | Zia | ☐ | ☐ |
| L12 | P2 | Improving Informally Romanized Language Identification. Benton, Gutkin, Kirov, Roark. EMNLP 2025 (arXiv 2504.21540) | Notes that Latin-script text lacks conventional spelling, causing high variability | Supports the "no standard spelling" premise. Check the exact statement | Sudais | ☐ | ☐ |
| L13 | P2 | PURUTT: Parallel Urdu and Roman Urdu Corpus for Toxic Comments and Transliteration (Zubair et al. line of work, 2026) | Corpus of over 72,000 annotated comments in Urdu and Roman Urdu | Optional real-usage check. **Check the license first**; cut if unclear (PLAN.md cut list item 1) | Younas | ☐ | ☐ |
| L14 | P2 | Indi-RomCoM. arXiv 2026 | Benchmark of romanized Indic-English code-mixed instructions across several tasks | Neighbouring romanization benchmark. Check: is Urdu included, are spelling variants controlled | Zia | ☐ | ☐ |
| L15 | P3 | Hinglish-CSR (GitHub project, not a paper) | Retrieval robustness with language switching and phonetic spelling noise; spelling noise reported to matter little for retrievers | Neighbouring evidence. Cite only as a project, not peer-reviewed | Sudais | ☐ | ☐ |
| L16 | P3 | "Benchmarking Language Models on Unicode, Romanized ..." (arXiv; the full title was cut off in the search result; Sinhala according to the snippet) | Script sensitivity across Unicode, Romanized and mixed script | Other-language script effect. Check task type (perplexity vs accuracy) | Younas | ☐ | ☐ |
| L17 | P3 | Roman Urdu POS tagging datasets and models (Springer, 2025) | Test sets with and without lexical variation; an LLM was tested | Evidence that lexical variation hurts a non-LLM and LLM task. Check numbers before using | Zia | ☐ | ☐ |
| L18 | P3 | Evaluating Robustness of LLMs Against Multilingual Typographical Errors. Zhao et al. ACL 2026 | Keyboard-aware typos across many models and tasks, including MCQ | Typos are errors, not alternate spellings; use as contrast | Sudais | ☐ | ☐ |
| L19 | P3 | Tokenization Falling Short: On Subword Robustness in LLMs. Chai et al. Findings of EMNLP 2024 | Character-level perturbations on MMLU and other benchmarks | Template for perturbation on MMLU-style data. Check exact claim | Younas | ☐ | ☐ |
| L20 | P3 | RomanSetu. Husain et al. 2024 | Romanization reportedly reduces token fertility while matching or beating native script on several tasks | Relevant to the tokenizer covariate. Check the tasks and claims | Zia | ☐ | ☐ |
| L21 | P3 | How Often Are Errors in Natural Language Reasoning Due to Paraphrastic Variability? Srikanth, Carpuat, Rudinger. TACL 2024 | A metric for variance in correctness attributable to paraphrasing | Possible statistical template for flip analysis. Check the metric definition | Sudais | ☐ | ☐ |
| L22 | P3 | Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts. Bandarkar et al. arXiv 2026 | Script match reported as main predictor of knowledge transfer failure | Mechanistic context. Check whether Urdu or MCQ is covered | Younas | ☐ | ☐ |
| L23 | P3 | Unseen Harm: cross-script safety inconsistency (Zehra et al. arXiv 2026) and Understood, Unaligned, or Unrouted? (NeurIPS 2026) | Cross-script safety evaluation across Urdu script and Roman Urdu | Safety task, different from ours. Related-work mention only; check venue status | Zia | ☐ | ☐ |

Add new rows as papers are found (IDs continue L24, L25, ...). Never delete a row; mark it `not relevant` with a reason.

## 3. Search log

Record **every** search: it is the evidence behind the sentence "to our knowledge, not found in our searches". An absence of results is only meaningful if the exact query, database, date and filters are recorded.

### 3.1 Searches done so far (during planning; repeat them on Day 1 and Day 4)

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

Use at least two phrasings of the language name ("Roman Urdu", "romanized Urdu", "Urdu written in Latin script", "transliterated Urdu"); a missing hit may only mean different wording.
If a search returns zero results, **log it** too.

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

Keep one BibTeX entry per **verified** paper in `paper/references.bib` (key format: `lastname2026keyword`). Do not add an entry for an unverified paper.

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

### L03 U-MIRAGE (Faheem et al., AbjadNLP 2026, pp. 453-460)
- Opened full text: 2026-11-16 (Younas). Venue: workshop paper (ACL Anthology).
- Dataset: 7,663 English medical MCQs (MIRAGE) translated into Urdu script and one Roman Urdu form (Section 3).
- Roman Urdu: one form only; English medical terms are kept on purpose (code-mixing, Section 3.1). Who translated (human or model) is not stated; validation is back-translation ROUGE-L 0.75 on 500 questions (Table 2).
- Models: 6 configurations (GPT-5-Nano, Gemini 2.0 Flash Lite, quantized Qwen 2.5 0.5B, Gemma 2 2B, LLaMA 3.2 1B in two precisions), zero-shot and chain-of-thought, accuracy only (Table 4).
- Direction of effect (zero-shot, Table 4): all configurations are lower in Urdu variants than English for GPT-5-Nano and Gemma, but not every row (quantized LLaMA 1B Roman Urdu is above English). Roman Urdu is 0.7 to 1.6 points above Urdu script for five configurations; Gemini is the exception (Urdu script 2.26 points higher).
- Text inconsistencies: abstract says 6-10% drop, results say 6-11%; "three proprietary models" but only two are named.
- Our difference: medical only, one Roman Urdu form with English insertions, no spelling variants, no per-item flips.
- Allowed wording: "reports that Roman Urdu was generally slightly ahead of Urdu script for most configurations". Not allowed: "Roman Urdu consistently better", or any number from the abstract.

### L02 Belebele (Bandarkar et al., ACL 2024, pp. 749-775, DOI 10.18653/v1/2024.acl-long.44)
- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed (ACL 2024 Long Papers).
- Task: multiple-choice reading comprehension, 900 questions over 488 FLORES-200 passages, 4 options, answerable from the passage alone (Sections 1, 3.1, Table 1). Not exam-style knowledge items.
- Urdu: both urd_Arab and urd_Latn exist (Appendix A.1, Table 4).
- How urd_Latn was made: annotators transliterated the native-script passages into Latin script with IndicXlit support (Section 3.3); one romanized version per passage.
- Script result: all models except Falcon are stronger in native script (Section 5, Impact of Script; Appendix A.7.3, Table 8). Urdu: GPT-3.5-Turbo 48.3 vs 40.3, LLaMA 2 70B 43.2 vs 38.0, InfoXLM 63.8 vs 42.6; Falcon is the exception (31.7 vs 34.2).
- Models are from 2023 (GPT-3.5-Turbo, LLaMA 1/2, Falcon, XLM-R family), not current models.
- Spelling variation: not found in the paper (Ctrl+F for "spelling": no hits; "variant" appears only as "language variants" and "romanized variant"). Checked 2026-11-16, Younas.
- Our difference: single romanization of reading-comprehension passages; no controlled spelling styles, no per-item answer flips, no exam-style knowledge items.
- Allowed wording: "Belebele includes a romanized Urdu split produced by transliteration, with one romanized version per item; to our knowledge it does not vary spelling styles."
- Not allowed: "Belebele shows Roman Urdu is worse" without naming the task and the models, or any claim about current models.