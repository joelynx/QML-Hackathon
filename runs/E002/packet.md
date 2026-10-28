# Verification packet: E002 (R0), validity-only

Assembled 2026-10-26 21:44 UAE from the factual fields of the E002 card (`EXPERIMENTS.md`) and the files named below. The generator's scorecard ratings are in `runs/E002/packet-selfrating.md`; open it only after writing your own ratings.

## Claim under review
E002 is the first reference (R0) of the Phase 3 vertical slice. Validity-only; the comparison checks are n/a because there is no prior incumbent. The claim:
1. The E002 pipeline fits and selects on DS1 only, has no leakage or lookahead, and writes outputs that the EV1 evaluation command accepts.
2. Its reported ds2s score, macro-F1 0.7065 (mean of 5 seeded runs), comes from the approved evaluation command.
3. The slice runs from a clean checkout, and its data provenance is recorded.
4. Every claim in the slice story (`README.md`, "Result so far") has evidence.

## Evaluation version and specification
- EV1, **approved** by the human 2026-10-26 21:26 UAE (revision 5). The approval covers `EVAL.md` sha256 `f758910b94defc3dbbbbb1c735c41d2611755b20ba578340cdd6de9c95a84be9` as presented and evaluation code `9a1922c8898b90db`. The approval line and the change history were written afterwards, as bookkeeping.
- `EVAL.md` lists known defects D1-D6 of the approved version, from the independent audit `EV1_R5_RECHECK.md`. They concern confirmation repairs, the order of input files, low-data provenance and output paths. The restrictions in force are in that table.
- `PROBLEM_BRIEF.md`: the scoring contract and the data. `hackathon_details.md`: the organisers' brief.

## Candidate revision and artifacts
- **Pipeline code** (`src/qhc/pipe/`):
  - Tuning launched with revision `cf7bd4bd0a9634f8`. The launch-time files are reconstructed in `runs/E002/pipe_at_tuning/` (raw hash `cf7bd4bd0a9634f8`, LF-normalised `0b21d3899b1cac7b`). The `pipe_revision` field in most `tuning.jsonl` lines is not the launch revision: it was read from disk when each line was written (E002 card).
  - The final runs used `da67af87f8b8fd73` (recorded in every run manifest).
  - With `75e043aa9915baf2`, all 5 seeds' ds2s predictions, DS1 out-of-fold predictions and model arrays were regenerated bit-identically (`runs/R0_repro_75e043aa/`).
  - Current: `ad80a50e051c6820`. It differs from `75e043aa9915baf2` only by added lines in `run.py`, the `lowdata` command (`runs/E002/pipe_diff_75e043aa_to_ad80a50e.diff`).
- **Evaluation code:** `src/qhc/*.py` at revision `9a1922c8898b90db`; fixtures `tests/test_scorer.py`, hash `7f323fb891968894`, 38 pass.
- **Artifacts** (`runs/E002/`):
  - `tuning.jsonl` and `tune_stdout.txt` (30 configurations);
  - `selected_config.json`;
  - `model_seed{0..9}.npz`;
  - `pred_ds2s_seed{0..4}.csv`, each with a `.run.json` manifest;
  - `oof_ds1_seed{0..9}.csv`;
  - `leakcheck_seed0.json`;
  - `seed_noise_ds1.json`.
- **Selected configuration:** ESN configuration 28 of 30: size 55, spectral radius 0.680, leak 0.102, input scale 0.980, density 0.054, bias 0.537; readout λ = 0.001.
- **Shared design** (`EXPERIMENTS.md`, "Declarations made before any tuning run"):
  - reservoir input: the patient-relative beat window;
  - readout input: K = 220 reservoir features plus 8 RR features;
  - readout: class-balanced multinomial logistic regression with L2, λ chosen from {0.001, 0.01, 0.1, 1} by DS1 grouped-CV out-of-fold macro-F1;
  - decision: argmax.

## Commands (project root, Windows, `.venv`)
```
.venv/Scripts/python -I -m qhc.units                                  # EV1 units (built in Phase 2; MIT-BIH-only rebuild: --splits ds1 ds2s ds2)
.venv/Scripts/python -I -m qhc.pipe.features --splits ds1 ds2s
.venv/Scripts/python -I -m qhc.pipe.run tune  --arm esn --exp E002
.venv/Scripts/python -I -m qhc.pipe.run final --exp E002 --seeds 0 1 2 3 4 --oof --splits ds2s
.venv/Scripts/python -I -m qhc.pipe.run final --exp E002 --seeds 5 6 7 8 9 --oof        # seed-noise diagnostic only
.venv/Scripts/python -I -m qhc.pipe.run leakcheck --exp E002 --seed 0
.venv/Scripts/python -I -m qhc.evaluate compare --split ds2s --role headline --cand runs/E003/pred_ds2s_seed0.csv ... seed4.csv --base runs/E002/pred_ds2s_seed0.csv ... seed4.csv --cand-id E003 --base-id E002 --out runs/E003/compare_ds2s_headline.json
```
The exact argv of the headline is in the last line of `runs/full_eval_log.jsonl`.

## Environment
- Python 3.12.10, Windows 11.
- torch 2.11.0+cu128 on an NVIDIA RTX 6000 Ada.
- `requirements-lock.txt`, plus `pip install -e .`.

## Data and split IDs
- **Raw data:** MIT-BIH Arrhythmia Database v1.0.0, downloaded by `scripts/download_data.py` from PhysioNet's open-data mirror and verified against PhysioNet's SHA256SUMS. Licence ODC-By 1.0.
- **Processed units:** `runs/data/processed/EV1/`, manifest `manifest.json`.
- **ds1:** 44 records in 43 subject groups; 50,964 beats to predict, 50,542 N/S/V units; 5 fixed grouped folds in `ds1_folds.json`.
- **ds2s:** 21 records (DS2 without 202); 47,129 units; 10.53 h.
- **Data card:** `EVAL.md`, "Data card".

## Seeds
- Tuning: reservoir seed 0, search seed 20261026.
- Final runs: reservoir seeds 0-4 (ds2s and DS1 out-of-fold).
- Seeds 5-9: DS1 out-of-fold only, for the seed-noise diagnostic.

## Raw results
- **ds2s, full (EV1).** From `runs/E003/compare_ds2s_headline.json`, arm `baseline`; labels sha256 prefix `bc99cc7493340d0a`.
  - Macro-F1 per seed: 0.7047, 0.7058, 0.7162, 0.7027, 0.7030; mean 0.7065.
  - Seed-averaged sensitivity / PPV / F1: N 0.907 / 0.985 / 0.944; S 0.595 / 0.269 / 0.370; V 0.953 / 0.697 / 0.805.
  - Paper-compatible metrics (de Chazal Table V): VEB Se 0.953, +P 0.697, FPR 0.030; SVEB Se 0.595, +P 0.268, FPR 0.063.
  - Review burden: 806 S-or-V flags per hour; 374 normal beats flagged per hour; 57 missed ectopic beats per hour.
- **DS1 out-of-fold (proxy):**
  - tuning, seed 0: best 0.6744; median of the 30 configurations 0.643; range 0.599-0.674;
  - mean over seeds 0-4: 0.6620;
  - seed-noise diagnostic (seeds 0-4 vs 5-9): +0.0039 [-0.015, +0.022], not triggered.
- **Lookahead check** (`leakcheck_seed0.json`): 731 DS1 beats (records 207, 209, 114, 201; first 150 s), 0 violations. A first attempt before the float64 change flagged 2 beats with probability differences of 1.8e-7 and 2.2e-8 (A011).

## Variants, evaluation count and access history
- **Variants in this line:** 30 ESN configurations, each at 4 λ values; one selected by DS1 out-of-fold score.
- **Full evaluations on EV1:** 1, the headline E003 vs E002 on ds2s, logged 2026-10-26 21:26:59.
- **Earlier entries in `runs/full_eval_log.jsonl`:** 5 re-scorings of the minimal references under draft r4, before approval.
- **ds2:** never scored with a model.
- **Confirmation set (SVDB):** no access (`runs/confirmation_access.jsonl` does not exist). Earlier non-scoring events are in the EVAL.md access log: the data-card inspection and the 17:45 incident.

## Segment results and anomaly facts
- **A009** (E001, diagnostic; DS1 out-of-fold, one untuned configuration per reservoir): RR features alone scored 0.637. Adding the raw beat window lowered this to 0.546. With the patient-relative window instead, relative window + RR scored 0.619, ESN + RR 0.634 and QRC + RR 0.600. The relative window was set as the shared input before tuning.
- **A010:** the ESN's best λ is at the grid's lower edge in 15 of 30 configurations, including the selected one; for the QRC, in 2 of 30.
- **A011:** float32 batch effects. Fixed with float64; the lookahead check passes.
- **A015:** ds2s per-class and per-record facts for both headline arms.
- **Leave-one-record-out headline delta:** from +0.011 (without 213) to +0.046 (without 232).

## Clean-environment reproduction
The run started 21:29 UAE and was still in progress when this packet was assembled. Its results are appended at the end of this file under "Clean-environment results" when it finishes (expected by about 22:05 UAE).

## Open-mode material
- **Scorecard:** `EVAL.md`, "Scorecard" (anchors and weights).
- **Deliverable builds:**
  - `README.md`: question, evaluation summary, "Result so far" story, reproduction commands, layout, licences;
  - demo `runs/demo/qrc_E003_rec232.png`, built by `python -I -m qhc.pipe.demo`;
  - code `src/qhc/`.
- **Data card:** `EVAL.md`, "Data card".

## Operating constraints for the verifier
- Never open `runs/data/processed/EV1/confirm/` or raw SVDB `.atr` files.
- Do not write into `runs/E002/` or `runs/E003/`. Reproduce into a new directory, for example `--exp V004_R0`; `final` reads `runs/<exp>/tuning.jsonl`, or `selected_config.json` when there is no tuning file.
- Any ds2s scoring is appended to `runs/full_eval_log.jsonl` and counts toward the 15-evaluation cap. The command accepts an identical headline rerun (same file contents), and logs it.
- Pipeline code must not read `labels_ds2s.csv`, `labels_ds2.csv` or `confirm/`. Check with `grep -rn "labels_ds2\|confirm/" src/qhc/pipe`.

## Clean-environment results
Appended 2026-10-26 21:58 UAE.

**Setup**
- A fresh copy of `src/`, `tests/`, `scripts/`, `pyproject.toml`, `requirements-lock.txt` and `README.md` (pipeline revision `75e043aa9915baf2`, evaluation `9a1922c8898b90db`), in a scratch directory outside the project.
- A new venv from the system Python 3.12.10, `pip install -r requirements-lock.txt`, then `pip install -e .`. The packages came from the local pip cache.
- **Download:** `scripts/download_data.py --db mitdb` gave 48 records and 144 files, verified against PhysioNet SHA256SUMS, 0 failed. SVDB was not downloaded.
- **Units:** `qhc.units --splits ds1 ds2s ds2`. The partial rebuild merges into an existing manifest and hashes `svdb/SHA256SUMS.txt`, so the project's `manifest.json` and SVDB's `RECORDS` and `SHA256SUMS.txt` (file lists only) were copied in first.
  - All 11 rebuilt MIT-BIH outputs have the same sha256 as the project manifest.
  - The input hashes and the per-split statistics are equal.

**Fixtures:** 37 passed and 1 failed. `test_splits_disjoint_and_released_files_are_label_free` needs `positions_svdb.csv`, which this copy does not build because SVDB was not built.

**Runs, then a comparison with the project's files**
- **Features:** ds1 and ds2s arrays equal.
- **E002:**
  - `tune --arm esn` selects configuration 28 with λ 0.001; the same λ is chosen in all 30 lines.
  - The tuning scores differ from the project's `runs/E002/tuning.jsonl` by at most 3.3e-4, best 0.674487 vs 0.674411. The project's tuning ran before the ESN state update was switched to float64 (A011, E002 card); this copy runs in float64 throughout.
  - `final` predictions for seeds 0-4: every `pred_ds2s_seed*.csv` and `oof_ds1_seed*.csv` is byte-identical to the project's.
  - `leakcheck`: 731 beats, 0 violations.
- **E003:**
  - `tune --arm qrc`: tuning lines identical (apart from time and revision fields); configuration 15, λ 0.1.
  - Every `pred_ds2s_seed*.csv` and `oof_ds1_seed*.csv` is byte-identical.
  - `leakcheck`: 731 beats, 0 violations.
- **Demo:** `qhc.pipe.demo` ran.

**Not done in the clean copy:** the ds2s scoring. The regenerated inputs are byte-identical to the logged headline inputs (hashes in `runs/full_eval_log.jsonl`).

**Wall-clock:** 21:29-21:56.
