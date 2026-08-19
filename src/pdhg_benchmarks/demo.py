"""Credential-free command-line demo for deterministic tiny LP generation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .generators import generate_demo
from .validators import validate_instance


def run(config_path: Path) -> dict[str, object]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict):
        raise ValueError("demo config must be a JSON-compatible YAML mapping")
    model = generate_demo(config)
    report = validate_instance(model)
    if not report["witness_feasible"]:
        raise RuntimeError("generated witness failed validation")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.config), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
