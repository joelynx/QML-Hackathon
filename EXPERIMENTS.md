# Experiments

One card per experiment, including failures, null results, and aborted runs. Keep raw outputs in `runs/<E###>/` and link them; don't paste them here. For a sweep, make one parent card and link a machine-readable manifest of the child runs. A "line" is the sequence of experiments pursuing the same idea and selected against the same validation units; "variants attempted in this line" counts failed runs and sweep members too.

## Index
| ID | One line | Type | Outcome | Verification | Adoption |
|---|---|---|---|---|---|
| E001 | Input-encoding probe on DS1: raw window vs patient-relative window vs RR only, one untuned ESN and QRC config | diagnostic | not assessed | not requested | n/a |
| E002 | R0: matched leaky-tanh ESN arm (DS1 tuning N = 30, 5 seeds); ds2s macro-F1 0.7065 (seed mean, baseline arm of the headline) | full (EV1) | not assessed (R0, no baseline) | **pass** (V004, validity-only) | **incumbent** (R0) |
| E003 | First quantum arm: 10-qubit finite-shot QRC (DS1 tuning N = 30, 5 seeds); **headline E003 vs E002: +0.0208 [-0.0157, +0.0617]** (EV1, rerun identically under EV2); slice family complete: V_f1 favorable, S_f1 / lowdata_k5 / lowdata_k11 no detectable change | full (EV1, EV2) | no detectable change (primary); V_f1 slice favorable | not requested | candidate |
| E004 | Control: classical-spin (mean-field) reservoir of E003's configuration, 5 seeds; **E003 vs E004 +0.0039 [-0.0028, +0.0115]** | full (EV2, secondary) | no detectable change | not requested | n/a |
| E005 | Control: separable QRC (E003's configuration with J = 0), 5 seeds; **E005 vs E003 -0.0009 [-0.0444, +0.0319]**; V F1 -0.063 [-0.132, -0.021] | full (EV2, secondary) | no detectable change | not requested | n/a |
| E006 | Control: readout on the 8 RR features alone (single deterministic run); ds2s macro-F1 0.6997 | full (EV2, `score`, descriptive) | not assessed (single run, no interval) | not requested | n/a |
| E007 | Reduced-data refit k = 5 (records 101, 122, 209, 215, 223) of both headline arms, 5 seeds each; **lowdata_k5 -0.0086 [-0.0858, +0.0794]** | full (EV2, `lowdata_k5`) | no detectable change | not requested | n/a (slice member) |
| E008 | Reduced-data refit k = 11 of both headline arms, 5 seeds each; **lowdata_k11 -0.0308 [-0.1045, +0.0546]** | full (EV2, `lowdata_k11`) | no detectable change | not requested | n/a (slice member) |
| E009 | Matched-λ diagnostic on DS1 OOF: both headline arms at every λ of the declared grid (A015) | diagnostic (DS1 OOF) | not assessed | not requested | n/a |
| E010 | A010 fairness check: ESN retuned over the same 30 configurations with the extended readout grid λ ∈ {1e-5, ..., 1}; **same selection as E002 (cfg28, λ 0.001); predictions byte-identical** | proxy (DS1 OOF) | not assessed | not requested | n/a |
| E011 | A010 fairness check, quantum side: QRC retuned the same way; **same selection as E003 (cfg15, λ 0.1); predictions byte-identical** | proxy (DS1 OOF) | not assessed | not requested | n/a |
| E012 | I004: exact-expectation QRC (shots = None), E003 configuration, 5 seeds; ds2s secondary vs E003 | proxy; full (EV2, secondary): E012 vs E003 +0.0005 [-0.0058, +0.0081] | no detectable change | pass (V005, validity) | n/a |
| E013 | I004: shot sweep {64, 256, 4096} at E003's configuration and lambda, DS1 OOF | proxy: 64 shots 0.648, 256 0.660, 1,024 0.667, 4,096 0.668, exact 0.669 | not assessed | pass (V005, validity) | n/a |
| E014 | I007: qubit count {6, 8, 12} and Z-only readout ablations; DS1-rule variant to ds2s secondary vs E003 | proxy; full (EV2, secondary): n6 selected (DS1 0.680); E014-n6 vs E003 +0.0078 [-0.0055, +0.0188] | no detectable change | pass (V005, validity) | n/a |
| E015 | I005: device-noise simulation (Rigetti Cepheus, IQM Garnet calibration); Rigetti to ds2s secondary vs E003 | proxy; full (EV2, secondary): Rigetti-noise vs E003 +0.0016 [-0.0331, +0.0248]; V F1 -0.053 [-0.114, -0.020] | no detectable change | pass (V005, validity) | n/a |
| E016 | I009 (review P1): gradient-boosting context model on window + RR, N = 30 DS1 budget; ds2s secondary vs E003 and E002 | proxy; full (EV2, secondary): E003 vs E016 +0.0057 [-0.1389, +0.0676] (w/o 232 -0.087); E002 vs E016 -0.0151 [-0.1896, +0.0766]; E016 V F1 0.943 | no detectable change | pass (V005, validity) | n/a |
| E017 | I008: kernel-target alignment, CKA and geometric difference of the feature maps on DS1 | diagnostic: CKA QRC-mean-field 0.986, QRC-ESN 0.525 | not assessed | pass (V005, validity) | n/a |
| E018 | SVDB confirmation of the frozen headline pair E003 vs E002 via the A018 predict-only path | full (EV2, confirmation): SVDB 0.6402 vs 0.6488 | not confirmed (delta -0.0085 [-0.0476, +0.0274]) | pass (V005, validity) | n/a |
| E019 | I006: Braket hardware features of E003's seed-0 circuit on a label-free ds2s subset | diagnostic: hardware vs exact features MAD 0.347, corr 0.70; class agreement 41.7% (ceiling 87.5%); USD 17.71 est. | not assessed | pass (V005, validity) | n/a |

## Declarations made before any tuning run (2026-10-26 ~19:15 UAE; EVAL.md matched-baseline rules 1-4)

Code: `src/qhc/pipe/` (pipeline revision `cf7bd4bd0a9634f8` at declaration; every run manifest records the revision it ran with). Evaluation: EV1 draft r5 (code `9a1922c8898b90db`), not yet approved; tuning uses DS1 only.

- **Shared pipeline (both arms, rule 1):**
  - Prediction set and units: EV1 `positions_ds1.csv` / `labels_ds1.csv`; training uses the N/S/V units of DS1 only.
  - Beat window: MLII by lead name, [t − 0.25 s, t + 0.45 s], bin-averaged to L = 40 points, minus median, divided by its sd (`features.beat_windows`).
  - **Reservoir input:** the patient-relative window = window minus the element-wise median of the previous 32 windows of the same record (`features.relative_windows`; chosen on E001's DS1 evidence before tuning). It is fed as 4 chunks of 10 samples, one per step; each beat starts from a fixed initial state.
  - RR block (8 features, shared, `features.rr_features`): pre-RR, post-RR, 10-beat mean RR, and log-ratios of pre/avg10, post/avg10, pre/post, avg10/avg50, and amplitude relative to the previous 32 beats.
  - Lookahead check: features pass `qhc.leakcheck` on 731 beats in DS1 records 207, 209, 114 and 201 (first 150 s); every arm's full pipeline is checked again before its first full evaluation (`run.py leakcheck`).
- **Readout (rule 1, rule 3):** standardised [K reservoir features | 8 RR features] -> class-balanced multinomial logistic regression with L2, full-batch L-BFGS (`readout.Readout`). Nested grid λ ∈ {0.001, 0.01, 0.1, 1}, the only readout search. Decision = argmax. Identical in both arms.
- **Readout dimension (rule 2):** K = 220 for both arms, fixed now. QRC: ⟨Z_q⟩ (10) and ⟨Z_q Z_r⟩ (45) after each of 4 steps. ESN: the first 55 units after each of 4 steps.
- **Search spaces (rule 3), N = 30 configurations per arm, drawn i.i.d. with numpy `default_rng(20261026)` in the key order below (`run.sample_configs`):**
  - **ESN** (`reservoirs.ESN`): size ∈ {55, 110, 220} (uniform choice); spectral radius ρ ~ U[0.5, 1.2]; leak rate ~ U[0.1, 1.0]; input scaling ~ log-U[0.1, 2.0]; density ~ U[0.05, 1.0]; bias scale ~ U[0, 1].
  - **QRC** (`reservoirs.QRC`, 10 qubits, statevector on GPU, 1,024 Z-basis shots per circuit per beat, per-beat deterministic shot streams): input scale (RY angle per unit input) ~ log-U[0.1, 2.0]; coupling J ~ U[0.1, 1.5]; transverse field h ~ U[0.1, 1.5]; depth (ZZ + RX layers per input step) ∈ {1, 2, 3}; topology ∈ {chain, ring}; coupling disorder ~ U[0, 1].
  - Every configuration in either space yields exactly K = 220 features.
- **Tuning protocol (rule 3):** each configuration is scored with reservoir seed 0 (and shot seed 0 for QRC) by pooled out-of-fold macro-F1 over the DS1 N/S/V units on the fixed folds `ds1_folds.json` (a *proxy* result). The configuration score is the best over the λ grid. The best (configuration, λ) wins; ties go to the lower index. No other selection, no reading of ds2s, ds2 or svdb.
- **Final runs:** seed indices 0-4 in both arms (rule 1). Reservoir seed s; QRC shot seed 1000 + s. The readout is refitted on all DS1 units with the selected λ. Model artifacts and run manifests per seed in `runs/E00X/`. Seed 0 is the tuning reservoir draw in both arms (a small, symmetric selection effect on DS1 only).
- **Seed-noise diagnostic (EVAL.md):** E002 seeds 0-4 against E002 seeds 5-9 on pooled DS1 out-of-fold predictions, `compare --split ds1 --role diagnostic`.
- **Headline pair (rule 4), named before any run:** candidate **E003** (QRC, 5 seeds) against baseline **E002** (ESN R0, 5 seeds) on ds2s, `compare --role headline`. It runs only after the author approves the evaluation version, and only after both arms pass the full-pipeline lookahead check.

## E001
- **Date:** 2026-10-26 ~18:55-19:00 UAE
- **Idea / anomaly links:** A009
- **Hypothesis and predeclared decision criterion:** exploratory, no criterion; the aim was to choose the shared reservoir input before tuning. Recorded as a design probe.
- **Change:** linear readout on RR only, raw window + RR, patient-relative window + RR, raw + relative + RR, and one untuned ESN and QRC configuration on either input.
- **Result type:** diagnostic (DS1 grouped-CV out-of-fold macro-F1; seed 0; no test data)
- **Candidate revision + config:** pipeline before declaration (no hash recorded; the scripts are inline commands in `runs/probes/P01_morphology/stdout.txt`). ESN: size 220, ρ 0.9, leak 0.5, input scale 0.5, density 0.2, bias 0.2. QRC: input scale 1.0, J 0.5, h 0.7, depth 2, ring, disorder 0.5, 1,024 shots.
- **Comparison baseline:** none (diagnostic)
- **Component / dependency parents:** none
- **Evaluation version / data and split IDs:** EV1 draft r4 data (DS1 rebuilt after R1); `ds1_folds.json`
- **Environment and exact command:** inline Python (copied in `runs/probes/P01_morphology/stdout.txt`)
- **Seeds / repetitions / variants attempted in this line:** 6 feature sets x 5 λ values, one seed each
- **Raw results and artifacts:** `runs/probes/P01_morphology/scores.json`, `stdout.txt`
- **Baseline score / candidate score / signed delta:** OOF macro-F1 at the best λ: RR only 0.637; raw window + RR 0.546; relative window + RR 0.619; raw + relative + RR 0.553; ESN(relative) + RR 0.634; QRC(relative) + RR 0.600. Earlier, on raw windows: ESN + RR 0.522, QRC + RR 0.537.
  - Per class (RR only vs ESN(relative) + RR): S F1 0.269 vs 0.240; V F1 0.669 vs 0.703; S sensitivity 0.524 vs 0.663 with S PPV 0.181 vs 0.146.
- **Uncertainty (method from EVAL.md):** none (single seed, proxy).
- **Segments and resource changes:** under 2 min of GPU time in total.
- **Mechanism check:** features finite; the simulator matches an independent dense-matrix implementation to 4e-7; shot-noise sd 0.030, as expected from 1,024 shots.
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** not assessed (diagnostic)
- **Verification:** not requested
- **Adoption:** n/a. Decision taken from it: both arms use the patient-relative window as reservoir input.
- **Limitations and next action:** one untuned configuration per reservoir; DS1-only evidence. RR alone is competitive with every reservoir (A009), so the R0 slice may not beat an RR-only readout.

## E002
- **Date:** 2026-10-26
- **Idea / anomaly links:** none (the R0 reference of Phase 3)
- **Hypothesis and predeclared decision criterion:** none; R0 is the reference. Validity-only verification after its ds2s score exists.
- **Change:** matched leaky-tanh ESN arm as declared above.
- **Result type:** proxy (DS1 tuning); **full** on ds2s as the baseline arm of the headline comparison (EV1 approved r5)
- **Candidate revision + config:** selected ESN configuration 28 of 30: size 55, ρ 0.680, leak 0.102, input scale 0.980, density 0.054, bias 0.537; λ = 0.001 (the lower edge of the declared grid, A010). Tuning ran with pipeline revision `cf7bd4bd0a9634f8`: the code the processes loaded at launch. It was verified by rebuilding the launch-time files in `runs/E002/pipe_at_tuning/`, whose raw-bytes hash is `cf7bd4bd0a9634f8` and line-ending-normalised hash `0b21d3899b1cac7b`. The `pipe_revision` field in `tuning.jsonl` is wrong for most lines: it was read from disk when each line was written, and files were edited during the run (feature loading for SVDB, the demo). None of those edits touched code the tuning executes. `run.py` now records the revision at process start. Final runs: pipeline `da67af87f8b8fd73`, evaluation `9a1922c8898b90db` (in every run manifest). Between tuning and the final runs, the ESN and the readout's prediction step were switched to float64 to make outputs batch-invariant (A011); the model definition did not change.
- **Comparison baseline:** none (R0)
- **Component / dependency parents:** none
- **Evaluation version / data and split IDs:** EV1 (approved r5, evaluation revision `9a1922c8898b90db`); ds1 for tuning; ds2s via the headline
- **Environment and exact command:** `python -I -m qhc.pipe.run tune --arm esn --exp E002`; then `final --exp E002 --seeds 0 1 2 3 4 --oof --splits ds2s` and `--seeds 5 6 7 8 9 --oof` for the seed-noise diagnostic
- **Seeds / repetitions / variants attempted in this line:** 30 configurations (seed 0) + 10 final seeds
- **Raw results and artifacts:** `runs/E002/`: `tuning.jsonl` and `tune_stdout.txt` (30 configurations); `selected_config.json`; `model_seed{0..9}.npz` (seed 0 sha256 prefix `0f5b4333465d9e48`); `oof_ds1_seed{0..9}.csv`; `pred_ds2s_seed{0..4}.csv` with `.run.json` manifests; `leakcheck_seed0.json`; `seed_noise_ds1.json`; ds2s scores in `runs/E003/compare_ds2s_headline.json` (arm `baseline`). Reproduction with pipeline `75e043aa9915baf2` (current at 21:30): `runs/R0_repro_75e043aa/`, all 5 seeds' ds2s and DS1 OOF predictions and model arrays bit-identical.
- **Baseline score / candidate score / signed delta:** R0 has no baseline. **Full (EV1, ds2s, 21 records, 47,129 units):** macro-F1 0.7065 (seed mean; per seed 0.7047, 0.7058, 0.7162, 0.7027, 0.7030). Seed-averaged sensitivity / PPV / F1: N 0.907 / 0.985 / 0.944; S 0.595 / 0.269 / 0.370; V 0.953 / 0.697 / 0.805. Paper-compatible (de Chazal Table V): VEB Se 0.953, +P 0.697, FPR 0.030; SVEB Se 0.595, +P 0.268, FPR 0.063. Review burden: 806 S-or-V flags per hour, of which 374 on normal beats; 57 missed ectopic beats per hour. DS1 OOF tuning (proxy, seed 0): best 0.6744, median of 30 configurations 0.643, range 0.599-0.674.
- **Uncertainty (method from EVAL.md):** seed-noise diagnostic (DS1 OOF, seeds 0-4 vs 5-9): +0.0039 [-0.015, +0.022], not triggered. ds2s intervals are on the headline comparison (E003).
- **Segments and resource changes:** tuning 370 s of compute; final runs about 10 s per seed.
- **Mechanism check:** full-pipeline lookahead check on 731 DS1 beats (records 207, 209, 114, 201): **passed** after the float64 change. The first attempt flagged 2 beats with probability differences of 1.8e-7 and 2.2e-8, which appeared with truncation alone (A011). The headline inputs pass every pre-label check of the evaluation command (dry run, no labels read). **Clean environment (2026-10-26 21:29-21:56, scratchpad copy, fresh venv from the lockfile, fresh MIT-BIH download):** the units match the project manifest. Retuning selects the same configuration and λ. Every ds2s and DS1 OOF prediction file of E002 and E003 is byte-identical to the scored ones. The E002 tuning scores differ by at most 3.3e-4, because the project's tuning predates the float64 switch (A011). Details: `runs/E002/packet.md`, "Clean-environment results". **One-command reproduction (EV2 code, pipeline `55884b1fb66732b9`, 23:23-23:49):** `scripts/reproduce.py --skip-data --check` in a fresh venv: 43/43 fixtures; the same selections in both arms; lookahead checks passed; all 10 headline prediction files identical to the logged hashes; headline table byte-identical; no test-split scoring (`runs/phase3/reproduce_check_EV2.md`). **Full clean build with SVDB (EV2 code, 22:15-22:32):** fresh download of both databases against the pinned sums-file hashes (144 + 234 files); full units build with all 14 output hashes equal to the project manifest; 43 of 43 fixtures pass (`runs/phase3/clean_build_EV2.md`).
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** not assessed (R0 has no baseline)
- **Verification:** **pass**: V004 (validity-only review, 2026-10-26 21:53-22:06; `VERIFICATIONS.md`, `runs/V004/`). The reviewer reran tuning, finals and the lookahead check with pipeline `55884b1fb66732b9`. It reproduced every ds2s prediction file byte-identically to the logged headline inputs, and every DS1 OOF file and model array. It ran no ds2s scoring. Findings, none blocking: M1, the packet named `ad80a50e` as the current revision while `55884b1f` was on disk (the rerun used `55884b1f`); M2, the tuning scores come from float32 code (A011); M3, README reproduction text, fixed 22:09; M4, the download script did not pin the sums-file hash, fixed 22:09; M5, the clean copy ran 37 of 38 fixtures because SVDB was not built.
- **Adoption:** **incumbent** (R0), from 2026-10-26 22:07 UAE
- **Limitations and next action:** λ at the lower edge of the declared grid (A010): the extended-grid fairness check is E010/E011, scored later as a secondary comparison. The PASS does not establish that the ESN baseline is fully tuned.

## E003
- **Date:** 2026-10-26
- **Idea / anomaly links:** none (the first quantum arm of the slice)
- **Hypothesis and predeclared decision criterion:** the finite-shot quantum reservoir features improve macro-F1 on ds2s over the matched ESN, under the EV1 decision rule (role headline: delta >= +0.02, 95% CI lower bound > 0, delta without record 232 > 0). Slice members S_f1 and V_f1 at 98.75%.
- **Change:** 10-qubit QRC arm as declared above.
- **Result type:** proxy (DS1 tuning); **full** (headline comparison on ds2s, EV1 approved r5)
- **Candidate revision + config:** selected QRC configuration 15 of 30: input scale 0.317, J 0.106, h 0.159, depth 2, ring, disorder 0.421; λ = 0.1. The selected couplings are weak (J ≈ 0.11 rad per layer), so the dynamics are close to a product state; the classical-spin control (I001) is therefore especially informative. Tuning ran with pipeline revision `cf7bd4bd0a9634f8`: the code the processes loaded at launch. It was verified by rebuilding the launch-time files in `runs/E002/pipe_at_tuning/`, whose raw-bytes hash is `cf7bd4bd0a9634f8` and line-ending-normalised hash `0b21d3899b1cac7b`. The `pipe_revision` field in `tuning.jsonl` is wrong for most lines: it was read from disk when each line was written, and files were edited during the run (feature loading for SVDB, the demo). None of those edits touched code the tuning executes. `run.py` now records the revision at process start. Final runs: pipeline `da67af87f8b8fd73`, evaluation `9a1922c8898b90db` (in every run manifest). Between tuning and the final runs, the ESN and the readout's prediction step were switched to float64 to make outputs batch-invariant (A011); the model definition did not change.
- **Comparison baseline:** E002 (R0), on the same ds2s units
- **Component / dependency parents:** none
- **Evaluation version / data and split IDs:** EV1 (approved r5, evaluation revision `9a1922c8898b90db`); ds1 for tuning; ds2s (21 records, 47,129 units)
- **Environment and exact command:** `python -I -m qhc.pipe.run tune --arm qrc --exp E003`; `final --exp E003 --seeds 0 1 2 3 4 --oof --splits ds2s`; then `python -I -m qhc.evaluate compare --split ds2s --role headline --cand runs/E003/pred_ds2s_seed*.csv --base runs/E002/pred_ds2s_seed*.csv --cand-id E003 --base-id E002 --out runs/E003/compare_ds2s_headline.json`
- **Seeds / repetitions / variants attempted in this line:** 30 configurations (seed 0) + 5 final seeds
- **Raw results and artifacts:** `runs/E003/`: `tuning.jsonl`, `selected_config.json`, `model_seed{0..4}.npz` (seed 0 sha256 prefix `a30c951215032d5b`), `oof_ds1_seed{0..4}.csv`, `pred_ds2s_seed{0..4}.csv` with manifests, `leakcheck_seed0.json`, `compare_ds1_oof_vs_E002.json`; **`compare_ds2s_headline.json`** (+ `_stdout.txt`); demo `runs/demo/qrc_E003_rec232.png`.
- **Baseline score / candidate score / signed delta:** **Full (EV1 headline, ds2s, logged 2026-10-26 21:26:59 as the first model scoring on the test splits; both arms passed in seed order 0-4):** E002 0.7065 / E003 **0.7273** (per seed 0.7312, 0.7295, 0.7252, 0.7202, 0.7305) / delta **+0.0208**. Without record 232: +0.0460. Slice family at 98.75%: **V_f1 +0.0688 [+0.0207, +0.1543], favorable**; S_f1 -0.0231 [-0.1456, +0.0978], no detectable change; lowdata_k5 and lowdata_k11 not yet run (E007, E008). Per-class F1 (95%, descriptive): N +0.0168 [+0.0024, +0.0302]; S -0.0231 [-0.1244, +0.0798]; V +0.0688 [+0.0295, +0.1293]. AUPRC (descriptive): S 0.232 vs 0.251, -0.019 [-0.074, +0.046]; V 0.955 vs 0.918, +0.036 [-0.001, +0.138]. Seed-averaged sensitivity / PPV / F1, E003: N 0.946 / 0.976 / 0.961; S 0.421 / 0.295 / 0.347; V 0.949 / 0.811 / 0.874. Paper-compatible: VEB Se 0.949, +P 0.811, FPR 0.016 (E002 0.953, 0.697, 0.030); SVEB Se 0.421, +P 0.294, FPR 0.039 (E002 0.595, 0.268, 0.063). Review burden per hour: S-or-V flags 608 vs 806; normal beats flagged 217 vs 374; missed ectopic 93 vs 57. DS1 OOF tuning (proxy, seed 0): best 0.6669, median 0.645 (ESN 0.6744 / 0.643); DS1 OOF 5-seed comparison +0.0051 [-0.044, +0.066].
- **Uncertainty (method from EVAL.md):** two-level record and seed bootstrap, B = 8,000, seed 20261026: primary 95% CI **[-0.0157, +0.0617]**. Outcome **no detectable change** (CI includes 0); the point delta meets the +0.02 practical threshold and the 232 condition holds, but neither changes the outcome. Leave-one-record-out delta: range +0.0111 (without 213) to +0.0460 (without 232); positive for every record left out.
- **Segments and resource changes:** tuning 590 s of compute; final runs about 15 s per seed; the headline comparison took about 12 min wall-clock (21:26:57-21:38:35), single-threaded CPU (8,000 replicates, AUPRC included). Trade-off on ds2s: the QRC arm flags fewer beats (higher S and V PPV, lower S sensitivity) than the ESN arm; the V gain is the robust part.
- **Mechanism check:** full-pipeline lookahead check on 731 DS1 beats: **passed** (0 violations). The simulator matches an independent dense-matrix implementation to 4e-7. Finite-shot features are batch-invariant (per-beat Philox streams, float64 CDF).
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** **no detectable change** (primary, headline; EV1, and identically under EV2). Slice family complete under EV2 (98.75%): **V_f1 +0.0688 [+0.0207, +0.1543] favorable**; S_f1 -0.0231 [-0.1456, +0.0978], lowdata_k5 (E007) -0.0086 [-0.0858, +0.0794], lowdata_k11 (E008) -0.0308 [-0.1045, +0.0546], each no detectable change. Scorecard Performance anchor 2 conditions are met (no detectable change overall; one family member with lower bound > 0; all four reported), pending the reviewer's rating.
- **Verification:** not requested (the primary does not meet the decision rule; the slice claim will be verified with the final candidate)
- **Adoption:** candidate (does not replace R0: no favorable primary outcome)
- **Limitations and next action:** the V gain over the ESN is reproduced by the classical mean-field model of the same circuit (E004: E003 vs E004 +0.0039 [-0.0028, +0.0115]; V F1 0.874 for both). It is therefore not attributable to quantum correlations (A016). Removing the couplings (E005) lowers V F1 (-0.063 [-0.132, -0.021]) and raises S F1. A010 caveat: E010/E011 pending. **EV2 rerun:** `runs/E003/compare_ds2s_headline_EV2.json`, logged 22:15:23 as EV2's first scoring. Every number and interval is identical to the EV1 run (only the command, scorer revision and time differ). Tables: `runs/tables/headline_ds2s.md`.

## E004
- **Date:** 2026-10-26 ~19:30 UAE
- **Idea / anomaly links:** I001, A012
- **Hypothesis and predeclared decision criterion:** control, no criterion (EVAL.md rule 7). If the QRC's advantage were quantum, the mean-field model of the same gates would score lower.
- **Change:** `reservoirs.MeanField` with E003's selected configuration and λ (no tuning of its own). Product-state Bloch vectors, ZZ gates replaced by neighbour-driven Z rotations, ZZ readout = product of single-qubit values; 1,024 shots per circuit as independent bits from per-beat Philox streams. Validated: it equals the exact statevector QRC at J = 0 to 3.5e-6.
- **Result type:** proxy (DS1 OOF); **full (EV2, `secondary`, descriptive)** on ds2s
- **Candidate revision + config:** pipeline `18b08b059ebe6518`; `runs/E004/selected_config.json`
- **Comparison baseline:** E003 (control comparison); also E002
- **Component / dependency parents:** E003 (configuration)
- **Evaluation version / data and split IDs:** EV1 draft r5 for the DS1 part; **EV2** (`8501643023cd2eb6`) for ds2s (21 records, 47,129 units)
- **Environment and exact command:** `python -I -m qhc.pipe.run control --exp E004 --kind mf --from-exp E003 --oof --splits ds2s`; `run leakcheck --exp E004 --seed 0`; ds2s: `python -I -m qhc.evaluate compare --split ds2s --role secondary --cand runs/E003/pred_ds2s_seed{0..4}.csv --base runs/E004/pred_ds2s_seed{0..4}.csv --cand-id E003 --base-id E004 --out runs/E004/compare_ds2s_secondary_E003_vs_E004.json`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds (reservoir seed s, shot seed 1000 + s)
- **Raw results and artifacts:** `runs/E004/` (OOF, ds2s predictions with manifests, models, lookahead check, `compare_ds2s_secondary_E003_vs_E004.json`); table `runs/tables/secondary_E003_vs_E004_ds2s.md`
- **Baseline score / candidate score / signed delta:** **Full (EV2, ds2s, secondary, logged 22:16):** E004 (mean-field) 0.7234 (per seed 0.7264, 0.7225, 0.7241, 0.7186, 0.7255) vs E003 (QRC) 0.7273: QRC minus mean-field **+0.0039**. Per-class F1 deltas: N +0.0011 [-0.0006, +0.0029]; S +0.0107 [-0.0002, +0.0246]; V -0.0001 [-0.0155, +0.0166]. AUPRC S 0.232 vs 0.221, V 0.955 vs 0.955. E004 seed-averaged Se / PPV / F1: N 0.944 / 0.976 / 0.960; S 0.415 / 0.283 / 0.336; V 0.950 / 0.810 / 0.874. Review burden per hour: 615 S-or-V flags, 224 normal beats flagged, 93 missed ectopic (E003: 608, 217, 93). DS1 OOF (proxy): 0.6671 vs 0.6671.
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000: 95% CI **[-0.0028, +0.0115]**; without 232 +0.0053; leave-one-record-out +0.0026 to +0.0053
- **Segments and resource changes:** about 75 s per seed (finite-shot sampling of independent bits)
- **Mechanism check:** the predictions differ from E003's (97.6-97.8% agreement; probability differences up to 0.6), so the mean-field code ran; the artifact metadata says arm `mf`; full-pipeline lookahead check passed (731 beats).
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** **no detectable change** (secondary, descriptive): the QRC and its classical mean-field model are indistinguishable on ds2s
- **Verification:** not requested
- **Adoption:** n/a (control)
- **Limitations and next action:** a secondary comparison: descriptive, not part of the slice family. Consequence: the headline's V gain over the ESN is shared by a classical simulation of the same gates (A016).

## E005
- **Date:** 2026-10-26 ~19:30 UAE
- **Idea / anomaly links:** I002, A012
- **Hypothesis and predeclared decision criterion:** control, no criterion (EVAL.md rule 7): removes every entangling gate.
- **Change:** E003's configuration with J = 0; everything else identical (QRC simulator, 1,024 shots).
- **Result type:** proxy (DS1 OOF); **full (EV2, `secondary`, descriptive)** on ds2s
- **Candidate revision + config:** pipeline `18b08b059ebe6518`; `runs/E005/selected_config.json`
- **Comparison baseline:** E003
- **Component / dependency parents:** E003 (configuration)
- **Evaluation version / data and split IDs:** EV1 draft r5 for the DS1 part; **EV2** for ds2s
- **Environment and exact command:** `python -I -m qhc.pipe.run control --exp E005 --kind sep --from-exp E003 --oof --splits ds2s`; `run leakcheck --exp E005 --seed 0`; ds2s: `compare --split ds2s --role secondary --cand runs/E005/pred_ds2s_seed{0..4}.csv --base runs/E003/pred_ds2s_seed{0..4}.csv --cand-id E005 --base-id E003 --out runs/E005/compare_ds2s_secondary_E005_vs_E003.json`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds
- **Raw results and artifacts:** `runs/E005/` (incl. `compare_ds2s_secondary_E005_vs_E003.json`); table `runs/tables/secondary_E005_vs_E003_ds2s.md`
- **Baseline score / candidate score / signed delta:** **Full (EV2, ds2s, secondary, logged 22:16):** E003 0.7273 / E005 (J = 0) 0.7264 (per seed 0.7272, 0.7299, 0.7223, 0.7298, 0.7229) / **-0.0009**. Per-class F1 deltas: N -0.0064 [-0.0166, +0.0029]; **S +0.0671 [-0.0139, +0.1308]; V -0.0634 [-0.1321, -0.0210]**. AUPRC S 0.287 vs 0.232; V 0.891 vs 0.955. E005 seed-averaged Se / PPV / F1: S 0.576 / 0.323 / 0.414; V 0.924 / 0.722 / 0.811. Review burden per hour: 697 S-or-V flags, 286 normal beats flagged, 69 missed ectopic (E003: 608, 217, 93). DS1 OOF (proxy): 0.6793 vs 0.6671.
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000: 95% CI **[-0.0444, +0.0319]**; without 232 -0.0212; leave-one-record-out -0.0212 (232) to +0.0133 (222)
- **Segments and resource changes:** about 26 s per seed
- **Mechanism check:** J = 0 in the selected configuration file and the artifact; lookahead check passed (731 beats).
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** **no detectable change** overall (secondary, descriptive). The couplings trade classes: without them V F1 is lower (95% CI excludes 0) and S F1 higher (CI includes 0)
- **Verification:** not requested
- **Adoption:** n/a (control)
- **Limitations and next action:** J = 0 lies outside the declared QRC search space (J ~ U[0.1, 1.5]). The DS1 proxy advantage of the separable variant (+0.012) did not carry over to ds2s overall (-0.0009). A016.

## E006
- **Date:** 2026-10-26 ~19:45 UAE
- **Idea / anomaly links:** I003, A009
- **Hypothesis and predeclared decision criterion:** control, no criterion (EVAL.md rule 7: "RR plus handcrafted features alone").
- **Change:** the shared readout on the 8 RR features only; λ chosen from the declared grid by DS1 OOF (0.1).
- **Result type:** proxy (DS1 OOF); **full (EV2, `score`, single deterministic run, descriptive)** on ds2s
- **Candidate revision + config:** pipeline at run time (in the manifest); `runs/E006/selected_config.json`
- **Comparison baseline:** E002 (descriptive)
- **Component / dependency parents:** none
- **Evaluation version / data and split IDs:** EV1 draft r5 for the DS1 part; **EV2** for ds2s
- **Environment and exact command:** `python -I -m qhc.pipe.run rronly --exp E006 --oof --splits ds2s`; ds2s: `python -I -m qhc.evaluate score --split ds2s --pred runs/E006/pred_ds2s_seed0.csv --id E006 --out runs/E006/score_ds2s.json`
- **Seeds / repetitions / variants attempted in this line:** 1 (deterministic); 4 λ values
- **Raw results and artifacts:** `runs/E006/` (incl. `score_ds2s.json`)
- **Baseline score / candidate score / signed delta:** **Full (EV2, ds2s, logged 22:16):** macro-F1 **0.6997** (one run), against E002 0.7065 and E003 0.7273 (seed means; no paired interval, descriptive only). Se / PPV / F1: N 0.952 / 0.989 / 0.970; S 0.471 / 0.333 / 0.390; V 0.834 / 0.663 / 0.739. Paper-compatible: VEB Se 0.834, +P 0.663, FPR 0.031; SVEB Se 0.471, +P 0.332, FPR 0.037. Review burden per hour: 624 S-or-V flags, 191 normal beats flagged, 98 S<->V swaps, 42 missed ectopic. DS1 OOF (proxy): 0.6367.
- **Uncertainty (method from EVAL.md):** none (a single deterministic run scored with `score`)
- **Segments and resource changes:** seconds
- **Mechanism check:** same readout code path as the arms; the features are the shared RR block.
- **Cost:** negligible
- **Execution:** completed
- **Outcome:** not assessed
- **Verification:** not requested
- **Adoption:** n/a (control)
- **Limitations and next action:** RR features use the next beat (one-beat lookahead) as EVAL.md allows. On ds2s the RR-only readout is close to the ESN arm overall (0.700 vs 0.707); its S F1 (0.390) is the highest of the three and its V F1 (0.739) the lowest. The reservoirs' contribution is mainly on V.

## E007
- **Date:** 2026-10-26 21:37-21:40 UAE
- **Idea / anomaly links:** EVAL.md slice (c) (pre-registered slice family member `lowdata_k5`)
- **Hypothesis and predeclared decision criterion:** slice family member (EVAL.md Comparison procedure): macro-F1 delta of the refitted QRC arm over the refitted ESN arm on ds2s, 98.75% CI, slice rule.
- **Change:** both headline arms keep their full-DS1 configuration and λ (E003 configuration 15, λ 0.1; E002 configuration 28, λ 0.001), reservoir seeds 0-4 and shot seeds 1000-1004. The readout's normalisation and weights are refitted on the 13,283 N/S/V units of the frozen k = 5 subset only. Assumption: λ is part of the selected configuration, so it is kept and not re-selected on the subset; EVAL.md lists "input normalisation, readout weights, decision rule" as refitted quantities.
- **Result type:** proxy (DS1 records outside the subset); **full (EV2, `lowdata_k5`, slice-family member)**
- **Candidate revision + config:** pipeline `ad80a50e051c6820` (`run.py lowdata`); evaluation `9a1922c8898b90db`; run manifests carry `parent_config_id` (`E003-qrc-cfg15` / `E002-esn-cfg28`), `train_records` and `refit_scope` `lowdata_k5`
- **Comparison baseline:** the refitted E002 arm (`runs/E007/E002/`)
- **Component / dependency parents:** E003, E002 (configurations)
- **Evaluation version / data and split IDs:** EV1 (approved r5) for the refit; **EV2** for the ds2s comparison; ds1 subset k5 from `lowdata_subsets.json`
- **Environment and exact command:** `python -I -m qhc.pipe.run lowdata --exp E007 --from-exp E003 --k 5 --splits ds2s`, the same with `--from-exp E002`; lookahead checks; ds2s: `python -I -m qhc.evaluate compare --split ds2s --role lowdata_k5 --cand runs/E007/E003/pred_ds2s_seed{0..4}.csv --base runs/E007/E002/pred_ds2s_seed{0..4}.csv --cand-id E007-E003-k5 --base-id E007-E002-k5 --out runs/E007/compare_ds2s_lowdata_k5.json`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds per arm; no variants
- **Raw results and artifacts:** `runs/E007/E003/`, `runs/E007/E002/` (models, `pred_ds2s_seed*.csv` with manifests, `heldout_ds1_seed*.csv`, `leakcheck_seed0.json`, `selected_config.json`); `runs/E007/heldout_ds1_proxy_E007_E008.json`; stdout `runs/E007/lowdata_stdout_E007_E008.txt`
- **Baseline score / candidate score / signed delta:** proxy, macro-F1 on the 37,259 DS1 units outside the subset, seed mean: ESN 0.6416 / QRC 0.6465 / +0.0049. S F1 0.227 vs 0.215; V F1 0.740 vs 0.764. **Full (EV2, ds2s, `lowdata_k5`, logged 22:16):** refitted ESN 0.6984 (0.7019, 0.6937, 0.7112, 0.7006, 0.6846) / refitted QRC 0.6898 (per seed 0.6977, 0.6884, 0.6801, 0.6828, 0.6999) / **-0.0086**. Per-class F1 deltas (95%): N +0.0082 [-0.0051, +0.0208]; S -0.0898 [-0.2313, +0.0937]; V +0.0558 [-0.0059, +0.1311]. Review burden per hour: QRC 589 S-or-V flags, 210 normal flagged, 110 missed ectopic; ESN 721, 303, 76.
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000, at 98.75% (slice level): **[-0.0858, +0.0794]**; without 232 +0.0425
- **Segments and resource changes:** QRC about 11 s per seed, ESN about 2 s
- **Mechanism check:** both arms pass the full-pipeline lookahead check (731 beats, 0 violations). A dry run of the staged D4 check (evaluation revision `8501643023cd2eb6`, no label access) accepts both arms for `lowdata_k5` and refuses them for `lowdata_k11`.
- **Cost:** < 0.05 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** **no detectable change** (slice member lowdata_k5, 98.75%)
- **Verification:** not requested
- **Adoption:** n/a (slice member)
- **Limitations and next action:** one subset per k (subset-selection uncertainty not measured); λ kept from full DS1 (assumption). The QRC refit loses S F1 and gains V F1, as in the headline; without 232 the delta is positive (+0.0425). The EV2 provenance checks (D4) accepted these runs before any label was read. Table `runs/tables/lowdata_k5_ds2s.md`.

## E008
- **Date:** 2026-10-26 21:41-21:44 UAE
- **Idea / anomaly links:** EVAL.md slice (c) (`lowdata_k11`)
- **Hypothesis and predeclared decision criterion:** as E007, with k = 11.
- **Change:** as E007, refitted on the 25,375 N/S/V units of the frozen k = 11 subset (106, 112, 115, 116, 119, 124, 205, 208, 209, 220, 223).
- **Result type:** proxy (DS1 records outside the subset); **full (EV2, `lowdata_k11`, slice-family member)**
- **Candidate revision + config:** as E007; `refit_scope` `lowdata_k11`
- **Comparison baseline:** the refitted E002 arm (`runs/E008/E002/`)
- **Component / dependency parents:** E003, E002 (configurations)
- **Evaluation version / data and split IDs:** EV1 (approved r5) for the refit; **EV2** for the ds2s comparison; ds1 subset k11 from `lowdata_subsets.json`
- **Environment and exact command:** `python -I -m qhc.pipe.run lowdata --exp E008 --from-exp E003 --k 11 --splits ds2s`, the same with `--from-exp E002`; lookahead checks; ds2s: `python -I -m qhc.evaluate compare --split ds2s --role lowdata_k11 --cand runs/E008/E003/pred_ds2s_seed{0..4}.csv --base runs/E008/E002/pred_ds2s_seed{0..4}.csv --cand-id E008-E003-k11 --base-id E008-E002-k11 --out runs/E008/compare_ds2s_lowdata_k11.json`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds per arm
- **Raw results and artifacts:** `runs/E008/E003/`, `runs/E008/E002/`; proxy summary in `runs/E007/heldout_ds1_proxy_E007_E008.json`
- **Baseline score / candidate score / signed delta:** proxy, macro-F1 on the 25,167 DS1 units outside the subset, seed mean: ESN 0.5636 / QRC 0.5651 / +0.0014. S F1 0.181 vs 0.135; V F1 0.572 vs 0.614. The held-out DS1 sets of E007 and E008 differ, so their proxies are not comparable with each other. **Full (EV2, ds2s, `lowdata_k11`, logged 22:16):** refitted ESN 0.7253 (0.7293, 0.7195, 0.7266, 0.7280, 0.7230) / refitted QRC 0.6944 (per seed 0.6981, 0.6972, 0.6881, 0.6923, 0.6964) / **-0.0308**. Per-class F1 deltas (95%): N +0.0106 [-0.0101, +0.0257]; S -0.1537 [-0.3130, +0.0443]; V +0.0506 [+0.0151, +0.1082]. Review burden per hour: QRC 644, 264, 106; ESN 851, 401, 40.
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000, at 98.75% (slice level): **[-0.1045, +0.0546]**; without 232 +0.0286
- **Segments and resource changes:** QRC about 28 s per seed, ESN about 5 s
- **Mechanism check:** lookahead check passed for both arms (731 beats, 0 violations); staged D4 dry run accepts `lowdata_k11` and refuses `lowdata_k5`.
- **Cost:** < 0.05 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** **no detectable change** (slice member lowdata_k11, 98.75%)
- **Verification:** not requested
- **Adoption:** n/a (slice member)
- **Limitations and next action:** one subset per k (subset-selection uncertainty not measured); λ kept from full DS1 (assumption). The QRC refit loses S F1 and gains V F1, as in the headline; without 232 the delta is positive (+0.0286). The EV2 provenance checks (D4) accepted these runs before any label was read. Table `runs/tables/lowdata_k11_ds2s.md`.

## E009
- **Date:** 2026-10-26 21:42-21:46 UAE
- **Idea / anomaly links:** A015 (open question), A010
- **Hypothesis and predeclared decision criterion:** diagnostic, no criterion. Question: is the QRC arm's lower false-alarm rate on ds2s a property of its features, or of its stronger selected readout regularisation (λ 0.1 vs 0.001)?
- **Change:** none to any arm. Both headline configurations (E002 cfg28, E003 cfg15), seeds 0-4 (QRC shot seeds 1000-1004), are scored by pooled DS1 out-of-fold predictions at each λ of the declared grid.
- **Result type:** diagnostic (DS1 OOF; no test split)
- **Candidate revision + config:** pipeline `ad80a50e051c6820`; script `runs/E009/matched_lambda.py`
- **Comparison baseline:** E002 at the same λ
- **Component / dependency parents:** E002, E003 (configurations)
- **Evaluation version / data and split IDs:** none (DS1 folds `ds1_folds.json`)
- **Environment and exact command:** `.venv/Scripts/python -I runs/E009/matched_lambda.py`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds x 4 λ x 2 arms
- **Raw results and artifacts:** `runs/E009/matched_lambda_ds1.json`, `runs/E009/stdout.txt`
- **Baseline score / candidate score / signed delta:** DS1 OOF macro-F1, seed mean (ESN / QRC / delta):
  - λ 0.001: 0.6620 / 0.6571 / -0.0049;
  - λ 0.01: 0.6608 / 0.6628 / +0.0020;
  - λ 0.1: 0.6339 / 0.6671 / +0.0332;
  - λ 1: 0.5968 / 0.6424 / +0.0456.
  - V false positives (ESN / QRC): 942 / 893, 987 / 867, 1,244 / 908, 1,474 / 1,036. V true positives: 2,986 / 2,805, 2,891 / 2,756, 2,764 / 2,767, 2,741 / 2,689.
  - S false positives: 3,303 / 3,403, 3,205 / 3,033, 3,087 / 2,446, 3,147 / 2,190. S true positives: 628 / 665, 650 / 654, 538 / 582, 340 / 443.
- **Uncertainty (method from EVAL.md):** not computed (diagnostic)
- **Segments and resource changes:** about 5 min of GPU
- **Mechanism check:** at their selected λ, the numbers equal the E002/E003 DS1 OOF results (0.6620, 0.6671).
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed
- **Outcome:** not assessed
- **Verification:** not requested
- **Adoption:** n/a
- **Limitations and next action:** DS1 proxy only. On DS1 the QRC features give fewer V false positives at every λ; the S false-positive reduction appears mainly at the QRC's selected λ = 0.1. At the ESN's λ = 0.001 the ESN is slightly better overall, and stronger regularisation hurts the ESN monotonically. On DS1 the ESN's V F1 is higher at its selected λ (0.774 vs 0.742); on ds2s the QRC's is (0.874 vs 0.805).

## E010
- **Date:** 2026-10-26 21:52 UAE (declared before running)
- **Idea / anomaly links:** A010
- **Hypothesis and predeclared decision criterion:** fairness check, no criterion. The ESN's selected λ sits at the lower edge of the declared grid. If the classical arm was under-regularised-tuned, an extended grid should raise its DS1 OOF score and change the ds2s comparison. Declared before running: the same 30 configurations (`sample_configs`, seed 20261026), tuning seed 0, nested grid λ ∈ {1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1}, best (configuration, λ) by pooled DS1 OOF macro-F1, ties to the lower index and the earlier grid value; final seeds 0-4 like E002. Reported as a `secondary` comparison E011 vs E010 on ds2s, alongside the headline, never replacing it.
- **Change:** readout grid extended downward (two values) for tuning; nothing else.
- **Result type:** proxy (DS1 OOF). No ds2s scoring: the selection is unchanged, so the predictions equal the headline inputs byte for byte
- **Candidate revision + config:** pipeline `55884b1fb66732b9` (adds `tune --lambdas`); results below when run
- **Comparison baseline:** E002 (declared grid)
- **Component / dependency parents:** E002 (search space)
- **Evaluation version / data and split IDs:** EV1 (approved r5); ds1; ds2s predictions written, not scored
- **Environment and exact command:** `python -I -m qhc.pipe.run tune --arm esn --exp E010 --lambdas 1e-5 1e-4 1e-3 1e-2 1e-1 1`; `final --exp E010 --seeds 0 1 2 3 4 --oof --splits ds2s`; `leakcheck --exp E010 --seed 0`
- **Seeds / repetitions / variants attempted in this line:** 30 configurations x 6 λ; 5 final seeds
- **Raw results and artifacts:** `runs/E010/` (`tuning.jsonl`, `tune_stdout.txt`, `selected_config.json`, models, `oof_ds1_seed*.csv`, `pred_ds2s_seed*.csv` with manifests, `final_stdout.txt`, lookahead check)
- **Baseline score / candidate score / signed delta:** best λ per configuration under the extended grid: 1e-5: 2, 1e-4: 3, 1e-3: 11, 1e-2: 11, 1e-1: 3, 1: 0. Selected: configuration 28, λ 0.001, DS1 OOF 0.6745 (as E002). Selected configuration's DS1 OOF by λ: 1e-5 0.6497, 1e-4 0.6637, **1e-3 0.6745**, 1e-2 0.6682, 1e-1 0.6408, 1 0.6048. All 5 `pred_ds2s_seed*.csv` and `oof_ds1_seed*.csv` files are byte-identical to E002's.
- **Uncertainty (method from EVAL.md):** not needed: identical predictions
- **Segments and resource changes:** tuning about 15 min (GPU shared with other jobs); finals about 1 min
- **Mechanism check:** the selection is identical, and so are the predictions (`filecmp`)
- **Cost:** estimated < 0.1 GPU-h
- **Execution:** completed
- **Outcome:** not assessed
- **Verification:** not requested
- **Adoption:** n/a
- **Limitations and next action:** A010 resolved: extending the grid does not change the selection, so the planned secondary comparison E011 vs E010 would repeat the headline exactly and was not run (no test-split access spent). Only 5 of 30 ESN configurations prefer λ < 1e-3 under the extended grid, none of them the selected one.

## E011
- **Date:** 2026-10-26 21:52 UAE (declared before running)
- **Idea / anomaly links:** A010
- **Hypothesis and predeclared decision criterion:** as E010, for the QRC arm, so that both arms get the same extended budget.
- **Change:** as E010.
- **Result type:** proxy (DS1 OOF). No ds2s scoring: the selection is unchanged, so the predictions equal the headline inputs byte for byte
- **Candidate revision + config:** pipeline `55884b1fb66732b9`; results below when run
- **Comparison baseline:** E010 in the secondary comparison; E003 for the DS1 proxy
- **Component / dependency parents:** E003 (search space)
- **Evaluation version / data and split IDs:** EV1 (approved r5); ds1; ds2s predictions written, not scored
- **Environment and exact command:** `python -I -m qhc.pipe.run tune --arm qrc --exp E011 --lambdas 1e-5 1e-4 1e-3 1e-2 1e-1 1`; `final --exp E011 --seeds 0 1 2 3 4 --oof --splits ds2s`; `leakcheck --exp E011 --seed 0`
- **Seeds / repetitions / variants attempted in this line:** 30 configurations x 6 λ; 5 final seeds
- **Raw results and artifacts:** `runs/E011/` (`tuning.jsonl`, `tune_stdout.txt`, `selected_config.json`, models, `oof_ds1_seed*.csv`, `pred_ds2s_seed*.csv` with manifests, `final_stdout.txt`, lookahead check)
- **Baseline score / candidate score / signed delta:** best λ per configuration under the extended grid: 1e-3: 2, 1e-2: 18, 1e-1: 10 (none below 1e-3). Selected: configuration 15, λ 0.1, DS1 OOF 0.6669 (as E003). Selected configuration's DS1 OOF by λ: 1e-5 0.6535, 1e-4 0.6588, 1e-3 0.6581, 1e-2 0.6599, **1e-1 0.6669**, 1 0.6396. All 5 `pred_ds2s_seed*.csv` and `oof_ds1_seed*.csv` files are byte-identical to E003's.
- **Uncertainty (method from EVAL.md):** not needed: identical predictions
- **Segments and resource changes:** tuning about 15 min (GPU shared with other jobs); finals about 1 min
- **Mechanism check:** the selection is identical, and so are the predictions (`filecmp`)
- **Cost:** estimated < 0.1 GPU-h
- **Execution:** completed
- **Outcome:** not assessed
- **Verification:** not requested
- **Adoption:** n/a
- **Limitations and next action:** A010 resolved: extending the grid does not change the selection, so the planned secondary comparison E011 vs E010 would repeat the headline exactly and was not run (no test-split access spent). Only 5 of 30 ESN configurations prefer λ < 1e-3 under the extended grid, none of them the selected one.

## Phase 4 declarations (2026-10-28 ~18:50 UAE, written before any E012+ model run; the free calibration fetch, device search and SVDB feature build started 18:45-18:48)

Authorized by the author 2026-10-28 ~18:20 ("Don't drop the experiments...") and again at ~18:36 (probe-count limit lifted for this work period; 20 min per probe, 3 GPU-h per run and per-task Braket approval stay; Braket cap USD 35; experiment freeze 22:00; push by 23:30).

- **Status of every ds2s comparison below:** `--role secondary`, descriptive. Every one is chosen after the ds2s headline and control results were seen (post-hoc choices, disclosed in the README). None replaces the headline E003 vs E002, none joins the slice family, and none can turn the inconclusive primary or the mean-field attribution (A016) into a quantum-benefit claim.
- **Test-split budget:** 7 of 15 used; 8 left. Declared here: E012 (1), E014 (1), E015 (1), E016 (2) = 5; 3 spare. `qhc.evaluate compare/score` on ds2s, ds2 or svdb is run only centrally, never from a compute lane; the lanes write label-free predictions and manifests only.
- **Code rule:** evaluation code (`src/qhc/*.py`, EV2 `8501643023cd2eb6`) and the existing pipeline (`src/qhc/pipe/*.py`, `55884b1fb66732b9`) are not edited. New code goes in `src/qhc/p4/<module>.py`; run manifests record `code_revision` as `eval <rev> / pipe <rev> / p4 <module> <sha16>`.
- **Common protocol unless a card says otherwise:** E003's selected QRC configuration (cfg15: input scale 0.317, J 0.106, h 0.159, depth 2, ring, disorder 0.421); readout `readout.Readout`, λ grid {0.001, 0.01, 0.1, 1}; DS1 OOF on the fixed folds `ds1_folds.json`; 5 seeds (reservoir seed s, shot or noise seed 1000 + s, s = 0-4); the readout is refitted on all DS1 units for ds2s predictions.

## E012
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / GPU0 lane
- **Idea / anomaly links:** I004; review P2
- **Hypothesis and predeclared decision criterion:** ablation, no decision criterion. Finite-shot noise (1,024 shots) may act as a regulariser or as a cost; exact expectations (`shots=None`) isolate it.
- **Change:** `reservoirs.QRC(shots=None)` with E003's configuration and λ = 0.1 (fixed, not reselected); shot seed n/a.
- **Result type:** proxy (DS1 OOF); full (EV2, `secondary`, descriptive) on ds2s
- **Comparison baseline:** E003 (finite-shot). ds2s: `compare --role secondary --cand E012 --base E003` (1 scoring), run whatever the DS1 result.
- **Component / dependency parents:** E003 (configuration)
- **Evaluation version / data and split IDs:** EV2; ds1, ds2s
- **Candidate revision + config:** `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 ablate f7fe9f52db014c44`; E003 cfg15, `shots=None`, λ 0.1 (best λ on DS1 for every seed was also 0.1)
- **Environment and exact command:** commands in `runs/E012/summary.json`; ds2s: `python -I -m qhc.evaluate compare --split ds2s --role secondary --cand runs/E012/pred_ds2s_seed{0..4}.csv --base runs/E003/pred_ds2s_seed{0..4}.csv --cand-id E012 --base-id E003 --out runs/E012/compare_ds2s_secondary_E012_vs_E003.json`
- **Seeds / repetitions / variants attempted in this line:** 5 seeds (reservoir seed s)
- **Raw results and artifacts:** `runs/E012/` (`oof_ds1_seed*.csv`, `model_seed*.npz`, `pred_ds2s_seed*.csv` + manifests, `leakcheck_seed0.json`, `summary.json`, `compare_ds2s_secondary_E012_vs_E003.json` + `_stdout.txt`)
- **Baseline score / candidate score / signed delta:** **proxy (DS1 OOF, 5 seeds):** E012 0.6693 vs E003 0.6671, +0.0022 (per-seed deltas −0.0003 to +0.0043, inside the seed spread). **Full (EV2, ds2s, secondary, descriptive; access logged 19:29:53, output written 19:41:44):** E012 0.7278 vs E003 0.7273, **+0.0005 [−0.0058, +0.0081]**; without 232 +0.0022. Per class: N +0.001 [−0.001, +0.002]; S −0.003 [−0.013, +0.010]; V +0.004 [−0.012, +0.021]. AUPRC S +0.004, V −0.000.
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000; leave-one-record-out −0.0003 (219) to +0.0022 (232)
- **Mechanism check:** exact features differ from the 1,024-shot features (mean absolute difference 0.017); DS1 OOF argmax agreement with E003 98.5-98.6%; ds2s agreement 98%; lookahead check passed (731 beats, 0 violations); `check_runs` passed.
- **Cost:** < 0.05 GPU-h, USD 0
- **Execution:** completed | **Outcome:** no detectable change (secondary, descriptive) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** shot noise at 1,024 shots costs nothing measurable on ds2s; the measurement model is not what limits the QRC arm.

## E013
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / GPU0 lane
- **Idea / anomaly links:** I004; review P2
- **Hypothesis and predeclared decision criterion:** proxy sweep, no decision criterion. Prediction: DS1 OOF macro-F1 flat from 1,024 shots upward, lower at 64 shots.
- **Change:** shots in {64, 256, 4096} (1,024 = E003, exact = E012), E003's configuration, λ fixed at 0.1; the best λ from the grid reported as a second column.
- **Result type:** proxy (DS1 OOF only; no ds2s scoring)
- **Comparison baseline:** E003 DS1 OOF (5 seeds); feature error against E012's exact features
- **Evaluation version / data and split IDs:** EV2; ds1
- **Candidate revision + config:** `p4 ablate f7fe9f52db014c44` (as E012); E003 cfg15, λ fixed 0.1
- **Environment and exact command:** `runs/E013/summary.json` (`commands`)
- **Seeds / repetitions / variants attempted in this line:** 3 shot counts x 5 seeds (+ 1,024 and exact as reference rows)
- **Raw results and artifacts:** `runs/E013/` (`oof_ds1_shots{n}_seed{s}.csv`, `table.csv`, `summary.json`)
- **Baseline score / candidate score / signed delta:** **proxy (DS1 OOF, 5-seed mean macro-F1, λ 0.1 / best λ; mean absolute feature error vs exact, seed 0):** 64 shots 0.6478 / 0.6481, error 0.0675; 256: 0.6598 / 0.6610, 0.0337; **1,024 (E003): 0.6671**, 0.0169; 4,096: 0.6681, 0.0084; exact (E012): 0.6693, 0. The declared prediction held: flat from 1,024 up, lower at 64 (−0.019).
- **Uncertainty (method from EVAL.md):** none (proxy; DS1 record-level uncertainty is about ±0.05)
- **Mechanism check:** feature error halves with each 4x in shots (1/sqrt(shots)); the 1,024-shot recompute reproduces E003's OOF files exactly.
- **Cost:** < 0.05 GPU-h, USD 0
- **Execution:** completed | **Outcome:** not assessed (proxy) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** prospective hardware arithmetic: 256 shots per circuit would cost about 0.008 DS1 macro-F1 (proxy) at a quarter of the shots.

## E014
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / GPU0 lane
- **Idea / anomaly links:** I007
- **Hypothesis and predeclared decision criterion:** ablation. K changes, so these are not members of the headline search (rule 2).
- **Change:** (a) qubit count n in {6, 8, 12}: each 10-sample input chunk is linearly resampled to n points (`np.interp`; identity at n = 10), ring over n qubits, couplings drawn from the reservoir seed, Z + ZZ readout per snapshot, K = 4(n + n(n-1)/2) = 84, 144, 312; (b) n = 10 with Z-only readout, K = 40. Everything else as E003 (1,024 shots). λ selected per variant from the declared grid by seed-0 DS1 OOF (the tuning protocol), then 5 seeds at that λ.
- **DS1-only selection rule for ds2s:** among the (a) variants, the highest 5-seed mean pooled DS1 OOF macro-F1 (ties to fewer qubits) gets ds2s predictions and one `compare --role secondary --cand <variant> --base E003` (1 scoring). (b) stays a DS1 proxy.
- **Result type:** proxy (DS1 OOF); full (EV2, secondary, descriptive) for the selected variant
- **Comparison baseline:** E003
- **Evaluation version / data and split IDs:** EV2; ds1, ds2s
- **Candidate revision + config:** `p4 ablate f7fe9f52db014c44`; generalised n-qubit QRC; at n = 10 bit-identical to `reservoirs.QRC` on 3,186 DS1 beats (finite-shot and exact); agrees with an independent dense reference to 2-5e-6 at n = 6-12
- **Environment and exact command:** `runs/E014/summary.json`; ds2s: `compare --split ds2s --role secondary --cand runs/E014/n6/pred_ds2s_seed{0..4}.csv --base runs/E003/pred_ds2s_seed{0..4}.csv --cand-id E014-n6 --base-id E003 --out runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json`
- **Seeds / repetitions / variants attempted in this line:** 4 variants x (4 λ at seed 0 + 5 seeds)
- **Raw results and artifacts:** `runs/E014/` (`table.csv`, `summary.json`, `n6/` with models, OOF, ds2s predictions + manifests, lookahead check; `compare_ds2s_secondary_E014n6_vs_E003.json`)
- **Baseline score / candidate score / signed delta:** **proxy (DS1 OOF, 5-seed mean macro-F1; E003 0.6671, K 220):** n = 6 (K 84, λ 0.1) **0.6803**; n = 8 (K 144, λ 0.1) 0.6673; n = 12 (K 312, λ 0.01) 0.6635; Z-only n = 10 (K 40, λ 0.1) 0.6776. **Selected by the declared rule: n = 6.** **Full (EV2, ds2s, secondary, descriptive; access logged 19:30:17, output written 19:40:06):** E014-n6 0.7351 vs E003 0.7273, **+0.0078 [−0.0055, +0.0188]**; without 232 +0.0004. Per class: N +0.002; S +0.028 [−0.009, +0.057]; V −0.007 [−0.027, +0.014].
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000; leave-one-record-out +0.0004 (232) to +0.0105 (222)
- **Mechanism check:** n = 10 equality check above; lookahead check passed for n6 (0 violations); `check_runs` passed; ds2s argmax agreement with E003 97%.
- **Cost:** < 0.1 GPU-h, USD 0
- **Execution:** completed | **Outcome:** no detectable change (secondary, descriptive) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** confound: changing n also resamples each 10-sample chunk to n points, so qubit count and input resolution move together. Smaller readouts (n = 6, Z-only) score higher on DS1 (A020). More qubits did not help.

## E015
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / GPU1 lane
- **Idea / anomaly links:** I005; review P2; EVAL.md hardware and noise tracks
- **Hypothesis and predeclared decision criterion:** device-noise simulation, a secondary candidate (EVAL.md). Prediction: at current two-qubit error rates the 80 ZZ gates per beat (160 native two-qubit gates) shrink the ZZ correlators and move V F1 towards the separable control's.
- **Change:** E003's circuit (seed couplings) simulated with stochastic Pauli trajectories: depolarising error after every single-qubit gate (median 1q error), two-qubit depolarising error after each of the 2 native two-qubit gates per ZZ (median 2q error), and per-qubit readout assignment error on every sampled bit. Rates come from the device calibration returned by the free Braket `GetDevice` call at fetch time (recorded with the time), for Rigetti Cepheus-1-108Q and IQM Garnet; if a device returns none, the provider's published figures with their source. 1,024 shots per circuit, split over trajectories; per-beat Philox streams keyed by (beat key, seed), so features do not depend on batching. The readout is trained on noisy DS1 features (noise-aware). Declared limitations: no idle T1/T2 decay, no crosstalk, no routing (a 10-qubit ring is assumed embeddable).
- **DS1-only rule for ds2s:** the Rigetti Cepheus model (the I006 target) gets ds2s predictions and one `compare --role secondary --cand E015-rigetti --base E003` (1 scoring), whatever its DS1 result. IQM Garnet stays a DS1 proxy. If no Rigetti rates exist, IQM takes its place.
- **Result type:** proxy (DS1 OOF); full (EV2, secondary, descriptive)
- **Comparison baseline:** E003 (noiseless finite-shot); E005 (separable) for context
- **Evaluation version / data and split IDs:** EV2; ds1, ds2s
- **Candidate revision + config:** `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 noise 8b1226919f8ca395`; E003 cfg15; T = 32 trajectories x 32 shots = 1,024 shots per circuit; λ 0.1 selected for both devices
- **Error rates (free `GetDevice` calibration, fetched 14:45:52Z / 14:45:55Z; medians over the whole chip, `runs/E015/calibration_*.json`):** Rigetti Cepheus-1-108Q: 1q error 0.00302 (simultaneous RB), CZ error 0.01168 (interleaved RB, 193 edges), readout error 0.031 (symmetric). IQM Garnet: 1q 0.00062, CZ 0.00446, readout 0.0100 (0→1) / 0.0273 (1→0). Depolarising probability q = r(d+1)/d.
- **Environment and exact command:** `runs/E015/summary.json` (`commands`); ds2s: `compare --split ds2s --role secondary --cand runs/E015/rigetti/pred_ds2s_seed{0..4}.csv --base runs/E003/pred_ds2s_seed{0..4}.csv --cand-id E015-rigetti --base-id E003 --out runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json`
- **Seeds / repetitions / variants attempted in this line:** 2 device models x 5 seeds (reservoir seed s, noise and shot seed 1000 + s)
- **Raw results and artifacts:** `runs/E015/` (`calibration_*.json`, `summary.json`, `rigetti/` and `iqm/` OOF, `rigetti/` models, ds2s predictions + manifests, `leakcheck_seed0.json`; the compare JSON)
- **Baseline score / candidate score / signed delta:** **proxy (DS1 OOF, 5-seed mean):** Rigetti 0.6463 (−0.021 vs E003, all 5 seeds negative; V F1 0.699 vs 0.742); IQM 0.6527 (−0.014). The card's prediction (V F1 moves towards the separable control's) did not hold on DS1: V F1 fell below both E003 and E005 (0.756). **Full (EV2, ds2s, secondary, descriptive; access logged 19:30:43, output written 19:42:35):** Rigetti-noise 0.7289 vs E003 0.7273, **+0.0016 [−0.0331, +0.0248]**; without 232 −0.0179. Per class: N +0.000; **S +0.058 [−0.036, +0.121]; V −0.053 [−0.114, −0.020]**. AUPRC V −0.023 [−0.089, −0.005]. On ds2s the noisy arm trades V for S, as the separable control E005 did (V −0.063, S +0.067).
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000; leave-one-record-out −0.0179 (232) to +0.0086 (219)
- **Mechanism check:** (i) rates 0, T = 1: bit-identical to `reservoirs.QRC` for seeds 0 and 1, batch-invariant; (ii) noisy/noiseless mean |Z| and |ZZ| shrink step by step (Rigetti Z 0.81→0.49, ZZ 0.67→0.28 over snapshots 1-4; IQM Z 0.93→0.79, ZZ 0.88→0.65); gates-only snapshot-1 values match the analytic prediction. Lookahead check passed (731 beats, 0 violations); `check_runs` passed.
- **Exploratory (seed 0, DS1 OOF):** a readout trained on noiseless features and applied to noisy features collapses to 0.278 (Rigetti) and 0.498 (IQM) against 0.668 (A021).
- **Cost:** about 0.5 GPU-h (Rigetti 16.9 min, IQM 9.8 min, lookahead 7.2 min), USD 0 (only free metadata calls)
- **Execution:** completed | **Outcome:** no detectable change (secondary, descriptive); V F1 lower (95% CI excludes 0) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** no idle T1/T2 decay, crosstalk or routing; on Rigetti arbitrary rotations compile to more than one pulse, so 1q error is probably underestimated; the noise simulation is therefore optimistic. The noise-aware readout recovers macro-F1 by moving the decision towards S; the V-class gain over the ESN (the headline's favorable slice) does not survive device noise at Rigetti's rates.

## E016
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / CPU B lane
- **Idea / anomaly links:** I009 (review P1); EVAL.md rule 7, "a strong classical reference for context only"
- **Hypothesis and predeclared decision criterion:** context, no criterion. Post-hoc: chosen after the ds2s results (the review found no strong non-reservoir classical model); disclosed.
- **Change:** `HistGradientBoostingClassifier` (scikit-learn 1.9.1) on the reservoir arms' inputs plus RR: [patient-relative window (40) | RR block (8)]; class-balanced sample weights; no early stopping. DS1 budget N = 30 configurations drawn i.i.d. with `default_rng(20261026)`: learning rate log-U[0.02, 0.3]; max leaf nodes in {15, 31, 63, 127}; min samples per leaf in {20, 50, 100, 200}; L2 log-U[1e-3, 10]; max iterations in {100, 200, 300}; max features U[0.5, 0.9] (so seeds differ). Scored by pooled DS1 OOF macro-F1 on the fixed folds with random state 0, in index order; the best wins, ties to the lower index. 20-minute wall-clock cap on the search: configurations not reached are recorded as not evaluated (realised N reported). Final: random states 0-4, refitted on all DS1 units.
- **ds2s:** `compare --role secondary --cand E003 --base E016` and `--cand E002 --base E016` (2 scorings).
- **Result type:** proxy (DS1 OOF); full (EV2, secondary, descriptive)
- **Comparison baseline:** E016 is the base in both (positive = the reservoir arm is better)
- **Evaluation version / data and split IDs:** EV2; ds1, ds2s
- **Candidate revision + config:** `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 boost c2c2fc47c011e891`; scikit-learn 1.9.1; realised N = 30 (500 s); selected cfg6: learning rate 0.02387, max leaf nodes 127, min samples per leaf 50, L2 0.8642, max iterations 300, max features 0.6804 (DS1 OOF 0.6718; median 0.6614, range 0.6503-0.6718)
- **Environment and exact command:** `runs/E016/summary.json`; ds2s: `compare --split ds2s --role secondary --cand runs/E003/pred_ds2s_seed{0..4}.csv --base runs/E016/pred_ds2s_seed{0..4}.csv --cand-id E003 --base-id E016 --out runs/E016/compare_ds2s_secondary_E003_vs_E016.json`; the same with E002 as candidate (`compare_ds2s_secondary_E002_vs_E016.json`)
- **Seeds / repetitions / variants attempted in this line:** 30 configurations (random state 0) + 5 final seeds (random state s; seeds agree on 99.3% of ds2s beats)
- **Raw results and artifacts:** `runs/E016/` (`tuning.jsonl`, models `model_seed*.pkl`, OOF, ds2s predictions + manifests, `leakcheck_seed0.json`, `summary.json`, both compare JSONs + `_stdout.txt`)
- **Baseline score / candidate score / signed delta:** **proxy (DS1 OOF, 5-seed mean):** E016 0.6702 (N 0.979, S 0.225, V 0.807) vs E003 0.6671, E002 0.6620, E006 0.6367. **Full (EV2, ds2s, secondary, descriptive; accesses logged 19:31:07 (E003 vs E016) and 19:31:33 (E002 vs E016), outputs written 19:41:01; positive = the reservoir arm is better):** E016 0.7216. **E003 vs E016 +0.0057 [−0.1389, +0.0676]**, without 232 **−0.0869**; per class N −0.016 [−0.030, −0.001], S +0.101 [−0.307, +0.270], **V −0.068 [−0.159, −0.031]**; AUPRC S −0.106 [−0.404, +0.001], V −0.038 [−0.122, −0.016]. **E002 vs E016 −0.0151 [−0.1896, +0.0766]**, without 232 **−0.1329**; per class N −0.033 [−0.054, −0.006], S +0.124 [−0.369, +0.384], **V −0.137 [−0.267, −0.067]**. E016 V F1 0.943 and S F1 0.246 (E003 0.874 / 0.347).
- **Uncertainty (method from EVAL.md):** two-level bootstrap, B = 8,000; leave-one-record-out E003 vs E016 −0.0869 (232) to +0.0236 (222); E002 vs E016 −0.1329 (232) to +0.0046 (222)
- **Mechanism check:** 5 distinct prediction and model hashes; `check_runs` passed; lookahead check passed (731 beats, 0 violations); DS1 seed-0 OOF reproduces the tuning score exactly.
- **Cost:** about 0.3 CPU-h, USD 0
- **Execution:** completed | **Outcome:** no detectable change in both comparisons (secondary, descriptive) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a (context)
- **Limitations and next action:** post-hoc (chosen after the ds2s results). The overall tie is carried by record 232's S beats, which the boosted trees rarely predict (A019); pooled over the other 20 records the boosted trees lead (−0.087 against E003, −0.133 against E002), though not in every record (not in 100, 123, 210 or 219; V005 F2), and their V F1 is higher than both reservoir arms' with a 95% CI that excludes 0. The matched ESN is a controlled comparator, not the strongest classical model.

## E017
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / CPU C lane
- **Idea / anomaly links:** I008; A016; scorecard Depth anchor 3
- **Hypothesis and predeclared decision criterion:** diagnostic. If the QRC and mean-field feature maps are near-identical as kernels (linear CKA near 1, geometric difference near 1), A016's attribution is supported at the representation level; per-patient kernel-target alignment shows where each map helps.
- **Change:** seed-0 DS1 features of E003 (QRC, 1,024 shots), the exact QRC (E012 setting), E004 (mean-field), E005 (separable), E002 (ESN) and RR only; standardised; linear kernels (the readout is linear). Centered kernel-target alignment (one-hot N/S/V targets, V-vs-rest, S-vs-rest) per DS1 record and pooled on a seeded stratified subsample; linear CKA between maps; the geometric difference of Huang et al. 2021 between the QRC and each classical map on a seeded subsample of 2,000 beats, trace-normalised, with a stated regulariser.
- **Result type:** diagnostic (DS1 only; no test labels)
- **Evaluation version / data and split IDs:** EV2; ds1
- **Candidate revision + config:** `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 kernels 647cb96976578b0d`; seed-0 reservoirs (match the saved artifacts); standardised on DS1 units; linear kernels
- **Environment and exact command:** `runs/E017/summary.json` (`command`); 108 s; a clean rerun gave byte-identical CSVs
- **Seeds / repetitions / variants attempted in this line:** subsample seed 20261026 (2,000 N + all 943 S + 2,000 V for CKA/KTA; 2,000 beats for the geometric difference); reference rows added: QRC with a new shot seed, QRC with reservoir seed 1, exact QRC vs exact mean-field
- **Raw results and artifacts:** `runs/E017/` (CSV tables, `summary.json` with formulas and verified citations)
- **Baseline score / candidate score / signed delta:** **diagnostic (DS1, reservoir block alone; adding RR changes ≤ 0.02):** linear CKA QRC-mean-field **0.986**, QRC-ESN 0.525, QRC-separable 0.510; references: QRC vs a new shot seed 0.992, vs reservoir seed 1 0.989, exact QRC vs exact mean-field 0.994. Centered KTA (one-hot / V-vs-rest): QRC 0.175 / 0.203, mean-field 0.159 / 0.184, ESN 0.246 / 0.248, separable 0.330 / 0.372, RR 0.181 / 0.158; S-vs-rest ≤ 0.04 for every map. Per record: QRC > ESN in 9 of 17 (one-hot) and 8 of 15 (V); QRC > mean-field in 13 of 17 (median +0.007), about as often as QRC beats its own seed-1 draw (14 of 17, +0.010); RR > QRC in 8 of 8 S records. Geometric difference g(K_C‖K_QRC) at λ 1e-3 / 1e-2 / 1e-1: mean-field 9.6 / 7.4 / 3.3 (shot-noise replicate 10.5 / 7.9 / 3.4), ESN 35 / 21 / 10, separable 27 / 23 / 13; no pair meets the paper's λ rule (training-error term < 0.045), not even the shot-noise replicate.
- **Uncertainty (method from EVAL.md):** none (diagnostic, one subsample)
- **Mechanism check:** regenerated reservoirs equal the saved artifacts; reference rows calibrate the scale of "same map".
- **Cost:** < 0.05 GPU-h, USD 0
- **Execution:** completed | **Outcome:** not assessed (diagnostic) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** at the representation level the mean-field map is as close to the QRC as the QRC is to itself under a new shot or reservoir seed, which supports A016; linear kernels on measured expectations, DS1 only. KTA does not predict readout F1 (the separable map has the highest KTA but the lowest ds2s V F1). References checked in a literature search: Kornblith et al., ICML 2019, PMLR 97:3519-3529; Cortes, Mohri & Rostamizadeh, JMLR 13:795-828 (2012); Huang et al., Nat. Commun. 12, 2631 (2021), doi:10.1038/s41467-021-22539-9.

## E018
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / CPU A lane (the test-split access itself is run centrally, not from the lane)
- **Idea / anomaly links:** A018; EVAL.md confirmation policy; progress-review takeaways
- **Hypothesis and predeclared decision criterion:** the pre-registered SVDB confirmation of the frozen headline pair E003 vs E002. *Confirmed* if the SVDB paired delta is > 0 and its 95% CI lower bound is > 0 (EVAL.md, fixed 2026-10-26).
- **Change:** none to the models. A predict-only path (`src/qhc/p4/predict.py`) loads each of the 10 saved headline artifacts, checks the regenerated reservoir against the saved `res_*` arrays, the shot count and the configuration, and writes predictions and manifests without touching the artifact. **Precondition:** its ds2s self-check (in a scratch directory) reproduces all 10 logged headline prediction hashes; hashes only, nothing scored. Then SVDB predictions, then `compare --split svdb --role confirmation` (its built-in placeholder-label preflight runs first).
- **Hard stop:** no access starts after 21:45 UAE; if it has not run, the README says so.
- **Result type:** full (EV2, confirmation)
- **Comparison baseline:** E002 (R0)
- **Evaluation version / data and split IDs:** EV2; svdb (78 records)
- **Candidate revision + config:** models unchanged: `runs/E003/model_seed{0..4}.npz`, `runs/E002/model_seed{0..4}.npz` (hashes unchanged before and after; all 77 files in `runs/E002/` and `runs/E003/` identical). Predict-only path `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 predict 08dc4140d5d45b6b`.
- **Precondition:** ds2s self-check reproduced **all 10** logged headline prediction hashes (`runs/E018/summary.md`); `check_runs` passed both arms on svdb; `scorer.validate` passed (184,389 prediction-set beats); placeholder-label preflight passed.
- **Environment and exact command:** `python -I -m qhc.evaluate compare --split svdb --role confirmation --cand runs/E018/E003/pred_svdb_seed{0..4}.csv --base runs/E018/E002/pred_svdb_seed{0..4}.csv --cand-id E003 --base-id E002 --out runs/E018/confirm_svdb.json --confirm-reason "..."` (verbatim in `runs/E018/summary.md`); access logged 19:29:19, completed 20:01:41
- **Seeds / repetitions / variants attempted in this line:** 5 seeds per arm; confirmation access 1 of 2
- **Raw results and artifacts:** `runs/E018/` (`E003/`, `E002/` SVDB predictions + manifests, `selfcheck_ds2s/`, `confirm_svdb.json`, `confirm_svdb_stdout.txt`, `summary.md/json`); `runs/confirmation_access.jsonl`; `runs/confirmation_reports/access_1.json` (sha256 `39c6b7e77a4353d6…`) and `index.jsonl`
- **Baseline score / candidate score / signed delta:** **Full (EV2, confirmation, SVDB, 78 records, 184,286 units):** E002 0.6488 / E003 0.6402 (per seed 0.6706, 0.6332, 0.6467, 0.6304, 0.6202) / **delta −0.0085, 95% CI [−0.0476, +0.0274]**. Per class: N +0.004 [−0.006, +0.014]; S −0.026 [−0.078, +0.024]; **V −0.003 [−0.089, +0.073]** (V F1 0.570 vs 0.574). AUPRC: S 0.301 vs 0.336 (−0.035 [−0.107, +0.022]); V 0.605 vs 0.677 (−0.073 [−0.185, +0.041]). Seed-averaged Se / PPV: E003 S 0.548 / 0.330, V 0.600 / 0.544; E002 S 0.529 / 0.374, V 0.763 / 0.463. Review burden per hour (39.0 h): S-or-V flags 801 vs 870; normal beats flagged 365 vs 413; missed ectopic 133 vs 111.
- **Uncertainty (method from EVAL.md):** two-level bootstrap over 78 records and seeds, B = 8,000; leave-one-record-out −0.0157 (859) to −0.0010 (892), negative for every record left out
- **Mechanism check:** see the precondition; every manifest points at the original artifact with an unchanged hash.
- **Cost:** CPU about 35 min (single-threaded bootstrap); USD 0
- **Execution:** completed | **Outcome:** **not confirmed** (pre-registered criterion: delta > 0 and CI lower bound > 0; observed delta −0.0085, CI includes 0: no detectable change) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** the ds2s V-class gain did not transfer: on SVDB the QRC arm's V F1 equals the ESN's (0.570 vs 0.574); its V PPV is higher (0.544 vs 0.463) and its V sensitivity lower (0.600 vs 0.763), the same direction of trade-off as on ds2s but without the F1 gain. SVDB differs in sampling rate (128 Hz, resampled) and lead; possible subject overlap with MIT-BIH (A006). The predict-only path ran with pipeline `55884b1fb66732b9` while the artifacts record `da67af87f8b8fd73`; the ds2s hash match covers the MIT-BIH path, and the SVDB resampling branch has no earlier reference output. No repair access is planned: no implementation defect is known.

## E019
- **Date / compute lane:** 2026-10-28 18:50 UAE (declared before running) / Braket lane
- **Idea / anomaly links:** I006; EVAL.md hardware track
- **Hypothesis and predeclared decision criterion:** diagnostic, label-free: how far hardware features of E003's seed-0 circuit are from the finite-shot and exact simulations (per-feature correlation, mean absolute difference), and how often the seed-0 readout's predicted class agrees with the simulation's. No macro-F1 is claimed.
- **Change:** a seeded draw of ds2s beats stratified by the seed-0 simulated predicted class (label-free; fixed before any task), 4 snapshot circuits per beat, several beats packed on disjoint 10-qubit rings of one device per task; device allowlist, shot cap and cost ledger in code. **Every task needs the author's approval with a cost estimate; Braket cap USD 35.** Abandoned and reported if results are not back by 21:30.
- **Result type:** diagnostic
- **Evaluation version / data and split IDs:** EV2; ds2s beats (inputs only, no labels read)
- **Approval and cost:** the author approved Rigetti Cepheus-1-108Q, 48 beats, 1 program-set task, cap USD 18.00 (~19:20 UAE). First submission refused by AWS before creation (missing service-linked role `AWSServiceRoleForAmazonBraket`; 0 tasks created, checked with `search_quantum_tasks`; USD 0). The author approved creating the role via API (done 15:57:26 UTC) and resubmitting the same job; `scripts/braket_submit.py` `ledger_total` was changed to release a refused pre-submit estimate (recorded in the ledger). Task `arn:aws:braket:us-west-1:…:quantum-task/73e0c152-76d6-432a-98fb-738ab43b9308` submitted 15:58:21 UTC, completed within minutes; results fetched with `AWS_PROFILE=qhack` (the SDK's program-set result reader ignores the session's profile). **Estimated cost USD 17.71** (USD 0.30 + 40 × 1,024 × 0.000425; actual billing to be checked by the author).
- **Candidate revision + config:** `src/qhc/p4/braket_hw.py`, `scripts/braket_submit.py` (`.venv-braket`); E003 seed-0 circuit (couplings from `runs/E003/model_seed0.npz`), 48 ds2s beats (16 per seed-0 simulated predicted class, `default_rng(20261026)`, `runs/E019/beats.json`, label-free), 4 snapshot circuits per beat, 5 disjoint 10-qubit rings per circuit (verbatim native gates on pinned physical qubits), 40 circuits x 1,024 shots
- **Environment and exact command:** `.venv-braket/Scripts/python scripts/braket_submit.py submit --plan runs/E019/plan_rigetti_b48.json --mode programset`; `... fetch ...`; `python -I -m qhc.p4.braket_hw analyse`
- **Raw results and artifacts:** `runs/E019/` (`results/*.json` per circuit with counts and task ARN, `analysis.json`, `analysis_features.npz`, `cost_ledger.jsonl`, `approval.json`, plans, device JSON, pricing, `submit*_stdout.txt`, `fetch_stdout.txt`, `analyse_stdout.txt`)
- **Baseline score / candidate score / signed delta:** **diagnostic (label-free, 48 beats):** hardware vs exact simulation: mean absolute feature difference **0.347** (Z 0.318, ZZ 0.354; by snapshot 0.373, 0.370, 0.335, 0.312), against 0.018 between the 1,024-shot and exact simulations; pooled feature correlation **0.70**, median per-feature correlation 0.53 (by snapshot 0.39, 0.63, 0.52, 0.48); regression slope of hardware on simulated ZZ 0.46 (contraction). Predicted class with the seed-0 readout (trained on noiseless simulated DS1 features): hardware agrees with the finite-shot simulation on **41.7%** of beats and with exact on 37.5%; the ceiling (finite-shot vs exact) is 87.5%. Hardware predictions are skewed to S (N 3, S 35, V 10 of 48).
- **Uncertainty (method from EVAL.md):** none (48 beats, diagnostic)
- **Mechanism check:** local-simulator validation of the same circuits (features within 3.5e-6 of our statevector; packed rings equal single rings; bit order checked against a reversed-order control); 48 of 48 beats complete on hardware.
- **Execution:** completed | **Outcome:** not assessed (diagnostic) | **Verification:** pass (V005, validity; 2026-10-28) | **Adoption:** n/a
- **Limitations and next action:** no readout-error mitigation; one task, one calibration state; 48 beats. The feature contraction and the S-skewed transfer match the device-noise simulation (E015, A021): a readout trained on noiseless features does not transfer to hardware features. EVAL.md's hardware track planned about 100 beats with a macro-F1 on the subset; this run is smaller and label-free (E019 card; USD 35 cap).
