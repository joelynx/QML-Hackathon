# Scorecard self-rating (generator), 2026-10-26 ~19:45 UAE: Phase 3 slice before the headline run

Internal assessment against the EVAL.md anchors; not yet rated by the critic, so every outcome is *not assessed*.

| Criterion | Rating | Evidence today | What moves it |
|---|---|---|---|
| Performance vs comparable classical baseline | 0 | No matched comparison on ds2s yet (waits for EV1 approval). DS1 OOF proxy: QRC 0.667 vs ESN 0.662, CI [-0.044, +0.066] | Run the headline E003 vs E002 (anchor 1 at least) |
| Ingenuity | 2 | Training-free physical feature map for inter-patient ECG; controls that isolate what is quantum exist (E004 mean-field, E005 separable); literature gap in PROBLEM_BRIEF.md | A Braket hardware feasibility run (anchor 3) |
| Depth | 1 | Per-class metrics; one ablation axis (entanglement: mean-field and separable); mechanism finding A012 on DS1 | Readout size, qubit count, shots and noise axes; per-patient analysis; device-noise simulation |
| Soundness | 2 | Patient-held-out split; equal declared budgets (N = 30 each); lookahead checks passed for every arm; seed-noise diagnostic passed; two-level bootstrap ready; limitations logged (A009-A012) | Access-logged SVDB confirmation, critic PASS, published variant count |
| Gate: deliverables complete | 0 | Code for both approaches and README exist; comparative evaluation and write-up missing | Headline + write-up |
| Gate: reproducible | 1 | README lists every command; not one command; clean environment untested | One script that regenerates the headline tables; clean-environment run |
