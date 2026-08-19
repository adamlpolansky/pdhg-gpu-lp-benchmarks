from __future__ import annotations

import hashlib

from pdhg_benchmarks.evidence import ASSETS, check, expected_assets


def test_public_evidence_and_assets_are_current() -> None:
    report = check()
    assert report["status"] == "ok"


def test_asset_rendering_is_deterministic() -> None:
    first = expected_assets()
    second = expected_assets()
    assert first == second
    for name, content in first.items():
        assert (ASSETS / name).read_text(encoding="utf-8") == content
        assert (
            hashlib.sha256(content.encode()).hexdigest()
            == hashlib.sha256(second[name].encode()).hexdigest()
        )
