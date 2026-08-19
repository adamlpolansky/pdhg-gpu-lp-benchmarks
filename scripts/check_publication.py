"""Fail closed when the curated repository violates its publication contract."""

from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 25 * 1024 * 1024

ROOT_FILES = {
    ".gitignore",
    "CITATION.cff",
    "LICENSE",
    "README.md",
    "THIRD_PARTY_NOTICES.md",
    "pyproject.toml",
}
EXACT_FILES = {
    ".github/workflows/ci.yml",
    "configs/demo/cs_tiny.yaml",
    "configs/demo/cvar_tiny.yaml",
    "configs/demo/mcf_tiny.yaml",
    "configs/demo/rbe_tiny.yaml",
    "configs/demo/rob_tiny.yaml",
    "tests/fixtures/pathological/network_capacity_violation.json",
}
ALLOWED_GROUPS = {
    "docs": {".md"},
    "docs/assets": {".svg"},
    "evidence": {".csv", ".json"},
    "scripts": {".py"},
    "src/pdhg_benchmarks": {".py", ".typed"},
    "tests": {".py"},
}
DENIED_SUFFIXES = {
    ".mps",
    ".gz",
    ".lp",
    ".sol",
    ".log",
    ".npy",
    ".npz",
    ".zip",
    ".xlsx",
    ".xls",
    ".parquet",
    ".sqlite",
    ".db",
    ".env",
    ".key",
    ".pem",
    ".lic",
    ".p12",
    ".pfx",
}
DENIED_NAMES = {"key.txt", "gurobi.lic"}
IGNORED_PARTS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache", "build", "dist"}


def _allowed(path: PurePosixPath) -> bool:
    text = path.as_posix()
    if text in ROOT_FILES or text in EXACT_FILES:
        return True
    parent = path.parent.as_posix()
    return parent in ALLOWED_GROUPS and path.suffix in ALLOWED_GROUPS[parent]


def _material_files(root: Path) -> list[Path]:
    result = []
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS or part.endswith(".egg-info") for part in relative.parts):
            continue
        if path.is_file() or path.is_symlink():
            result.append(path)
    return sorted(result)


def _tracked_files(root: Path) -> list[Path] | None:
    if not (root / ".git").exists():
        return None
    result = (
        subprocess.run(["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True)
        .stdout.decode("utf-8")
        .split("\0")
    )
    return [root / item for item in result if item]


def _signatures() -> list[tuple[str, re.Pattern[str]]]:
    joined = lambda *parts: "".join(parts)  # noqa: E731
    literal_patterns = {
        "windows user path": r"[A-Za-z]:[\\/]" + joined("Us", "ers") + r"[\\/]",
        "mounted user path": r"/mnt/[a-z]/" + joined("Us", "ers") + r"/",
        "unix home path": r"/" + joined("ho", "me") + r"/",
        "university address": "@" + joined("cu", "ni") + r"\.cz",
        "placeholder address": joined("adam", "@example", ".com"),
        "cloud credential field": joined("WLS", "ACCESS", "ID"),
        "cloud credential value": joined("WLS", "SE", "CRET"),
        "license identifier field": joined("LICENSE", "ID"),
        "private key": joined("BEGIN ", "OPEN", "SSH"),
        "rsa key": joined("BEGIN ", "RSA"),
        "solver log name": joined("solver", r"\.log"),
        "effective parameter dump": joined("effective", "_parameters.json"),
        "git worktree dump": joined("status", "_porcelain"),
        "dirty file dump": joined("dirty", "_files"),
        "machine identity field": joined("host", "name"),
        "process identity field": joined("process", "_id"),
    }
    patterns = [
        (name, re.compile(pattern, re.IGNORECASE)) for name, pattern in literal_patterns.items()
    ]
    patterns.extend(
        [
            (
                "generic credential assignment",
                re.compile(
                    r"\b(?:"
                    + joined("to", "ken")
                    + "|"
                    + joined("pass", "word")
                    + "|"
                    + joined("se", "cret")
                    + r")\b\s*[:=]\s*[^\s$<{]",
                    re.IGNORECASE,
                ),
            ),
            (
                "private email",
                re.compile(
                    r"\b[A-Z0-9._%+-]+@(?!users\.noreply\.github\.com\b)[A-Z0-9.-]+\.[A-Z]{2,}\b",
                    re.IGNORECASE,
                ),
            ),
            ("raw run identifier", re.compile(r'["](?:run' + "_id|attempt" + r'_id)["]\s*:')),
        ]
    )
    return patterns


def _check_csv_schema(path: Path) -> None:
    allowed = {
        "family",
        "instance_label",
        "size",
        "band",
        "density_cell",
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
        "block",
        "planned_slots",
        "attempted_solves",
        "terminal_records",
        "optimal",
        "suboptimal",
        "timeouts",
        "resource_skips",
        "execution_failures",
        "numerical_failures",
        "gpu_confirmed_runs",
        "strict_quality_passes",
        "diagnostic_solves",
        "notes",
        "instance_name",
        "official_source_url",
        "source_sha256",
        "creator_or_submitter",
        "license_url",
        "adaptation_notice",
    }
    with path.open("r", encoding="utf-8", newline="") as handle:
        fields = csv.DictReader(handle).fieldnames or []
    unexpected = set(fields) - allowed
    if unexpected:
        raise ValueError(f"unapproved evidence columns in {path.name}: {sorted(unexpected)}")


def scan(root: Path) -> dict[str, int]:
    material = _material_files(root)
    tracked = _tracked_files(root)
    files = tracked if tracked is not None else material
    errors: list[str] = []
    total = 0
    for path in files:
        relative = PurePosixPath(path.relative_to(root).as_posix())
        if not _allowed(relative):
            errors.append(f"path outside allowlist: {relative}")
        if path.is_symlink():
            errors.append(f"symbolic link: {relative}")
            continue
        size = path.stat().st_size
        total += size
        if size > MAX_FILE_BYTES:
            errors.append(f"file exceeds 5 MiB: {relative}")
        lowered = relative.name.lower()
        if any(lowered.endswith(suffix) for suffix in DENIED_SUFFIXES):
            errors.append(f"denied suffix: {relative}")
        if lowered in DENIED_NAMES:
            errors.append(f"denied filename: {relative}")
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"non-text tracked file: {relative}")
            continue
        for label, pattern in _signatures():
            if pattern.search(text):
                errors.append(f"{label}: {relative}")
        if relative.parent.as_posix() == "evidence" and relative.suffix == ".csv":
            try:
                _check_csv_schema(path)
            except ValueError as error:
                errors.append(str(error))
    if total > MAX_TOTAL_BYTES:
        errors.append("tracked content exceeds 25 MiB")
    if tracked is not None:
        tracked_set = {path.resolve() for path in tracked}
        extras = [path for path in material if path.resolve() not in tracked_set]
        for path in extras:
            relative = path.relative_to(root).as_posix()
            if _allowed(PurePosixPath(relative)):
                errors.append(f"untracked publication material: {relative}")
    if (root / ".gitmodules").exists():
        errors.append("submodule declaration present")
    sys.path.insert(0, os.fspath(root / "src"))
    try:
        from pdhg_benchmarks.evidence import check

        check()
    except Exception as error:  # publication gate reports a concise category only
        errors.append(f"evidence validation failed: {type(error).__name__}")
    finally:
        sys.path.pop(0)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)
    return {
        "files": len(files),
        "bytes": total,
        "largest_bytes": max(path.stat().st_size for path in files),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    report = scan(args.root.resolve())
    print(f"publication scan passed: {report['files']} files, {report['bytes']} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
