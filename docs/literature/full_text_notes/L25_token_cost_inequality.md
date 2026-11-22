# L25: Token Cost Inequality: Measuring Tokenization Disparities Across Scripts in Roman Urdu and Urdu

**Document identifier:** L25  
**Date reviewed:** 2026-11-22  
**Reviewer:** Younas Khan (Role C)  
**Inspection method:** Full-text PDF independently accessed and reviewed from ACL Anthology.

## 1. Bibliographic Details

- **Title:** Token Cost Inequality: Measuring Tokenization Disparities Across Scripts in Roman Urdu and Urdu
- **Authors:** Waleed Jamil, Saima Rafi, Yanchao Yu
- **Venue:** Proceedings of the Fifth Workshop on Generation, Evaluation and Metrics (GEM)
- **Date:** July 2026
- **Pages:** 563-573
- **DOI:** 10.18653/v1/2026.gem-main.54
- **Official ACL Anthology page:** https://aclanthology.org/2026.gem-main.54/
- **Official PDF:** https://aclanthology.org/2026.gem-main.54.pdf
- **Bibliographic and full-text verification:** Verified.

## 2. Methodology

- 10,000 examples were sampled from each of Roman-Urdu-Parl, OPUS100 English-Urdu, and Dakshina Urdu.
- Tokenizer families: cl100k_base, mT5, and ByT5.
- Measures included Token Cost Inequality (TCI), tokens per word, fixed-budget character retention, cost multipliers, and lightweight normalization.
- Character-retention budgets were 16, 32, 64, 128, and 256 tokens.

## 3. Main Findings

- Tokenization disparities depend strongly on tokenizer design.
- Mean TCI for Roman-Urdu-Parl was 0.473 for cl100k_base, 0.967 for mT5, and 0.669 for ByT5.
- At a 16-token fixed budget, cl100k_base retained 74.1% of Roman Urdu surface content versus 44.9% of Urdu surface content.
- Lightweight normalization produced negligible improvements.
- Token cost alone did not determine retained character coverage.

## 4. Limitations

- Only three tokenizer families were evaluated.
- Fixed-budget character retention measures surface coverage, not semantic preservation.
- The study did not evaluate downstream task performance or generation quality.
- The sample was limited to 10,000 examples per dataset.
- Normalization was lightweight rather than comprehensive.

## 5. Relevance to Our Research

L25 is relevant background for token-cost and fixed-budget interpretation. It does not evaluate LLM answer accuracy, Urdu knowledge MCQs, answer flips, or differences among RU-P, RU-R, and RU-X. It must not be used as direct evidence that controlled spelling variants change model answers.
