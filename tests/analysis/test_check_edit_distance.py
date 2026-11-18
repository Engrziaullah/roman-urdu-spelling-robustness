from src.analysis.check_edit_distance import check_edit_distance_csv, main


def write_csv(path, text):
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_edit_distance_csv(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance\n"
        "RU-P vs RU-R,1.5,0.2\n"
        "RU-P vs RU-X,2,0.4\n"
        "RU-R vs RU-X,1,0.3\n",
    )

    assert check_edit_distance_csv(csv_path) == []


def test_missing_column_is_reported(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair\nRU-P vs RU-R\n",
    )

    assert check_edit_distance_csv(csv_path) == [
        "Missing required column: mean_char_edit_distance"
    ]


def test_normalized_column_is_optional(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance\n"
        "RU-P vs RU-R,1.5\n"
        "RU-P vs RU-X,2\n"
        "RU-R vs RU-X,1\n",
    )

    assert check_edit_distance_csv(csv_path) == []


def test_invalid_normalized_distance_is_reported(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance\n"
        "RU-P vs RU-R,1.5,1.2\n"
        "RU-P vs RU-X,2,0.4\n"
        "RU-R vs RU-X,1,0.3\n",
    )

    assert "Row 2: mean_normalized_edit_distance must be between 0 and 1." in (
        check_edit_distance_csv(csv_path)
    )


def test_missing_value_is_reported(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance\n"
        "RU-P vs RU-R,,0.2\n"
        "RU-P vs RU-X,2,0.4\n"
        "RU-R vs RU-X,1,0.3\n",
    )

    problems = check_edit_distance_csv(csv_path)

    assert "Row 2: missing value in column(s): mean_char_edit_distance." in problems


def test_unexpected_pair_and_numeric_ranges_are_reported(tmp_path):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance\n"
        "RU-P vs RT,-1,1.2\n"
        "RU-P vs RU-R,1,0.2\n"
        "RU-R vs RU-X,1,0.3\n",
    )

    problems = check_edit_distance_csv(csv_path)

    assert any("unexpected variant_pair" in problem for problem in problems)
    assert any("must be non-negative" in problem for problem in problems)
    assert any("must be between 0 and 1" in problem for problem in problems)
    assert any("Missing expected variant_pair: RU-P vs RU-X" in problem for problem in problems)


def test_cli_prints_ok(tmp_path, capsys):
    csv_path = write_csv(
        tmp_path / "edit_distance.csv",
        "variant_pair,mean_char_edit_distance,mean_normalized_edit_distance\n"
        "RU-P vs RU-R,1.5,0.2\n"
        "RU-P vs RU-X,2,0.4\n"
        "RU-R vs RU-X,1,0.3\n",
    )

    assert main([str(csv_path)]) == 0
    assert capsys.readouterr().out == "OK\n"
