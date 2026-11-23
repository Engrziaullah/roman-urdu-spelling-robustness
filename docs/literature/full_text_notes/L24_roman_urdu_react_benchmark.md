# L24: Roman Urdu Input Costs Small Local ReAct Agents — Full-Text Verification Notes

**Document identifier:** L24  
**Date verified:** 2026-11-23
**Verifier:** Younas Khan (Role C)
**Inspection method:** Actual seven-page PDF (`04_RomanUrdu_ReAct.pdf`, 239.6 kB, md5 `3b8c0761f40054db9386b44b506b4465`) inspected. Bibliographic details and principal results cross-checked against public repository README and published results tables. Raw experimental calls (3,838 calls) were not independently rerun.

---

## 1. Bibliographic Details & Metadata Status

- **Full Title:** Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions
- **Authors:** Muzammal Hussain and Maryam Khalid
- **Date:** November 2026 (Published 7 November 2026, Version 1)
- **Publication / Venue Status:** Resource type Preprint (Zenodo), license CC BY 4.0. Not peer-reviewed.
- **Identifiers & Records:**
  - **Preprint record:** "Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions". Authors: Muzammal Hussain and Maryam Khalid. Published 7 November 2026, Version 1, resource type Preprint, license CC BY 4.0. File: `04_RomanUrdu_ReAct.pdf` (239.6 kB, md5 `3b8c0761f40054db9386b44b506b4465`). DOI `10.5281/zenodo.24045043` is the Version 1 DOI (Zenodo's own citation uses this one); DOI `10.5281/zenodo.24045042` is the all-versions DOI. Not peer-reviewed.
  - **Software / data record:** "Roman Urdu ReAct benchmark: clinic questions in English and Roman Urdu for small local agents". Author: Muzammal Hussain. Version v1.0.0, 7 November 2026, MIT license. DOI `10.5281/zenodo.24044983` (version DOI; all-versions DOI `10.5281/zenodo.24044982`). GitHub: https://github.com/MHKhan50/roman-urdu-react-bench (tag v1.0.0).
  - **Relationship:** The two Zenodo records link to each other: the preprint "is supplemented by" the software, and the software "is supplement to" the preprint.
  - **Verification status:** Full text verified from the actual seven-page PDF and repository outputs; raw calls not independently rerun. Preprint; do not describe as peer-reviewed.

---

## 2. Study Design & Methodology

- **Domain & Research Objective:** Fictional physiotherapy-clinic questions for small local ReAct agents. Evaluates how Roman Urdu input affects conversational agents equipped with tool-calling capabilities to answer outpatient queries (scheduling, triage, dosage, patient lookup).
- **Dataset & Scale:**
  - 96 fictional clinical questions constructed from 12 parameterized question templates (4 instances per template, 2 distinct patient name sets).
  - Total of 3,838 scored model/tool-calling interactions (two timeout calls excluded).
- **Input Conditions (Three Paired Forms):**
  1. *English:* Standard medical clinic prompt baseline.
  2. *Common Roman Urdu:* Conventionally transliterated Roman Urdu.
  3. *Chat-Spelling Roman Urdu:* Casual, informal chat-style transliteration with colloquial contractions and variant spellings.
- **Models Evaluated:**
  - Qwen2.5 3B, Qwen2.5 7B, Llama 3.2 3B, and Llama 3.1 8B.
- **Evaluation Methods:**
  - Direct answering, ReAct with an English example, ReAct with a Roman Urdu example, and Translate-then-ReAct.
- **Evaluation Controls:**
  - Deterministic evaluation at temperature 0.
  - Single evaluation pass per model and condition (no repeated-run noise analysis); two timeout calls excluded.
- **Statistical Methods:**
  - Overall task completion accuracy across the 96 questions.
  - Paired percentile bootstrap for accuracy differences across input forms on matched items.

---

## 3. Key Findings & Quantitative Results

1. **Severe Degradation from English to Roman Urdu:**
   - Under the English-example ReAct condition, switching to Common Roman Urdu caused substantial accuracy drops across three of the four evaluated local agents:
     - Qwen2.5 3B: **-34.7** percentage points
     - Llama 3.2 3B: **-31.2** percentage points
     - Llama 3.1 8B: **-21.9** percentage points
   - Qwen2.5 7B showed slight resilience, gaining **+1.0** point.
2. **Further Cost of Chat-Spelling:**
   - For Qwen2.5 3B, Common Roman Urdu achieved **57.9%** accuracy and Chat Spelling achieved **36.5%** accuracy.
   - The paper reports a paired loss of **−22.1 percentage points** based on 95 matched items.
3. **Numerical Clarification on Paired Difference:**
   - The reported **−22.1 percentage-point** difference is a paired comparison on matched items, not a simple marginal subtraction of the displayed marginal percentages (57.9% − 36.5% = 21.4 percentage points). Both numbers are preserved as reported; do not replace the paired result with the marginal subtraction.
   - Published tables and repository outputs were cross-checked, but the 3,838 raw experimental calls were not independently rerun.

---

## 4. Clinician Review & Benchmark Limitations

The paper notes several important limitations and documents a post-hoc clinician audit:
1. **Fictional Clinic Domain:** Physiotherapy clinic domain; 12 templates written by one person.
2. **Model & Run Scope:** Four small models; single sample per question at temperature 0; two timeout calls excluded (3,838 scored calls).
3. **Single Clinician Reviewer:** The clinical audit was conducted by only a single reviewer evaluating 48 items (covering only one of the two name sets; all 48 gold answers were judged medically correct).
4. **Unrealistic Clinical Scenarios:** 16 items (from templates T03–T06) were judged clinically unrealistic in real-world outpatient practice.
5. **Grammatical & Gender Agreement Errors:** 7 Roman Urdu items exhibited Urdu grammatical gender-agreement violations.

---

## 5. Overlap and Fundamental Distinctions with Our Research

### Overlap:
- **Direct Empirical Precedent:** Closest known empirical study evaluating paired Roman Urdu input forms on language models. Reports that informal chat spelling reduced task accuracy in the evaluated small local ReAct agents on fictional physiotherapy-clinic queries.

### Fundamental Methodological & Scientific Distinctions:
| Dimension | Hussain and Khalid (2026, preprint) [L24] | Our Study |
|---|---|---|
| **Task** | Clinic ReAct agent tool calling & multi-step execution | Factual knowledge examination MCQs (UrduMMLU) |
| **Language Conditions** | 3 conditions: English, Common Roman Urdu, Chat Roman Urdu | 5 matched conditions: Native Urdu (`NU`), Standard Roman (`RU-P`), Reduced Roman (`RU-R`), English-orthography Roman (`RU-X`), and Back-transliteration (`RT`) |
| **Native Script Reference** | None (uses English as baseline; no Perso-Arabic Urdu) | `NU` (Nastaliq Perso-Arabic Urdu source) |
| **Bidirectional Transliteration** | None | `RT` (Nastaliq back-transliteration to measure script roundtrip) |
| **Primary Metric** | Overall task accuracy & accuracy drops (macro accuracy) | **Answer Flip Rate (AFR)**: within-item answer choice flips under semantics-preserving spelling variations |
| **Spelling Control** | Heuristic common vs. chat contrast | Rule-governed, deterministic orthographic engine holding words and syntax constant (`docs/RULES.md`) |
| **Baseline Noise Control** | Single run (no repeated-run baseline) | Repeated-run noise subset (3 repeats) to separate spelling flips from temperature/sampling noise |

---

## 6. Refined Research-Gap Wording

> [!IMPORTANT]
> **Do NOT claim that no prior study has evaluated paired Roman Urdu spelling.**
> Hussain and Khalid (2026, preprint) has demonstrated paired spelling sensitivity in local clinic ReAct agents.

- **Allowed, source-qualified gap phrasing for our manuscript:**
  - *"While Hussain and Khalid (2026, preprint) observed that informal chat spelling degraded task accuracy in small clinical ReAct agents across two Roman Urdu renderings (a 22.1 paired percentage-point drop on Qwen2.5 3B), the reviewed literature has not yet established whether item-level answer choices flip across systematic, rule-governed Roman Urdu orthographic conventions on factual multiple-choice benchmarks, nor compared them against native Nastaliq (`NU`) and back-transliterated (`RT`) baselines while controlling for repeated-run noise."*
- **Disallowed gap phrasing:**
  - *"We present the first study of Roman Urdu spelling variation on language models."*
  - *"No previous work has evaluated paired Roman Urdu spelling forms."*
  - *"Hussain and Khalid (2026, preprint) measured answer flip rates across spelling conditions."*

---

## 7. Citation & BibTeX

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

- **Software Citation (Separate):** Software/data DOI `10.5281/zenodo.24044983` (author Muzammal Hussain, v1.0.0, MIT) is recorded separately and must not be cited as the paper DOI.
