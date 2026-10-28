# Scorecard self-rating (generator), 2026-10-26 23:55 UAE: Phase 3 close-out

These are internal ratings against the EVAL.md anchors. The critic has not rated them, so every outcome stays *not assessed*. The two gate rows are rated by the critic only; the generator column records only whether the anchor's conditions appear to be met.

Changes since 22:33:
- The write-up draft (`WRITEUP.md`) now exists.
- `scripts/reproduce.py` has been run end to end as one command (`reproduce_check_EV2.md`).

| Criterion | Rating | Evidence | What moves it |
|---|---|---|---|
| Performance relative to the comparable classical baseline | 2 | Overall: no detectable change, +0.0208 [-0.0157, +0.0617]. The V_f1 slice is favorable at 98.75%, +0.0688 [+0.0207, +0.1543], with all four family members reported (E003, E007, E008) | SVDB confirmation; it moves the rating to anchor 3 only if the primary is favorable, which is not expected |
| Ingenuity | 2 | `WRITEUP.md` §3: the limitation, the literature gap, the sceptical prior with citations, and the matching rule. The controls isolate what is quantum (E004 mean-field, E005 separable); their answer is "not quantum" (A016). No hardware link yet | A Braket feasibility run (anchor 3) |
| Depth | 1 | Per-class, per-record and review-burden analysis (A015). Ablation axes: entanglement (E004, E005); readout regularisation (E009, E010/E011); reduced training data (E007, E008). Of the anchor's listed axes, only entanglement is covered | Readout size or qubit count, and shots or noise (anchor 2); device-noise simulation, a hardware subset and a kernel diagnostic (anchor 3) |
| Soundness | 2 | Patient-held-out split; equal declared budgets, with a fairness check that left the selection unchanged; record and seed CIs; lookahead checks; pre-registered order enforced; limitations in `WRITEUP.md` §6, including the 17:45 SVDB incident; critic PASS on R0 (V004); every write-up number cites an experiment or anomaly ID | Access-logged SVDB confirmation; the variant count (7 of 15 so far) published in the final write-up; critic check of claim traceability |
| Gate: deliverables complete (critic) | conditions appear met; critic check pending | All four present: code for both approaches (`src/qhc/pipe/`); comparative evaluation (`runs/tables/`); the explanation (`WRITEUP.md`, a draft); reproduction instructions (`README.md`) | Final write-up after Phase 4, then the critic's check |
| Gate: reproducible (critic) | conditions appear met; critic check pending | One command (`scripts/reproduce.py --skip-data --check`) in a fresh venv from the lockfile regenerates all 10 headline prediction files and the headline table byte-identically (`reproduce_check_EV2.md`). Fresh download with pinned hashes plus a full units build: `clean_build_EV2.md` | The critic reruns it in the reserve window, ideally in one pass including the download |
