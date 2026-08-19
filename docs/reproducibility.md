# Reproducibility

## Public, credential-free layer

Create a clean virtual environment and run:

```bash
python -m pip install -e ".[dev]"
python -m ruff check .
python -m pytest -q
python -m pdhg_benchmarks.demo --config configs/demo/cs_tiny.yaml
python -m pdhg_benchmarks.evidence --build
python -m pdhg_benchmarks.evidence --check
python scripts/check_publication.py
git diff --exit-code
```

The five files under `configs/demo/` exercise deterministic tiny structural analogues of every controlled family. They generate an in-memory sparse LP, verify an explicit feasibility witness, and print only a structural summary and stable digest. They do not solve the model or collect environment metadata.

`pdhg_benchmarks.evidence --build` deterministically reconstructs the three SVG files from the public CSV snapshot and refreshes SHA-256 entries in `evidence/provenance.json`. Repeating it over the same snapshot must produce a clean Git diff. `--check` independently validates schemas, denominators, claims, attribution, digests, and rendered bytes.

## Licensed integration boundary

The original measurements used Gurobi Optimizer 13.0.2, including its GPU-capable Linux build. Gurobi is proprietary and is not distributed here. The optional command below only installs the tested Python API version; it does not provide a licence, GPU hardware, benchmark models, or the private runner.

```bash
python -m pip install -e ".[gurobi]"
```

The full benchmark matrix is intentionally not rerun in public CI. Raw logs, raw records, MPS files, environment dumps, and licensed machine metadata remain in the private audit repository. The curated aggregate snapshot is tied to source checkpoint `7c3365f7e7176fb61a586a65cd806ae82c663712`.
