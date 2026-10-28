# Scorecard self-rating (generator), 2026-10-26 22:33 UAE: after the complete slice family and controls (EV2)

Internal assessment against the EVAL.md anchors; not critic-rated, so the outcomes stay *not assessed*.

| Criterion | Rating | Evidence | What moves it |
|---|---|---|---|
| Performance relative to the comparable classical baseline | 2 | No detectable change overall (+0.0208 [-0.0157, +0.0617]). V_f1 is favorable at 98.75% (+0.0688 [+0.0207, +0.1543]) with all four family members reported: E003 headline, E007, E008 | SVDB confirmation, for anchor 3 only if the primary is favorable (not expected) |
| Ingenuity | 2 | README: the limitation, the literature gap and the sceptical prior, with citations. Controls isolate what is quantum (E004 mean-field, E005 separable), and their answer is "not quantum" (A016). No hardware link | A Braket feasibility run (anchor 3) |
| Depth | 1 | Per-class, per-record and review-burden analysis (A015). Ablation axes: entanglement (E004, E005) on ds2s; readout regularisation (E009, E010/E011); reduced training data (E007, E008). Only one of the anchor's listed axes (entanglement) is covered | Readout size or qubit count, and shots or noise (anchor 2); device-noise simulation and a hardware subset (anchor 3) |
| Soundness | 2 | Patient-held-out split; equal declared budgets, plus a fairness check that left the selection unchanged; record and seed CIs; lookahead checks; pre-registered order enforced; limitations logged; critic PASS on R0 (V004) | Access-logged SVDB confirmation, the published variant count (7 of 15 so far), every claim traced in the write-up |
| Gate: deliverables complete | 0 | Code for both approaches, comparative evaluation tables (`runs/tables/`) and reproduction instructions exist. The write-up is still a README paragraph | Write-up draft, then critic check |
| Gate: reproducible | 2 | Clean environment from the lockfile with a fresh download of both databases (pinned sums): 43/43 fixtures, 14/14 manifest hashes (`runs/phase3/clean_build_EV2.md`); a separate clean run regenerated every scored prediction byte-identically. `scripts/reproduce.py` exists but has not been run end to end as one command | Run `scripts/reproduce.py --check` in a fresh copy; critic check |
