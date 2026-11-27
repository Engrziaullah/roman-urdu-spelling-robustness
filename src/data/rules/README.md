# Data rule tables

These files are UTF-8 CSVs with the exact header rows shown below. They contain
headers only until the team approves rule content; do not add spelling entries
without native-reader review.

- `ru_r_wordmap.csv`: `ru_p,ru_r,op_id,note`. Exact whole-word replacements
  from RU-P to RU-R.
- `ru_r_rules.csv` and `ru_x_rules.csv`:
  `order,pattern,replacement,op_id,note`. Rules are applied by ascending integer
  `order`, after the RU-R word map where applicable, and only at whole-word
  boundaries.
- `protected_patterns.csv`: `pattern_id,kind,pattern,note`. `kind` is `regex`
  or `literal`; literal patterns are escaped before matching. Regex uses Python
  `re` syntax with `re.UNICODE`; patterns are applied in file order to each field.
  Rows with `note` beginning `EXAMPLE` are ignored. Matching spans that overlap
  or touch are masked as one protected span before transformation.
- `ru_p_lexicon.csv`: `urdu_word,ru_p,note`. Approved RU-P spellings only.

CSV uses RFC 4180 quoting, with no second escaping layer. Do not put newlines
inside fields. Per-item `protected_tokens` are supplied to engine calls and are
not stored in these files.
