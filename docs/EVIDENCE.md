# Evidence index

One row per claim or number in [`README.md`](../README.md): where it comes from, the artifact that holds it, the command that produced it, its result type and the evaluation version. Paths are relative to the repository root. Commands are run from the root with `.venv/Scripts/python -I -m ...` (shown as `python -I -m ...`). Experiment cards with full run manifests are in `EXPERIMENTS.md`.

- **Result types.** *full*: scored on a test split by the approved evaluation command and logged in `runs/full_eval_log.jsonl`; *proxy*: DS1 out-of-fold (training patients only); *diagnostic*: a mechanism check with no test-split score; *n/a*: data provenance, verification or reproduction evidence, arithmetic, or literature.
- **Evaluation versions.** EV1 = approved r5, evaluation code `9a1922c8898b90db` (2026-10-26 21:26 UAE). EV2 = EV1 plus guard fixes only, code `8501643023cd2eb6` (22:14). Scorer, units, metric, split and thresholds are identical; the EV1 headline was rerun under EV2 with identical numbers. Outputs carry their version as `scorer.code_revision`.
- **`compare` shorthand.** `python -I -m qhc.evaluate compare --split ds2s --role <role> --cand <5 prediction files> --base <5 prediction files> --cand-id <id> --base-id <id> --out <json>`; the exact file lists are on each card.
- `runs/data/` (raw data and processed units) is not in the repository; `python scripts/download_data.py` and `python -I -m qhc.units` rebuild it.

## Data and split

| Claim in README | ID | Artifact | Command | Type | EV |
|---|---|---|---|---|---|
| ds2s = DS2 without 202: 21 records, 10.53 h, 47,523 predicted beats, 47,129 units (N 42,148 / S 1,781 / V 3,200); DS1 50,542 units; SVDB 184,286 units | EVAL.md data card and split table | `runs/data/processed/EV1/manifest.json` (rebuilt); counts also in `runs/phase3/clean_build_EV2.md` | `python -I -m qhc.units` | n/a | EV1/EV2 |
| Records 201 and 202 come from the same subject; 202 removed from the test split | A004 | record headers 201.hea, 202.hea; PhysioNet mitdb page (accessed 2026-10-28) | n/a | n/a | EV1 |
| Record 232 holds 1,381 of the 1,781 ds2s S units (77.5%) | A001, A015, EVAL.md | `runs/E003/failure_analysis_ds2s.txt`; S support 1,781 in `runs/E003/compare_ds2s_headline_EV2.json` | derived from the logged comparison output (no further label access) | full (derived) | EV1/EV2 |
| Record 114 stores MLII in channel 1; lead chosen by name | A005 | record headers | n/a | n/a | n/a |
| SVDB: 78 records at 128 Hz, S beats over 73 of 78 records (largest 14.9%); no demographics | EVAL.md SVDB data card; A006 | SVDB headers; PhysioNet svdb page | n/a | n/a | EV1 |
| MIT-BIH population caution ("Pooled results should not be interpreted as estimates of arrhythmia prevalence...") | Limitation 10 | https://physionet.org/content/mitdb/1.0.0/ (accessed 2026-10-28) | n/a | n/a | n/a |
| No digital band-pass or baseline filter; non-finite samples set to 0; SVDB polyphase-resampled to 360 Hz | code | `src/qhc/pipe/features.py` (`load_signal`, `beat_windows`) | n/a (code reading) | n/a | pipeline `55884b1fb66732b9` |

## Baseline R0 (E002) and shared pipeline

| Claim in README | ID | Artifact | Command | Type | EV |
|---|---|---|---|---|---|
| Patient-relative window recovers most of the accuracy that raw morphology loses across patients (RR only 0.637; window + RR 0.546; relative window + RR 0.619) | E001, A009 | `runs/probes/P01_morphology/scores.json`, `stdout.txt` | inline session commands (copied in `stdout.txt`) | diagnostic | EV1 draft r4 data |
| Simulator matches an independent dense-matrix implementation to 4e-7 | E001 mechanism check | `runs/probes/P01_morphology/stdout.txt` | as above | diagnostic | n/a |
| ESN selected configuration (size 55, ρ 0.68, leak 0.10, input scale 0.98, density 0.054, bias 0.54, λ 0.001); DS1 OOF 0.674 | E002 | `runs/E002/selected_config.json`, `runs/E002/tuning.jsonl` | `python -I -m qhc.pipe.run tune --arm esn --exp E002` | proxy | EV1 (pre-approval data, DS1 only) |
| E002 ds2s macro-F1 0.7065 (seeds 0.7027-0.7162); Se/PPV/F1 N 0.907/0.985/0.944, S 0.595/0.269/0.370, V 0.953/0.697/0.805 | E002 | `runs/E003/compare_ds2s_headline.json` (arm `baseline`); predictions `runs/E002/pred_ds2s_seed{0..4}.csv` | `python -I -m qhc.pipe.run final --exp E002 --seeds 0 1 2 3 4 --oof --splits ds2s`; then the headline `compare` | full | EV1 (identical under EV2) |
| Extended λ grid (to 1e-5) selects the same ESN configuration and λ; predictions byte-identical | E010, A010 | `runs/E010/` (`tuning.jsonl`, `selected_config.json`) | `python -I -m qhc.pipe.run tune --arm esn --exp E010 --lambdas 1e-5 1e-4 1e-3 1e-2 1e-1 1`; `final --exp E010 ...` | proxy | EV1 |
| Same for the QRC (configuration 15, λ 0.1) | E011 | `runs/E011/` | `python -I -m qhc.pipe.run tune --arm qrc --exp E011 --lambdas 1e-5 1e-4 1e-3 1e-2 1e-1 1` | proxy | EV1 |
| V004 PASS (validity only): critic reran tuning, finals and lookahead in the project venv (pipeline `55884b1fb66732b9`), 5 ds2s prediction files byte-identical; read, did not rerun, the clean-environment evidence | V004 | `VERIFICATIONS.md` V004; `runs/V004/` (`compare_repro.json`, `hashcheck.json`, `driver_log.json`) | `runs/V004/driver.py` | n/a (verification) | EV1 |
| Clean environment and fresh download reproduce every scored prediction file; one-command check reproduces all 10 headline files and the table byte for byte (26 min) | E002 card; reproduction reports | `runs/phase3/clean_build_EV2.md`, `runs/phase3/reproduce_check_EV2.md`, `runs/phase3/reproduce_check_EV2/repro_check.log` | `python scripts/reproduce.py --skip-data --check` (in a fresh copy) | n/a (reproduction) | EV2 |
| Critic rerun from a clean environment and fresh download: 10/10 headline files and the table byte-identical, 27.3 min, no manual step beyond the README's audit-mode file copy; E018 and Phase 4 validity PASS | V005 | `VERIFICATIONS.md` (V005), `runs/V005/` | README Section 9 audit mode (`scripts/reproduce.py --check`) in a fresh copy | verification | EV2 |
| Every reservoir arm passes the full-pipeline lookahead check (731 DS1 beats, 0 violations); the shared features (incl. the RR block used by E006) pass at the feature level | E002-E005, E007, E008 cards; EXPERIMENTS.md declarations | `runs/E00{2..5}/leakcheck_seed0.json`, `runs/E007/E00{2,3}/leakcheck_seed0.json`, `runs/E008/E00{2,3}/leakcheck_seed0.json` | `python -I -m qhc.pipe.run leakcheck --exp <E###> --seed 0` | diagnostic | EV1/EV2 |
| Tuning scores from float32 code; float64 retune selects the same configurations (scores within 3.3e-4) | A011, V004 M2 | `runs/V004/compare_repro.json`; E002 card | as V004 | diagnostic | EV1 |

## Quantum arm (E003) and controls

| Claim in README | ID | Artifact | Command | Type | EV |
|---|---|---|---|---|---|
| QRC selected configuration (input scale 0.317, J 0.106, h 0.159, depth 2, ring, disorder 0.42, λ 0.1); DS1 OOF 0.667 | E003 | `runs/E003/selected_config.json`, `runs/E003/tuning.jsonl` | `python -I -m qhc.pipe.run tune --arm qrc --exp E003` | proxy | EV1 |
| 220 features = 4 snapshots × (10 ⟨Z⟩ + 45 ⟨ZZ⟩); 1,024 shots per snapshot circuit | E003 card; declarations | `src/qhc/pipe/reservoirs.py` (`QRC`) | n/a (code) | n/a | n/a |
| Mean-field model equals the exact statevector QRC at J = 0 to 3.5e-6 | E004 card | `src/qhc/pipe/reservoirs.py` (`MeanField`); E004 card | validation recorded on the card | diagnostic | n/a |
| Hardware arithmetic: 4 × 1,024 = 4,096 shots per beat; 4,096 × 47,523 = 194,654,208 ≈ 194.7 M shots for ds2s, one seed; 80 logical ZZ interactions in the longest snapshot (2 layers × 10 ring edges × 4 steps), 200 per beat (20 + 40 + 60 + 80) | progress review; E003 configuration | `runs/E003/selected_config.json`; `src/qhc/pipe/reservoirs.py`; `PROGRESS_REVIEW_2026-10-28.md` | arithmetic | n/a (prospective; nothing measured) | n/a |

## Results on ds2s

| Claim in README | ID | Artifact | Command | Type | EV |
|---|---|---|---|---|---|
| Headline: 0.7273 vs 0.7065, +0.0208 [−0.0157, +0.0617], no detectable change (CI includes 0); without 232 +0.0460; leave-one-record-out +0.0111 (without 213) to +0.0460 (without 232) | E003 vs E002 | `runs/E003/compare_ds2s_headline.json` (EV1, logged 21:26:59); `runs/E003/compare_ds2s_headline_EV2.json` (EV2 rerun, logged 22:15:23, identical); `runs/tables/headline_ds2s.md` | `compare --role headline --cand runs/E003/pred_ds2s_seed{0..4}.csv --base runs/E002/pred_ds2s_seed{0..4}.csv --cand-id E003 --base-id E002 --out runs/E003/compare_ds2s_headline.json` | full (pre-registered primary) | EV1 and EV2 |
| E003 per-seed macro-F1 0.7312, 0.7295, 0.7252, 0.7202, 0.7305 | E003 | same | same | full | EV1/EV2 |
| Slice V-F1 0.874 vs 0.805, +0.0688 [+0.0207, +0.1543] (98.75%), favorable | E003 vs E002 | same (`slices.members.V_f1`) | same | full (pre-registered slice) | EV1/EV2 |
| Slice S-F1 0.347 vs 0.370, −0.0231 [−0.1456, +0.0978], no detectable change | E003 vs E002 | same (`slices.members.S_f1`) | same | full (pre-registered slice) | EV1/EV2 |
| Per-class F1 (95%, descriptive): N +0.0168 [+0.0024, +0.0302]; V +0.0688 [+0.0295, +0.1293]; S −0.0231 [−0.1244, +0.0798]. AUPRC V 0.955 vs 0.918, +0.036 [−0.001, +0.138] | E003 vs E002 | same (`per_class_f1`, `auprc`) | same | full (secondary metrics) | EV1/EV2 |
| E003 Se/PPV/F1: N 0.946/0.976/0.961; S 0.421/0.295/0.347; V 0.949/0.811/0.874; S PPV 0.27-0.30 in both arms | E003 | same (`arms.*.seed_average.per_class`) | same | full (secondary metrics) | EV1/EV2 |
| Review burden per hour (10.53 h): flags 806 vs 608 (−198); normal flagged 374 vs 217 (−157); missed ectopic 57 vs 93 (+36, +63%: 92.76 / 56.74); S sensitivity 59.5% vs 42.1% (−17.4 points); V sensitivity 95.3% vs 94.9% | E003 vs E002 | same (`arms.*.seed_average.review_burden`, `per_class`) | same | full (secondary metrics, descriptive) | EV1/EV2 |
| V false positives 1,324 → 709 per seed (records 117, 222, 105, 111, 212; S→V in 232); V TP 3,050 vs 3,036; 310 fewer S TP per seed, 288 in record 232 (781 vs 493 of 1,381) | A015 | `runs/E003/failure_analysis_ds2s.txt` | analysis of the logged comparison output (no further label access) | full (derived, descriptive) | EV1 |
| Refit on 5 training patients: 0.6898 vs 0.6984, −0.0086 [−0.0858, +0.0794] (98.75%) | E007 | `runs/E007/compare_ds2s_lowdata_k5.json`; `runs/tables/lowdata_k5_ds2s.md` | `python -I -m qhc.pipe.run lowdata --exp E007 --from-exp E003 --k 5 --splits ds2s` (and `--from-exp E002`); `compare --role lowdata_k5 ...` | full (pre-registered slice) | EV2 |
| Refit on 11 training patients: 0.6944 vs 0.7253, −0.0308 [−0.1045, +0.0546] (98.75%) | E008 | `runs/E008/compare_ds2s_lowdata_k11.json`; `runs/tables/lowdata_k11_ds2s.md` | `python -I -m qhc.pipe.run lowdata --exp E008 --from-exp E003 --k 11 --splits ds2s` (and `--from-exp E002`); `compare --role lowdata_k11 ...` | full (pre-registered slice) | EV2 |
| QRC vs mean-field: 0.7273 vs 0.7234, +0.0039 [−0.0028, +0.0115]; V F1 both round to 0.874, difference −0.0001 [−0.0155, +0.0166]; S F1 +0.0107 [−0.0002, +0.0246]; mean-field 615 flags, 224 normal flagged, 93 missed per hour | E004, A016 | `runs/E004/compare_ds2s_secondary_E003_vs_E004.json`; `runs/tables/secondary_E003_vs_E004_ds2s.md` | `python -I -m qhc.pipe.run control --exp E004 --kind mf --from-exp E003 --oof --splits ds2s`; `compare --role secondary --cand runs/E003/... --base runs/E004/... --cand-id E003 --base-id E004` | full (secondary, descriptive) | EV2 |
| Separable vs QRC: 0.7264 vs 0.7273, −0.0009 [−0.0444, +0.0319]; V F1 −0.0634 [−0.1321, −0.0210]; S F1 +0.0671 [−0.0139, +0.1308] | E005, A016 | `runs/E005/compare_ds2s_secondary_E005_vs_E003.json`; `runs/tables/secondary_E005_vs_E003_ds2s.md` | `python -I -m qhc.pipe.run control --exp E005 --kind sep --from-exp E003 --oof --splits ds2s`; `compare --role secondary --cand runs/E005/... --base runs/E003/... --cand-id E005 --base-id E003` | full (secondary, descriptive) | EV2 |
| RR only: 0.6997; S F1 0.390, V F1 0.739 | E006 | `runs/E006/score_ds2s.json` | `python -I -m qhc.pipe.run rronly --exp E006 --oof --splits ds2s`; `python -I -m qhc.evaluate score --split ds2s --pred runs/E006/pred_ds2s_seed0.csv --id E006 --out runs/E006/score_ds2s.json` | full (`score`, single run, descriptive) | EV2 |
| On DS1 the QRC gives fewer V false positives than the ESN at every λ; the S-side reduction is mainly the QRC's selected λ | E009 | `runs/E009/matched_lambda_ds1.json` | `python -I runs/E009/matched_lambda.py` | diagnostic (DS1 OOF) | none (DS1 only) |
| Figure: per-class F1 per arm | E002-E006 | `docs/figures/ds2s_per_class_f1.png` | `python -I scripts/make_figure.py` (reads the four JSONs above; no label access) | full (derived) | EV1/EV2 |

## Evaluation process

| Claim in README | ID | Artifact | Command | Type | EV |
|---|---|---|---|---|---|
| Pre-registration; EV1 approved 2026-10-26 21:26, EV2 22:14; 43 fixture tests | EVAL.md | `EVAL.md`; `tests/test_scorer.py` | `python -I -m pytest -q` | n/a | EV1, EV2 |
| 7 of 15 test-split scorings used before Phase 4: the headline under EV1 and its identical EV2 rerun (2), plus E004, E005, E006, E007 and E008 (5) | EVAL.md, STATE.md | `runs/full_eval_log.jsonl` (12 lines incl. 5 pre-approval reference re-scorings that do not count) | appended automatically by `qhc.evaluate` | n/a | EV1/EV2 |
| SVDB guard incident 2026-10-26 ~17:45: no label values or scores displayed or stored; V002 judged SVDB not compromised | EVAL.md access log, V002 | `EVAL.md` ("Access log"); `VERIFICATIONS.md` V002 | n/a | n/a | EV1 draft |
| SVDB demo shot-key mismatch; no scored result affected | A017 | `ANOMALIES.md` A017; `PROGRESS_REVIEW_2026-10-28.md` | review probe (synthetic beat) | diagnostic | n/a |
| Saved-artifact loading gap; predict-only path for the confirmation | A018 | `ANOMALIES.md` A018; `src/qhc/p4/predict.py` | n/a | n/a | EV2 |
| Annotation totals differ from de Chazal Table II by at most 2 beats per class | A008 | `tests/test_scorer.py::test_units_match_current_dataset_counts`; `EV1_R3_REVIEW.md` | `python -I -m pytest -q` | n/a | EV1 |

## Literature and citations

| Claim in README | Source | How checked | Type |
|---|---|---|---|
| de Chazal et al. 2004 report SVEB positive predictivity 38.5% on DS2 | doi:10.1109/tbme.2004.827359 | abstract via the paperfetch store (2026-10-28) | n/a |
| Bowles et al. 2024: 12 models, 160 datasets; classical models outperform; removing entanglement often as good or better | doi:10.48550/arxiv.2403.07059 | abstract and notes in the paperfetch store | n/a |
| Pandey 2026: advantages disappear under matched size and tuning (abstract only) | doi:10.48550/arxiv.2607.09905 | abstract in the paperfetch store; full text not accessed | n/a |
| Gupta et al. 2025: "no consistent trend to support empirical quantum utility in digital health" | doi:10.1038/s41746-025-01597-z | abstract (PubMed) via the paperfetch store | n/a |
| Kornjača et al. 2024: classical-spin control; Huang et al. 2021: geometric difference | doi:10.48550/arxiv.2407.02553; doi:10.1038/s41467-021-22539-9 | metadata and abstracts in the paperfetch store | n/a |
| "No quantum reservoir study on MIT-BIH with an inter-patient split and a matched classical reservoir was found" | our scan, about 31 papers, 2026-10-26 | `PROBLEM_BRIEF.md` ("Problem selection"); paperfetch tag `qhack-phase1` | n/a (scoped to our search) |
| Data citations (MIT-BIH, SVDB Greenwald 1990 Ph.D. thesis, PhysioNet standard citation) | https://physionet.org/content/mitdb/1.0.0/, https://physionet.org/content/svdb/1.0.0/ | copied from the PhysioNet pages, accessed 2026-10-28 | n/a |
| Jaeger 2001, GMD Report 148 | carried over from the 2026-10-26 draft | not re-checked against a source in this session | n/a |

## Phase 4 and the SVDB confirmation (results filled 2026-10-28 ~20:10 UAE)

Designs on the cards in `EXPERIMENTS.md` (declared 2026-10-28 ~18:50 UAE, before any run); results on the same cards. Every ds2s comparison here is secondary, descriptive and post-hoc; E018 is the pre-registered confirmation.

| Experiment | What it tests | Artifact | Command | Type | EV | Result |
|---|---|---|---|---|---|---|
| E012 | exact expectations vs 1,024 shots, E003 configuration, λ 0.1 | `runs/E012/` | `python -I -m qhc.p4.ablate e012`; `compare --role secondary --cand E012 --base E003` | proxy; full (secondary) | EV2 | E012 vs E003 +0.0005 [−0.0058, +0.0081], no detectable change; DS1 OOF 0.6693 vs 0.6671 (`runs/E012/compare_ds2s_secondary_E012_vs_E003.json`, `summary.json`) |
| E013 | shot sweep {64, 256, 4,096} on DS1 | `runs/E013/` | `python -I -m qhc.p4.ablate e013 --shots 64 256 4096 1024` | proxy | EV2 (DS1 only) | DS1 OOF 0.6478 / 0.6598 / 0.6671 / 0.6681 / 0.6693 at 64 / 256 / 1,024 / 4,096 / exact (`runs/E013/table.csv`, `summary.json`) |
| E014 | qubit count {6, 8, 12} and Z-only readout; DS1-rule variant to ds2s | `runs/E014/` | `python -I -m qhc.p4.ablate e014 --variant <n6/n8/n12/z10>`; `e014-final`; `compare --role secondary --cand <variant> --base E003` | proxy; full (secondary) | EV2 | DS1 OOF n6 0.6803, n8 0.6673, n12 0.6635, Z-only 0.6776 (E003 0.6671); n6 selected; E014-n6 vs E003 +0.0078 [−0.0055, +0.0188] (`runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json`, `table.csv`) |
| E015 | device-noise trajectories at Rigetti Cepheus and IQM Garnet calibration rates; Rigetti to ds2s | `runs/E015/` | `python -I -m qhc.p4.noise rates / check / run --device rigetti --splits ds2s / report`; `compare --role secondary --cand E015-rigetti --base E003` | proxy; full (secondary) | EV2 | rates in `runs/E015/calibration_*.json`, `summary.json`; DS1 OOF Rigetti 0.6463, IQM 0.6527; Rigetti vs E003 +0.0016 [−0.0331, +0.0248], V F1 −0.053 [−0.114, −0.020] (`runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json`) |
| E016 | gradient-boosting context model, N = 30 DS1 configurations | `runs/E016/` | `python -I -m qhc.p4.boost tune / final --splits ds2s / leakcheck --seed 0`; `compare --role secondary --cand E003 --base E016` and `--cand E002 --base E016` | proxy; full (secondary) | EV2 | E003 vs E016 +0.0057 [−0.1389, +0.0676] (w/o 232 −0.0869; V −0.068 [−0.159, −0.031]); E002 vs E016 −0.0151 [−0.1896, +0.0766] (w/o 232 −0.1329) (`runs/E016/compare_ds2s_secondary_E00{3,2}_vs_E016.json`); S predictions label-free count in `summary.json` |
| E017 | kernel-target alignment, linear CKA, geometric difference on DS1 | `runs/E017/` | `python -I -m qhc.p4.kernels --out runs/E017` | diagnostic | EV2 (DS1 only) | CKA QRC–mean-field 0.986, QRC–ESN 0.525; KTA and geometric differences in `runs/E017/summary.json` and CSVs |
| E018 | SVDB confirmation of the frozen pair E003 vs E002 (confirmed if delta > 0 and 95% CI lower bound > 0) | `runs/E018/`; `runs/confirmation_reports/` | `python -I -m qhc.p4.predict predict --exp E00{2,3} --split ds2s ...` (hash self-check), `... --split svdb ...`; `python -I -m qhc.evaluate compare --split svdb --role confirmation ...` | full (confirmation) | EV2 | **not confirmed**: 0.6402 vs 0.6488, −0.0085 [−0.0476, +0.0274]; V F1 0.570 vs 0.574 (`runs/E018/confirm_svdb.json`; archive `runs/confirmation_reports/access_1.json`, sha256 39c6b7e7…; self-check `runs/E018/summary.md`) |
| E019 | Braket hardware features of E003's seed-0 circuits on a label-free ds2s subset | `runs/E019/` (incl. `cost_ledger.jsonl`) | `python -m qhc.p4.braket_hw prepare / plan / reference / analyse`; `scripts/braket_submit.py` (`.venv-braket`, per-task approval) | diagnostic | EV2 | hardware vs exact MAD 0.347 (shot-vs-exact 0.018), pooled corr 0.70, ZZ slope 0.46, class agreement 41.7% (ceiling 87.5%) (`runs/E019/analysis.json`); task ARN and cost in `runs/E019/cost_ledger.jsonl`, `results/` |
