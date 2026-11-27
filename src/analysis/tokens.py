import argparse
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from .bootstrap import bootstrap_mean_ci


TOKEN_METRICS = [
    "n_tokens_question",
    "n_tokens_options",
    "n_tokens_total",
    "n_chars_total",
]


def token_counts(items_path: str | Path, tokenizer_name: str = "xlm-roberta-base") -> pd.DataFrame:
    """Count question and option tokens using an open-tokenizer proxy.

    Closed API models do not expose their tokenizers, so these counts are a
    proxy; this limitation must be stated in the paper.

    Args:
        items_path: JSONL file following the CONTRACTS items format.
        tokenizer_name: Hugging Face tokenizer name or local path.

    Returns:
        One row per item and condition with token and character counts.
    """
    try:
        from transformers import AutoTokenizer
    except ImportError as exc:
        raise ImportError(
            'Token counting requires transformers; run "pip install transformers".'
        ) from exc

    tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)
    items = pd.read_json(items_path, lines=True)
    rows = []
    for _, item in items.iterrows():
        question = item["question"]
        options = item["options"]
        question_tokens = len(tokenizer.encode(question, add_special_tokens=False))
        options_tokens = sum(
            len(tokenizer.encode(option, add_special_tokens=False))
            for option in options
        )
        row = {
            "item_id": item["item_id"],
            "condition": item["condition"],
            "n_tokens_question": question_tokens,
            "n_tokens_options": options_tokens,
            "n_tokens_total": question_tokens + options_tokens,
            "n_chars_total": len(question) + sum(len(option) for option in options),
        }
        if "domain" in item:
            row["domain"] = item["domain"]
        rows.append(row)

    columns = ["item_id", "condition", *TOKEN_METRICS]
    if "domain" in items.columns:
        columns.insert(2, "domain")
    return pd.DataFrame(rows, columns=columns)


def token_summary_table(counts: pd.DataFrame, n_boot: int = 10000, seed: int = 42) -> pd.DataFrame:
    """Summarize token/character counts by condition with domain-stratified CIs."""
    required = {"item_id", "condition", *TOKEN_METRICS}
    missing = required - set(counts.columns)
    if missing:
        raise ValueError(f"Token-count table missing required columns: {sorted(missing)}")
    if counts.duplicated(["item_id", "condition"]).any():
        raise ValueError("Duplicate item/condition rows in token-count table.")
    if counts[TOKEN_METRICS].isna().any().any():
        raise ValueError("Token-count table contains missing metric values.")
    rows = []
    for group_index, (condition, group) in enumerate(
        counts.groupby("condition", sort=True)
    ):
        row = {"condition": condition, "n_items": group["item_id"].nunique()}
        strata = group["domain"].to_numpy() if "domain" in group.columns else None
        for metric_index, metric in enumerate(TOKEN_METRICS):
            values = group[metric].to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean_ci(
                values,
                n_boot=n_boot,
                seed=seed + group_index * len(TOKEN_METRICS) + metric_index,
                strata=strata,
            )
            row[metric + "_mean"] = values.mean()
            row[metric + "_median"] = float(np.median(values))
            row[metric + "_ci_low"] = ci_low
            row[metric + "_ci_high"] = ci_high
        rows.append(row)
    return pd.DataFrame(rows)


def token_comparison_table(
    counts: pd.DataFrame, reference: str = "NU", n_boot: int = 10000, seed: int = 42
) -> pd.DataFrame:
    """Return paired per-item count differences against NU for each condition."""
    required = {"item_id", "condition", *TOKEN_METRICS}
    missing = required - set(counts.columns)
    if missing:
        raise ValueError(f"Token-count table missing required columns: {sorted(missing)}")
    if counts.duplicated(["item_id", "condition"]).any():
        raise ValueError("Duplicate item/condition rows in token-count table.")
    if counts[TOKEN_METRICS].isna().any().any():
        raise ValueError("Token-count table contains missing metric values.")
    wide = counts.pivot(index="item_id", columns="condition", values=TOKEN_METRICS)
    if reference not in wide.columns.get_level_values(1):
        raise ValueError(f"Reference condition {reference} is absent from token counts.")
    domain_map = None
    if "domain" in counts.columns:
        if counts.groupby("item_id", dropna=False)["domain"].nunique(dropna=False).gt(1).any():
            raise ValueError("An item has conflicting domain values in token-count data.")
        domain_map = counts.drop_duplicates("item_id").set_index("item_id")["domain"]
    rows = []
    for condition_index, condition in enumerate(wide.columns.get_level_values(1).unique()):
        if condition == reference:
            continue
        paired = wide.loc[:, pd.IndexSlice[:, [reference, condition]]]
        if paired.isna().any().any():
            raise ValueError(f"Token counts are not paired for {reference} and {condition}.")
        for metric_index, metric in enumerate(TOKEN_METRICS):
            differences = (
                paired[(metric, condition)] - paired[(metric, reference)]
            ).to_numpy(dtype=float)
            ci_low, ci_high = bootstrap_mean_ci(
                differences,
                n_boot=n_boot,
                seed=seed + condition_index * len(TOKEN_METRICS) + metric_index,
                strata=domain_map.loc[wide.index].to_numpy() if domain_map is not None else None,
            )
            rows.append({
                "condition": condition,
                "reference": reference,
                "metric": metric,
                "n_items": len(differences),
                "mean_difference": differences.mean(),
                "ci_low": ci_low,
                "ci_high": ci_high,
            })
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Count question and option tokens in an items JSONL file.")
    parser.add_argument("--items", required=True, help="Path to items JSONL file.")
    parser.add_argument("--out", help="Output directory (defaults to a temporary directory).")
    parser.add_argument("--tokenizer", default="xlm-roberta-base", help="Open tokenizer name or local path.")
    args = parser.parse_args(argv)

    output_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="roman-urdu-token-counts-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "token_counts.csv"
    counts = token_counts(args.items, tokenizer_name=args.tokenizer)
    counts.to_csv(output_path, index=False)
    token_summary_table(counts).to_csv(output_dir / "token_summary.csv", index=False)
    token_comparison_table(counts).to_csv(output_dir / "token_comparisons.csv", index=False)
    print(f"Wrote token counts to {output_path}")


if __name__ == "__main__":
    main()
