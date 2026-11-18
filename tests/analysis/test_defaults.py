import inspect

from src.analysis.accuracy import accuracy_table
from src.analysis.compare import compare_to_noise
from src.analysis.flips import dual_flip_rates_table, flip_rates_table
from src.analysis.kappa import kappa_table, kappa_with_ci
from src.analysis.mcnemar import mcnemar_table
from src.analysis.noise import noise_table
from src.analysis.tables import make_accuracy_table, make_flip_rates_table, write_all_tables


def test_bootstrap_function_defaults_are_10000():
    functions = [
        accuracy_table,
        compare_to_noise,
        flip_rates_table,
        dual_flip_rates_table,
        kappa_with_ci,
        kappa_table,
        mcnemar_table,
        noise_table,
        make_accuracy_table,
        make_flip_rates_table,
        write_all_tables,
    ]

    for function in functions:
        assert inspect.signature(function).parameters["n_boot"].default == 10000


def test_tables_cli_bootstrap_default_is_10000(monkeypatch, tmp_path):
    import src.analysis.tables as tables_module

    calls = {}

    def fake_write_all_tables(results_path, items_path, output_dir, **kwargs):
        calls["kwargs"] = kwargs

    monkeypatch.setattr(tables_module, "write_all_tables", fake_write_all_tables)
    tables_module.main([
        "--results", "results.jsonl",
        "--items", "items.jsonl",
        "--out", str(tmp_path),
    ])

    assert calls["kwargs"]["n_boot"] == 10000
