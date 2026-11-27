# LITERATURE: Literature Table and Search Log

**Owner:** The whole team. Reading and verification are shared across all members (see the Reader column in Section 2). **Status:** `v1` (2026-11-19: Nov 17-19 searches logged, rows L24 to L37 added, arXiv ID corrections applied; see the corrections log at the end of Section 7).

> **How to read verification status.** The per-paper `Opened` / `Verified` boxes in Section 2 and the notes in Section 7 are the source of truth. A box is ticked only after a team member has opened the full text and checked the details against it.
> L24: researcher-supplied paper text was reviewed, but independent publication, DOI, Zenodo archive, code/data archive, and GitHub repository verification remains unresolved. L25: full text and bibliographic metadata have been independently reviewed. L28: official source not reliably located and remains unresolved. Rows L26 to L37 otherwise come from search results, snippets, or AI-assisted checks and are **not fully verified** unless their table entry says otherwise.
> **Do not cite a paper in the draft until its Verified box is ticked.**

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
| L01 | P1 | **UrduMMLU: A Massive Multitask Benchmark for Urdu Language Understanding.** Ahmer Tabassum, Sarfraz Ahmad, Hasan Iqbal, Owais Aijaz, Momina Ahsan, and Preslav Nakov. MBZUAI. 2026. arXiv v1 2606.07167 (submitted 5 June 2026); submitted to ACL Rolling Review in May 2026. | Native Urdu exam-style and web-derived MCQs (26,431 items, 26 subdomains, five domains); 30 LLMs evaluated under English and Urdu prompts, plus 1-, 3-, and 5-shot evaluation of four open-source models. Official Hugging Face card checked; card metadata records CC BY 4.0, 26,431 MCQs, and `urdummlu.json`. The downloadable archive has not been independently downloaded and inspected. | **Our source data.** Verified from full text and dataset-card metadata. Dataset archive contents remain to be independently inspected; no Roman Urdu or within-Roman-Urdu spelling conditions are evaluated in the paper. | Sudais | ☑ | ☑ |
| L02 | P1 | Belebele. Bandarkar et al. ACL 2024 | Parallel reading-comprehension MCQs in 122 language variants; **reported to include Urdu in Nastaliq (urd_Arab) and Latin script (urd_Latn)** | **Biggest novelty threat.** Check: does `urd_Latn` exist, how was it produced (transliteration tool? one romanization?), what do the results say about Urdu script vs Latin, any spelling variation. If it only has one romanization and reading comprehension, our spelling manipulation is still open | Younas | ☑ | ☑ |
| L03 | P1 | U-MIRAGE. Faheem et al. AbjadNLP 2026 | Urdu and Roman Urdu medical QA benchmark with chain-of-thought; Roman Urdu reported better than Nastaliq | Closest design (script comparison on QA). Check: how Roman Urdu was produced, how many forms, models, the direction and size of the effect, domain | Zia | ☑ | ☑ |
| L04 | P1 | **Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real World Setting.** Manurag Khullar, Utkarsh Desai, Poorva Malviya, Aman Dalmia, Zheyuan Ryan Shi. arXiv:2512.10780v2 (originally submitted 11 Dec 2025, revised 30 Mar 2026). DOI 10.48550/arXiv.2512.10780. | Native vs romanized script triage on maternal/newborn health (3,153 sampled messages from ~133k WhatsApp chats); Romanized inputs drop up to 24 pp; HealthBench weighted-F1 drops 5.4 pp; cross-model agreement 56.8% Romanized vs 66.5% native; evaluated GPT-4o, Claude Sonnet 4.5, DeepSeek V3, Llama 4, Qwen. Human validation $\kappa = 0.74$. | **Verified from arXiv v2 HTML full text.** Preprint only (peer-reviewed venue not confirmed). Demonstrates script degradation in Indic languages, but does NOT include Urdu, does not test multiple Roman Urdu spelling conventions, and its "Flip Rate" (temperature instability) is NOT our AFR across spelling variants. | Sudais | ☑ | ☑ |
| L05 | P1 | Evaluating Large Language Models on Urdu Idioms. Khan and Akter. Findings of EMNLP 2026; arXiv:2510.17460 | Native Urdu vs Roman Urdu idiom translation; native script reported better | Script effect with opposite sign to U-MIRAGE. Check: venue status, number of Roman Urdu forms, metrics | Younas | ☑ | ☑ |
| L06 | P2 | Robustness of LLMs to transliteration perturbations in Bangla. Haider et al. 2025 (BanglaLP workshop) | Transliteration-based perturbations of Bangla data to test LLM robustness | Method precedent in a neighbouring language. Check: how perturbations were built, tasks (MCQ?), whether spelling styles were controlled | Zia | ☐ | ☐ |
| L07 | P2 | Language Models are not Equally Robust to Non-Canonical Tokenization across Languages. Ghosh and Jyothi. arXiv 2026 (arXiv:2607.26831) | Tokenization perturbations across many languages, including MMLU-style tasks | Tokenization is not orthography. Check: what exactly was perturbed and whether the surface string stays fixed | Younas | ☑ | ☑ |
| L08 | P2 | Formality is Favored. Li et al. EMNLP 2024 | LLMs reported to prefer formal text with fewer spelling errors | Justifies **register control** in RULES.md. Check the exact claim and scope | Zia | ☐ | ☐ |
| L09 | P2 | **A Dataset of Roman Urdu Text with Spelling Variations for Sentence Level Sentiment Analysis.** Mudasar Ahmed Soomro, Rafia Naz Memon, Asghar Ali Chandio, Mehwish Leghari, Muhammad Hanif Soomro. *Data in Brief*, Vol. 57, Art. 111170 (published 23 Nov 2024). DOI 10.1016/j.dib.2024.111170. CC BY 4.0. | Lexicon of 5,244 unique Roman Urdu headwords (19,527 spelling forms, Var-1 to Var-5, frequency-based Common spelling, English translation) and 28,090 sentiment reviews (5 classes; SVM 99%, RCNN 93%). Mendeley v5 (DOI 10.17632/v5jfhsvtmd.5, CC BY 4.0). | **Verified from PMC full text.** Peer-reviewed. Attests extensive natural spelling variation; normalizes variants rather than testing LLM answer stability. Does NOT evaluate LLMs, MCQs, AFR, or our five conditions (NU, RU-P, RU-R, RU-X, RT). Note paper discrepancies: 41 vs 42 single-variant words; 7 vs 8 sources. | Sudais | ☑ | ☑ |
| L10 | P2 | Code-Switching as a Safety Failure Mode in LLMs (RUAB). Jamil and Rafi. AbjadNLP 2026 | Safety evaluation across English, mixed and transliterated Roman Urdu; spellings reportedly normalised before testing | Supports "spelling is usually normalised away". Check the exact normalisation statement | Younas | ☑ | ☑ |
| L11 | P2 | Does Script Matter? Evaluating LLMs for Urdu Sentiment across Nastaliq, Roman Urdu and Code-Switched Text. Zenodo preprint 2026 | Sentiment across three forms; Roman Urdu reported best | Preprint. Check: peer-review status, forms compared, spelling handling | Zia | ☐ | ☐ |
| L12 | P2 | Improving Informally Romanized Language Identification. Benton, Gutkin, Kirov, Roark. EMNLP 2025 (arXiv 2504.21540) | Notes that Latin-script text lacks conventional spelling, causing high variability | Supports the "no standard spelling" premise. Check the exact statement | Sudais | ☐ | ☐ |
| L13 | P2 | PURUTT: Parallel Urdu and Roman Urdu Corpus for Toxic Comments and Transliteration. Saeed, Khalil, Kamiran. IEEE Access 2025 (vol. 13) | Corpus of over 72,000 annotated parallel comments in Urdu and Roman Urdu | Optional real-usage check. Repository records report a full-text review, but the DOI and CC BY 4.0 licence are unresolved: an exact DOI lookup did not resolve and later evidence could not reconfirm the licence. Do not cite the DOI or licence as verified. | Younas | ☑ | ☐ |
| L14 | P2 | Indi-RomCoM. arXiv 2026 | Benchmark of romanized Indic-English code-mixed instructions across several tasks | Neighbouring romanization benchmark. Check: is Urdu included, are spelling variants controlled | Zia | ☐ | ☐ |
| L15 | P3 | Hinglish-CSR (GitHub project, not a paper) | Retrieval robustness with language switching and phonetic spelling noise; spelling noise reported to matter little for retrievers | Neighbouring evidence. Cite only as a project, not peer-reviewed | Sudais | ☐ | ☐ |
| L16 | P3 | Script Sensitivity: Benchmarking Language Models on Unicode, Romanized and Mixed-Script Sinhala. Rajapakse and Weerasinghe. arXiv:2601.14958 | Script sensitivity across Unicode, Romanized and mixed script | Other-language script effect. Evaluates perplexity across scripts; shows >300x degradation in Romanized text | Younas | ☑ | ☑ |
| L17 | P3 | Roman Urdu POS tagging datasets and models (Springer, 2025) | Test sets with and without lexical variation; an LLM was tested | Evidence that lexical variation hurts a non-LLM and LLM task. Check numbers before using | Zia | ☐ | ☐ |
| L18 | P3 | Evaluating Robustness of LLMs Against Multilingual Typographical Errors. Zhao et al. ACL 2026 | Keyboard-aware typos across many models and tasks, including MCQ | Typos are errors, not alternate spellings; use as contrast | Sudais | ☐ | ☐ |
| L19 | P3 | Tokenization Falling Short: On Subword Robustness in Large Language Models. Chai et al. Findings of EMNLP 2024 | Character-level perturbations and subword fragility on MMLU and reasoning benchmarks | Template for perturbation on MMLU-style data. Evaluates BPE-dropout and typographical noise | Younas | ☑ | ☑ |
| L20 | P3 | RomanSetu. Husain et al. 2024 | Romanization reportedly reduces token fertility while matching or beating native script on several tasks | Relevant to the tokenizer covariate. Check the tasks and claims | Zia | ☐ | ☐ |
| L21 | P3 | How Often Are Errors in Natural Language Reasoning Due to Paraphrastic Variability? Srikanth, Carpuat, Rudinger. TACL 2024 | A metric for variance in correctness attributable to paraphrasing | Possible statistical template for flip analysis. Check the metric definition | Sudais | ☐ | ☐ |
| L22 | P3 | Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts. Bandarkar et al. Findings of EMNLP 2026; arXiv:2603.17070 | Script match reported as main predictor of knowledge transfer failure | Mechanistic context. Identifies cross-script entity transliteration mismatch as primary failure mode | Younas | ☑ | ☑ |
| L23 | P3 | Unseen Harm: cross-script safety inconsistency (Zehra et al. arXiv 2026) and Understood, Unaligned, or Unrouted? (NeurIPS 2026) | Cross-script safety evaluation across Urdu script and Roman Urdu | Safety task, different from ours. Related-work mention only; check venue status | Zia | ☐ | ☐ |

| L24 | P1 | **Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions.** Muzammal Hussain and Maryam Khalid. November 2026, Version 1, Zenodo preprint (DOI 10.5281/zenodo.24045043; all-versions DOI 10.5281/zenodo.24045042), CC BY 4.0. Not peer-reviewed. Software/data: DOI 10.5281/zenodo.24044983 (v1.0.0, MIT) by Muzammal Hussain on GitHub (https://github.com/MHKhan50/roman-urdu-react-bench). | Evaluates how Roman Urdu affects small local ReAct agents on fictional physiotherapy-clinic questions. 96 questions from 12 templates (4 instances/template, 2 name sets) across 3 language forms (English, common Roman Urdu, chat spelling). Models: Qwen2.5 3B, Qwen2.5 7B, Llama 3.2 3B, Llama 3.1 8B. Methods: Direct answering, ReAct (English example), ReAct (Roman Urdu example), translate-then-ReAct. Under English-example ReAct, Roman Urdu accuracy drops 34.7 pp (Qwen2.5 3B), 31.2 pp (Llama 3.2 3B), and 21.9 pp (Llama 3.1 8B); Qwen2.5 7B shows +1.0 pp. Chat spelling causes further 22.1 pp paired loss for Qwen2.5 3B (57.9% common vs 36.5% chat; paired diff −22.1 pp on 95 matched items, distinct from 21.4 pp marginal subtraction). Limitations: fictional clinic, 12 templates by 1 person, 4 small models, 1 sample/question, 2 timeout calls excluded (3,838 scored calls). Clinician review: 48 items (1 name set) checked; all gold answers correct; 16 items (T03–T06) judged unrealistic; 7 Roman Urdu items had gender-agreement issues. | **Full-text verified from 7-page PDF (04_RomanUrdu_ReAct.pdf) and cross-checked against public repository.** Raw calls not independently rerun; preprint, not peer-reviewed. Closest known paired Roman Urdu study; do not claim “first study.” Evaluates agent accuracy on clinic queries, not our 5-condition MCQ Answer Flip Rate; no native Nastaliq (`NU`) or back-transliteration (`RT`). | Younas | ☑ | ☑ |
| L25 | P2 | **Waleed Jamil, Saima Rafi, and Yanchao Yu.** "Token Cost Inequality: Measuring Tokenization Disparities Across Scripts in Roman Urdu and Urdu." *Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM)*, July 2026, pp. 563-573. DOI 10.18653/v1/2026.gem-main.54. | Full text independently reviewed. Samples 10,000 examples from each of Roman-Urdu-Parl, OPUS100 English-Urdu, and Dakshina Urdu; evaluates cl100k_base, mT5, and ByT5 using TCI, tokens per word, fixed-budget character retention, cost multipliers, and lightweight normalization. | **Verified from full text and official bibliographic record.** Tokenization efficiency and surface coverage are relevant background, but the study does not evaluate MCQ answer accuracy or compare RU-P, RU-R, and RU-X. | Younas | ☑ | ☑ |
| L26 | P3 | Sodhar et al. 2026. Reproducible framework for evaluating Romanized Sindhi output consistency in conversational LLMs (pilot study; ijournalar.com; title cut off in the search snippet) | Consistency of Romanized Sindhi **output** of a chat model | Probably `not relevant`: Sindhi, output side rather than input spelling, journal quality unclear. Check venue, then mark | Younas | ☐ | ☐ |
| L27 | P3 | SafeSwitch: A Localized Benchmark for LLM Safety in Urdu and Pashto across Language Forms and Prompting Strategies. M. Ali (PDF on a public blob host, no venue found) | Safety benchmark across language forms; the snippet cites a Roman Urdu adversarial benchmark as ref [9], probably L10 | Not peer-reviewed as far as found. Do not cite unless a proper venue is found | Younas | ☐ | ☐ |
| L28 | P2 | **Facts Follow the Spelling: How Names Are Written Shapes Cross-Lingual Knowledge Transfer** (provisional title; official record not reliably located) | No authors, year, venue, DOI, methodology, findings, or limitations are established. | A reliable official source and full text are required before this entry can be reviewed. Do not use alleged findings as evidence; keep peer-review status and all substantive claims unresolved. | Younas | ☐ | ☐ |
| L29 | P3 | Zhou and Duan. "Exploring and improving consistency in large language models for multiple-choice question assessment". IEEE IJCNN 2024 | Proposes consistency metrics for MCQ answers across original and variant questions | Method precedent for the flip/consistency metric. Check the metric definition and the IEEE record | Younas | ☐ | ☐ |
| L30 | P3 | "Roman Urdu Sentiment Analysis: Traditional Approaches vs LLMs" (noted as IEEE 2025) | Sentiment task, not MCQs | Low priority. Official IEEE record and authors not confirmed | Younas | ☐ | ☐ |
| L31 | P3 | Kodavali and Singh. LANTERN: Language Model Assessment on Noisy and Transformed Tasks for Understanding Error and Robustness Nuances. ICASSP 2026 | Robustness framework on noisy and transformed MCQs | Contrast: noise, not alternate spellings. Check the perturbation types | Younas | ☐ | ☐ |
| L32 | P3 | Yu, Xie, Ma and Li. "Small Edits, Shifting Decisions: Benchmarking LLM Accuracy and Reliability on French Input Variants". arXiv:2610.33493 (preprint) | Diacritic and typo variants of French input, six models, two LLM families | Most similar design in another language. Check whether per-item answer changes are reported. Preprint | Younas | ☐ | ☐ |
| L33 | P3 | Takizawa, Sugawara and Aizawa. "MCQFormatBench: Robustness tests for multiple-choice questions". 2025 (ACL Anthology) | MCQ format robustness tests; the snippet mentions an answer changing after a question change | Possible reference for the flip metric. Check the exact claim and venue | Younas | ☐ | ☐ |
| L34 | P3 | Gan et al. "Reasoning robustness of LLMs to adversarial typographical errors". 2024 (ACL Anthology) | Typo robustness of reasoning | Contrast: adversarial typos, not spelling styles. Confirm venue | Younas | ☐ | ☐ |
| L35 | P3 | Molfese et al. "Right answer, wrong score: Uncovering the inconsistencies of LLM evaluation in multiple-choice question answering". Findings 2025 | Inconsistencies in how MCQ answers are extracted and scored | Supports our parser design and invalid-rate reporting. Confirm venue | Younas | ☐ | ☐ |
| L36 | P3 | Saji et al. "RomanLens: The role of latent romanization in multilinguality in LLMs". Findings 2025 | Latent romanization inside LLMs | Optional mechanism background | Younas | ☐ | ☐ |
| L37 | P2 | "Romanization Flattens the Field: Script and Metric Sensitivity in Sinhala SLM Evaluation" (NeurIPS 2026 virtual page; authors not recorded) | Per the abstract: downstream evaluation with 9,479 items, eleven instruction-tuned checkpoints and 208,538 generations; the romanized side comes from a deterministic rule-based transliterator; script effect described as a flattening (a 22.4-point spread becomes 6.7). It refers to the L16 benchmark | Close design in another language (accuracy across scripts, rule-based variants). Found in an ad-hoc web search on 2026-11-19, not in a logged database search. Check: venue, task, whether any item-level instability is reported | Younas | ☐ | ☐ |

Status for L24-L28: L24 is full-text verified from the 7-page PDF and cross-checked against repository outputs; L25 is full-text and bibliographically verified; L28 is unresolved; L26 and L27 retain their existing unverified statuses. Rows L29-L37 remain search-record entries until individually verified.

Add new rows as papers are found (IDs continue L38, L39, ...). Never delete a row; mark it `not relevant` with a reason.

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
| 2026-11-17 | Google Scholar | `"Roman Urdu" benchmark transliterated` | none | 231 | 7 distinct | Screened 30 (pages 1-3). Existing: L03, L05, L10, L17. New: L24, L25, L30. Rest: transliteration, MT, TTS, sentiment and hate speech datasets |
| 2026-11-17 | arXiv (all fields) | `"Roman Urdu" benchmark transliterated` | none | 1 | 0 | Only hit: Roman Urdu hate speech detection (arXiv:2608.18142) |
| 2026-11-17 | Google Scholar | `"romanized Urdu" benchmark` | none | 50 | 2 | Screened 30 (pages 1-3). L05 repeat; L26 new. Borderline, not added: Benton et al. 2025 (language ID), Maab et al. 2026 |
| 2026-11-17 | arXiv (all fields) | `"romanized Urdu" benchmark` | none | 3 | 1 | L05 only |
| 2026-11-17 | Semantic Scholar | `"romanized Urdu" benchmark` | none | about 880,000 (quotes not enforced) | 1 | Screened 10. L05 only. Count not comparable with other databases |
| 2026-11-17 | Google Scholar | `"Urdu" "Latin script" LLM evaluation` | none | 295 | 3 | Screened 30 (pages 1-3). L03, L23 existing; L27 new. Others are P3 background, not direct |
| 2026-11-17 | arXiv (all fields) | `"Urdu" "Latin script" LLM evaluation` | none | 1 | 0 | BanglaShield (arXiv:2610.24288): Bangla, not Urdu |
| 2026-11-17 | Google Scholar | `Belebele urd_Latn` | none | not recorded | 1 | Screened 10 (page 1). L02 itself; others use Belebele as one of many benchmarks. **Fill in the total hits count** |
| 2026-11-17 | Hugging Face dataset card | `facebook/belebele` | none | n/a | 1 | Confirms `urd_Latn` ("Urdu (Romanized)"), 900 rows per variant, license cc-by-sa-4.0. The card does not say how it was produced |
| 2026-11-17 | GitHub repository search | `urd_Latn` | type=repositories | 0 | 0 | No repository matched |
| 2026-11-17 | GitHub (facebookresearch/belebele README) | `urd_Latn` | none | 1 | 1 | Language table row confirms `urd_Latn`. Open item: meaning of the caret marker (check the README footnote) |
| 2026-11-17 | Google Scholar | `"answer flip rate" spelling variants multiple choice LLM` | none | 2 | 0 | Both papers use the term for unrelated things (RecurTrace arXiv:2609.03379; "No Matter Who You Are", EMNLP 2026). arXiv not searched |
| 2026-11-17 and 2026-11-19 | Google Scholar | `spelling variation LLM multiple choice answer consistency romanized` | none | 307 | 4 new | Screened 20 (pages 1-2, page 3 not opened). New: L28, L29, L35, L36. Existing: L04, L14, L26 |
| 2026-11-19 | Google Scholar | `"label flip" romanized LLM` | none | 1 | 0 | FLAICOL (Dravidian code-mixed offensive language detection) uses "label flip" for augmentation. Not used |
| 2026-11-19 | Google Scholar | `"prediction flip" transliterated LLM` | none | 0 | 0 | No matches |
| 2026-11-19 | Google Scholar | `typo robustness LLM multiple choice` | none | about 19,300 | 4 new | Screened 10 (page 1 only). New: L31, L32, L33, L34. Existing: L18. None uses Roman Urdu |
| 2026-11-19 | Google Scholar | `"Roman Urdu" LLM benchmark` | none | about 248 | 0 new | Screened 10 (page 1 only). Existing: L03, L05, L23. None varies Roman Urdu spelling for MCQs |
| 2026-11-19 | Web search (ad hoc, not a database search) | arXiv ID check for L16 and L07 and L22 | none | n/a | 1 new (L37) | Used only to confirm arXiv IDs (see corrections log); it surfaced L37. Not part of the evidence for the novelty sentence |

### 3.2 Searches to run on Day 1 and again on Day 4 (record date, filters, counts)

| Query | Where | Done (Day 1) | Done (Day 4) |
|---|---|---|---|
| `"Roman Urdu" benchmark transliterated` | Scholar, arXiv | ☑ 2026-11-17 | ☐ |
| `"romanized Urdu" benchmark` | Scholar, arXiv, Semantic Scholar | ☑ 2026-11-17 | ☐ |
| `"Urdu" "Latin script" LLM evaluation` | Scholar, arXiv | ☑ 2026-11-17 | ☐ |
| `"Roman Urdu" "spelling variants" LLM` | Scholar, arXiv | ☐ | ☐ |
| `"Roman Urdu" MCQ LLM` | Scholar, arXiv | ☐ | ☐ |
| `"transliterated Urdu"` LLM benchmark | Scholar, arXiv | ☐ | ☐ |
| `Belebele urd_Latn` | Scholar, Hugging Face, GitHub | ☑ 2026-11-17 | ☐ |
| `romanized` MMLU benchmark (Hindi, Bengali, Punjabi, Sinhala, any South Asian language) | Scholar, arXiv | ☐ | ☐ |
| `answer flip rate` spelling variants multiple choice LLM | Scholar, arXiv | Scholar ☑ 2026-11-17, arXiv ☐ | ☐ |

Use at least two phrasings of the language name ("Roman Urdu", "romanized Urdu", "Urdu written in Latin script", "transliterated Urdu"); a missing hit may only mean different wording.
If a search returns zero results, **log it** too.

## 4. Claims register: what we may and may not say

| Topic | Allowed wording | Not allowed |
|---|---|---|
| Novelty | "To our knowledge, and as of [date], we did not find a study that ... in our searches (Section X, Appendix Y)." | "No one has done this." "First study ..." (unless the literature table fully supports it) |
| Closest prior work | Verified from the seven-page preprint PDF (Zenodo DOI 10.5281/zenodo.24045043): describe Hussain and Khalid (2026, preprint) as reporting that informal chat spelling reduced task accuracy in evaluated small local clinic ReAct agents on physiotherapy queries (a 22.1 paired pp drop on 95 matched items for Qwen2.5 3B). Our study differs in evaluating factual knowledge MCQs, systematically controlling three orthographic conventions (RU-P, RU-R, RU-X) alongside native (NU) and back-transliterated (RT) baselines, and measuring within-item Answer Flip Rates while isolating repeated-run noise. | "First study of Roman Urdu spelling effects." Presenting an unverified record as peer-reviewed. Claiming no prior paired Roman Urdu spelling study exists |
| Gap statement (draft) | The verified L24 preprint (Hussain and Khalid, 2026) reports paired Roman Urdu spelling evaluation in clinical ReAct agent tool use on specific evaluated models. Our study asks whether item-level answer choice flips occur across rule-governed Roman Urdu orthographic conventions on knowledge multiple-choice questions, compared with native Nastaliq and back-transliterated conditions and repeated-run noise controls. While L24 is now full-text verified, unresolved candidates such as L28 remain pending verification. | "No prior work exists." Conflating agent accuracy drop with multiple-choice Answer Flip Rate |
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
| L02 | `bandarkar2024belebele` | 2026-11-16 | Younas |
| L03 | `faheem2026umirage` | 2026-11-16 | Younas |
| L05 | `khan2026urduidioms` | 2026-11-16 | Younas |
| L07 | `ghosh2026tokenization` | 2026-11-16 | Younas |
| L10 | `jamil2026ruab` | 2026-11-16 | Younas |
| L13 | `saeed2025purutt` | 2026-11-16 | Younas |
| L16 | `rajapakse2026sinhala` | 2026-11-16 | Younas |
| L19 | `chai2024tokenization` | 2026-11-16 | Younas |
| L22 | `bandarkar2026scripts` | 2026-11-16 | Younas |
| L01 | `tabassum2026urdummlu` | 2026-11-21 | Younas |
| L04 | `khullar2025scriptgap` | 2026-11-21 | Younas |
| L09 | `soomro2024romanurdu` | 2026-11-21 | Younas |
| L25 | `jamil2026tokencost` | 2026-11-22 | Younas |
| L24 | `hussainKhalid2026romanurdu` | 2026-11-23 | Younas |

## 6. Day 4 literature checklist (with the claims audit in `PLAN.md`)

- [x] All P1 papers opened and verified (L01 to L05, and L24).
- [ ] Every paper cited in the draft has its verification box ticked.
- [ ] Section 3.2 searches repeated; dates and counts recorded.
- [ ] L13: re-open the publisher page and reconfirm the DOI and the CC BY 4.0 license (a later AI-assisted review could not reconfirm them).
- [ ] L16, L07, L22: confirm the corrected arXiv IDs when you next open each paper (see the corrections log).
- [ ] Belebele `urd_Latn` search: fill in the missing total hits count in Section 3.1.
- [ ] Any new closest-prior-work found late is added here and the novelty wording is changed (claims change, data does not).
- [ ] The related-work section uses **only** verified entries.

## 7. Verification notes (one block per verified paper)

### L01 UrduMMLU: A Massive Multitask Benchmark for Urdu Language Understanding (Tabassum et al., MBZUAI, arXiv v1 2026)
- Opened full text: 2026-11-21 (Younas). Full-text URL: https://arxiv.org/html/2606.07167v1
- Authors: Ahmer Tabassum, Sarfraz Ahmad, Hasan Iqbal, Owais Aijaz, Momina Ahsan, and Preslav Nakov.
- Affiliation: MBZUAI.
- Year/version: 2026; arXiv v1 submitted 5 June 2026, arXiv ID 2606.07167.
- Publication status: the official project page records submission to ACL Rolling Review in May 2026. EMNLP 2026 is not a verified venue.
- Official URLs:
  - arXiv: https://arxiv.org/abs/2606.07167
  - Project: https://mbzuai-nlp.github.io/UrduMMLU/
  - Code: https://github.com/MBZUAI-NLP/UrduMMLU
  - Dataset: https://huggingface.co/datasets/MBZUAI/UrduMMLU
- Dataset: 26,431 native Urdu MCQs, 26 subdomains, and five domains (STEM, Humanities, Social Sciences, Profession, and Other). Sources include native Urdu MCQ websites and Pakistani SSC/HSSC examination PDFs.
- Dataset-card metadata: the official Hugging Face card for https://huggingface.co/datasets/MBZUAI/UrduMMLU records 26,431 Urdu MCQs, CC BY 4.0 licensing, and the dataset file `urdummlu.json`. The downloadable dataset archive has not been independently downloaded and inspected in this repository.
- Annotation: 12,759 exam-derived questions have human-annotated labels; 13,672 web-derived questions have human-validated answer labels. A total of 17 annotators participated. Observed agreement was 89.98%, and simplified Cohen's kappa was 0.8663.
- Methodology: multi-stage extraction, normalization, cleaning, and deduplication; dual human annotation of exam-derived questions; strict consensus filtering. Accuracy is the primary metric. Thirty LLMs were evaluated under English and Urdu prompts. Four open-source models were additionally evaluated in 1-, 3-, and 5-shot settings.
- Main findings supported by the paper: Gemini-3.5-Flash achieved the highest reported overall accuracy; models generally performed better on STEM than Urdu-centred Humanities; prompt-language changes had limited effect for most models; few-shot prompting produced modest gains.
- Limitations: focus on Pakistani SSC/HSSC curricula and selected Urdu MCQ websites; no Indian Urdu curricula, dialectal variation, or Urdu-English code-switching coverage; four-option MCQs only; no open-ended writing or option-order robustness evaluation.
- Licenses: the arXiv paper is CC BY 4.0, the Hugging Face dataset card records the dataset licence as CC BY 4.0, and the code is GPL-3.0. The downloadable dataset archive has not been independently downloaded or inspected.
- Our difference: UrduMMLU provides the native Urdu MCQ source and an evaluation foundation. It does not experimentally investigate Roman Urdu spelling variation, RU-P versus RU-R versus RU-X, back-transliteration, or Answer Flip Rate across spelling conditions.
- Allowed wording: "UrduMMLU provides a large native-Urdu, four-option exam benchmark and an evaluation foundation for our dataset."
- Not allowed: using UrduMMLU as evidence of Roman Urdu spelling robustness or as proof of the research gap by itself.

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
- Spelling variation: not studied in the paper (confirmed by searching the PDF for "spelling" and "variant"; the paper varies languages and scripts, not orthographic styles). Checked 2026-11-16, Younas.
- Our difference: single romanization of reading-comprehension passages; no controlled spelling styles, no per-item answer flips, no exam-style knowledge items.
- Allowed wording: "Belebele includes a romanized Urdu split produced by transliteration, with one romanized version per item; to our knowledge it does not vary spelling styles."
- Not allowed: "Belebele shows Roman Urdu is worse" without naming the task and the models, or any claim about current models.

### L04 Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real World Setting (Khullar et al., arXiv v2 2026)
- Opened full text: 2026-11-21 (Younas). Full-text URL: https://arxiv.org/html/2512.10780v2
- Authors: Manurag Khullar, Utkarsh Desai, Poorva Malviya, Aman Dalmia, and Zheyuan Ryan Shi.
- Bibliographic details: arXiv:2512.10780v2 (originally submitted 11 December 2025; revised v2 30 March 2026). DOI: 10.48550/arXiv.2512.10780.
- Publication status: arXiv preprint (v2). Peer-reviewed venue not independently confirmed; cite strictly as an arXiv preprint.
- Verification scope: Full HTML paper and official arXiv metadata inspected. Supplementary data, code repository, and peer-reviewed venue were not independently verified.
- Dataset & task: Real-world maternal and newborn healthcare triage based on ~133,000 de-identified WhatsApp messages; 3,153 sampled single-turn patient messages across Hindi, Telugu, Kannada, Marathi, Punjabi, Nepali, and an English baseline.
- Methodology: Native-script versus Romanized input comparison using raw messages without synthetic normalization; fixed prompt template, deterministic temperature 0. Evaluated frontier proprietary and open-weights models: GPT-4o, Claude Sonnet 4.5, DeepSeek V3, Llama 4, and Qwen models. Dual human expert cross-validation on 200 messages achieved 87.5% agreement and Cohen's kappa = 0.74.
- Main findings:
  - Romanized inputs consistently underperform native-script inputs, with performance gaps reaching up to 24 percentage points depending on model and language.
  - Secondary validation on HealthBench shows an average 5.4 percentage-point drop in weighted-F1 for Romanized input.
  - Full cross-model agreement falls from 66.5% under native script to 56.8% under Romanized script.
  - Comprehension failures (inability to resolve colloquial transliterated phrasing) and classification failures (correct symptom recognition but wrong urgency category) both contribute substantially to the script gap.
  - Proposes uncertainty-based selective routing and script-aware prompting as mitigations.
- Critical metric distinction: The paper's "Flip Rate" evaluates prediction changes across decoding temperatures for the same input string (a test of sampling noise/stochasticity). It is fundamentally distinct from our project's Answer Flip Rate (AFR), which measures choice flips across systematically controlled orthographic conditions (NU, RU-P, RU-R, RU-X, RT) at temperature 0.
- Limitations & project relevance:
  - Urdu is not evaluated.
  - Task is healthcare triage classification, not exam-style knowledge MCQs.
  - Does not test multiple Roman Urdu spelling conventions (evaluates native script vs. a single romanization).
  - Serves as strong real-world evidence for script-level degradation, but does not answer our within-Roman-Urdu spelling robustness question.
- Allowed wording: "Khullar et al. (2025/2026, arXiv:2512.10780) show that LLM performance on Indic clinical triage drops by up to 24 percentage points when queries are Romanized instead of in native script."
- Not allowed: Claiming Khullar et al. evaluated Urdu, evaluated multiple Roman Urdu spelling conventions, or that their temperature-based flip rate is comparable to our Answer Flip Rate across spelling conditions.

### L05 Evaluating Large Language Models on Urdu Idioms (Khan and Akter, Findings of EMNLP 2026, arXiv:2510.17460)
- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed (Findings of EMNLP 2026; arXiv:2510.17460).
- Authors: Muhammad Farmal Khan and Mousumi Akter (TU Dortmund / RC Trustworthy Data Science and Security).
- Dataset: 4,000 aligned idiom-sentence pairs for Urdu-to-English translation in two script forms: Native Urdu script (Perso-Arabic) and Romanized Urdu.
- Tasks: idiomatic translation, paraphrasing, idiom span detection, and back-translation.
- Prompting strategies: zero-shot, few-shot learning, cultural prompting, idiomatic prompting.
- Evaluation metrics: BLEU, chrF, BERTScore, COMET, XCOMET, LASER, LaBSE, USE.
- Script and orthography findings: models consistently performed more stably on native Perso-Arabic script; performance dropped noticeably on Romanized Urdu across models and metrics. The authors explicitly cite the lack of standardized orthography (spelling variability) in Romanized Urdu as a major obstacle to model consistency and idiom span detection.
- Roman Urdu variation: single transliteration per idiom-sentence pair; no controlled manipulation of spelling styles.
- Our difference: figurative language translation/detection vs our exam-style factual knowledge MCQs (UrduMMLU); they observe Roman Urdu orthographic noise as an uncontrolled obstacle, whereas our study systematically manipulates orthographic style (RU-P, RU-R, RU-X) while keeping words, syntax, and semantics identical, evaluating answer flip rates.
- Allowed wording: "Khan and Akter (2026) report that LLMs perform worse on Romanized Urdu idiom translation than on native Perso-Arabic script, noting that unstandardized orthography impairs consistency, though they did not experimentally control spelling styles."
- Not allowed: claiming Khan and Akter evaluated spelling flip rates or multiple-choice knowledge tasks.

### L07 Language Models are not Equally Robust to Non-Canonical Tokenization across Languages (Ghosh and Jyothi, arXiv 2026, arXiv:2607.26831)
- Opened full text: 2026-11-16 (Younas). Venue: preprint (arXiv:2607.26831).
- Authors: Poulami Ghosh and Preethi Jyothi (IIT Bombay).
- Task: evaluation of LLM robustness under alternative, non-canonical tokenizations across 27 languages and 6 downstream tasks.
- Key findings: tokenization invariance is not universal across languages; instruction-tuned models suffer substantial relative performance drops (e.g. Llama-3.1-8B dropped 23.7%, Qwen3-8B 11.4%). Languages with higher token fragmentation exhibit significantly greater vulnerability to non-canonical tokenizations.
- Our difference: tokenization perturbation alters subword segmentation of identical surface strings, whereas our study manipulates orthography (RU-P, RU-R, RU-X) where surface strings differ but underlying words and semantics are held constant.
- Allowed wording: "Ghosh and Jyothi (2026) report that LLM sensitivity to non-canonical tokenizations varies across languages and scales with token fragmentation; however, tokenization perturbation is distinct from orthographic variation."
- Not allowed: equating tokenization perturbation with human orthographic variation.

### L09 A Dataset of Roman Urdu Text with Spelling Variations for Sentence Level Sentiment Analysis (Soomro et al., Data in Brief 2024)
- Opened full text: 2026-11-21 (Younas). Full-text URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/
- Authors: Mudasar Ahmed Soomro, Rafia Naz Memon, Asghar Ali Chandio, Mehwish Leghari, and Muhammad Hanif Soomro.
- Venue & Bibliographic details: *Data in Brief*, Volume 57, Article 111170, published 23 November 2024. DOI: 10.1016/j.dib.2024.111170. Open access under CC BY 4.0.
- Dataset repository: Mendeley Data, Version 5, published 7 October 2024. DOI: 10.17632/v5jfhsvtmd.5, CC BY 4.0. Landing page, metadata, and license inspected; individual downloadable dataset files have not been independently parsed.
- Dataset 1 (Word spelling variations lexicon):
  - 5,244 unique Roman Urdu headwords; 19,527 total spelling forms.
  - Up to five spelling variants per word (schema includes `Common`, `Var-1` to `Var-5`, and `English` translation).
  - Common spelling chosen strictly based on corpus frequency.
  - Extracted from 20,232 initial Roman Urdu reviews through tokenization, cleaning, and manual word identification.
- Dataset 2 (Sentence-level sentiment reviews):
  - 28,090 reviews classified into five categories (*Very Positive*, *Positive*, *Neutral*, *Negative*, *Very Negative*).
  - Collected via ParseHub scraping and manual extraction. Inclusion criteria: minimum 75% Roman Urdu, minimum 100 words, and at least two Roman Urdu words.
  - Subset of 831 reviews independently annotated by 3 of 5 annotators with majority voting.
- Experimental results:
  - Word spelling classification: Support Vector Machine (SVM) achieved 99% accuracy on an 80/20 train/test split.
  - Sentence-level sentiment classification: Recurrent Convolutional Neural Network (RCNN) achieved 93% accuracy.
- Internal discrepancies in the paper:
  - Single-spelling words: Section 2 narrative reports 41 words with one spelling, whereas Table 1 explicitly reports 42 words.
  - Source count: Narrative reports 7 internet-based sources, but explicitly names 8 platforms/websites.
  - Both discrepancies are recorded as reported without silent resolution.
- Our difference and research relevance:
  - Linguistic attestation: Confirms pervasive natural spelling variation in real-world Roman Urdu (up to 5 variants per word), providing external justification for the orthographic operations in `docs/RULES.md`.
  - Methodological contrast: Soomro et al. focus on spelling normalization/deduplication to train traditional classifiers (SVM/RCNN). They do NOT evaluate LLM robustness, do not test examination MCQs, do not measure Answer Flip Rate (AFR), and do not evaluate our five conditions (NU, RU-P, RU-R, RU-X, RT).
- Allowed wording: "Soomro et al. (2024) document 19,527 naturally occurring spelling forms across 5,244 Roman Urdu words, demonstrating the empirical breadth of unstandardized orthography in user-generated text."
- Not allowed: Claiming Soomro et al. evaluated LLM answer robustness, measured Answer Flip Rate, or evaluated multiple-choice questions.

### L10 Code-Switching as a Safety Failure Mode in LLMs (RUAB) (Jamil and Rafi, AbjadNLP 2026, pp. 295-300)
- Opened full text: 2026-11-16 (Younas). Venue: workshop paper (AbjadNLP 2026, ACL Anthology).
- Correction 2026-11-22: the ACL Anthology record (2026.abjadnlp-1.37, DOI 10.18653/v1/2026.abjadnlp-1.37) gives pages 295-300; the earlier heading said 116-132. The "explicitly normalised" statement below was not confirmed in an independent check. Re-read the setup section of the PDF and copy the exact sentence before using that wording; until then use only "RUAB holds semantic intent constant across English, mixed and transliterated Roman Urdu conditions".
- Authors: Waleed Jamil and Saima Rafi (Edinburgh Napier University).
- Dataset: Roman Urdu Adversarial Benchmark (RUAB), consisting of 400 safety-relevant intents across 3 variants: Standard English, Mixed Roman Urdu, and Transliterated Roman Urdu (1,200 inputs).
- Normalisation statement: spellings in transliterated Roman Urdu were explicitly normalised before testing to ensure uniform vocabulary.
- Our difference: safety benchmark where Roman Urdu spellings were normalised away; our study focuses on factual knowledge MCQs and directly evaluates unstandardized spelling variations (answer flip rates).
- Allowed wording: "Jamil and Rafi (2026) evaluated Roman Urdu safety guardrails in RUAB, but explicitly normalised spellings prior to testing."
- Not allowed: citing RUAB as evaluating orthographic robustness or answer instability.

### L13 PURUTT (Saeed, Khalil, Kamiran, IEEE Access 2025, vol. 13, pp. 21635-21651, DOI: 10.1109/ACCESS.2025.3538411)
- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed open access journal (IEEE Access, vol. 13).
- Corpus: Parallel Urdu and Roman Urdu Corpus for Toxic Comments and Transliteration (PURUTT).
- Size and composition: 72,771 annotated parallel comments in Perso-Arabic Urdu script and Roman Urdu (Latin script); GitHub repository: `hafizhassaan/Urdu-Toxic-Comments`.
- DOI/status: the exact DOI 10.1109/ACCESS.2025.3538411 did not resolve in a Crossref exact-DOI lookup recorded in this repository. It remains unresolved pending publisher verification; do not present the DOI as established.
- Licence/status: repository notes have not reconciled the claim that the paper/dataset is CC BY 4.0 with the later inability to reconfirm the licence at an authoritative publisher record. The licence remains unresolved; do not grant reuse or attribution conclusions until it is confirmed.
- Role in our project: Optional real-usage check for Roman Urdu orthography (Section 6 of PLAN.md; cut list item 1 if 4-day sprint time is constrained).
- Source-qualified wording: "Repository notes report that PURUTT contains 72,771 parallel comments in Urdu and Roman Urdu. The DOI and CC BY 4.0 licence remain unresolved and must not be cited until confirmed."
- Not allowed: citing PURUTT as having controlled orthographic conditions or exam MCQs.

### L16 Script Sensitivity: Benchmarking Language Models on Unicode, Romanized and Mixed-Script Sinhala (Rajapakse and Weerasinghe, arXiv:2601.14958)
- Opened full text: 2026-11-16 (Younas). Venue: preprint (arXiv:2601.14958).
- Authors: Minuri Rajapakse and Ruvan Weerasinghe.
- Language and task: Sinhala language modeling and open generation across Unicode, Romanized (Singlish), and mixed script evaluated via perplexity.
- Key findings: models exhibit extreme script sensitivity when switching from Unicode to Romanized text, with median performance degradation exceeding 300x. Parameter scale did not reliably protect against script degradation.
- Our difference: Sinhala language generation evaluated by perplexity across scripts; our study tests Roman Urdu knowledge MCQs evaluated by zero-shot accuracy and within-item answer flip rate across systematic spelling conventions within the Latin script.
- Allowed wording: "Rajapakse and Weerasinghe (2026) document high script sensitivity (>300x perplexity degradation) in Romanized Sinhala, demonstrating that Latin-script variants pose severe challenges for LLMs in South Asian languages."
- Not allowed: citing this paper as evidence for multiple-choice exam accuracy flips or Urdu.

### L19 Tokenization Falling Short: On Subword Robustness in Large Language Models (Chai et al., Findings of EMNLP 2024, pp. 15610-15627)
- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed (Findings of EMNLP 2024).
- Authors: Yekun Chai, Yewei Fang, Qiwei Peng, and Xuhong Li.
- Scope and benchmark: evaluates subword robustness and "the curse of tokenization" across reasoning and MMLU-style benchmarks (`TKEval`).
- Key findings: subword boundary shifts and minor typos cause severe unexpected degradation in LLM reasoning; parameter scaling alone does not resolve subword brittleness; subword regularisation (BPE-dropout) mitigates fragility.
- Our difference: evaluates random typographical errors, character swaps, and synthetic subword perturbations; our work evaluates intentional, rule-governed human orthographic styles (RU-P, RU-R, RU-X) holding words, syntax, and semantics identical.
- Allowed wording: "Chai et al. (2024) demonstrate that subword tokenization boundaries induce brittleness on MMLU-style reasoning tasks under typographical perturbations."
- Not allowed: equating random subword noise/typos with controlled orthographic styles.

### L22 Large Reasoning Models Struggle to Transfer Parametric Knowledge Across Scripts (Bandarkar et al., Findings of EMNLP 2026, arXiv:2603.17070)
- Opened full text: 2026-11-16 (Younas). Venue: peer-reviewed (Findings of EMNLP 2026).
- Authors: Lucas Bandarkar, Alan Ansell, and Trevor Cohn.
- Scope: cross-lingual parametric knowledge transfer across scripts using *ECLeKTic* and *MultiLoKo* datasets on reasoning models.
- Key findings: script mismatch between entity/query and parametric knowledge is the single dominant predictor of knowledge transfer failure; models fail specifically at cross-script entity alignment/transliteration.
- Our difference: evaluates transfer across distinct language scripts (e.g. Cyrillic, Greek, Arabic, Latin); our study fixes the script to Latin and tests whether orthographic variation within Roman Urdu induces answer instability on exam MCQs.
- Allowed wording: "Bandarkar et al. (2026) show that cross-script transliteration mismatch is a primary bottleneck in parametric knowledge transfer for reasoning models."
- Not allowed: claiming Bandarkar et al. evaluated spelling variations within Roman Urdu.

### L24 Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions (Hussain and Khalid, 2026, preprint)
- Verified full text: 2026-11-23 (Younas). Primary source: actual seven-page PDF (`04_RomanUrdu_ReAct.pdf`, 239.6 kB, md5 `3b8c0761f40054db9386b44b506b4465`) inspected.
- Bibliographic details and principal results cross-checked against public repository README and published results tables. Raw experimental calls (3,838 calls) were not independently rerun.
- Authors: Muzammal Hussain and Maryam Khalid.
- Date: November 2026 (7 November 2026, Version 1).
- Publication status: Version 1 preprint on Zenodo, resource type Preprint, license CC BY 4.0. Not peer-reviewed.
- Identifiers & records:
  - Paper / preprint DOI: `10.5281/zenodo.24045043` (Version 1 DOI, cited by Zenodo; all-versions DOI `10.5281/zenodo.24045042`).
  - Software / data DOI: `10.5281/zenodo.24044983` (version DOI; all-versions DOI `10.5281/zenodo.24044982`). Author: Muzammal Hussain. Version: v1.0.0. License: MIT. Public GitHub repository: https://github.com/MHKhan50/roman-urdu-react-bench (tag v1.0.0).
  - Relationship: The two Zenodo records link to each other (preprint is supplemented by software; software is supplement to preprint).
- Research objective: Evaluate how Roman Urdu input affects small local ReAct agents answering fictional physiotherapy-clinic questions (scheduling, triage, dosage, patient lookup).
- Dataset & benchmark design:
  - 96 fictional clinical questions constructed from 12 parameterized question templates (4 instances per template, 2 distinct patient name sets).
  - 3 paired language forms: English prompt baseline, Common Roman Urdu, and Chat-Spelling Roman Urdu.
  - 4 local models evaluated: Qwen2.5 3B, Qwen2.5 7B, Llama 3.2 3B, and Llama 3.1 8B.
  - 4 evaluation methods: Direct answering, ReAct with an English example, ReAct with a Roman Urdu example, and Translate-then-ReAct.
  - Evaluation controls: Single evaluation pass at deterministic temperature 0 (no repeated-run noise analysis); 3,838 total scored model/tool calls (two timeout calls excluded).
- Main findings & numerical clarification:
  - Under ReAct with English example, switching from English to Common Roman Urdu caused substantial accuracy drops in three of four models: Qwen2.5 3B dropped -34.7 percentage points, Llama 3.2 3B dropped -31.2 percentage points, and Llama 3.1 8B dropped -21.9 percentage points; Qwen2.5 7B showed slight resilience (+1.0 percentage points).
  - Chat spelling imposed a further performance penalty on sensitive models: for Qwen2.5 3B, Common Roman Urdu achieved 57.9% accuracy and Chat Spelling achieved 36.5% accuracy.
  - *Numerical clarification on paired difference:* The paper reports a paired loss of −22.1 percentage points based on 95 matched items. This paired comparison uses matched items and is distinct from simple marginal subtraction of the displayed percentages (57.9% − 36.5% = 21.4 pp); the 22.1 pp paired result is preserved as reported.
- Important benchmark limitations & clinician review:
  - Synthetic domain: Fictional physiotherapy clinic; 12 templates written by one person.
  - Model scope: Four small local models; one sample per question at temperature 0; two timeout calls excluded (3,838 scored calls).
  - Clinician audit: A post-hoc audit conducted by 1 clinician on 48 items (covering only one of the two name sets):
    - All 48 gold answers were judged medically correct.
    - 16 items (from templates T03–T06) were judged clinically unrealistic for outpatient practice.
    - 7 Roman Urdu items exhibited Urdu grammatical gender-agreement errors.
- BibTeX entry for paper:
  ```bibtex
  @misc{hussainKhalid2026romanurdu,
    author = {Hussain, Muzammal and Khalid, Maryam},
    title = {Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions},
    year = {2026},
    publisher = {Zenodo},
    doi = {10.5281/zenodo.24045043},
    note = {Version 1 preprint}
  }
  ```
- Software citation note: Software/data DOI `10.5281/zenodo.24044983` (author Muzammal Hussain, v1.0.0, MIT) is recorded separately and not conflated with the paper citation.
- Overlap & research relevance: Closest known empirical study evaluating paired Roman Urdu input forms on language models. Reports that informal chat spelling reduced task accuracy in the evaluated small local ReAct agents on fictional physiotherapy-clinic queries.
- Differences from our research:
  - Task: Clinical agent tool-calling execution vs. our factual knowledge multiple-choice questions (UrduMMLU).
  - Conditions: English, common Roman Urdu, chat Roman Urdu vs. our five matched conditions (NU, RU-P, RU-R, RU-X, RT).
  - Metrics: Macro task accuracy drops via paired bootstrap vs. our primary metric, **Answer Flip Rate (AFR)**, which measures within-item choice flips under semantics-preserving spelling changes.
  - Script controls: No native Nastaliq (`NU`) or back-transliteration (`RT`) conditions; does not test multiple rule-governed Roman Urdu orthographies (RU-P, RU-R, RU-X).
- Internal, source-qualified wording only: "Hussain and Khalid (2026, preprint) report that informal chat spelling reduced task accuracy by 22.1 paired percentage points in small local ReAct agents across two Roman Urdu forms on clinic queries."
- Allowed, source-qualified gap phrasing for our manuscript: "While Hussain and Khalid (2026, preprint) observed that informal chat spelling degraded task accuracy in small clinical ReAct agents across two Roman Urdu renderings (a 22.1 paired percentage-point drop on Qwen2.5 3B), the reviewed literature has not yet established whether item-level answer choices flip across systematic, rule-governed Roman Urdu orthographic conventions on factual multiple-choice benchmarks, nor compared them against native Nastaliq (`NU`) and back-transliterated (`RT`) baselines while controlling for repeated-run noise."
- Not allowed: Claiming our study is the first to evaluate paired Roman Urdu spelling; presenting Hussain and Khalid (2026, preprint) as peer-reviewed; claiming Hussain and Khalid evaluated multiple-choice questions or measured Answer Flip Rate.

### L25 Token Cost Inequality: Measuring Tokenization Disparities Across Scripts in Roman Urdu and Urdu (Jamil, Rafi, and Yu, GEM 2026)
- Reviewed full text: 2026-11-22 (Younas). Official record: https://aclanthology.org/2026.gem-main.54/
- Authors: Waleed Jamil, Saima Rafi, and Yanchao Yu.
- Venue: Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM), July 2026, pages 563-573.
- DOI: 10.18653/v1/2026.gem-main.54.
- PDF: https://aclanthology.org/2026.gem-main.54.pdf
- Verification: full text independently accessed and reviewed; bibliographic details verified.
- Methodology:
  - 10,000 sampled examples from each of Roman-Urdu-Parl, OPUS100 English-Urdu, and Dakshina Urdu.
  - Three tokenizer families: cl100k_base, mT5, and ByT5.
  - Measures: Token Cost Inequality (TCI), tokens per word, fixed-budget character retention, cost multipliers, and lightweight normalization.
  - Fixed budgets: 16, 32, 64, 128, and 256 tokens.
- Main findings:
  - Tokenization disparities depend strongly on tokenizer design.
  - Roman-Urdu-Parl mean TCI: 0.473 for cl100k_base, 0.967 for mT5, and 0.669 for ByT5.
  - With cl100k_base and a 16-token budget, Roman Urdu retained 74.1% of surface content versus 44.9% for Urdu.
  - Lightweight normalization produced negligible improvements.
  - Token cost alone does not determine retained character coverage.
- Limitations:
  - Only three tokenizer families were evaluated.
  - Fixed-budget character retention is not semantic preservation.
  - No downstream task performance or generation-quality evaluation was conducted.
  - Samples were limited to 10,000 examples per dataset.
  - Normalization was lightweight rather than comprehensive.
- Relevance: relevant token-cost and fixed-budget background, but it does not evaluate LLM answer accuracy, Urdu MCQs, or comparisons among RU-P, RU-R, and RU-X.
- Allowed wording: "Jamil, Rafi, and Yu (2026) found tokenizer-dependent disparities in Roman-Urdu/Urdu token cost and fixed-budget surface retention."
- Not allowed: citing L25 as evidence of answer accuracy changes, MCQ performance, or RU-P/RU-R/RU-X robustness.

### L28 Facts Follow the Spelling: How Names Are Written Shapes Cross-Lingual Knowledge Transfer
- Status: unresolved. No reliable official paper record or full text has been located.
- Author, year, venue, DOI, methodology, findings, limitations, and peer-review status are not established.
- Do not use the provisional title or alleged findings as evidence in the project literature review.
- Reliable source required: locate an official publication or stable preprint record and review the full text before changing this status.

### Corrections log (2026-11-19)

Checked against the arXiv abstract pages through web search on 2026-11-19. Re-confirm when you next open each paper.

- **L07 (Ghosh and Jyothi):** the correct ID is arXiv:2607.26831 (submitted 29 Jul 2026). The earlier ID 2602.05282 was wrong.
- **L16 (Rajapakse and Weerasinghe):** the correct ID is arXiv:2601.14958 (v1 submitted 21 Jan 2026). v1 was titled "A Comprehensive Benchmark of Language Models on Unicode and Romanized Sinhala"; the later version (v3, 8 May 2026) is titled "Script Sensitivity: Benchmarking Language Models on Unicode, Romanized and Mixed-Script Sinhala". Check that the numbers quoted in the L16 note above (for example, the 300x median degradation) match the version you read. The BibTeX key was changed from `rajapakse2024sinhala` to `rajapakse2026sinhala`, and the year in the allowed wording from 2024 to 2026. The earlier ID 2410.22230 was wrong.
- **L22 (Bandarkar, Ansell and Cohn):** the correct ID is arXiv:2603.17070 (submitted 17 Mar 2026). The earlier ID 2603.18742 was wrong. The arXiv page shows a preprint only, so re-confirm the "Findings of EMNLP 2026" venue before citing it as peer-reviewed.
- **L03:** the Section 2 boxes were still unticked although Section 5 and Section 7 record it as verified on 2026-11-16 (Younas). The boxes now match those records. Untick them if that record is wrong.
- **L13:** the 2026-11-16 repository note records a full-text review and reports CC BY 4.0. A later exact-DOI lookup did not resolve 10.1109/ACCESS.2025.3538411, and the licence could not be reconfirmed. The conflict remains unresolved; the DOI and licence are not verified.

## 8. Thematic synthesis for this project (provisional)

This synthesis consolidates the existing table and notes; it is not a new full-text verification pass. Section 2 checkboxes remain the source of truth. In particular, search-result notes, abstracts, and bibliographic records do not establish full-text findings.

### Urdu NLP and benchmarks

The project’s source benchmark is UrduMMLU (L01), a native-Urdu exam-style multiple-choice resource. L01 was verified from the arXiv full text on 2026-11-21, including its dataset size, domains, sources, annotation process, methodology, reported findings, limitations, URLs, and publication status. The official Hugging Face dataset card was subsequently checked: it records 26,431 Urdu MCQs, CC BY 4.0, and `urdummlu.json`. The downloadable dataset archive has not been independently downloaded and inspected. EMNLP 2026 is not confirmed as a venue; the record is an arXiv v1 preprint submitted to ACL Rolling Review in May 2026. Belebele (L02) is also repository-recorded as full-text verified and includes Urdu native- and Latin-script reading-comprehension versions, with one transliterated form per item. U-MIRAGE (L03) and the Urdu idiom study (L05) are also repository-recorded as verified, but their medical-QA and translation tasks do not establish effects on exam-style knowledge MCQs.

### Roman Urdu datasets and linguistic resources

The Soomro et al. Data in Brief paper (L09) has been verified from the open-access full text in PMC (PMC11683287). It documents 19,527 spelling forms across 5,244 Roman Urdu headwords and 28,090 sentiment reviews under CC BY 4.0, but its focus is lexicon-based normalization rather than testing LLM answer flips across controlled spelling styles. PURUTT (L13) has a repository-recorded full-text check, but its DOI and license have conflicting notes; resolve those against the publisher before relying on them. Neither item is evidence that controlled spelling variants change knowledge-MCQ answers.

### Native-script versus Romanized evaluation

Belebele (L02) compares native and a single Latin-script rendering in reading comprehension. U-MIRAGE (L03) compares Urdu and one Roman Urdu form in medical QA. Script Gap (L04) is an arXiv preprint (v2, 2026) verified from full text, demonstrating native vs. romanized performance drops in real-world maternal/newborn triage across Indic languages and Nepali; it does not evaluate Urdu or multiple Roman Urdu spelling styles. These works motivate script comparisons, but do not by themselves answer whether multiple meaning-preserving Roman Urdu spellings change answers to the same knowledge item.

### Roman Urdu spelling variation and normalization

Soomro et al. (L09) provides attested spelling-variation data, verified from full text. Like RUAB (L10), its objective is to normalize spelling variation rather than evaluate LLM answer sensitivity across multiple meaning-preserving Roman Urdu conventions. The verified L24 preprint (Hussain and Khalid, 2026) describes a paired Roman Urdu clinic ReAct evaluation on physiotherapy queries and reports an accuracy cost for chat spelling (−22.1 paired pp for Qwen2.5 3B across 95 matched items). It does not describe factual MCQs or our within-item answer flip rate across multiple rule-governed Roman Urdu conventions.

### Tokenization and multilingual model behavior

The repository records full-text checks of L07 and L19, which concern non-canonical tokenization or character perturbations rather than controlled human orthographic styles. Token Cost Inequality (L25) has now been independently full-text reviewed and is bibliographically verified. Jamil, Rafi, and Yu (2026) sampled 10,000 examples from each of three datasets, compared cl100k_base, mT5, and ByT5, and measured TCI, token cost, and fixed-budget character retention. Its Roman-Urdu-Parl TCI values were 0.473, 0.967, and 0.669 respectively, and lightweight normalization had negligible effects. The study is relevant to token-cost interpretation but does not evaluate LLM answer accuracy or compare RU-P, RU-R, and RU-X; fixed-budget character retention is not semantic preservation and is not an answer-instability outcome.

### Factual consistency and answer stability

The repository-recorded review of L22 concerns knowledge transfer across scripts, not alternative spellings within Roman Urdu. L03 reports aggregate accuracy by condition, while L29 is an unverified candidate for multiple-choice consistency methods. In the verified materials currently documented here, the reviewed literature has not yet established whether item-level answer choices flip across controlled Roman Urdu spelling styles on knowledge MCQs.

### Provisional gap and relation to the five conditions

The verified L24 preprint (Hussain and Khalid, 2026) describes paired Roman Urdu spelling evaluation in local clinical ReAct agents on physiotherapy queries, with English, common Roman Urdu, and chat spelling conditions. A distinct question for our study is whether meaning-preserving, rule-defined Roman Urdu spelling conventions alter item-level multiple-choice answers on Urdu knowledge questions. This study will compare five matched conditions (NU, RU-P, RU-R, RU-X, and RT), measure within-item Answer Flip Rates across the Roman Urdu variants, and distinguish spelling effects from repeated-run variability. L25 is different: it is a verified tokenization-efficiency study and does not answer the answer-instability question.

NU provides the source-script reference. RU-P, RU-R, and RU-X permit comparisons among the project’s specified Roman Urdu spellings while holding item meaning and register constant. RT provides the project’s back-transliterated-script condition; it should be interpreted according to the frozen protocol, not as another Roman spelling style. None of the reviewed materials establishes outcomes for these five project conditions. While L24 is now full-text verified (with reported degradation applying specifically to its evaluated local models and clinic benchmark), unresolved candidates such as L28 and pending searches must be resolved before finalizing the empirical gap.

### Source checks during this consolidation

- [UrduMMLU arXiv record](https://arxiv.org/abs/2606.07167): full text checked; official project and Hugging Face [dataset card](https://huggingface.co/datasets/MBZUAI/UrduMMLU) checked for 26,431 MCQs, CC BY 4.0, and `urdummlu.json`. The downloadable dataset archive was not independently downloaded and inspected.
- [Script Gap arXiv record](https://arxiv.org/abs/2512.10780): arXiv:2512.10780v2 HTML full text and metadata verified; peer-reviewed venue not confirmed.
- [Token Cost Inequality ACL Anthology record](https://aclanthology.org/2026.gem-main.54/): full text and bibliographic details verified; DOI 10.18653/v1/2026.gem-main.54.
- [Soomro et al. PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/) / [DOI](https://doi.org/10.1016/j.dib.2024.111170): verified from PMC full text and Mendeley Data landing page (v5, DOI 10.17632/v5jfhsvtmd.5).
- [PURUTT DOI as recorded in the table](https://doi.org/10.1109/ACCESS.2025.3538411): the Crossref exact-DOI lookup did not resolve, and a title lookup was rate-limited. This does not establish that the paper or DOI is invalid; the existing DOI/license conflict remains unresolved.
- [Hussain and Khalid (2026, preprint) L24]: Full-text verified from 7-page PDF (04_RomanUrdu_ReAct.pdf, md5 3b8c0761f40054db9386b44b506b4465) and cross-checked against public repository outputs. Preprint DOI 10.5281/zenodo.24045043 (Version 1; all-versions 10.5281/zenodo.24045042, CC BY 4.0, not peer-reviewed) by Muzammal Hussain and Maryam Khalid; software record DOI 10.5281/zenodo.24044983 (v1.0.0, MIT) by Muzammal Hussain on GitHub (https://github.com/MHKhan50/roman-urdu-react-bench). Raw experimental calls were not independently rerun.
- Facts Follow the Spelling (L28): the OpenReview API check was blocked by a browser verification page. Title, authors, review status, venue, and findings remain unverified.
