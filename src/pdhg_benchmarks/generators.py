"""Deterministic, tiny LP generators representing the five controlled families.

These demos preserve each family's structural idea but intentionally do not recreate the
licensed benchmark runs or large materialized models.
"""

from __future__ import annotations

import random
from collections.abc import Callable, Mapping

from .model import Constraint, SparseLP

Config = Mapping[str, int | float | str]


def _bounds(
    count: int, upper: float | None = None
) -> tuple[tuple[float, ...], tuple[float | None, ...]]:
    return (tuple(0.0 for _ in range(count)), tuple(upper for _ in range(count)))


def cutting_stock(config: Config) -> SparseLP:
    rng = random.Random(int(config.get("seed", 11)))
    items = int(config.get("items", 4))
    stock_length = int(config.get("stock_length", 20))
    widths = [2 + rng.randrange(max(2, stock_length // 3)) for _ in range(items)]
    patterns: list[tuple[int, ...]] = []
    for item, width in enumerate(widths):
        pattern = [0] * items
        pattern[item] = stock_length // width
        patterns.append(tuple(pattern))
    for shift in range(items):
        remaining = stock_length
        pattern = [0] * items
        for item in range(items):
            index = (item + shift) % items
            units = min(2, remaining // widths[index])
            pattern[index] = units
            remaining -= units * widths[index]
        if any(pattern) and tuple(pattern) not in patterns:
            patterns.append(tuple(pattern))
    demands = [1 + rng.randrange(3) for _ in range(items)]
    witness = [0.0] * len(patterns)
    for item, demand in enumerate(demands):
        witness[item] = float((demand + patterns[item][item] - 1) // patterns[item][item])
    constraints = tuple(
        Constraint(
            tuple(
                (column, float(pattern[item]))
                for column, pattern in enumerate(patterns)
                if pattern[item]
            ),
            ">=",
            float(demands[item]),
            f"demand_{item}",
        )
        for item in range(items)
    )
    lower, upper = _bounds(len(patterns))
    return SparseLP(
        family="cutting-stock",
        variable_names=tuple(f"pattern_{i}" for i in range(len(patterns))),
        objective=tuple(1.0 for _ in patterns),
        lower_bounds=lower,
        upper_bounds=upper,
        constraints=constraints,
        witness=tuple(witness),
        metadata={"seed": int(config.get("seed", 11)), "stock_length": stock_length},
    )


def multicommodity_flow(config: Config) -> SparseLP:
    nodes = int(config.get("nodes", 6))
    commodities = int(config.get("commodities", 3))
    if nodes < 4:
        raise ValueError("nodes must be at least 4")
    names = tuple(
        f"flow_{commodity}_{arc}" for commodity in range(commodities) for arc in range(nodes)
    )
    witness = [0.0] * len(names)
    constraints: list[Constraint] = []
    for commodity in range(commodities):
        source = commodity % nodes
        sink = (source + 2) % nodes
        witness[commodity * nodes + source] = 1.0
        witness[commodity * nodes + ((source + 1) % nodes)] = 1.0
        for node in range(nodes):
            outgoing = commodity * nodes + node
            incoming = commodity * nodes + ((node - 1) % nodes)
            rhs = 1.0 if node == source else -1.0 if node == sink else 0.0
            constraints.append(
                Constraint(
                    ((outgoing, 1.0), (incoming, -1.0)), "=", rhs, f"balance_{commodity}_{node}"
                )
            )
    for arc in range(nodes):
        coefficients = tuple((commodity * nodes + arc, 1.0) for commodity in range(commodities))
        used = sum(witness[index] for index, _ in coefficients)
        constraints.append(Constraint(coefficients, "<=", max(2.0, used), f"capacity_{arc}"))
    lower, upper = _bounds(len(names))
    rng = random.Random(int(config.get("seed", 11)))
    return SparseLP(
        family="multicommodity-flow",
        variable_names=names,
        objective=tuple(0.5 + rng.random() for _ in names),
        lower_bounds=lower,
        upper_bounds=upper,
        constraints=tuple(constraints),
        witness=tuple(witness),
        metadata={"seed": int(config.get("seed", 11)), "nodes": nodes, "commodities": commodities},
    )


def random_bounded_equality(config: Config) -> SparseLP:
    seed = int(config.get("seed", 11))
    columns = int(config.get("columns", 12))
    rows = int(config.get("rows", columns // 2))
    degree = int(config.get("column_degree", 2))
    if rows < degree or columns < 2:
        raise ValueError("invalid sparse equality dimensions")
    topology = random.Random(seed * 101 + 1)
    coefficients_rng = random.Random(seed * 101 + 2)
    witness_rng = random.Random(seed * 101 + 3)
    objective_rng = random.Random(seed * 101 + 4)
    row_coefficients: list[list[tuple[int, float]]] = [[] for _ in range(rows)]
    for column in range(columns):
        chosen = topology.sample(range(rows), degree)
        for row in chosen:
            coefficient = 1.0 if coefficients_rng.randrange(2) else -1.0
            row_coefficients[row].append((column, coefficient))
    witness = tuple(0.1 + 0.8 * witness_rng.random() for _ in range(columns))
    constraints = tuple(
        Constraint(tuple(values), "=", sum(witness[j] * a for j, a in values), f"row_{row}")
        for row, values in enumerate(row_coefficients)
    )
    lower, upper = _bounds(columns, 1.0)
    objective = tuple(1.0 if objective_rng.randrange(2) else -1.0 for _ in range(columns))
    return SparseLP(
        family="random-bounded-equality",
        variable_names=tuple(f"x_{column}" for column in range(columns)),
        objective=objective,
        lower_bounds=lower,
        upper_bounds=upper,
        constraints=constraints,
        witness=witness,
        metadata={"seed": seed, "stream_count": 4, "column_degree": degree},
    )


def cvar_portfolio(config: Config) -> SparseLP:
    seed = int(config.get("seed", 11))
    assets = int(config.get("assets", 4))
    scenarios = int(config.get("scenarios", 8))
    beta = float(config.get("beta", 0.95))
    cap = float(config.get("cap", 0.6))
    if not 0.0 < beta < 1.0 or assets * cap < 1.0:
        raise ValueError("invalid CVaR beta or cap")
    rng = random.Random(seed)
    returns = [[-0.03 + 0.06 * rng.random() for _ in range(assets)] for _ in range(scenarios)]
    names = tuple(
        [f"weight_{j}" for j in range(assets)]
        + ["alpha"]
        + [f"excess_{s}" for s in range(scenarios)]
    )
    alpha_index = assets
    witness_weights = [1.0 / assets] * assets
    losses = [-sum(row[j] * witness_weights[j] for j in range(assets)) for row in returns]
    alpha = max(losses)
    witness = tuple(witness_weights + [alpha] + [0.0] * scenarios)
    constraints: list[Constraint] = [
        Constraint(tuple((j, 1.0) for j in range(assets)), "=", 1.0, "budget")
    ]
    for scenario, row in enumerate(returns):
        coefficients = [(j, -row[j]) for j in range(assets)]
        coefficients.extend(((alpha_index, -1.0), (assets + 1 + scenario, -1.0)))
        constraints.append(Constraint(tuple(coefficients), "<=", 0.0, f"tail_{scenario}"))
    lower = tuple([0.0] * assets + [None] + [0.0] * scenarios)
    upper = tuple([cap] * assets + [None] * (scenarios + 1))
    objective = tuple([0.0] * assets + [1.0] + [1.0 / ((1.0 - beta) * scenarios)] * scenarios)
    return SparseLP(
        family="cvar-portfolio",
        variable_names=names,
        objective=objective,
        lower_bounds=lower,
        upper_bounds=upper,
        constraints=tuple(constraints),
        witness=witness,
        metadata={"seed": seed, "assets": assets, "scenarios": scenarios, "beta": beta, "cap": cap},
    )


def robust_production_inventory(config: Config) -> SparseLP:
    seed = int(config.get("seed", 11))
    horizon = int(config.get("horizon", 5))
    capacity = float(config.get("capacity", 8.0))
    rng = random.Random(seed)
    worst_demands = [2.0 + rng.random() for _ in range(horizon)]
    names = tuple(
        [f"production_{t}" for t in range(horizon)] + [f"inventory_{t}" for t in range(horizon)]
    )
    witness = [0.0] * (2 * horizon)
    constraints: list[Constraint] = []
    for period, demand in enumerate(worst_demands):
        witness[period] = demand
        coefficients = [(period, 1.0), (horizon + period, -1.0)]
        if period:
            coefficients.append((horizon + period - 1, 1.0))
        constraints.append(Constraint(tuple(coefficients), "=", demand, f"balance_{period}"))
        constraints.append(Constraint(((period, 1.0),), "<=", capacity, f"capacity_{period}"))
    lower = tuple([0.0] * (2 * horizon))
    upper = tuple([capacity] * horizon + [None] * horizon)
    objective = tuple([1.0 + 0.1 * period for period in range(horizon)] + [0.05] * horizon)
    return SparseLP(
        family="robust-production-inventory",
        variable_names=names,
        objective=objective,
        lower_bounds=lower,
        upper_bounds=upper,
        constraints=tuple(constraints),
        witness=tuple(witness),
        metadata={"seed": seed, "horizon": horizon, "uncertainty": "box-upper-envelope"},
    )


FAMILY_GENERATORS: dict[str, Callable[[Config], SparseLP]] = {
    "cs": cutting_stock,
    "mcf": multicommodity_flow,
    "rbe": random_bounded_equality,
    "cvar": cvar_portfolio,
    "rob": robust_production_inventory,
}


def generate_demo(config: Config) -> SparseLP:
    family = str(config.get("family", ""))
    try:
        generator = FAMILY_GENERATORS[family]
    except KeyError as error:
        raise ValueError(f"unknown demo family: {family!r}") from error
    return generator(config)
