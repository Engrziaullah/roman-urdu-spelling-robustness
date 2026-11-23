# L24: Roman Urdu Input Costs Small Local ReAct Agents — Full-Text Verification Notes

**Document identifier:** L24  
**Date reviewed:** 2026-11-21  
**Reviewer:** Younas Khan (Role C)  
**Inspection method:** The researcher supplied and the paper text was reviewed. Independent DOI, Zenodo archive, GitHub repository, and publication venue verification remain unresolved.

---

## 1. Bibliographic Details & Metadata Status

- **Full Title:** Roman Urdu Input Costs Small Local ReAct Agents up to 35 Accuracy Points: A Paired Benchmark on Clinic Questions
- **Author:** M. Hussain (single author)
- **Date:** November 2026 (7 November 2026)
- **Publication / Venue Status:** Self-archived preprint / unrefereed technical report. No peer-reviewed venue or conference publication is confirmed.
- **Identifiers & DOI Flags:**
  - Paper DOI recorded in the supplied text: `10.5281/zenodo.24045042`
  - A separate code/data archive DOI is mentioned; it must not be conflated with the paper DOI.
  - The alternate DOI `10.5281/zenodo.24044983` appears in existing repository records, but its exact role and relationship are unresolved.
  - Neither the Zenodo records nor the GitHub repository/archive has been independently verified.
  - Publication venue and peer-review status remain unverified; do not describe the paper as peer-reviewed.

---

## 2. Study Design & Methodology

- **Domain & Task:** Clinical ReAct agent workflows. Small language models operating as conversational agents equipped with tool-calling capabilities to answer patient clinic queries (scheduling, triage, dosage, patient lookup).
- **Scale:**
  - 96 fictional clinical questions constructed from 12 parameterized question templates.
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
- **Potential Direct Empirical Precedent:** The supplied L24 text is the closest known prior work in repository review investigating paired Roman Urdu spelling variations and reports accuracy differences across input forms. This is not an independent bibliographic or peer-review verification.

### Fundamental Methodological & Scientific Distinctions:
| Dimension | Hussain (2026) [L24] | Our Study |
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
> Hussain (2026) has demonstrated paired spelling sensitivity in local clinic ReAct agents.

- **Allowed, source-qualified gap phrasing for our manuscript:**
  - *"While Hussain (2026) observed that informal chat spelling degraded task accuracy in small clinical ReAct agents across two Roman Urdu renderings, no prior work has isolated within-item answer flip rates across systematic, rule-governed Roman Urdu orthographic conventions on factual multiple-choice benchmarks, nor compared them against native Nastaliq (`NU`) and back-transliterated (`RT`) baselines while controlling for repeated-run noise."*
- **Disallowed gap phrasing:**
  - *"We present the first study of Roman Urdu spelling variation on language models."*
  - *"No previous work has evaluated paired Roman Urdu spelling forms."*
  - *"Hussain (2026) measured answer flip rates across spelling conditions."*
