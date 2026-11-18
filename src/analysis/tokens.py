import argparse
import tempfile
from pathlib import Path

import pandas as pd


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
        rows.append({
            "item_id": item["item_id"],
            "condition": item["condition"],
            "n_tokens_question": question_tokens,
            "n_tokens_options": options_tokens,
            "n_tokens_total": question_tokens + options_tokens,
            "n_chars_total": len(question) + sum(len(option) for option in options),
        })

    return pd.DataFrame(
        rows,
        columns=[
            "item_id",
            "condition",
            "n_tokens_question",
            "n_tokens_options",
            "n_tokens_total",
            "n_chars_total",
        ],
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Count question and option tokens in an items JSONL file.")
    parser.add_argument("--items", required=True, help="Path to items JSONL file.")
    parser.add_argument("--out", help="Output directory (defaults to a temporary directory).")
    parser.add_argument("--tokenizer", default="xlm-roberta-base", help="Open tokenizer name or local path.")
    args = parser.parse_args(argv)

    output_dir = Path(args.out) if args.out else Path(tempfile.mkdtemp(prefix="roman-urdu-token-counts-"))
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "token_counts.csv"
    token_counts(args.items, tokenizer_name=args.tokenizer).to_csv(output_path, index=False)
    print(f"Wrote token counts to {output_path}")


if __name__ == "__main__":
    main()
