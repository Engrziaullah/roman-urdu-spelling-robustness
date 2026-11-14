# Roman Urdu Spelling Robustness

Do LLM answers change when only the Roman Urdu spelling changes?
This project tests LLMs on Urdu exam-style knowledge MCQs written in
Nastaliq script and in several controlled Roman Urdu spelling variants.

## Research question
1. How often does a model's answer change across spelling variants
   (RU-P, RU-R, RU-X) of the same item? (primary)
2. How large is the Nastaliq vs Roman Urdu accuracy gap?
3. How much of the effect comes from the conversion itself (round-trip RT)?
4. Which items break, and does token length matter?

## Conditions
| Code | Meaning |
|------|---------|
| NU   | Original Nastaliq (UrduMMLU) |
| RU-P | Maximal phonetic Roman Urdu |
| RU-R | Reduced Roman Urdu (vowel elision) |
| RU-X | English-orthography Roman Urdu |
| RT   | Round-trip: RU-P transliterated back to Nastaliq |

## Data
- Source: UrduMMLU (Tabassum et al., EMNLP 2026), Hugging Face `MBZUAI/UrduMMLU`, CC BY 4.0.
- 500 items sampled (seed 42, first 200 = core set).

## Team
- Zia Ullah: data lead
- Sudais Khan: evaluation engineer
- Younas Khan: analysis and writing

## Repo structure
- `data/` sampled items and frozen variants
- `src/` sampling, variant generation, evaluation, analysis
- `notebooks/` Colab notebooks
- `results/` raw model outputs (logs)
- `paper/` draft

## Reproducibility
- Seed: 42
- Models, versions, run dates: see `results/RUN_LOG.md`
- API keys are never stored in this repo (use Colab Secrets).

## Status
Work in progress. Data freeze: [date].
