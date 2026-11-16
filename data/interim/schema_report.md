# UrduMMLU Schema Inspection Report

- Local source: `data\raw\urdummlu.json`
- Local record count: **26,431**
- Hugging Face dataset: `MBZUAI/UrduMMLU`
- Dataset revision/commit: `aae060a8564c261393de206c94a4557c850e7f2f`
- Available splits and sizes: NOT VERIFIED (Hugging Face dataset-server API unavailable)
  - Detail: `URLError: <urlopen error [Errno 11002] getaddrinfo failed>`
- Local data loading method: FALLBACK: read existing local JSON because datasets.load_dataset failed: ImportError: DLL load failed while importing _compute: An Application Control policy has blocked this file.

## Columns, JSON-level types, and examples

### `correct_key`
- Observed types: `string` (26,431)
- Examples:
  - `"B"`
  - `"C"`
  - `"D"`

### `domain`
- Observed types: `string` (26,431)
- Examples:
  - `"STEM"`
  - `"Social Sciences"`
  - `"Humanities"`

### `id`
- Observed types: `int` (26,431)
- Examples:
  - `0`
  - `1`
  - `2`

### `length_tier`
- Observed types: `null` (13,672), `string` (12,759)
- Examples:
  - `"long"`
  - `"short"`
  - `null`

### `level`
- Observed types: `string` (26,431)
- Examples:
  - `"SSC-II"`
  - `"SSC-I"`
  - `"HSSC-I"`

### `options`
- Observed types: `object` (26,431)
- Examples:
  - `{"A": "کوویلنٹ بانڈ", "B": "کوآرڈینیٹ کوویلنٹ بانڈ", "C": "میٹلک بانڈ", "D": "آئیونک بانڈ"}`
  - `{"A": "C10H20", "B": "C2H2", "C": "CH4", "D": "C2H4"}`
  - `{"A": "ان بُجھا چونا", "B": "چونے کا پانی", "C": "سوڈا لائم", "D": "سوڈیم زیولائٹ"}`

### `question`
- Observed types: `string` (26,431)
- Examples:
  - `"لیوس ایسڈ۔ بیس ری ایکشن کی پروڈکٹ اڈکٹ میں کون سا بانڈ ہوتا ہے؟"`
  - `"ان ہائیڈرو کاربن مالیکیولز میں سے کون سا برومین کے ایکوس سلوشن پر کوئی اثر نہیں کرے گا؟"`
  - `"پرمانینٹ ہارڈنیس کو ____ سے ختم کیا جاسکتا ہے۔"`

### `source`
- Observed types: `list[object]` (26,431)
- Examples:
  - `[{"name": "BISE Multan 2025", "url": "https://www.bisemultan.edu.pk"}]`
  - `[{"name": "BISE Multan 2025", "url": "https://www.bisemultan.edu.pk"}, {"name": "Ustad 360", "url": "https://www.ustad360.com"}]`
  - `[{"name": "FBISE", "url": "https://www.fbise.edu.pk"}]`

### `subdomain`
- Observed types: `string` (26,431)
- Examples:
  - `"chemistry"`
  - `"biology"`
  - `"general science"`

## Answer representation
- `correct_key` JSON types: {'string': 26431}
- Observed answer values: {'B': 6486, 'C': 6549, 'D': 6681, 'A': 6673, 'E': 42}
- Interpretation: determine from the values above whether answers are option letters, indices, or text.

## Number of options per item

| Option count | Items |
|---:|---:|
| 4 | 26,272 |
| 5 | 159 |

## Domain and subject representation

- Unique domains (5): `Humanities, Other, Profession, STEM, Social Sciences`
- Exactly five domains? **Yes**
- Unique subjects/subdomains (26): 26

| Domain | Items |
|---|---:|
| Humanities | 11,010 |
| Other | 1,365 |
| Profession | 975 |
| STEM | 5,113 |
| Social Sciences | 7,968 |

| Subdomain | Items |
|---|---:|
| biology | 931 |
| chemistry | 936 |
| civics | 675 |
| commerce | 423 |
| computer science | 823 |
| current and international affairs | 437 |
| economics | 907 |
| education | 836 |
| ethics | 228 |
| fine arts | 148 |
| general knowledge | 1,365 |
| general science | 926 |
| geography | 630 |
| health and physical education | 742 |
| islamic studies | 1,497 |
| mathematics | 876 |
| pakistan studies | 1,895 |
| physics | 621 |
| professional development | 514 |
| professional studies | 461 |
| psychology | 460 |
| psychometrics | 185 |
| sociology | 778 |
| urdu grammar | 756 |
| urdu language | 2,522 |
| urdu literature | 5,859 |

## Duplicate and empty-item checks
- Duplicate IDs: **0**
- Duplicate question strings (trimmed exact match): **0**
- Empty/whitespace-only questions: **0**
- Empty/missing key-field counts: `{}`

## Dataset-card license text

Dataset-card metadata license identifier: `cc-by-4.0`

Relevant dataset-card lines:
- `license: cc-by-4.0`
- `## License`
- `Released under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).`

## Proposed source mapping (text only; not applied to CONTRACTS.md)

| Project field | Candidate UrduMMLU field | Notes |
|---|---|---|
| `source_row` | `id` | Preserve source identifier as a string in output if required by the contract. |
| `domain` | `domain` | Confirm values and five-domain count above. |
| `subject` | `subdomain` | Source calls this `subdomain`. |
| `question` | `question` | Original Urdu question stem. |
| `options` | `options` | Preserve option order; source may use keyed object A–E. |
| `gold` | `correct_key` | Convert only if required; verify answer key exists in the options keys. |

## Important compatibility notes
- The contract example shows four options A–D, but the source inspection may show four and five-option items. Do not force all records to four options.
- If any record has option key `E`, the team must agree how the contract's A–D wording is handled before sampling.
- This report describes the local JSON. Hub revision, split and license are marked unverified if the online metadata requests fail.
- No source records were edited.
