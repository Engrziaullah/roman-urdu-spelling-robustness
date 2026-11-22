# L04: Script Gap — Full-Text Verification Notes

**Document identifier:** L04  
**Date verified:** 2026-11-21  
**Verifier:** Younas Khan (Role C)  
**Inspection method:** Full HTML paper (`https://arxiv.org/html/2512.10780v2`) and official arXiv metadata inspected. Supplementary data, code repository, and peer-reviewed publication venue were not independently verified.

---

## 1. Bibliographic Details

- **Full Title:** Script Gap: Evaluating LLM Triage on Indian Languages in Native vs Romanized Scripts in a Real World Setting
- **Complete Author List:** Manurag Khullar, Utkarsh Desai, Poorva Malviya, Aman Dalmia, Zheyuan Ryan Shi
- **arXiv Identifier:** arXiv:2512.10780v2
- **Original Submission Date:** 11 December 2025 (v1)
- **Revision Date:** 30 March 2026 (v2)
- **DOI:** 10.48550/arXiv.2512.10780
- **Official URLs:**
  - arXiv abstract page: https://arxiv.org/abs/2512.10780
  - arXiv HTML full text: https://arxiv.org/html/2512.10780v2
- **Publication / Venue Status:** arXiv preprint (v2). A peer-reviewed venue (e.g., EMNLP or similar) was not independently confirmed. Cite strictly as an arXiv preprint.

---

## 2. Dataset, Domain, and Task

- **Domain:** Maternal and newborn healthcare triage in underserved communities.
- **Source Data:** Approximately 133,000 de-identified WhatsApp messages collected from real-world user interactions with health platforms in India.
- **Evaluation Sample:** 3,153 sampled single-turn patient messages.
- **Languages Covered:**
  - Native Indic languages: Hindi, Telugu, Kannada, Marathi, Punjabi, Nepali.
  - Comparison baseline: English.
- **Core Contrast:** Paired evaluation of patient queries submitted in native Indic script versus Romanized (Latin-script transliterated) text.
- **Human Annotation & Validation:** A subset of 200 messages underwent dual human expert cross-validation, achieving 87.5% inter-annotator agreement and Cohen's $\kappa = 0.74$.

---

## 3. Evaluated Models & Experimental Setup

- **Models Evaluated:**
  - Frontier proprietary models: OpenAI GPT-4o, Anthropic Claude Sonnet 4.5.
  - Open-weights frontier models: DeepSeek V3, Meta Llama 4, and Alibaba Qwen family models.
- **Prompting & Evaluation Protocol:**
  - Evaluated on raw messages without synthetic normalization.
  - Fixed prompt template across conditions.
  - Deterministic decoding: temperature = 0.

---

## 4. Key Findings

1. **Systematic Script Degradation:**
   - LLMs perform consistently worse on Romanized Indic inputs compared to native Indic script across all tested languages and models.
   - In several language–model pairings, performance gaps reach up to 24 percentage points.
2. **Benchmark Validation on HealthBench:**
   - In secondary validation on the HealthBench clinical benchmark, Romanized input incurs an average 5.4 percentage-point drop in weighted-F1 score compared to native script.
3. **Cross-Model Consistency:**
   - Full agreement across all tested models drops significantly from 66.5% under native script to 56.8% under Romanized script, demonstrating that romanization induces inter-model disagreement.
4. **Failure Mode Analysis (Comprehension vs. Classification):**
   - *Comprehension failures:* The model fails to ground colloquial transliterated vocabulary, non-standard spelling, or dialectal tokens into medical entities.
   - *Classification failures:* The model successfully identifies patient intent and extracts relevant medical symptoms, yet misassigns the appropriate clinical triage urgency category. Both failure modes contribute substantially to the script gap.
5. **Proposed Mitigations:**
   - *Uncertainty-based selective routing:* Deferring highly uncertain Romanized queries to human clinicians or native-script translation pipelines.
   - *Script-aware prompting:* Conditioning prompts explicitly with transliteration and script-context guidance.

---

## 5. Critical Metric Distinction: Flip Rate vs. AFR

> [!WARNING]
> **Do not conflate L04's "Flip Rate" with our project's Answer Flip Rate (AFR).**

- **L04 "Flip Rate":** Measures whether an LLM's triage classification flips when decoding temperature is varied on the *identical input string* (a measure of decoding sensitivity and sampling noise).
- **Our Answer Flip Rate (AFR):** Measures whether an LLM's selected multiple-choice answer letter flips across *systematically controlled spelling conditions* (NU, RU-P, RU-R, RU-X, and RT) for the *same item* at deterministic temperature 0.
- These are distinct experimental variables: temperature stochasticity on fixed text versus orthographic variation at fixed zero temperature. They must not be cited as equivalent measures.

---

## 6. Limitations & Relevance to This Project

### Limitations
1. **No Urdu evaluation:** Urdu is not included in the dataset or evaluation (Hindi, Telugu, Kannada, Marathi, Punjabi, Nepali only).
2. **Clinical triage, not knowledge MCQs:** The task is classification of patient intent into triage buckets, not multiple-choice question answering testing factual knowledge.
3. **No orthographic variation within Roman script:** The paper tests native script versus a single Romanized input form; it does not evaluate multiple controlled Roman Urdu spelling styles or conventions.

### Project Relevance
- **Motivation for script-gap investigation:** Confirms that Romanized text in South Asian languages causes severe performance drops in modern LLMs (including GPT-4o, Claude Sonnet 4.5, and Llama 4).
- **Mechanistic precedent:** Supports the hypothesis that lack of standardized orthography degrades subword tokenization and downstream reasoning.
- **Clear boundary for our novelty:** Establishes that while script differences (Native vs. Romanized) are known to harm LLM performance, the effect of *systematic within-script spelling variation* (such as RU-P vs. RU-R vs. RU-X) remains unaddressed.

---

## 7. Wording Guidelines for Manuscript

- **Allowed phrasing:**
  - *"Khullar et al. (2025/2026, arXiv:2512.10780) demonstrate that modern LLMs suffer significant performance degradations—up to 24 percentage points—when clinical triage queries in Indic languages are presented in Romanized script rather than native script."*
  - *"While Khullar et al. document a substantial Native-versus-Romanized script gap in clinical triage, their study does not evaluate Urdu, does not test multiple Roman spelling conventions, and evaluates temperature-induced flip rates rather than orthographic flip rates."*
- **Disallowed phrasing:**
  - Do NOT cite L04 as a peer-reviewed publication (cite as an arXiv preprint).
  - Do NOT claim L04 evaluated Urdu or Roman Urdu.
  - Do NOT cite L04's "Flip Rate" as prior work measuring Answer Flip Rate across spelling variants.
