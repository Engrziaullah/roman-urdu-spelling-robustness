# L09: Roman Urdu Spelling Variations and Sentiment Dataset — Full-Text Verification Notes

**Document identifier:** L09  
**Date verified:** 2026-11-21  
**Verifier:** Younas Khan (Role C)  
**Inspection method:** Full text inspected via PubMed Central open-access article (`https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/`). Mendeley dataset landing page (`https://data.mendeley.com/datasets/v5jfhsvtmd/5`) inspected for metadata, versioning, and license; individual downloadable dataset files have not been independently parsed.

---

## 1. Bibliographic Details

- **Full Title:** A Dataset of Roman Urdu Text with Spelling Variations for Sentence Level Sentiment Analysis
- **Complete Author List:** Mudasar Ahmed Soomro, Rafia Naz Memon, Asghar Ali Chandio, Mehwish Leghari, Muhammad Hanif Soomro
- **Journal:** *Data in Brief*, Volume 57, Article 111170
- **Publication Date:** 23 November 2024 (online open access)
- **DOI:** [10.1016/j.dib.2024.111170](https://doi.org/10.1016/j.dib.2024.111170)
- **Full-Text URL:** https://pmc.ncbi.nlm.nih.gov/articles/PMC11683287/
- **Article License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Publication / Venue Status:** Peer-reviewed data article in *Data in Brief* (Elsevier).

---

## 2. Dataset Overview and Composition

The paper presents two interrelated dataset components:

### Dataset 1: Roman Urdu Word Spelling Variations Lexicon
- **Scale:** 5,244 unique Roman Urdu headwords; 19,527 total spelling forms.
- **Variant Coverage:** Up to five spelling variants per word.
- **Schema:** Contains columns for:
  - `Common`: The standardized/representative spelling selected strictly based on empirical frequency in the corpus.
  - `Var-1` through `Var-5`: Observed alternative spelling variants.
  - `English`: English translation/meaning of the Roman Urdu word.
- **Construction:** Extracted from an initial corpus of 20,232 Roman Urdu reviews through word tokenization, noise removal, and manual linguistic validation.

### Dataset 2: Sentence-Level Sentiment Reviews
- **Scale:** 28,090 annotated Roman Urdu reviews.
- **Sentiment Classes (5 categories):** *Very Positive*, *Positive*, *Neutral*, *Negative*, *Very Negative*.
- **Collection Method:** Sourced using ParseHub automated scraping and manual collection from internet platforms.
- **Inclusion Criteria:**
  - Minimum 75% Roman Urdu content.
  - Minimum review length of 100 words.
  - At least two Roman Urdu words per sentence.
- **Human Annotation Protocol:** A subset of 831 reviews was independently annotated by three out of five annotators, with final class labels assigned via majority voting.

---

## 3. Experimental Baselines and Performance

- **Word Spelling Classification:**
  - Support Vector Machine (SVM) model trained to map spelling variants to their canonical root.
  - Evaluated on an 80/20 train/test split.
  - Reported accuracy: **99%**.
- **Sentence-Level Sentiment Classification:**
  - Recurrent Convolutional Neural Network (RCNN) architecture trained on the 5-class sentiment dataset.
  - Reported classification accuracy: **93%**.

---

## 4. Internal Document Discrepancies

The following two internal reporting discrepancies are identified in the published article and must be recorded explicitly without silent resolution:

1. **Single-Spelling Word Count Discrepancy:**
   - In Section 2 (Dataset Description narrative), the authors state that **41** words had only one recorded spelling.
   - In Table 1 (Summary of Spelling Variation Distribution), the table explicitly records **42** words with one spelling.
2. **Data Source Count Discrepancy:**
   - The article narrative states that reviews were scraped from **seven** internet-based sources.
   - However, the text explicitly enumerates **eight** distinct website/platform names.

---

## 5. Dataset Repository and Availability

- **Repository:** Mendeley Data
- **Dataset Title:** A Dataset of Roman Urdu Text with Spelling Variations for Sentence Level Sentiment Analysis
- **Version:** Version 5
- **Dataset Publication Date:** 7 October 2024
- **Dataset DOI:** [10.17632/v5jfhsvtmd.5](https://doi.org/10.17632/v5jfhsvtmd.5)
- **Dataset URL:** https://data.mendeley.com/datasets/v5jfhsvtmd/5
- **Dataset License:** Creative Commons Attribution 4.0 International (CC BY 4.0)
- **Verification Note:** The Mendeley Data landing page, DOI redirect, metadata, and license have been verified. The individual raw downloadable data files have not yet been independently parsed or ingested into this repository.

---

## 6. Critical Research Relevance to This Project

- **Linguistic Precedent for Natural Variation:**
  - L09 proves that naturally occurring Roman Urdu exhibits pervasive orthographic instability (up to 5 variants per word across nearly 20,000 forms).
  - This supports the linguistic justification in `docs/RULES.md` for our deterministic spelling operations (e.g., vowel deletion and consonant substitutions in `RU-R` and `RU-X`).
- **Fundamental Methodological Distinction:**
  - *L09 Approach:* Normalization / deduplication approach. Naturally occurring variants are identified to *collapse* them back into a single most-frequent "common" spelling to train sentiment classifiers.
  - *Our Approach:* Robustness / instability measurement. We hold question semantics and register constant and systematically manipulate orthographic conventions (`NU`, `RU-P`, `RU-R`, `RU-X`, and `RT`) to evaluate LLM sensitivity.
  - L09 does **not** evaluate LLMs (evaluates traditional ML/DL: SVM and RCNN).
  - L09 does **not** test question answering or examination MCQs.
  - L09 does **not** measure answer flips across spelling variants (our Answer Flip Rate).

---

## 7. Wording Guidelines for Manuscript

- **Allowed phrasing:**
  - *"Soomro et al. (2024) document 19,527 naturally occurring spelling forms across 5,244 Roman Urdu words, demonstrating the empirical breadth of unstandardized orthography in real-world user text."*
  - *"While prior resources like Soomro et al. (2024) develop lexicons to normalize Roman Urdu spelling variation away for sentiment classification, our study tests the inverse: whether preserving semantics while systematically manipulating spelling conventions induces answer flips in frontier LLMs."*
- **Disallowed phrasing:**
  - Do NOT cite Soomro et al. as an LLM robustness benchmark.
  - Do NOT claim Soomro et al. measured Answer Flip Rate or evaluated multiple-choice questions.
  - Do NOT assert that Soomro et al. evaluated cross-script conditions like Nastaliq (`NU`) or back-transliteration (`RT`).
