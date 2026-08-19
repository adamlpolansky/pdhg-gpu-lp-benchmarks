"""Small, solver-independent sparse LP representation used by public demos."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Literal

Sense = Literal["<=", ">=", "="]


@dataclass(frozen=True)
class Constraint:
    """One sparse linear constraint."""

    coefficients: tuple[tuple[int, float], ...]
    sense: Sense
    rhs: float
    name: str


@dataclass(frozen=True)
class SparseLP:
    """A compact LP plus an explicit feasibility witness."""

    family: str
    variable_names: tuple[str, ...]
    objective: tuple[float, ...]
    lower_bounds: tuple[float | None, ...]
    upper_bounds: tuple[float | None, ...]
    constraints: tuple[Constraint, ...]
    witness: tuple[float, ...]
    metadata: dict[str, int | float | str] = field(default_factory=dict)

    def canonical_payload(self) -> dict[str, object]:
        return {
            "family": self.family,
            "variable_names": self.variable_names,
            "objective": self.objective,
            "lower_bounds": self.lower_bounds,
            "upper_bounds": self.upper_bounds,
            "constraints": [
                {
                    "coefficients": row.coefficients,
                    "sense": row.sense,
                    "rhs": row.rhs,
                    "name": row.name,
                }
                for row in self.constraints
            ],
            "witness": self.witness,
            "metadata": self.metadata,
        }

    def sha256(self) -> str:
        payload = json.dumps(
            self.canonical_payload(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
