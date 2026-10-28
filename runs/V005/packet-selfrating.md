# V005 generator self-rating (open only after recording your own ratings)

Coordinator, 2026-10-28 ~20:12 UAE, against the EVAL.md scorecard anchors.

| Criterion | Rating | Reason |
|---|---|---|
| Performance | 2 | No detectable change overall; slice-family member V_f1 has 98.75% CI lower bound > 0, all four reported. Not 3: primary not favorable and SVDB not confirmed (E018). |
| Ingenuity | 3 | Limitation, literature gap (scoped to our search), mean-field and separable controls, and a real-hardware feasibility link (E019). |
| Depth | 3 | Ablations along entanglement (E005), readout size and qubit count (E014), shots (E012/E013), noise (E015); device-noise simulation and a real-hardware subset; per-patient/per-class analysis (A015) and a kernel/geometric diagnostic (E017). |
| Soundness | 3 if the critic passes, else 2 | Patient-held-out split, equal tuning, two-level CIs, lookahead checks, access-logged external confirmation run and reported as not confirmed, variant count published, claims traceable. Needs a critic PASS for 3. |
| Gate: deliverables complete | 3 (critic's check) | All four brief items present in the repository. |
| Gate: reproducible | 2 unless the critic checks a clean environment + fresh download | One command (`scripts/reproduce.py`); clean-environment check run by the coordinator, not yet by a critic. |
