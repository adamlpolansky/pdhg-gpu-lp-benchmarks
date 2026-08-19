from __future__ import annotations

import pytest

from pdhg_benchmarks.privacy import validate_public_record


def test_public_writer_accepts_only_curated_fields() -> None:
    record = {
        "family": "cs",
        "instance_label": "CS-S",
        "size": "S",
        "rows": 4,
        "columns": 8,
        "nonzeros": 16,
        "method": "demo",
        "device": "cpu",
        "tolerance": "",
        "terminal_outcome": "validated",
        "solver_status": "not_solved",
        "runtime_s": None,
        "quality_metric": "witness_residual",
        "quality_value": 0.0,
        "strict_quality_pass": True,
        "gpu_confirmed": False,
        "resource_outcome": "not_applicable",
    }
    assert validate_public_record(record) == record


@pytest.mark.parametrize(
    "field",
    ["host", "user", "pid", "executable", "dirty", "run_id", "attempt_id", "credential"],
)
def test_public_writer_rejects_machine_and_run_metadata(field: str) -> None:
    with pytest.raises(ValueError):
        validate_public_record({field: "value"})


@pytest.mark.parametrize(
    "value",
    ["X:/" + "Users/person/file", "/" + "home/person/file", "/mnt/x/" + "Users/person/file"],
)
def test_public_writer_rejects_absolute_local_paths(value: str) -> None:
    with pytest.raises(ValueError, match="absolute local path"):
        validate_public_record({"instance_label": value})
