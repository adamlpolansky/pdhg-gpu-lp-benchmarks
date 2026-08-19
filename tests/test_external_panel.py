from __future__ import annotations

from pathlib import Path

from pdhg_benchmarks.external_panel import (
    read_csv,
    select_instances,
    summarize_primary,
    validate_attribution,
)

ROOT = Path(__file__).resolve().parents[1]


def test_external_attribution_and_selector() -> None:
    rows = read_csv(ROOT / "evidence" / "external_attribution.csv")
    validate_attribution(rows)
    selected = select_instances(rows, [rows[2]["instance_name"], rows[0]["instance_name"]])
    assert [row["instance_name"] for row in selected] == [
        rows[2]["instance_name"],
        rows[0]["instance_name"],
    ]


def test_primary_denominators() -> None:
    rows = read_csv(ROOT / "evidence" / "external_primary_results.csv")
    summary = summarize_primary(rows)
    assert summary["slots"] == 48
    assert summary["status_counts"] == {"OPTIMAL": 48}
    assert summary["matched_pairs"] == 16
    assert summary["gpu_faster_pairs"] == 14
    assert summary["stable_pairs"] == 8
    assert summary["stable_gpu_faster_pairs"] == 6
    assert summary["winner_counts"] == {"barrier": 2, "dual_simplex": 2, "pdhg_gpu_tol_1e6": 4}
