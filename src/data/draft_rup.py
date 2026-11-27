"""RU-P draft workflow scaffold with an injected client and no provider adapter."""

from __future__ import annotations
import argparse
import csv
import hashlib
import json
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Protocol, Sequence

import yaml

from src.data.invariants import validate_rup_proxy
from src.data.rule_engine import LEXICON_HEADER


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "data" / "processed" / "items_nu.jsonl"
DEFAULT_OUTPUT = ROOT / "data" / "interim" / "rup_draft.jsonl"
DEFAULT_PROMPT_RECORD = ROOT / "data" / "interim" / "rup_prompt.md"
DEFAULT_CACHE = Path(tempfile.gettempdir()) / "roman_urdu_rup_cache.jsonl"
DEFAULT_FAILURES = Path(tempfile.gettempdir()) / "rup_draft_failures.jsonl"
MAX_ATTEMPTS = 3
BACKOFF_INITIAL_S = 1.0

DRAFT_INSTRUCTIONS = (
    "Transliterate the Urdu question and every option into Roman Urdu only. "
    "Do not translate, correct, summarise, or reword. Preserve digits, option "
    "labels, formulas, units, URLs, Latin-script words, and all other protected "
    "tokens unchanged. Use the provided lexicon for listed words. Follow only "
    "team-approved RU-P conventions. Return JSON only with exactly the keys "
    "question and options."
)


class DraftConfigurationError(ValueError):
    """The helper model configuration is unresolved or unsafe for drafting."""


class DraftClientError(Exception):
    """A client reports a retryable request failure."""


class DraftClient(Protocol):
    """Injected helper-client interface; provider implementations are out of scope."""

    def complete(self, prompt: str, model_string: str) -> str:
        """Return the raw text response for one prompt."""
        ...


@dataclass(frozen=True)
class DraftResult:
    rows: tuple[dict[str, Any], ...]
    cache_hits: int
    failures: int

    @property
    def flagged_items(self) -> int:
        """Count rows carrying a failure or diagnostic note."""
        return sum(
            bool(row.get("notes"))
            for row in self.rows
        )


def load_model_config(path: Path) -> dict[str, Any]:
    """Load model configuration without reading API-key environment variables."""
    with path.open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle)
    if not isinstance(payload, dict):
        raise DraftConfigurationError(f"{path} must contain a YAML mapping")
    return payload


def validate_helper_config(config: Mapping[str, Any]) -> dict[str, str]:
    """Require a resolved helper that is distinct from every evaluated model."""
    helper = config.get("helper")
    evaluated = config.get("evaluated_models")
    if not isinstance(helper, Mapping) or not isinstance(evaluated, list):
        raise DraftConfigurationError(
            "models config must contain helper and evaluated_models"
        )
    provider = helper.get("provider")
    model_string = helper.get("model_string")
    if (
        not isinstance(provider, str)
        or not provider.strip()
        or provider.strip().upper() in {"TODO", "TBD"}
        or not isinstance(model_string, str)
        or not model_string.strip()
        or model_string.strip().upper() in {"TODO", "TBD"}
    ):
        raise DraftConfigurationError(
            "helper provider and model_string must be resolved, not TODO/TBD"
        )
    helper_model = {
        "provider": provider.strip(),
        "model_string": model_string.strip(),
    }
    for index, model in enumerate(evaluated):
        if not isinstance(model, Mapping):
            raise DraftConfigurationError(
                f"evaluated_models[{index}] must be a mapping"
            )
        evaluated_string = model.get("model_string")
        evaluated_provider = model.get("provider")
        same_string = (
            isinstance(evaluated_string, str)
            and evaluated_string.strip().upper() not in {"TODO", "TBD"}
            and evaluated_string.strip() == helper_model["model_string"]
        )
        same_provider_model = (
            isinstance(evaluated_provider, str)
            and evaluated_provider.strip() == helper_model["provider"]
            and same_string
        )
        if same_string or same_provider_model:
            raise DraftConfigurationError(
                "helper model must not match an evaluated model "
                f"(evaluated_models[{index}])"
            )
    return helper_model


def load_lexicon(path: Path) -> dict[str, str]:
    """Load the approved RU-P lexicon and reject duplicate source words."""
    lexicon: dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != LEXICON_HEADER:
            raise ValueError(
                f"{path} must have exact header {','.join(LEXICON_HEADER)}"
            )
        for line_number, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"{path} has malformed CSV row at line {line_number}")
            urdu_word = row["urdu_word"]
            ru_p = row["ru_p"]
            if not urdu_word or not ru_p:
                raise ValueError(
                    f"{path} row {line_number} requires urdu_word and ru_p"
                )
            if urdu_word in lexicon:
                raise ValueError(
                    f"{path} has duplicate urdu_word at line {line_number}"
                )
            lexicon[urdu_word] = ru_p
    return lexicon


def build_prompt(item: Mapping[str, Any], lexicon: Mapping[str, str]) -> str:
    """Create the constrained JSON-only drafting prompt for one source item."""
    question = item.get("question")
    options = item.get("options")
    if not isinstance(question, str) or not isinstance(options, list):
        raise ValueError(f"item {item.get('item_id', '<unknown>')}: invalid source fields")
    source = {"question": question, "options": options}
    lexicon_text = json.dumps(dict(sorted(lexicon.items())), ensure_ascii=False)
    source_text = json.dumps(source, ensure_ascii=False)
    return (
        f"{DRAFT_INSTRUCTIONS}\n"
        f"Lexicon JSON: {lexicon_text}\n"
        f"Source JSON: {source_text}"
    )


def _cache_key(prompt: str, model_string: str) -> str:
    payload = json.dumps(
        {"model_string": model_string, "prompt": prompt},
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _load_cache(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    cache: dict[str, str] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if (
                not isinstance(row, dict)
                or not isinstance(row.get("cache_key"), str)
                or not isinstance(row.get("raw_output"), str)
            ):
                raise ValueError(f"{path} has invalid cache row at line {line_number}")
            cache[row["cache_key"]] = row["raw_output"]
    return cache


def _append_jsonl(path: Path, row: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def _fetch_response(
    client: DraftClient,
    prompt: str,
    model_string: str,
    max_attempts: int,
    backoff_initial_s: float,
    sleep: Callable[[float], None],
) -> str:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least one")
    if backoff_initial_s < 0:
        raise ValueError("backoff_initial_s must be non-negative")
    for attempt in range(max_attempts):
        try:
            response = client.complete(prompt, model_string)
        except DraftClientError:
            if attempt + 1 == max_attempts:
                raise
            sleep(backoff_initial_s * (2 ** attempt))
            continue
        if not isinstance(response, str):
            raise DraftClientError("client response must be text")
        return response
    raise DraftClientError("request attempts exhausted")


def parse_response(raw_output: str, option_count: int) -> tuple[dict[str, Any] | None, str | None]:
    """Validate exact JSON shape and return a reason code for malformed responses."""
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError:
        return None, "bad_json"
    if (
        not isinstance(payload, dict)
        or set(payload) != {"question", "options"}
        or not isinstance(payload.get("question"), str)
        or not isinstance(payload.get("options"), list)
    ):
        return None, "invalid_schema"
    if not payload["question"].strip() or any(
        not isinstance(option, str) or not option.strip()
        for option in payload["options"]
    ):
        return None, "empty_field"
    if len(payload["options"]) != option_count:
        return None, "wrong_option_count"
    return payload, None


def _proxy_flags(
    source: Mapping[str, Any],
    draft: Mapping[str, Any],
    protected_tokens: Sequence[str],
) -> list[str]:
    report = validate_rup_proxy(source, draft, protected_tokens)
    flags: list[str] = []
    for diagnostic in report["diagnostics"]:
        if "positional order assumed" in diagnostic:
            continue
        if "token count differs" in diagnostic:
            flags.append("token_count_mismatch")
        elif "digit sequence differs" in diagnostic:
            flags.append("digit_sequence_mismatch")
        elif diagnostic.startswith("gold:"):
            flags.append("gold_mismatch")
        elif diagnostic.startswith("options:"):
            flags.append("option_count_mismatch")
        elif "protected token" in diagnostic:
            flags.append("protected_token_mismatch")
        else:
            flags.append("proxy_check_failed")
    return list(dict.fromkeys(flags))


def _failed_row(
    source: Mapping[str, Any],
    reason_code: str,
) -> dict[str, Any]:
    """Retain the source text in a clearly rejected RU-P contract row."""
    row = dict(source)
    row["condition"] = "RU-P"
    row["verified"] = False
    row["notes"] = f"DRAFT_FAILED:{reason_code}"
    return row


def draft_items(
    items: Sequence[Mapping[str, Any]],
    client: DraftClient,
    model_config: Mapping[str, Any],
    lexicon: Mapping[str, str],
    *,
    cache_path: Path = DEFAULT_CACHE,
    failures_path: Path = DEFAULT_FAILURES,
    output_path: Path | None = None,
    prompt_record_path: Path | None = None,
    protected_tokens_by_item: Mapping[str, Sequence[str]] | None = None,
    pilot: int | None = None,
    max_attempts: int = MAX_ATTEMPTS,
    backoff_initial_s: float = BACKOFF_INITIAL_S,
    sleep: Callable[[float], None] = time.sleep,
) -> DraftResult:
    """Draft RU-P rows, caching raw responses and retaining every failed item."""
    helper = validate_helper_config(model_config)
    selected = list(items)
    if pilot is not None:
        if pilot < 1:
            raise ValueError("pilot must be a positive item count")
        selected = selected[:pilot]
    cache = _load_cache(cache_path)
    protected_by_item = protected_tokens_by_item or {}
    output: list[dict[str, Any]] = []
    prompts_used: list[tuple[str, str]] = []
    seen_item_ids: set[str] = set()
    cache_hits = 0
    failures = 0

    for source in selected:
        item_id = str(source.get("item_id", "<unknown>"))
        if item_id in seen_item_ids:
            raise ValueError(f"duplicate item_id in draft input: {item_id}")
        seen_item_ids.add(item_id)
        if source.get("condition") != "NU":
            raise ValueError(f"item {item_id}: drafting input condition must be NU")
        source_options = source.get("options")
        if not isinstance(source_options, list):
            raise ValueError(f"item {item_id}: source options must be a list")
        prompt = build_prompt(source, lexicon)
        prompts_used.append((item_id, prompt))
        key = _cache_key(prompt, helper["model_string"])
        raw_output = cache.get(key)
        if raw_output is not None:
            cache_hits += 1
        else:
            try:
                raw_output = _fetch_response(
                    client,
                    prompt,
                    helper["model_string"],
                    max_attempts,
                    backoff_initial_s,
                    sleep,
                )
            except DraftClientError:
                failed = _failed_row(source, "request_failed")
                output.append(failed)
                failures += 1
                _append_jsonl(failures_path, {
                    "item_id": item_id,
                    "reason_code": "request_failed",
                    "raw_output": None,
                    "model_string": helper["model_string"],
                })
                continue
            cache[key] = raw_output
            _append_jsonl(cache_path, {"cache_key": key, "raw_output": raw_output})

        payload, reason_code = parse_response(raw_output, len(source_options))
        if reason_code is not None or payload is None:
            output.append(_failed_row(source, reason_code or "invalid_schema"))
            failures += 1
            _append_jsonl(failures_path, {
                "item_id": item_id,
                "reason_code": reason_code or "invalid_schema",
                "raw_output": raw_output,
                "model_string": helper["model_string"],
            })
            continue

        row = dict(source)
        row["condition"] = "RU-P"
        row["question"] = payload["question"]
        row["options"] = payload["options"]
        row["verified"] = False
        item_protected = protected_by_item.get(item_id, ())
        flags = _proxy_flags(source, row, item_protected)
        row["notes"] = ";".join(f"DRAFT_FLAG:{flag}" for flag in flags)
        output.append(row)
    result = DraftResult(tuple(output), cache_hits, failures)
    if output_path is not None:
        write_jsonl(output_path, result.rows)
    if prompt_record_path is not None:
        write_prompt_record(
            prompt_record_path, helper["model_string"], prompts_used
        )
    return result


def write_jsonl(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    """Write all contract rows as UTF-8 JSON Lines."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        for row in rows:
            handle.write(json.dumps(dict(row), ensure_ascii=False) + "\n")


def write_prompt_record(
    path: Path,
    model_string: str,
    prompts: Sequence[tuple[str, str]],
) -> None:
    """Record each exact prompt and model string as JSON Lines in a Markdown file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("# RU-P prompt record\n\n")
        for item_id, prompt in prompts:
            handle.write(json.dumps({
                "item_id": item_id,
                "model_string": model_string,
                "prompt": prompt,
            }, ensure_ascii=False) + "\n")


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main(client: DraftClient | None = None) -> None:
    """Run the injected-client scaffold or refuse when no adapter is supplied."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="input_path", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--prompt-record", type=Path, default=DEFAULT_PROMPT_RECORD)
    parser.add_argument("--config", type=Path, default=ROOT / "configs" / "models.yaml")
    parser.add_argument(
        "--lexicon", type=Path,
        default=ROOT / "src" / "data" / "rules" / "ru_p_lexicon.csv",
    )
    parser.add_argument("--cache", type=Path, default=DEFAULT_CACHE)
    parser.add_argument("--failures", type=Path, default=DEFAULT_FAILURES)
    parser.add_argument("--pilot", type=int, default=None)
    args = parser.parse_args()

    model_config = load_model_config(args.config)
    try:
        validate_helper_config(model_config)
    except DraftConfigurationError as exc:
        parser.error(str(exc))
    if client is None:
        raise SystemExit(
            "No provider integration is included. Supply an approved DraftClient "
            "to main() or draft_items(); no network request was made."
        )
    rows = _read_jsonl(args.input_path)
    lexicon = load_lexicon(args.lexicon)
    result = draft_items(
        rows,
        client,
        model_config,
        lexicon,
        cache_path=args.cache,
        failures_path=args.failures,
        output_path=args.out,
        prompt_record_path=args.prompt_record,
        pilot=args.pilot,
    )
    print(
        f"Items drafted: {len(result.rows)}; flagged: {result.flagged_items}; "
        f"cache hits: {result.cache_hits}; failures: {result.failures}"
    )


if __name__ == "__main__":
    main()
