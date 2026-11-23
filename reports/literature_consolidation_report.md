# Literature Consolidation Report

## Scope and repository status

This audit consolidated the existing literature work without creating a second literature database or replacing prior notes. The canonical literature table, claims register, verification checklist, and prior verification notes are in [docs/LITERATURE.md](../docs/LITERATURE.md). The detailed, incremental search history is preserved in [docs/literature_search_notes.md](../docs/literature_search_notes.md).

Detailed L24 and L25 full-text notes now exist under `docs/literature/full_text_notes/`. No literature CSV, BibTeX file, or downloaded paper PDFs are required or assumed. The proposal DOCX is present, but its informal novelty percentage is not evidence and is not included in the synthesis. Repeated search-log snapshots have different counts and screening progress; they remain intact rather than being reconciled by guessing which is authoritative.

## Materials discovered and consolidated

- Existing literature table: L01-L37, with priority, preliminary notes, reader, and verification checkboxes.
- Existing claims register, search log, verification checklist, nine paper-specific verification notes, and corrections log in `docs/LITERATURE.md`.
- Additional dated search snapshots in `docs/literature_search_notes.md`.
- The existing proposal and project methodology documents provide context, but do not replace paper-level verification.
- Consolidation was added as a thematic synthesis at the end of `docs/LITERATURE.md`; the historical search notes and existing table were not rewritten.

## Literature reviewed and verification status

### Repository-recorded full-text checks

The literature file records full-text checks for L02, L03, L05, L07, L10, L13, L16, L19, and L22. These are repository records from prior work, not nine fresh full-text reviews in this consolidation. Their stated findings and limits are summarized in the existing verification notes. L13 is a special case: its prior checked status conflicts with a later note that the DOI and CC BY 4.0 license could not be reconfirmed. Do not rely on its license until checked again at the publisher.

### Official-source checks made during this consolidation

These are limited checks and do not change any literature-table checkbox:

| Entry | Source check | What remains unchecked |
|---|---|---|
| L01 UrduMMLU | Full text and official Hugging Face dataset card metadata verified; 26,431 MCQs, `urdummlu.json`, and CC BY 4.0 confirmed | The downloadable dataset archive has not been independently downloaded and inspected |
| L04 Script Gap | Full text verified from official [arXiv record](https://arxiv.org/abs/2512.10780) and HTML full text (v2): title, authors, version history, dataset, methodology, and findings confirmed | Peer-reviewed venue not confirmed (preprint only); code/supplementary data not independently verified |
| L09 Soomro et al. | Full text verified from PMC (PMC11683287) and [publisher DOI](https://doi.org/10.1016/j.dib.2024.111170); Mendeley Data v5 (DOI 10.17632/v5jfhsvtmd.5) landing page inspected | Raw downloadable Mendeley dataset files have not been independently parsed |
| L25 Token Cost Inequality | Official [ACL Anthology record](https://aclanthology.org/2026.gem-main.54/) and PDF independently reviewed; title, authors, venue, pages, DOI, methodology, findings, and limitations verified | None for bibliographic or full-text verification |
| L13 PURUTT | Exact DOI lookup did not resolve at Crossref; title query was rate-limited | Publisher identity, DOI, paper details, and license conflict |
| L28 Facts Follow the Spelling | No reliable official record or full text was located | Official record, authors, venue/review status, full text, methodology, and findings |

L25 was newly marked full-text and bibliographically verified. For L24 (Hussain and Khalid, 2026, preprint), bibliographic metadata was checked against Zenodo records on 2026-11-22 (Preprint DOI 10.5281/zenodo.24045043 / all-versions 10.5281/zenodo.24045042, CC BY 4.0, not peer-reviewed; software record DOI 10.5281/zenodo.24044983, MIT). Study content was reviewed from supplied paper text; comparison with the Zenodo PDF, GitHub inspection, and source-data checking for the 22.1 vs 21.4 pp discrepancy remain open. L28 remains unresolved. The official arXiv and Anthology pages are useful sources but do not substitute for full-text checks where full text is required.

### Duplicate and conflicting records to review

- The search notes say L05 appeared as both a journal and arXiv result. Confirm that these are versions of the same work and use one canonical citation, retaining the preprint identifier only as a locator if appropriate.
- The corrections log records earlier incorrect arXiv IDs for L07, L16, and L22. Reconfirm the current IDs against each source; L16 also has a version-title change, and L22’s peer-reviewed venue claim still needs confirmation.
- L13’s claimed DOI, publisher record, and CC BY 4.0 status remain in conflict. Resolve before using its citation or license claim.
- L28 has no reliable official author or bibliographic record. Do not infer a name, venue, DOI, or findings until a stable official source is located.

## Thematic synthesis

1. **Urdu NLP and benchmarks.** UrduMMLU (L01) supplies the project’s native-Urdu exam-style MCQ context and has been verified from full text. Its official Hugging Face card records 26,431 MCQs, CC BY 4.0, and `urdummlu.json`; the downloadable archive has not been independently downloaded and inspected. Belebele (L02) is repository-recorded as verified and offers Urdu reading-comprehension items in native and one Latin-script form. U-MIRAGE (L03) and the Urdu idiom study (L05) provide distinct Urdu/Roman Urdu task comparisons; neither establishes controlled spelling effects on knowledge MCQs.
2. **Roman Urdu datasets and linguistic resources.** Soomro et al. (L09) is a verified full-text source on attested Roman Urdu spelling variation; only its raw downloadable Mendeley dataset files remain unparsed and uninspected. PURUTT (L13) is repository-recorded as a parallel corpus, but its DOI and licence conflict remains unresolved. These resources may inform linguistic context, not answer stability in the project’s task.
3. **Native-script versus Romanized evaluation.** L02, L03, and L04 compare script forms in reading comprehension, medical QA, and health triage, respectively. Their tasks and single or limited script renderings differ from testing multiple controlled Roman Urdu conventions on the same knowledge item.
4. **Spelling variation and normalization.** L09 is relevant to natural Roman Urdu variants; repository notes for RUAB (L10) record that transliterated spellings were normalized before its safety evaluation. This supports a narrowly stated contrast, not a broad claim that prior work uniformly normalizes spelling. Hussain and Khalid (2026, preprint) [L24] supplies a close clinic ReAct spelling benchmark in the researcher-supplied text; bibliographic metadata was checked against Zenodo records on 2026-11-22 (not peer-reviewed), while comparison with the Zenodo PDF, GitHub repo inspection, and source-data check for the 22.1 vs 21.4 pp discrepancy remain open.
5. **Tokenization and multilingual behavior.** L07 and L19 are repository-recorded research on tokenization/character perturbations. L25 has now been full-text reviewed and bibliographically verified: it evaluates fixed-budget token cost and surface coverage for cl100k_base, mT5, and ByT5 across Roman Urdu and Urdu. It does not evaluate MCQ answer accuracy or controlled RU-P/RU-R/RU-X spelling conditions.
6. **Factual consistency and answer stability.** L22 concerns cross-script knowledge transfer. L29 is an unverified candidate on MCQ consistency. The verified set documented here does not establish prior measurement of per-item answer flips across controlled Roman Urdu spelling styles on knowledge MCQs.
7. **Research gap and motivation.** Existing search records say their screened queries had not found a direct match. That is provisional and bounded by the recorded queries, dates, and screening—not proof that no such study exists. L24, L28, and other unverified candidates must be checked before finalizing the gap.

## Provisional gap and contribution

A careful provisional gap is: *the reviewed and recorded searches have not yet established a study that varies rule-defined, meaning-preserving Roman Urdu spelling conventions on Urdu knowledge multiple-choice questions and measures per-item answer flips against native Urdu and back-transliterated baselines with repeated-run variability distinguished*. This statement must be narrowed or revised if verification of L24, L28, or further searches finds closer work.

The project conditions create a structured comparison: NU is the native-script reference; RU-P, RU-R, and RU-X compare the project’s defined Roman Urdu spelling conventions while preserving content and register; RT is the back-transliterated Nastaliq condition. Together, they are designed to separate script and within-Roman-Urdu spelling contrasts. This is a description of the experiment, not evidence that the conditions produce any particular result.

The project can estimate condition-associated answer stability on its sampled items and evaluated models after data, outputs, and annotations are validated. It cannot infer universal model behavior, establish causality beyond the controlled protocol, claim novelty from incomplete searches, or report empirical effects before real outputs are available.

## Still incomplete

- For L24 (Hussain and Khalid, 2026, preprint): (a) compare the supplied text with the Zenodo PDF (04_RomanUrdu_ReAct.pdf, md5 3b8c0761f40054db9386b44b506b4465), (b) the GitHub repository has not been opened, (c) the 22.1-point versus 21.4-point difference still needs source-data checking.
- Recheck L13’s publisher record, DOI, and license; do not rely on its conflicting license notes until resolved.
- Locate and inspect an official record and full text for L28; all its bibliographic and substantive fields remain unknown.
- Independently download and inspect the UrduMMLU archive if archive-content verification is required; the card metadata alone is not archive inspection.
- Continue the existing Day 4 searches, preserve exact queries and screening counts, and investigate duplicate/conflicting records rather than silently merging them.
- Create a bibliography only for papers that meet the repository’s full verification standard; no BibTeX file was created in this consolidation.

## Files changed in this consolidation

- Modified [docs/LITERATURE.md](../docs/LITERATURE.md): appended the provisional thematic synthesis and source-check notes. Existing uncommitted edits were preserved; no verification checkboxes were changed.
- Updated [reports/literature_consolidation_report.md](./literature_consolidation_report.md), the priority inventory, the literature table and L24 notes, and created the L25 full-text note.

No datasets, model configurations, evaluation code, annotation assignments, or prior search logs were changed.
