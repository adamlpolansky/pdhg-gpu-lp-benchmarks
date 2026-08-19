# Public evidence data dictionary

## Controlled-family result files

`cs_results.csv`, `mcf_results.csv`, `rbe_results.csv`, `cvar_results.csv`, and `rob_results.csv` each contain exactly 48 planned rows.

| Field | Meaning |
|---|---|
| `family` | Public family key. |
| `instance_label`, `size` | Sanitized family/size identity. |
| `rows`, `columns`, `nonzeros` | Materialized LP dimensions. |
| `method` | Frozen method profile. |
| `device` | `cpu` or `gpu`; GPU validity still requires `gpu_confirmed=true`. |
| `tolerance` | Requested PDHG profile; empty for dual simplex and barrier. |
| `planned_slot` | Whether the row belongs to the frozen matrix. |
| `attempted_solve` | Whether the solver optimization call began. |
| `terminal_outcome` | Completed, time limit, or pre-attempt resource skip. |
| `solver_status` | Solver-returned status; empty when no solve was attempted. |
| `runtime_s` | Solver runtime in seconds; empty for pre-attempt skips. |
| `quality_metric`, `quality_value` | Named public quality statistic and value when available. |
| `strict_quality_pass` | Historical common absolute gate; empty when not evaluated. |
| `gpu_confirmed` | Positive GPU-use evidence for an attempted GPU row. |
| `resource_outcome` | Sanitized resource classification without machine paths or process metadata. |

## External files

`external_primary_results.csv` has 48 certified rows and adds public instance name, nonzero band, and density cell. Its quality value is a descriptive maximum quality score. `external_diagnostic_summary.json` preserves denominators and the post-run status of the `1e-4` diagnostic set without exposing raw identifiers.

`external_attribution.csv` provides the public source URL, source digest, creator or submitter, per-instance licence URL, and LP-relaxation adaptation notice for each of the eight models. No model file is redistributed.

## Status and provenance

`experiment_status.csv` is the six-block denominator ledger. `analysis_validation.json` records checks on the aggregate analysis only. `provenance.json` records the private source checkpoint, checkpoint identities, deterministic seeds, curated solver/hardware contract, transformations, exclusions, and SHA-256 values for every other evidence file and each SVG asset. It excludes its own digest to avoid a circular checksum.
