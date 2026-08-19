"""Public contract, inventory validation, selection, and analysis for the external panel."""

from __future__ import annotations

import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ATTRIBUTION_FIELDS = (
    "instance_name",
    "official_source_url",
    "source_sha256",
    "creator_or_submitter",
    "license_url",
    "adaptation_notice",
)

PRIMARY_METHODS = (
    "dual_simplex",
    "barrier",
    "pdhg_cpu_tol_1e6",
    "pdhg_cpu_tol_1e8",
    "pdhg_gpu_tol_1e6",
    "pdhg_gpu_tol_1e8",
)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_attribution(rows: list[dict[str, str]]) -> None:
    if len(rows) != 8 or len({row["instance_name"] for row in rows}) != 8:
        raise ValueError("the attribution inventory must contain eight unique instances")
    for row in rows:
        if tuple(row) != ATTRIBUTION_FIELDS:
            raise ValueError("unexpected attribution schema")
        for field in ("official_source_url", "license_url"):
            parsed = urlparse(row[field])
            if parsed.scheme != "https" or not parsed.netloc:
                raise ValueError(f"invalid public URL in {field}")
        digest = row["source_sha256"]
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError("invalid source digest")
        if "integrality removed" not in row["adaptation_notice"].lower():
            raise ValueError("missing LP-relaxation adaptation notice")


def select_instances(rows: list[dict[str, str]], names: list[str]) -> list[dict[str, str]]:
    """Return named public inventory entries in requested order, rejecting ambiguity."""

    by_name = {row["instance_name"]: row for row in rows}
    if len(by_name) != len(rows) or len(names) != len(set(names)):
        raise ValueError("selection inputs must be unique")
    missing = [name for name in names if name not in by_name]
    if missing:
        raise ValueError(f"unknown external-panel instances: {missing}")
    return [by_name[name] for name in names]


def matched_speedups(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], dict[str, float]] = defaultdict(dict)
    for row in rows:
        method = row["method"]
        if method.startswith("pdhg_cpu_") or method.startswith("pdhg_gpu_"):
            key = (row["instance_label"], row["tolerance"])
            grouped[key][row["device"]] = float(row["runtime_s"])
    pairs: list[dict[str, Any]] = []
    for (instance, tolerance), runtimes in sorted(grouped.items()):
        if set(runtimes) != {"cpu", "gpu"}:
            continue
        pairs.append(
            {
                "instance": instance,
                "tolerance": tolerance,
                "cpu_runtime_s": runtimes["cpu"],
                "gpu_runtime_s": runtimes["gpu"],
                "speedup": runtimes["cpu"] / runtimes["gpu"],
            }
        )
    return pairs


def summarize_primary(rows: list[dict[str, str]]) -> dict[str, Any]:
    pairs = matched_speedups(rows)
    stable = [
        pair for pair in pairs if pair["cpu_runtime_s"] >= 1.0 and pair["gpu_runtime_s"] >= 1.0
    ]
    by_instance: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_instance[row["instance_label"]].append(row)
    winners = Counter(
        min(instance_rows, key=lambda row: float(row["runtime_s"]))["method"]
        for instance_rows in by_instance.values()
    )
    return {
        "slots": len(rows),
        "instances": len(by_instance),
        "status_counts": dict(sorted(Counter(row["solver_status"] for row in rows).items())),
        "terminal_counts": dict(sorted(Counter(row["terminal_outcome"] for row in rows).items())),
        "matched_pairs": len(pairs),
        "gpu_faster_pairs": sum(pair["speedup"] > 1.0 for pair in pairs),
        "median_speedup": statistics.median(pair["speedup"] for pair in pairs),
        "stable_pairs": len(stable),
        "stable_gpu_faster_pairs": sum(pair["speedup"] > 1.0 for pair in stable),
        "winner_counts": dict(sorted(winners.items())),
    }
