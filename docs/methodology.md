# Methodology

## Study design

The snapshot reports six completed experimental blocks: five controlled, deterministically generated LP families and one external validation panel. The controlled ladders use six frozen size classes. The external panel contains eight performance-blind selected MIPLIB 2017 models transformed into LP relaxations by removing integrality.

Each planned controlled-family size has eight method profiles: dual simplex; barrier without crossover; PDHG on CPU at `1e-4`, `1e-6`, and `1e-8`; and PDHG on GPU at the same requested tolerances. The benchmark used one fresh process and one new solver environment per attempted solve, with 24 threads, default presolve, and a 1,200-second limit. GPU categorization required a positive runtime marker.

## Outcomes are not interchangeable

- A planned slot is a frozen matrix position.
- An attempted solve reached `Model.optimize()`.
- A terminal record is a final classification, including a pre-attempt resource skip.
- `OPTIMAL`, `SUBOPTIMAL`, and `TIME_LIMIT` are solver statuses.
- Execution and numerical failures are normalized terminal categories, not synonyms for `SUBOPTIMAL`.
- A strict quality result is separate from solver status and execution validity.

The external full audit has 64 terminal records and 64 attempted solves: 60 `OPTIMAL` plus four `SUBOPTIMAL`. The normalized categories are 60 completed, three numerical failures, and one execution failure. The latter four are solver-returned `SUBOPTIMAL` records, not crashes in the generic sense.

## Quality interpretation

The historical strict gate combines solver quality attributes with independent objective, primal-row, and bound checks. It is intentionally retained as a descriptive field even when its fixed absolute threshold is stricter than a requested PDHG profile. A quality-gate failure therefore does not by itself mean the solver failed or returned no solution.

The public `quality_value` is the solver maximum violation for controlled families and a documented descriptive maximum quality score for the external panel. Missing values remain empty; they are never imputed. Where a common independently recomputable KKT residual was unavailable, the private analysis did not invent a binary substitute.

## Certified external analysis

The certified primary subset contains dual simplex, barrier, and CPU/GPU PDHG at `1e-6` and `1e-8`: six methods across eight instances, or 48 slots. All 48 are `OPTIMAL`. The 16 PDHG CPU/GPU pairs match instance, tolerance profile, and relevant parameters. Speedup is CPU solver runtime divided by GPU solver runtime.

The `1e-4` exclusion is explicitly post-run and not preregistered. All 16 excluded rows remain summarized as diagnostics, including their four `SUBOPTIMAL` outcomes. Winner counts use the fastest solver runtime among six certified methods for each of eight instances.

## Non-claim

Relationships with rows, columns, nonzeros, density, or aspect ratio are descriptive. Results apply to the frozen models, software build, and one hardware environment; they are not a causal or predictive solver-selection model.
