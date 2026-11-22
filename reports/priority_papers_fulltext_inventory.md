# Priority Papers Full-Text Inventory

**Phase:** 2 - Full-text verification  
**Scope:** L01, L04, L09, L24, L25, and L28 only  
**Method:** Repository inventory plus full-text/bibliographic review status recorded in the canonical literature table and detailed notes. No replacement papers were added and no L24 or L28 bibliographic evidence was fabricated.

## Paper inventory

| ID | Exact title | Complete author list | Year | Venue | DOI | Official publication URL | arXiv URL | Local PDF location | Current verification status | Priority reason |
|---|---|---|---|---|---|---|---|---|---|---|
| L01 | UrduMMLU: A Massive Multitask Benchmark for Urdu Language Understanding | Ahmer Tabassum; Sarfraz Ahmad; Hasan Iqbal; Owais Aijaz; Momina Ahsan; Preslav Nakov | 2026 | arXiv v1 preprint, arXiv:2606.07167; officially submitted to ACL Rolling Review in May 2026. EMNLP 2026 is not verified. | NOT FOUND | [Official arXiv page](https://arxiv.org/abs/2606.07167) / [full text](https://arxiv.org/html/2606.07167v1) / [project page](https://mbzuai-nlp.github.io/UrduMMLU/) / [code](https://github.com/MBZUAI-NLP/UrduMMLU) / [dataset card](https://huggingface.co/datasets/MBZUAI/UrduMMLU) | https://arxiv.org/abs/2606.07167 | NOT FOUND | Opened: yes. Verified: yes for the paper and Hugging Face card metadata. The card records 26,431 Urdu MCQs, CC BY 4.0, and `urdummlu.json`. The downloadable dataset archive has not been independently downloaded and inspected. | P1 source benchmark for native Urdu knowledge MCQs. The paper does not study Roman Urdu spelling variation or AFR. |
| L04 | Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real World Setting | Manurag Khullar, Utkarsh Desai, Poorva Malviya, Aman Dalmia, Zheyuan Ryan Shi | 2025 (originally submitted 11 Dec 2025; revised v2 30 Mar 2026) | arXiv preprint (v2), arXiv:2512.10780v2; peer-reviewed venue not independently confirmed | 10.48550/arXiv.2512.10780 | [Official arXiv page](https://arxiv.org/abs/2512.10780) / [HTML full text](https://arxiv.org/html/2512.10780v2) | https://arxiv.org/abs/2512.10780 | Inspected online (HTML full text) | Opened: yes. Verified: yes for claims supported by arXiv v2 HTML full text and metadata. Supplementary data, code, and peer-reviewed venue not independently verified. | P1 mechanism/effect-size reference for native versus romanized scripts. Verified: clinical triage on 3,153 messages from ~133k chats across 6 Indic languages + English baseline; up to 24 pp gap; HealthBench 5.4 pp weighted-F1 drop; 56.8% vs 66.5% agreement; models include GPT-4o, Claude Sonnet 4.5, DeepSeek V3, Llama 4, Qwen; human validation $\kappa = 0.74$. Does not include Urdu; no Roman Urdu spelling variants; paper's Flip Rate is across temperatures, not our AFR. |
| L09 | A Dataset of Roman Urdu Text with Spelling Variations for Sentence Level Sentiment Analysis | Mudasar Ahmed Soomro; Rafia Naz Memon; Asghar Ali Chandio; Mehwish Leghari; Muhammad Hanif Soomro | 2024 (published 23 Nov 2024) | Data in Brief, Volume 57, Article 111170 | 10.1016/j.dib.2024.111170 | [PMC full text](https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/) / [Publisher DOI](https://doi.org/10.1016/j.dib.2024.111170) / [Mendeley Data v5](https://data.mendeley.com/datasets/v5jfhsvtmd/5) | NOT FOUND | Inspected online (PMC full text) | Opened: yes. Verified: yes for claims supported by full text and Mendeley landing page metadata. Article: CC BY 4.0; dataset: CC BY 4.0. Raw downloadable dataset files not independently parsed. | P2 evidence for extensive natural Roman Urdu spelling variation (5,244 words, 19,527 forms, Var-1 to Var-5) and 28,090 sentiment reviews. Normalizes variants (SVM 99%, RCNN 93%); does not evaluate LLM answer robustness, MCQs, AFR, or our 5 conditions (NU, RU-P, RU-R, RU-X, RT). Note paper discrepancies: 41 vs 42 single-variant words; 7 vs 8 sources. |
| L24 | Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions | M. Hussain | 2026 (7 November 2026) | Supplied text describes an unrefereed preprint; publication venue and peer-review status not independently verified | 10.5281/zenodo.24045042 appears in the supplied text; separate code/data archive DOI unresolved | NOT FOUND (Zenodo and GitHub records unverified) | NOT FOUND | Supplied paper text | Opened: yes for supplied paper text. Bibliographic/full-record verification: unresolved. The paper record, Zenodo archive, GitHub archive, and venue are not independently verified. | P1 closest prior work on paired Roman Urdu spelling evaluation. 96 fictional questions, 12 templates, 3,838 calls, 4 local models, temp 0, 1 run; English, common Roman Urdu, and chat spelling. Three of four models showed substantial common-Roman-Urdu drops under the English-example ReAct condition. Preserved discrepancy: 22.1 pp chat-spelling loss for Qwen2.5 3B and displayed 57.9% vs 36.5% (21.4 pp). Limitations: 1 clinician reviewer, 48 items from 1 name set, 16 unrealistic, 7 gender issues. Agent accuracy, not MCQ AFR. |
| L25 | Token Cost Inequality: Measuring Tokenization Disparities Across Scripts in Roman Urdu and Urdu | Waleed Jamil; Saima Rafi; Yanchao Yu | 2026 | Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM), July 2026, pages 563-573 | 10.18653/v1/2026.gem-main.54 | https://aclanthology.org/2026.gem-main.54/ | NOT FOUND | [PDF](https://aclanthology.org/2026.gem-main.54.pdf) | Opened: yes. Verified: yes for full text and bibliographic details. | P2 token-cost and fixed-budget context. 10,000 samples per dataset; cl100k_base, mT5, and ByT5; TCI/tokens per word/character retention. Mean Roman-Urdu-Parl TCI: 0.473, 0.967, 0.669. At 16 cl100k_base tokens, Roman Urdu retained 74.1% versus 44.9% for Urdu. Lightweight normalization negligible; no downstream-task or MCQ answer-flip evaluation. |
| L28 | Facts Follow the Spelling: How Names Are Written Shapes Cross-Lingual Knowledge Transfer | NOT FOUND | NOT FOUND | NOT FOUND; only a provisional title is available | NOT FOUND | NOT FOUND | NOT FOUND | NOT FOUND | Opened: no. Verified: no. A reliable official source and full text could not be located. | P2 unresolved candidate. Authors, year, venue, DOI, methodology, findings, and peer-review status are not established. Do not use alleged findings as evidence. A stable official source is required before review. |

## Existing bibliography and literature-comparison material

- **Canonical literature table:** [docs/LITERATURE.md](../docs/LITERATURE.md), Section 2. This is the only in-repository literature comparison table found.
- **Search history:** [docs/literature_search_notes.md](../docs/literature_search_notes.md).
- **Consolidation report:** [reports/literature_consolidation_report.md](literature_consolidation_report.md).
- **Proposal:** [docs/Roman_Urdu_Script_Spelling_Robustness_Research_Proposal_UPDATED.docx](../docs/Roman_Urdu_Script_Spelling_Robustness_Research_Proposal_UPDATED.docx).
- **Bibliography files:** NOT FOUND. No `.bib`, `.ris`, `.enw`, or other bibliography file was found.
- **Downloaded PDFs:** NOT FOUND. No PDF matching the six paper IDs or titles was found in the repository or Git-tracked files.
- **Canonical verification boxes:** L01, L04, L09, and L25 are marked Opened and Verified in `docs/LITERATURE.md`. L24 has supplied-paper text reviewed but remains not fully bibliographically/archivally verified. L28 remains unresolved and unchecked.

## Full-text accessibility

### Already has a repository-recorded official source page

- **L01:** full text is accessible at `https://arxiv.org/html/2606.07167v1`; the official arXiv, project, code, and [dataset card](https://huggingface.co/datasets/MBZUAI/UrduMMLU) are recorded. The card metadata has been checked for 26,431 MCQs, CC BY 4.0, and `urdummlu.json`; the downloadable archive has not been independently downloaded and inspected.
- **L04:** full text accessible at `https://arxiv.org/html/2512.10780v2`; official arXiv record at `https://arxiv.org/abs/2512.10780`. HTML full text and arXiv metadata have been verified.
- **L09:** full text accessible at `https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/`; publisher DOI at `https://doi.org/10.1016/j.dib.2024.111170`; Mendeley Data v5 landing page at `https://data.mendeley.com/datasets/v5jfhsvtmd/5`. Article full text and dataset metadata have been verified.
- **L24:** The supplied paper text is reviewed, but the DOI, separate code/data archive DOI, Zenodo record, GitHub repository, and venue remain unverified. No paper/archive DOI is treated as the same record.
- **L25:** official ACL Anthology page and PDF have been reviewed. Bibliographic details and full-text findings are verified.

### Official source page not found

- **L28:** no official publication URL or arXiv/OpenReview record is available in the repository. The only recorded platform is OpenReview, but a stable official URL is NOT FOUND.

### Additional unresolved record outside the six-paper inventory scope

- **L13 PURUTT:** repository notes record a prior full-text review, but the DOI and CC BY 4.0 licence are unresolved. The exact DOI lookup recorded in the repository did not resolve 10.1109/ACCESS.2025.3538411, and the later evidence did not reconfirm the licence. Do not cite the DOI or licence as verified until a publisher or other authoritative record is checked.

### Accessible full text present locally

No L24, L25, or L28 PDF is stored locally. L01, L04, L09, and L25 were verified through supplied or official online full text; L24 was reviewed from supplied paper text without independent record verification.

## Need to obtain or inspect

Still unresolved:

1. L24 - independently verify the publication record, Zenodo paper DOI, separate code/data archive DOI, and GitHub repository; confirm venue and peer-review status.
2. L28 - locate a stable official record and full text, then verify all bibliographic and substantive details.
