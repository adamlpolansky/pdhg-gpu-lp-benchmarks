"""Common structural and witness validation for portable demo LPs."""

from __future__ import annotations

import math
from typing import Any

from .model import SparseLP


def _row_violation(lhs: float, sense: str, rhs: float) -> float:
    if sense == "<=":
        return max(0.0, lhs - rhs)
    if sense == ">=":
        return max(0.0, rhs - lhs)
    return abs(lhs - rhs)


def validate_instance(model: SparseLP, tolerance: float = 1e-10) -> dict[str, Any]:
    columns = len(model.variable_names)
    if not columns or len(set(model.variable_names)) != columns:
        raise ValueError("variable names must be non-empty and unique")
    vectors = (model.objective, model.lower_bounds, model.upper_bounds, model.witness)
    if any(len(values) != columns for values in vectors):
        raise ValueError("all column vectors must match the variable count")
    if any(not math.isfinite(value) for value in model.objective + model.witness):
        raise ValueError("objective and witness values must be finite")
    bound_violation = 0.0
    for value, lower, upper in zip(
        model.witness, model.lower_bounds, model.upper_bounds, strict=True
    ):
        if lower is not None:
            bound_violation = max(bound_violation, lower - value)
        if upper is not None:
            bound_violation = max(bound_violation, value - upper)
    row_violation = 0.0
    nonzeros = 0
    for row in model.constraints:
        indices = [index for index, _ in row.coefficients]
        if len(indices) != len(set(indices)) or any(
            index < 0 or index >= columns for index in indices
        ):
            raise ValueError(f"invalid sparse indices in {row.name}")
        nonzeros += len(row.coefficients)
        lhs = sum(model.witness[index] * coefficient for index, coefficient in row.coefficients)
        row_violation = max(row_violation, _row_violation(lhs, row.sense, row.rhs))
    max_violation = max(0.0, row_violation, bound_violation)
    return {
        "family": model.family,
        "rows": len(model.constraints),
        "columns": columns,
        "nonzeros": nonzeros,
        "max_constraint_violation": max(0.0, row_violation),
        "max_bound_violation": max(0.0, bound_violation),
        "witness_feasible": max_violation <= tolerance,
        "sha256": model.sha256(),
    }
