"""Validate and deterministically render the curated public evidence snapshot."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .external_panel import matched_speedups, read_csv, summarize_primary, validate_attribution

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = ROOT / "evidence"
ASSETS = ROOT / "docs" / "assets"
SOURCE_SHA = "7c3365f7e7176fb61a586a65cd806ae82c663712"

CONTROLLED_FIELDS = (
    "family",
    "instance_label",
    "size",
    "rows",
    "columns",
    "nonzeros",
    "method",
    "device",
    "tolerance",
    "planned_slot",
    "attempted_solve",
    "terminal_outcome",
    "solver_status",
    "runtime_s",
    "quality_metric",
    "quality_value",
    "strict_quality_pass",
    "gpu_confirmed",
    "resource_outcome",
)

EXTERNAL_FIELDS = (
    "family",
    "instance_label",
    "band",
    "density_cell",
    "rows",
    "columns",
    "nonzeros",
    "method",
    "device",
    "tolerance",
    "terminal_outcome",
    "solver_status",
    "runtime_s",
    "quality_metric",
    "quality_value",
    "strict_quality_pass",
    "gpu_confirmed",
)

CONTROLLED_EXPECTED = {
    "cs": {"optimal": 48, "timeouts": 0, "resource": 0, "gpu": 18, "strict": 12},
    "mcf": {"optimal": 36, "timeouts": 4, "resource": 8, "gpu": 15, "strict": 9},
    "rbe": {"optimal": 43, "timeouts": 5, "resource": 0, "gpu": 18, "strict": 17},
    "cvar": {"optimal": 46, "timeouts": 2, "resource": 0, "gpu": 18, "strict": 26},
    "rob": {"optimal": 46, "timeouts": 2, "resource": 0, "gpu": 18, "strict": 9},
}


def _sha256(path: Path) -> str:
    data = path.read_bytes()
    if path.suffix in {".csv", ".json", ".svg"}:
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _svg_document(width: int, height: int, body: list[str], title: str, description: str) -> str:
    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f"<title>{html.escape(title)}</title>",
            f"<desc>{html.escape(description)}</desc>",
            '<rect width="100%" height="100%" fill="#0b1020"/>',
            '<g font-family="Arial, sans-serif" fill="#e7edf7">',
            *body,
            "</g>",
            "</svg>",
            "",
        ]
    )


def _runtime_matrix(rows: list[dict[str, str]]) -> str:
    instances = sorted({row["instance_label"] for row in rows})
    methods = [
        "dual_simplex",
        "barrier",
        "pdhg_cpu_tol_1e6",
        "pdhg_cpu_tol_1e8",
        "pdhg_gpu_tol_1e6",
        "pdhg_gpu_tol_1e8",
    ]
    values = {(row["instance_label"], row["method"]): float(row["runtime_s"]) for row in rows}
    logs = [math.log10(value) for value in values.values()]
    lower, upper = min(logs), max(logs)
    body = [
        '<text x="32" y="38" font-size="24" font-weight="700">Certified primary runtime matrix</text>',
        '<text x="32" y="62" font-size="13" fill="#aebbd0">48 OPTIMAL slots: 8 instances × 6 methods; seconds, log color scale</text>',
    ]
    left, top, cell_w, cell_h = 190, 110, 112, 44
    labels = ["Dual", "Barrier", "CPU 1e-6", "CPU 1e-8", "GPU 1e-6", "GPU 1e-8"]
    for column, label in enumerate(labels):
        body.append(
            f'<text x="{left + column * cell_w + cell_w / 2:.0f}" y="96" font-size="12" text-anchor="middle">{label}</text>'
        )
    for row_index, instance in enumerate(instances):
        y = top + row_index * cell_h
        body.append(
            f'<text x="180" y="{y + 27}" font-size="12" text-anchor="end">{html.escape(instance)}</text>'
        )
        for column, method in enumerate(methods):
            runtime = values[(instance, method)]
            scaled = (math.log10(runtime) - lower) / (upper - lower or 1.0)
            red = int(38 + 174 * scaled)
            green = int(174 - 100 * scaled)
            x = left + column * cell_w
            body.append(
                f'<rect x="{x}" y="{y}" width="108" height="40" rx="4" fill="rgb({red},{green},132)"/>'
            )
            body.append(
                f'<text x="{x + 54}" y="{y + 25}" font-size="11" text-anchor="middle">{runtime:.3g}s</text>'
            )
    body.append(
        '<text x="32" y="493" font-size="12" fill="#aebbd0">Descriptive result on the frozen panel; not a universal solver ranking.</text>'
    )
    return _svg_document(
        900,
        515,
        body,
        "Certified primary runtime matrix",
        "All 48 certified primary runtimes, in seconds.",
    )


def _speedup_chart(rows: list[dict[str, str]]) -> str:
    pairs = matched_speedups(rows)
    maximum = max(pair["speedup"] for pair in pairs)
    body = [
        '<text x="32" y="38" font-size="24" font-weight="700">Matched PDHG GPU/CPU runtime speedups</text>',
        '<text x="32" y="62" font-size="13" fill="#aebbd0">16 matched instance/tolerance pairs; ratio = CPU runtime ÷ GPU runtime</text>',
    ]
    left, top, width, bar_h = 210, 92, 620, 22
    for index, pair in enumerate(pairs):
        y = top + index * 27
        speedup = pair["speedup"]
        bar_width = width * speedup / maximum
        label = f"{pair['instance']} {pair['tolerance']}"
        color = "#4fd1a1" if speedup > 1.0 else "#f09a76"
        body.append(
            f'<text x="200" y="{y + 16}" font-size="11" text-anchor="end">{html.escape(label)}</text>'
        )
        body.append(
            f'<rect x="{left}" y="{y}" width="{bar_width:.2f}" height="{bar_h}" rx="3" fill="{color}"/>'
        )
        body.append(
            f'<text x="{min(860, left + bar_width + 6):.2f}" y="{y + 16}" font-size="11">{speedup:.2f}×</text>'
        )
    body.append(
        '<text x="32" y="548" font-size="12" fill="#aebbd0">Matched-profile solver-runtime comparison; not time-to-common-quality.</text>'
    )
    return _svg_document(
        930,
        570,
        body,
        "Matched PDHG speedups",
        "Sixteen CPU/GPU pairs at equal requested tolerance profiles.",
    )


def _rob_scaling(rows: list[dict[str, str]]) -> str:
    by_size: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        if row["runtime_s"]:
            by_size[row["size"]].append(float(row["runtime_s"]))
    order = ["S", "M", "L", "XL", "XXL", "XXXL"]
    medians = [statistics.median(by_size[size]) for size in order]
    maximum = max(medians)
    body = [
        '<text x="32" y="38" font-size="24" font-weight="700">ROB runtime scaling</text>',
        '<text x="32" y="62" font-size="13" fill="#aebbd0">Median solver runtime among terminal OPTIMAL runs at each frozen size</text>',
    ]
    for index, (size, value) in enumerate(zip(order, medians, strict=True)):
        x = 70 + index * 110
        height = 300 * math.log10(1.0 + value) / math.log10(1.0 + maximum)
        y = 400 - height
        body.append(
            f'<rect x="{x}" y="{y:.2f}" width="72" height="{height:.2f}" rx="4" fill="#7aa2f7"/>'
        )
        body.append(f'<text x="{x + 36}" y="422" font-size="12" text-anchor="middle">{size}</text>')
        body.append(
            f'<text x="{x + 36}" y="{max(85, y - 7):.2f}" font-size="11" text-anchor="middle">{value:.2f}s</text>'
        )
    body.append(
        '<text x="32" y="456" font-size="12" fill="#aebbd0">Descriptive scaling on one fixed hardware/software environment; timeouts are excluded from medians.</text>'
    )
    return _svg_document(
        760, 480, body, "ROB runtime scaling", "Median runtimes by frozen ROB size."
    )


def expected_assets() -> dict[str, str]:
    primary = read_csv(EVIDENCE / "external_primary_results.csv")
    rob = read_csv(EVIDENCE / "rob_results.csv")
    return {
        "primary_runtime_matrix.svg": _runtime_matrix(primary),
        "matched_pdhg_speedups.svg": _speedup_chart(primary),
        "runtime_scaling.svg": _rob_scaling(rob),
    }


def build() -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    for name, content in expected_assets().items():
        (ASSETS / name).write_text(content, encoding="utf-8", newline="\n")
    provenance_path = EVIDENCE / "provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    provenance["file_sha256"] = {
        path.name: _sha256(path)
        for path in sorted(EVIDENCE.iterdir())
        if path.is_file() and path.name != "provenance.json"
    }
    provenance["asset_sha256"] = {path.name: _sha256(path) for path in sorted(ASSETS.glob("*.svg"))}
    provenance_path.write_text(
        json.dumps(provenance, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )


def _validate_controlled(family: str) -> None:
    rows = read_csv(EVIDENCE / f"{family}_results.csv")
    if len(rows) != 48 or tuple(rows[0]) != CONTROLLED_FIELDS:
        raise ValueError(f"unexpected {family} evidence shape")
    expected = CONTROLLED_EXPECTED[family]
    actual = {
        "optimal": sum(row["solver_status"] == "OPTIMAL" for row in rows),
        "timeouts": sum(row["terminal_outcome"] == "timeout" for row in rows),
        "resource": sum(row["terminal_outcome"] == "resource_skip_before_attempt" for row in rows),
        "gpu": sum(row["gpu_confirmed"] == "true" for row in rows),
        "strict": sum(row["strict_quality_pass"] == "true" for row in rows),
    }
    if actual != expected:
        raise ValueError(f"{family} denominator mismatch: {actual}")
    if any(row["family"] != family or row["planned_slot"] != "true" for row in rows):
        raise ValueError(f"invalid {family} identity or planning flag")


def check() -> dict[str, Any]:
    for family in CONTROLLED_EXPECTED:
        _validate_controlled(family)
    status_rows = read_csv(EVIDENCE / "experiment_status.csv")
    if len(status_rows) != 6 or {row["block"] for row in status_rows} != {
        *CONTROLLED_EXPECTED,
        "external",
    }:
        raise ValueError("experiment status must describe exactly six blocks")
    primary = read_csv(EVIDENCE / "external_primary_results.csv")
    if len(primary) != 48 or tuple(primary[0]) != EXTERNAL_FIELDS:
        raise ValueError("unexpected external primary evidence shape")
    summary = summarize_primary(primary)
    expected_summary = {
        "slots": 48,
        "instances": 8,
        "status_counts": {"OPTIMAL": 48},
        "terminal_counts": {"completed": 48},
        "matched_pairs": 16,
        "gpu_faster_pairs": 14,
        "stable_pairs": 8,
        "stable_gpu_faster_pairs": 6,
        "winner_counts": {"barrier": 2, "dual_simplex": 2, "pdhg_gpu_tol_1e6": 4},
    }
    for key, value in expected_summary.items():
        if summary[key] != value:
            raise ValueError(f"external primary mismatch for {key}: {summary[key]!r}")
    if not math.isclose(summary["median_speedup"], 4.03663976563391, rel_tol=1e-12):
        raise ValueError("external primary median speedup mismatch")
    diagnostic = json.loads(
        (EVIDENCE / "external_diagnostic_summary.json").read_text(encoding="utf-8")
    )
    if diagnostic["full_audit"]["solver_statuses"] != {"OPTIMAL": 60, "SUBOPTIMAL": 4}:
        raise ValueError("external full-audit status mismatch")
    if diagnostic["full_audit"]["terminal_categories"] != {
        "completed": 60,
        "execution_failure": 1,
        "numerical_failure": 3,
    }:
        raise ValueError("external full-audit terminal mismatch")
    attribution = read_csv(EVIDENCE / "external_attribution.csv")
    validate_attribution(attribution)
    provenance = json.loads((EVIDENCE / "provenance.json").read_text(encoding="utf-8"))
    if provenance["source_checkpoint_sha"] != SOURCE_SHA:
        raise ValueError("source checkpoint mismatch")
    for name, digest in provenance["file_sha256"].items():
        if _sha256(EVIDENCE / name) != digest:
            raise ValueError(f"evidence checksum mismatch: {name}")
    assets = expected_assets()
    for name, content in assets.items():
        path = ASSETS / name
        if path.read_text(encoding="utf-8") != content:
            raise ValueError(f"non-deterministic or stale asset: {name}")
        if _sha256(path) != provenance["asset_sha256"][name]:
            raise ValueError(f"asset checksum mismatch: {name}")
    return {"status": "ok", "files": len(provenance["file_sha256"]), **summary}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.build:
        build()
    report = check()
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
