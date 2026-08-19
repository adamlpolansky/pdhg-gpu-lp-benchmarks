from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdhg_benchmarks.demo import run
from pdhg_benchmarks.generators import FAMILY_GENERATORS, generate_demo
from pdhg_benchmarks.validators import validate_instance

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("family", sorted(FAMILY_GENERATORS))
def test_demo_configs_are_deterministic_and_feasible(family: str) -> None:
    config_path = ROOT / "configs" / "demo" / f"{family}_tiny.yaml"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    first = generate_demo(config)
    second = generate_demo(config)
    assert first.sha256() == second.sha256()
    assert validate_instance(first)["witness_feasible"] is True
    assert run(config_path)["sha256"] == first.sha256()


def test_unknown_family_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown demo family"):
        generate_demo({"family": "unknown"})
