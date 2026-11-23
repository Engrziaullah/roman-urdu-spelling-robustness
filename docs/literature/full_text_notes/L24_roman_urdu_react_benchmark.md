# L24: Roman Urdu Input Costs Small Local ReAct Agents — Full-Text Verification Notes

**Document identifier:** L24  
**Date reviewed:** 2026-11-21  
**Reviewer:** Younas Khan (Role C)  
**Inspection method:** The researcher-supplied paper text was reviewed, and bibliographic metadata was checked against the Zenodo records on 2026-11-22. The supplied text still has to be compared with the Zenodo PDF 04_RomanUrdu_ReAct.pdf (md5 3b8c0761f40054db9386b44b506b4465).

---

## 1. Bibliographic Details & Metadata Status

- **Full Title:** Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions
- **Authors:** Muzammal Hussain and Maryam Khalid
- **Date:** Published 7 November 2026, Version 1
- **Publication / Venue Status:** Resource type Preprint (Zenodo), license CC BY 4.0. Not peer-reviewed.
- **Identifiers & Zenodo Records (checked on 2026-11-22):**
  - **Preprint record:** "Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions". Authors: Muzammal Hussain and Maryam Khalid. Published 7 November 2026, Version 1, resource type Preprint, license CC BY 4.0. File: `04_RomanUrdu_ReAct.pdf` (239.6 kB, md5 `3b8c0761f40054db9386b44b506b4465`). DOI `10.5281/zenodo.24045042` is the all-versions DOI; DOI `10.5281/zenodo.24045043` is the Version 1 DOI (Zenodo's own citation uses this one). Not peer-reviewed.
  - **Software record:** "Roman Urdu ReAct benchmark: clinic questions in English and Roman Urdu for small local agents". Author: Muzammal Hussain. Version v1.0.0, 7 November 2026, MIT license. DOI `10.5281/zenodo.24044983` (version DOI; all-versions DOI `10.5281/zenodo.24044982`). GitHub: https://github.com/MHKhan50/roman-urdu-react-bench (tag v1.0.0).
  - **Relationship:** The two Zenodo records are different records and link to each other: the preprint "is supplemented by" the software, and the software "is supplement to" the preprint.
  - **Remaining open items for L24:**
    (a) compare the supplied text with the Zenodo PDF `04_RomanUrdu_ReAct.pdf` (md5 `3b8c0761f40054db9386b44b506b4465`),
    (b) the GitHub repository has not been opened,
    (c) the 22.1-point versus 21.4-point difference still needs source-data checking.

---

## 2. Study Design & Methodology

- **Domain & Task:** Clinical ReAct agent workflows. Small language models operating as conversational agents equipped with tool-calling capabilities to answer patient clinic queries (scheduling, triage, dosage, patient lookup).
- **Scale:**
  - 96 fictional clinical questions constructed from 12 parameterized question templates. Study content comes from the researcher-supplied text, and still has to be compared with the Zenodo PDF `04_RomanUrdu_ReAct.pdf` (md5 `3b8c0761f40054db9386b44b506b4465`).
  - Total of 3,838 scored model/tool-calling interactions.
- **Input Conditions (Three Paired Forms):**
  1. *English:* Standard medical clinic prompt baseline.
  2. *Common Roman Urdu:* Conventionally transliterated Roman Urdu.
  3. *Chat-Spelling Roman Urdu:* Casual, informal chat-style transliteration with colloquial contractions and variant spellings.
- **Models Evaluated:**
  - Four small, locally deployable models evaluated using ReAct and other reported evaluation conditions.
- **Evaluation Controls:**
  - Deterministic evaluation at temperature 0.
  - Single evaluation run per model and condition (no repeat-run stochasticity analysis).
- **Statistical Methods:**
  - Overall task completion accuracy across the 96 questions.
  - Paired percentile bootstrap for accuracy differences across input forms.

---

## 3. Key Findings & Quantitative Results

1. **Severe Degradation from English to Roman Urdu:**
   - Under the English-example ReAct condition, switching to Common Roman Urdu caused substantial accuracy drops across three of the four evaluated local agents:
     - Model 1: **-34.7** percentage points
     - Model 2: **-31.2** percentage points
     - Model 3: **-21.9** percentage points
   - One model showed anomalous resilience, gaining **+1.0** point.
2. **Further Cost of Chat-Spelling:**
   - Chat-spelling Roman Urdu imposed an additional performance penalty beyond common Roman Urdu on sensitive models.
3. **Data Discrepancy Flag:**
   - *Reported vs. Calculated Difference:* The supplied text reports that chat spelling costs Qwen2.5 3B a further **22.1 percentage points**. However, the common-Roman-Urdu table comparison shows **57.9% versus 36.5%**, a **21.4 percentage-point** difference. This discrepancy is preserved and remains unresolved; do not silently reconcile it.

---

## 4. Clinician Review & Benchmark Limitations

The paper includes a post-hoc clinician audit of the benchmark questions, which revealed several critical limitations:
1. **Single Clinical Reviewer:** The clinical audit was conducted by only a single reviewer.
2. **Synthetic Patient Name Bias:** Exactly 48 of the 96 items (50%) were derived from only a single synthetic patient name set, limiting demographic and linguistic diversity.
3. **Unrealistic Clinical Scenarios:** 16 questions were flagged by the clinician as clinically unrealistic or implausible in real-world outpatient practice.
4. **Grammatical & Gender Agreement Errors:** 7 items contained Urdu grammatical gender-agreement violations in their Roman Urdu rendering.
5. **Single-Run Constraint:** All results derive from a single evaluation pass at temperature 0, precluding measurement of decoding stochasticity or baseline execution noise.

---

## 5. Overlap and Fundamental Distinctions with Our Research

### Overlap:
- **Potential Direct Empirical Precedent:** The supplied L24 text is the closest known prior work in repository review investigating paired Roman Urdu spelling variations and reports accuracy differences across input forms. Bibliographic metadata was checked against Zenodo records on 2026-11-22 (not peer-reviewed); comparison with the Zenodo PDF, GitHub inspection, and source-data checking for the 22.1 vs 21.4 pp discrepancy remain open.

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
  - *"While Hussain and Khalid (2026, preprint) observed that informal chat spelling degraded task accuracy in small clinical ReAct agents across two Roman Urdu renderings, no prior work has isolated within-item answer flip rates across systematic, rule-governed Roman Urdu orthographic conventions on factual multiple-choice benchmarks, nor compared them against native Nastaliq (`NU`) and back-transliterated (`RT`) baselines while controlling for repeated-run noise."*
- **Disallowed gap phrasing:**
  - *"We present the first study of Roman Urdu spelling variation on language models."*
  - *"No previous work has evaluated paired Roman Urdu spelling forms."*
  - *"Hussain and Khalid (2026, preprint) measured answer flip rates across spelling conditions."*
