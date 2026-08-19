# Limitations and non-claims

- The study is a bounded case study on frozen LPs, one Gurobi build, and one hardware/software environment.
- GPU PDHG is not always fastest; two of the 16 certified matched pairs favor CPU PDHG.
- Matched-profile speedup does not measure time-to-common-quality.
- The primary external subset uses a post-run exclusion of tolerance `1e-4`; it is labeled rather than presented as preregistered.
- A terminal record can be a time limit, resource skip, numerical failure, or execution failure instead of an `OPTIMAL` solve.
- Time limits are censored outcomes, not execution crashes.
- A historical strict quality-gate failure is not equivalent to solver failure or lack of a solution.
- Basis availability differs by algorithm; no-basis barrier or PDHG output is not automatically non-optimal.
- The MCF XXXL block was skipped before attempt after a RAM safety gate. Those eight planned slots remain visible.
- Public CI validates code, aggregate evidence, figures, and publication hygiene. It cannot reproduce the licensed GPU campaign.
- Adam Luboš Polanský designed and implemented the experimental pipeline and analysis around Gurobi; he did not implement Gurobi PDHG or a CUDA solver kernel.
- `ready_to_share` in the evidence validation file means the sanitized analysis is internally consistent. It is not a repository-security conclusion.
