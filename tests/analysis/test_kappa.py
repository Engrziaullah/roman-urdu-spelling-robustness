import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from src.analysis.kappa import (
    cohen_kappa,
    counts_from_wide,
    evaluate_kappa_sheet,
    fleiss_kappa,
    kappa_with_ci,
    main,
)


def test_hand_computed():
    wide = pd.DataFrame(
        [["A", "A", "A"],
         ["A", "A", "B"],
         ["A", "B", "C"],
         ["A", "A", "INVALID"]]
    )
    counts, cats = counts_from_wide(wide)
    assert cats == ["A", "B", "C", "INVALID"]
    assert abs(fleiss_kappa(counts) - (-5 / 37)) < 1e-9


def test_perfect_agreement_is_one():
    wide = pd.DataFrame([["A", "A", "A"], ["B", "B", "B"], ["C", "C", "C"]])
    counts, _ = counts_from_wide(wide)
    assert abs(fleiss_kappa(counts) - 1.0) < 1e-9


def test_everyone_same_answer_is_nan():
    wide = pd.DataFrame([["A", "A", "A"]] * 5)
    counts, _ = counts_from_wide(wide)
    assert np.isnan(fleiss_kappa(counts))


def test_ci_function_matches_point_estimate():
    rng = np.random.default_rng(0)
    rows = []
    for _ in range(200):
        base = rng.choice(list("ABCD"))
        rows.append([base if rng.random() < 0.7 else rng.choice(list("ABCD")) for _ in range(3)])
    counts, _ = counts_from_wide(pd.DataFrame(rows))
    k, lo, hi = kappa_with_ci(counts, np.arange(200), n_boot=200)
    assert abs(k - fleiss_kappa(counts)) < 1e-12
    assert lo <= hi


def test_cohen_kappa_hand_computed():
    r1 = ["y"] * 20 + ["n"] * 10
    r2 = ["y"] * 15 + ["n"] * 15
    k, po = cohen_kappa(r1, r2)
    assert abs(po - (25 / 30)) < 1e-9
    assert abs(k - (2 / 3)) < 1e-9


def test_cohen_kappa_perfect():
    r1 = ["y", "n", "y", "n", "y"]
    r2 = ["y", "n", "y", "n", "y"]
    k, po = cohen_kappa(r1, r2)
    assert k == 1.0
    assert po == 1.0


def test_evaluate_kappa_sheet():
    df = pd.DataFrame({
        "item_id": [f"umm-{i:04d}" for i in range(1, 51)],
        "condition": ["RU-P"] * 50,
        "rater_1": ["y"] * 45 + ["n"] * 5,
        "rater_2": ["y"] * 46 + ["n"] * 4,
    })
    res = evaluate_kappa_sheet(df, target_threshold=0.80)
    assert res["n_items"] == 50
    assert res["raw_agreement"] >= 0.90
    assert res["cohen_kappa"] > 0.0


def test_evaluate_kappa_sheet_warning():
    df = pd.DataFrame({
        "item_id": [f"umm-{i:04d}" for i in range(1, 11)],
        "condition": ["RU-P"] * 10,
        "rater_1": ["y", "n"] * 5,
        "rater_2": ["n", "y"] * 5,
    })
    with pytest.warns(UserWarning, match="below the target threshold"):
        res = evaluate_kappa_sheet(df, target_threshold=0.80)
    assert res["passed"] is False
    assert res["cohen_kappa"] < 0.0


def test_evaluate_kappa_sheet_missing_columns():
    df = pd.DataFrame({
        "item_id": ["umm-0001"],
        "rater_1": ["y"],
    })
    with pytest.raises(ValueError, match="missing required columns"):
        evaluate_kappa_sheet(df)


def test_evaluate_kappa_sheet_rejects_duplicate_item_condition():
    df = pd.DataFrame({
        "item_id": ["i1", "i1"],
        "condition": ["RU-P", "RU-P"],
        "rater_1": ["y", "n"],
        "rater_2": ["y", "n"],
    })
    with pytest.raises(ValueError, match="duplicate item-condition"):
        evaluate_kappa_sheet(df)


@pytest.mark.parametrize(
    ("rater_1", "rater_2", "message"),
    [
        (["y", None], ["y", "n"], "missing ratings"),
        (["y", "maybe"], ["y", "n"], "labels outside y/n"),
    ],
)
def test_evaluate_kappa_sheet_rejects_missing_or_invalid_labels(rater_1, rater_2, message):
    df = pd.DataFrame({
        "item_id": ["i1", "i2"],
        "condition": ["RU-P", "RU-R"],
        "rater_1": rater_1,
        "rater_2": rater_2,
    })
    with pytest.raises(ValueError, match=message):
        evaluate_kappa_sheet(df)


def test_evaluate_kappa_sheet_reports_insufficient_class_variation():
    df = pd.DataFrame({
        "item_id": ["i1", "i2"],
        "condition": ["RU-P", "RU-R"],
        "rater_1": ["y", "y"],
        "rater_2": ["y", "y"],
    })
    result = evaluate_kappa_sheet(df)
    assert np.isnan(result["cohen_kappa"])
    assert result["status"] == "UNDEFINED_NO_CLASS_VARIATION"


def test_kappa_cli_unanimous_ratings_and_input_unchanged(tmp_path, capsys):
    sheet = tmp_path / "kappa.csv"
    sheet.write_text(
        "item_id,condition,rater_1,rater_2\nitem-1,RU-P,y,y\nitem-2,RU-R,y,y\n",
        encoding="utf-8",
    )
    original = sheet.read_bytes()

    main([str(sheet)])

    output = capsys.readouterr().out
    assert "Items evaluated: 2" in output
    assert "Raw agreement:   1.0000" in output
    assert "Cohen's kappa:   undefined" in output
    assert "Status: UNDEFINED" in output
    assert sheet.read_bytes() == original


def test_kappa_cli_hand_computed_example(tmp_path, capsys):
    sheet = tmp_path / "kappa.csv"
    sheet.write_text(
        "item_id,condition,rater_1,rater_2\n"
        "item-1,RU-P,y,y\n"
        "item-2,RU-P,y,n\n"
        "item-3,RU-P,n,y\n"
        "item-4,RU-P,n,n\n",
        encoding="utf-8",
    )

    with pytest.warns(UserWarning, match="below the target threshold"):
        main([str(sheet)])

    output = capsys.readouterr().out
    assert "Items evaluated: 4" in output
    assert "Raw agreement:   0.5000" in output
    assert "Cohen's kappa:   0.0000" in output
    assert "Status: WARNING" in output


def test_kappa_cli_accepts_template_path(capsys):
    template = Path("annotations/kappa_template.csv")

    with pytest.raises(ValueError, match="Kappa sheet is empty"):
        main([str(template)])
