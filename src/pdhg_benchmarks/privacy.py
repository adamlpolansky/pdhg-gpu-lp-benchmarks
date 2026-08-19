"""Privacy-by-construction helpers for any future public result writer."""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any

PUBLIC_METADATA_FIELDS = frozenset(
    {
        "family",
        "instance_label",
        "size",
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
        "resource_outcome",
    }
)

_LOCAL_PATH = re.compile(r"(?:[A-Za-z]:[\\/]|/(?:home|Users|mnt)/)", re.IGNORECASE)
_PRIVATE_FIELD_FRAGMENTS = (
    "host",
    "user",
    "process" + "_id",
    "pid",
    "executable",
    "dirty",
    "status" + "_porcelain",
    "run" + "_id",
    "attempt" + "_id",
    "credential",
    "pass" + "word",
    "se" + "cret",
    "to" + "ken",
    "wls" + "accessid",
    "wls" + "secret",
    "license" + "id",
)


def validate_public_record(record: Mapping[str, Any]) -> dict[str, Any]:
    """Return a plain safe record or reject it before serialization."""

    unexpected = set(record) - PUBLIC_METADATA_FIELDS
    if unexpected:
        raise ValueError(f"non-public fields: {sorted(unexpected)}")
    for key, value in record.items():
        lowered = key.lower()
        if any(fragment in lowered for fragment in _PRIVATE_FIELD_FRAGMENTS):
            raise ValueError("private metadata field")
        if isinstance(value, str) and _LOCAL_PATH.search(value):
            raise ValueError("absolute local path")
    return dict(record)
