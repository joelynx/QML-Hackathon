# Evaluation specification (open mode)

- **Version:** **EV2** | **State:** **approved** (2026-10-26 22:14 UAE). EV2 = EV1 (approved r5) plus the guard fixes for the known defects D1-D6 (`EV1_R5_RECHECK.md`). The scorer, units, metric, split, thresholds and slice family are unchanged. Evaluation code `8501643023cd2eb6`, fixtures `8a0ffb8e64f4f88b` (43 pass). EV1 history below.
- **EV2 approval:** approved by the author 2026-10-26 22:14 UAE ("Approved to both."). Both the D1-D6 fix and a full clean build that rebuilds the SVDB units in a scratch copy were approved in that message. The r5 code is preserved in `runs/EV1_r5_snapshot/`.
  - **Version label in outputs:** `evalspec.EV` still reads "EV1". It names the unit set (`runs/data/processed/EV1/`, unchanged in EV2), and the approved code was deployed unchanged. The evaluation version of any output is identified by its `code_revision`: `9a1922c8898b90db` = EV1 r5, `8501643023cd2eb6` = EV2. Renaming the label would change the code, which needs the author's approval.
  - **Counting:** test-split scorings are counted cumulatively across EV1 and EV2 against the cap of 15 (EV1: 1, the headline).
- **EV1:** **approved** (revision 5, after the independent review of r3 and the re-check V003 of r4)
- **Approval:** approved by the author 2026-10-26 21:26 UAE ("Approved."). The approval covers this file as presented, sha256 `f758910b94defc3dbbbbb1c735c41d2611755b20ba578340cdd6de9c95a84be9` (before this approval line and the change-history entry were written, which is bookkeeping), evaluation-code revision `9a1922c8898b90db` (top-level `src/qhc/*.py`, LF-normalised), fixtures `7f323fb891968894` (38 pass), processed units in `runs/data/processed/EV1/` with `lowdata_subsets.json` sha256 `6348bd6c817b057c55e885bcfefd3f041e3563d74a53de841f88bfde78d982f1`. Any change to the evaluation code or this specification from here needs the author's approval and creates a new version.
  - Drafted 2026-10-26 ~17:29 UAE.
  - Metric review V001 (2026-10-26): 3 blocking, 7 should-fix and some minor findings.
  - All are addressed (see "Response to V001" at the end).
  - Re-check V002 (2026-10-26): every finding resolved except S7, which was partly fixed; no new blocking issue; the SVDB incident does not compromise the confirmation set.
  - The V002 residuals are closed in revision 3.
  - Independent review of r3 (`EV1_R3_REVIEW.md`, supplied by the author 2026-10-26 ~18:25): recommended a focused revision (R1-R6, five additional changes, six small corrections) before approval. All are addressed in revision 4 (see "Response to the independent review of r3" at the end).
  - Re-check V003 of r4 (2026-10-26): NEEDS-CHANGES, 1 blocking (order on the test splits only partly enforced), 3 should-fix (copies as seeds, a failure after a logged confirmation access, a repair with different models) and 6 minor. All are addressed in revision 5 (see "Response to V003" at the end).
  - V003 follow-up on an intermediate r5 (revision `ba12ebc1e0ad903c`): APPROVE-READY, every earlier finding resolved; one should-fix (N1) and four minor (N2-N5). N1-N4 are fixed in the final r5; N5 is handled procedurally (below).
- **Brief version:** `hackathon_details.md` as read 2026-10-26. Problem C1, chosen by the author 2026-10-26 (PROBLEM_BRIEF.md).
- **Code revision:** no git repository yet.
  - Revision = first 16 hex of sha256 over `cat src/qhc/*.py` (files in sorted order, line endings normalised to LF; `qhc.evaluate.code_revision()` computes it and every output records it): **`9a1922c8898b90db`** (r5 scorer identity).
  - Scope: the evaluation code is the top-level `src/qhc/*.py` only. Pipeline and model code lives in the `src/qhc/pipe/` subpackage, is identified by its own hash on each experiment card and run manifest, and never changes this revision.
  - History: r1-r2 `dd225b75db9a8c68` (the r3 reference results were computed here); r3 `9c74cdcb7d673bc7`; r4 `a2439884ff2f1909` (the r4 reference re-scorings in `runs/EV1_reference_r4/` were computed here; r5 changes no metric, so they stand). The r3 source and processed outputs are kept in `runs/EV1_r3_snapshot/`.
  - Fixture tests `tests/test_scorer.py`: `7f323fb891968894`.
  - Environment: `requirements-lock.txt` (pip freeze, Python 3.12.10). The project package is installed separately with `pip install -e .` from the project root (the lockfile no longer carries an absolute editable path).
  - Raw-data download and verification: `python scripts/download_data.py`.

## Data card
Two databases, both open access on PhysioNet under the Open Data Commons Attribution License v1.0. The brief places no restriction on data, so they are allowed. Attribution is required: Moody & Mark 2001 (IEEE EMB 20(3):45-50) for MIT-BIH; Greenwald 1990 (PhD thesis, Harvard-MIT HST) for SVDB; plus the standard PhysioNet citation.

### MIT-BIH Arrhythmia Database v1.0.0: training, tuning, and primary test
- **Source and link:** https://physionet.org/content/mitdb/1.0.0/. Files from the AWS mirror `https://physionet-open.s3.amazonaws.com/mitdb/1.0.0/`, downloaded 2026-10-26.
- **Licence, and allowed under the rules?:** ODC-By 1.0; yes.
- **Provenance:** from the database documentation (https://physionet.org/physiobank/database/html/mitdbdir/intro.htm, read 2026-10-26).
  - Origin: over 4,000 long-term Holter recordings made by the Beth Israel Hospital Arrhythmia Laboratory between 1975 and 1979, about 60% from inpatients.
  - Selection:
    - Records 100-124: 23 records whose tapes and half-hour segments were chosen at random.
    - Records 200-234: 25 records selected for rare but clinically important arrhythmias.
  - Subjects: 47 (25 men aged 32-89, 22 women aged 23-89). Records 201 and 202 are the same man (A004).
  - Annotation: a slope-sensitive QRS detector proposed beats. Two cardiologists then annotated each record independently, and disagreements were "reviewed and resolved by consensus".
  - Digitisation: 360 Hz, 11-bit over ±5 mV, 0.1-100 Hz analog band-pass.
- **Size, fields, date range:**
  - 48 records of about 30.1 min, two leads each. The upper lead is usually modified limb lead II (MLII); record 114 is reversed (A005). Records 102 and 104 use V5.
  - About 109,000 beat labels, recorded 1975-1979.
  - Fields used: the MLII signal, chosen by lead name, and the reference beat annotations (`.atr`: sample index and symbol).
- **Raw download path and hash:**
  - Path: `runs/data/raw/mitdb/` (144 files), untouched.
  - Every file matches PhysioNet's `SHA256SUMS.txt`. The hash of that sums file is `b61158a96d5f2ca80edfb354a9a66a6324836c390a84e1966dcee2b907d6be43`.
- **Cleaning steps and code revision:**
  - No edits to raw files.
  - **Beat positions:** only beat annotation codes (`evalspec.BEAT_SYMBOLS`). Non-beat annotations are never beat positions, including `!` (ventricular flutter wave). 472 of these in DS1 record 207 were released as positions in r1-r3 (A007).
  - In r4 the MIT-BIH splits were rebuilt with `python -I -m qhc.units --splits ds1 ds2s ds2`. The SVDB outputs were kept from the r3 build: the SVDB symbol counts above contain no `!`, so R1 cannot change them, and the SVDB annotations were not reopened. ds2s, ds2 and svdb outputs are byte-identical to r3; only the DS1 positions and labels changed.
  - `python -I -m qhc.units` writes to `runs/data/processed/EV1/`, with hashes in `manifest.json`:
    - `positions_<split>.csv`: all beat annotation positions, with a label-free `predict` flag.
    - `records_<split>.csv`: record durations.
    - `labels_<split>.csv`: scorer only.
  - **Prediction set (label-free):** every beat annotation except the first and last of each record and any beat within 1.0 s of the record start or end. Pipelines must predict every beat in this set, F and Q beats included.
  - **Evaluation units:** the prediction-set beats whose AAMI class is N, S or V. AAMI mapping as in de Chazal 2004: N = N L R e j; S = A a J S; V = V E; F = F; Q = / f Q.
  - Paced records 102, 104, 107 and 217 are excluded everywhere.
- **Known biases and gaps:**
  - Population: 1970s ambulatory recordings from one hospital and an older population; 47 subjects.
  - S beats are rare and concentrated by patient (A001).
  - One subject sits on both sides of the published split (A004).
  - Leads vary by record (A005).
  - Beat locations come from expert annotations, not a detector, so detection errors are absent.
  - F (fusion, 0.8%) and Q beats are predicted but not scored in the primary metric. How they get classified is reported.
- **Validity: what the data measures vs what the decision needs:**
  - The decision is to flag ectopic beats for review in long ambulatory ECGs from patients the model has not seen. The labels are cardiologist consensus beat classes, which match the decision unit directly.
  - Gaps:
    - Clinical action is usually taken at the episode or rhythm level, not per beat.
    - Oracle beat positions overstate real-world performance.
    - Generalisation is measured on 21 MIT-BIH test patients plus the 78 SVDB records, a small and old population.
- **Synthetic or simulated parts (declared):** none in the data. Quantum reservoirs are simulated on classical hardware. Their outputs are model features, not data, and every simulated or hardware-run arm is labelled as such.

### MIT-BIH Supraventricular Arrhythmia Database (SVDB) v1.0.0: confirmation set
- **Source and link:** https://physionet.org/content/svdb/1.0.0/. Files from the AWS mirror, downloaded 2026-10-26. Approved by the author 2026-10-26.
- **Licence, and allowed under the rules?:** ODC-By 1.0; yes.
- **Provenance:** 78 half-hour two-lead recordings "chosen to supplement the examples of supraventricular arrhythmias in the MIT-BIH Arrhythmia Database". `ANNOTATORS` lists only "atr: reference beat and signal quality annotations". The PhysioNet page does not state how many subjects there are or who annotated.
- **Size, fields, date range:**
  - 78 records at 128 Hz, 230,400 samples (30 min) each. Leads are named only ECG1 and ECG2.
  - Headers carry no demographics. Recording dates are not stated.
  - Annotation symbols: N 162,339; S 12,188; V 9,943; J 9; a 1; F 23; Q 79; non-beat `~` 1,082, `|` 2,211, `+` 1; B 1.
- **Raw download path and hash:**
  - Path: `runs/data/raw/svdb/` (234 data files), untouched.
  - All files match PhysioNet's `SHA256SUMS.txt`, whose hash is `59791a754f68ac6889424a22aced4bffc90b6d03389f9f49ae95b6e345be3552`.
- **Cleaning steps and code revision:**
  - Same unit rules and code as MIT-BIH, at the native 128 Hz.
  - SVDB labels are written to `runs/data/processed/EV1/confirm/` and read only through the guarded confirmation path.
  - **Pipeline input, fixed now without labels:** channel 0 (`ECG1`), resampled from 128 Hz to the pipeline's working rate by polyphase resampling, then the same filtering as for MIT-BIH.
- **Known biases and gaps:**
  - Different sampling rate and unknown lead identity from MIT-BIH, so all models face a domain shift.
  - Subject overlap with MIT-BIH cannot be checked (A006). If records share subjects, the record bootstrap is anti-conservative.
  - The recordings were selected for supraventricular arrhythmia, so the S prevalence (6.6% of units) is higher than in MIT-BIH (1.9% in ds1, 3.8% in ds2s).
- **Validity:** its S beats are spread over 73 of 78 records (the largest record holds 14.9%). It therefore tests S-class generalisation far better than ds2s, where record 232 holds 77.5% (A001).
- **Synthetic or simulated parts:** none.

## Technical metric
- **Metric, direction, units:** macro-averaged F1 over the AAMI classes N, S and V, on the evaluation units of a split, beats pooled across records. Higher is better; units are F1 points in [0, 1].
  - Per-class F1 = 2TP / (2TP + FP + FN).
  - A class absent from both truth and predictions scores 1. A class with TP = 0 but some FP or FN scores 0.
  - Hard decisions come from the `pred` column. Each arm's decision rule (argmax or thresholds) must be produced by the same procedure in both arms, fitted on DS1 within the tuning budget.
- **Secondary metrics, reported for every scored arm, per seed and seed-averaged (none of them sets the outcome):**
  - **N/S/V-restricted** (counts over N/S/V-truth units only):
    - per-class sensitivity, PPV and F1;
    - record-averaged sensitivity and PPV (`nsv_record_avg_*`), averaged over the records containing that class, or predicting it for PPV;
    - class-specific false S and V flags per hour (`nsv_class_false_flags_per_hour`).
    - These are *not* EC57 measures and are not directly comparable with the literature.
  - **Paper-compatible** (`paper_compatible`): the gross (beat-pooled) VEB and SVEB sensitivity, positive predictivity and false-positive rate of de Chazal 2004, Table V(a)-(b), over the full prediction set.
    - VEB: FP = Nv + Sv; Fv and Qv are neither rewarded nor penalised.
    - SVEB: FP = Ns + Vs + Fs; Qs is neither rewarded nor penalised.
    - Any truth class outside N/S/V/F/Q (one SVDB `B` beat) counts as Q.
    - These follow the paper's printed definitions. The complete EC57 standard and its later revisions were not audited.
  - **Review burden** (`review_burden`; full prediction set, per hour of recording):
    - all S-or-V flags;
    - normal beats flagged;
    - F/Q beats flagged;
    - S<->V class swaps (an ectopic beat flagged with the wrong class);
    - missed ectopic beats (S or V predicted N).
  - per-class AUPRC for S and V (threshold-free), with the same paired bootstrap in comparisons;
  - how F and Q beats were classified;
  - per-record N/S/V confusion matrices and per-record 5 x 3 paper-compatible tables (truth N/S/V/F/Q by prediction), per seed.
  - A macro-F1 gain is never presented as proof that every clinically relevant error improved. The review-burden and paper-compatible tables are reported next to it.
  - Per-record macro-F1 is deliberately not used: with the vacuous-class rule, one false flag in an S-free record moves its S-F1 from 1 to 0.
- **Why this metric (tied to the user's decision; alternatives considered and why not):**
  - The user reviews flagged beats, and two kinds of error cost them:
    - A missed ectopic beat (low sensitivity) can hide an arrhythmia.
    - A false flag (low PPV) adds review burden. The `rr_rule` reference has S PPV 0.257, about 413 false S flags per hour.
  - F1 per class combines sensitivity and PPV. Macro-averaging weights the rare S and V classes equally with N, which is about 89% of beats.
  - Alternatives:
    - **Accuracy:** dominated by N; the all-N constant scores 0.894 on ds2s.
    - **Balanced accuracy:** ignores false alarms.
    - **Macro AUROC:** threshold-free, but insensitive to the operating point the user experiences. AUPRC is reported as the threshold-free secondary instead.
    - **Per-class sensitivity and PPV (N/S/V-restricted, and the paper-compatible VEB/SVEB measures):** several numbers, no single decision rule. Reported as secondary.
    - **Matthews correlation:** sound, but not standard in this literature, where F1 is (e.g. Niu et al. 2020, `doi:10.1109/jbhi.2019.2942938`).
- **Declared before modeling on:** 2026-10-26 (PROBLEM_BRIEF.md, Phase 1); no model exists yet. **Review of the choice:** V001 (2026-10-26), findings addressed below; re-check requested.
- **Prediction unit, target, decision-time boundary:**
  - Unit: one prediction-set beat. Scored if it is an evaluation unit. Target: its AAMI class among N, S and V.
  - **Boundary:** for beat i at R-peak sample t_i, inputs may use the signal and beat positions of the same record up to b_i = max(t_{i+1}, t_i + 1.0 s), and all earlier data, plus parameters fitted on DS1.
    - This is one-beat lookahead with latency max(1 s, next RR interval). The latency exceeds the next RR interval when that interval is shorter than 1 s. The longest next-RR interval in ds2s is 5.87 s; 15.6% of ds2s units have a next beat more than 1 s away.
  - Not allowed:
    - any label of a test record;
    - any statistic of a test record computed beyond b_i (e.g. whole-record mean RR, whole-record amplitude normalisation);
    - anything fitted on ds2s, ds2 or svdb.
  - **Enforcement:**
    - `qhc.leakcheck.check_lookahead` takes a pipeline's per-record function f(signal, samples, fs) -> per-beat outputs. It replaces the signal after b_i with noise, drops positions after b_i, and requires row i unchanged. Fixtures: a causal feature passes; a whole-record mean RR fails; a 3 s window fails.
    - Every pipeline must pass it on at least 200 beats from at least 3 DS1 records before its first full evaluation, and the result goes on the experiment card.
    - Fitting anything across test records (for example normalisation statistics of the test split) is not allowed. The lookahead check works per record, so this is checked by code review in every verification.
    - Released files for test splits (`positions_*`, `records_*`) contain no label-derived field (tested). The `predict` flag is recomputed from positions and record length alone in the tests.
  - **Pre-declared sensitivity analysis (optional, headline pair only):** a causal-only boundary b_i = t_i + 0.5 s, so post-RR is available only when the next beat falls within 0.5 s. A secondary full evaluation, counted against the cap.
- **Split and construction:**

  | Split ID | Records | Prediction set | Units (N / S / V) | Role |
  |---|---|---|---|---|
  | `ds1` | de Chazal DS1, 22 records | 50,964 (51,436 in r1-r3, A007) | 50,542 (45,813 / 943 / 3,786) | All training and tuning, by grouped 5-fold CV on fixed folds (`ds1_folds.json`) |
  | `ds2s` | de Chazal DS2 without record 202, 21 records (10.53 h) | 47,523 | 47,129 (42,148 / 1,781 / 3,200) | **Primary full evaluation** |
  | `ds2` | de Chazal DS2, 22 records | 49,657 | 49,262 (44,207 / 1,836 / 3,219) | Secondary, for comparison with published numbers only; counts against the cap |
  | `svdb` | SVDB, 78 records | 184,389 | 184,286 (162,160 / 12,193 / 9,933) | Confirmation; access-capped |

  - Fold contents (N / S / V): fold0 11,343 / 113 / 612; fold1 10,604 / 104 / 126; fold2 7,615 / 383 / 965; fold3 9,020 / 107 / 685; fold4 7,231 / 236 / 1,398. Record 209 holds 383 of the 943 DS1 S units, so S cannot be balanced further at the record level.
  - Tuning score: macro-F1 on pooled out-of-fold DS1 predictions (a *proxy* result).
  - Preprocessing: every fitted quantity is fitted on DS1 only, inside the CV fold when tuning.
  - Overlap checks:
    - Records are disjoint across ds1, ds2s and svdb (tested).
    - The 201/202 subject overlap is removed from ds2s.
    - MIT-BIH/SVDB subject overlap cannot be checked (A006).
    - **Counts against de Chazal 2004** (corrected in r4; the r1-r3 claim of an exact reproduction was false):
      - EV1 uses de Chazal's record split and AAMI class mapping, with the documented current-annotation differences below (A008).
      - Totals are over all beat annotations, before EV1's edge and first/last exclusions.
      - Fixture `test_units_match_current_dataset_counts` checks the current counts and this difference table. It does not verify the historical table.
      - Labels are not altered to force agreement. The cause of the differences is unverified.

      | Split / class | de Chazal Table II | Current annotations | Current minus paper |
      |---|---:|---:|---:|
      | DS1 N | 45,868 | 45,866 | -2 |
      | DS1 S | 942 | 944 | +2 |
      | DS1 V | 3,787 | 3,788 | +1 |
      | DS1 F / Q | 415 / 8 | 415 / 8 | 0 / 0 |
      | DS2 N | 44,258 | 44,259 | +1 |
      | DS2 S / V | 1,837 / 3,221 | 1,837 / 3,221 | 0 / 0 |
      | DS2 F / Q | 388 / 7 | 388 / 7 | 0 / 0 |

    - **Literature comparisons on ds2 are contextual only:**
      - EV1 removes edge beats, predicts three classes, selects MLII by name, and imposes a stricter temporal boundary.
      - de Chazal's Section IV-D features use a whole-record average RR and a local average over surrounding intervals, which EV1 forbids. This is disclosed, not loosened.
- **Scorer revision / command / output:** revision `8501643023cd2eb6` (EV2; EV1 r5 was `9a1922c8898b90db`).
  - `python -I -m qhc.evaluate score --split ds2s --pred P.csv --id NAME --out runs/E###/score_ds2s.json` (refused for svdb)
  - `python -I -m qhc.evaluate compare --split ds2s --role headline --cand C_seed*.csv --base B_seed*.csv --cand-id X --base-id Y --out runs/E###/compare_ds2s.json`
  - **Roles** (`--role`, required):
    - `headline`: ds2s only. The single pre-registered pair; refused once a different headline is logged.
    - `lowdata_k5`, `lowdata_k11`: ds2s only; members of the slice family.
    - `secondary`: ds2s or ds2; descriptive.
    - `confirmation`: svdb only.
    - `diagnostic`: ds1, ds2s or ds2. Minimal references and the seed-noise check; may use fewer than 5 runs per arm and no run manifests.
  - Prediction file: CSV with `beat_id,pred,prob_N,prob_S,prob_V`, one row per prediction-set beat. Probabilities are mandatory.
  - **Run manifest (strict roles: every role except `diagnostic`):** next to each prediction file, `<file without .csv>.run.json` with `arm_id, seed, split, config_id, code_revision, model_artifact, model_artifact_sha256, reservoir_seed, shot_seed, prediction_sha256`. `shot_seed` is null for arms without measurement sampling. The low-data roles also need `parent_config_id` (the headline configuration of that arm), `train_records` (the DS1 records the readout was fitted on) and `refit_scope` (the role) (EV2, D4).
  - **Checked before any label access** (tested):
    - exactly 5 files per arm in strict roles;
    - no file given twice, by resolved path, across both arms (all roles);
    - every manifest present and complete, its prediction hash matching the file, and its model artifact present with a matching hash;
    - one `arm_id` and one `config_id` per arm, and different `arm_id`s for the two arms;
    - within an arm: distinct seed ids, distinct model-artifact files with distinct content hashes, and distinct (reservoir_seed, shot_seed) pairs;
    - the same seed indices in both arms (matched rule 1);
    - the role allowed for the split, the order rules below, and the predictions valid against the label-free prediction set;
    - low-data roles (EV2, D4): every run's `parent_config_id` equals the `config_id` of its own arm in the logged headline (candidate to candidate, baseline to baseline), its `train_records` equal the frozen subset for k, and its `refit_scope` equals the role;
    - `--out` (EV2, D5): not an input prediction file or run manifest, a referenced model artifact, either evaluation ledger, a confirmation report, or a path inside the processed data; for the confirmation split it must not exist yet (D2).
    - Strict arms are scored in seed order and diagnostic arms in content-hash order, so the same files in any order or location give identical numbers (EV2, D3).
    - Identical predictions from different valid runs are allowed; provenance is validated, not prediction diversity.
  - **Order on the test splits ds2s and ds2** (tested; review V003 B1):
    - Until the headline is logged, the only predictions that may be scored there are the four minimal-reference prediction files of `runs/EV1_reference_r4/` (their sha256 are frozen in `evalspec.REFERENCE_PRED_SHA256`).
    - `diagnostic` comparisons there are limited to those files at all times.
    - `score`, `secondary` and the low-data roles there are refused until the headline is logged.
    - The headline is refused if the log holds any earlier non-reference scoring of ds2s or ds2, and it must compare models: the minimal references alone cannot be the headline (V003 N1).
    - The confirmation split is refused until a (non-reference) headline is logged on ds2s (V003 N2).
    - `--out` may not resolve to an input prediction file or run manifest (V003 N4); EV2 extends the protected set (D5, above).
    - **Limit (V003 N5):** these rules are enforced in the evaluation command only. Pipeline code (`src/qhc/pipe/`) never reads `labels_ds2s.csv`, `labels_ds2.csv` or `confirm/`; every verification checks this by code search (`grep -rn "labels_ds2\|confirm/" src/qhc/pipe`).
    - The headline and each low-data comparison run once per split. Identity is the per-arm set of file content hashes, so an identical rerun (for example after a crash before the output was written) is accepted whatever the paths. A run with any other file is refused; later variants use `--role secondary`.
    - A headline or low-data comparison that needs a corrected implementation is a defect: it is logged in this file, and rerunning it needs a new evaluation version approved by the author.
  - Every scoring of ds2s, ds2 or svdb is appended to `runs/full_eval_log.jsonl` (time, role, IDs, file hashes, per-arm content identity, code revision) before labels are read. A summary is printed; the output is written atomically through a unique temporary file in the output directory; if `--out` cannot be written, the result goes to a fallback file under `runs/`.
  - Outputs:
    - `score`: aggregate, per-class and secondary metrics, per-record confusion matrices, input hashes, scorer identity and command.
    - `compare`:
      - scorer identity (code revision and the frozen constants), input and run-manifest hashes;
      - `primary`: inference label, delta, CI and its level, outcome and the reason for it, outcome without the 232 condition, suspicious flag;
      - `slices` (headline and low-data roles): family, m, level, member deltas, CIs and slice decisions;
      - per-class F1 and S/V AUPRC deltas with 95% CIs; the leave-one-record-out table;
      - `arms`: per-seed and seed-averaged summaries with every secondary metric and the per-record confusions.
- **Minimal reference used for the uncertainty estimate:** `runs/EV1_reference_r4/` (revision `a2439884ff2f1909`; r5 adds only the per-record 5 x 3 tables and command-level checks, so these values stand). The r3 outputs in `runs/EV1_reference/` (revision `dd225b75db9a8c68`) are historical. References predict from positions only, with one-hot probabilities.
  - `const_n`: every beat N.
  - `rr_rule`: S when pre-RR < 0.85 x the mean of the previous 10 pre-RR intervals, else N; never V.

    | Reference | ds1 | ds2s | ds2 |
    |---|---|---|---|
    | `const_n` | 0.3170 | 0.3147 | 0.3153 |
    | `rr_rule` | 0.3920 (r3: 0.3924, before the R1 fix, A007) | 0.4549 | 0.4526 |

  - The ds2s and ds2 reference predictions are byte-identical to r3.
  - `rr_rule` on ds2s:
    - N/S/V-restricted S: sensitivity 0.844, PPV 0.257; record-averaged sensitivity 0.859, PPV 0.261; 412.9 class-specific false S flags per hour; AUPRC 0.223.
    - Paper-compatible SVEB: Se 0.844, +P 0.257 (FP includes 3 F beats predicted S), FPR 0.095.
    - Review burden: 556.1 S-or-V flags per hour, of which 157.8 on normal beats, 255.1 S<->V swaps (V beats flagged S) and 0.4 on F/Q beats; 75.0 missed ectopic beats per hour.
    - F beats were predicted N 384 / S 3.
  - Diagnostic comparison of `rr_rule` against `const_n` on ds2s (`--role diagnostic`, one run per arm):
    - Delta +0.1401, 95% CI [+0.0225, +0.2443] with B = 8,000. r3 gave [+0.0220, +0.2424] with B = 2,000; only the replicate set differs.
    - Without 232: +0.0494; leave-one-record-out range +0.049 (232) to +0.153 (221).
    - Per-class delta: S +0.394 [+0.048, +0.682]; N +0.026 [−0.005, +0.065]; V 0.
    - Outcome "favorable" (reason: meets the decision rule), with the suspicious flag, as expected for a reference against a constant.
    - Runtime 55 s for one run per arm; about 5 min is expected for 5 runs per arm (the AUPRC bootstrap dominates).
  - Seed noise for the real comparison is examined by the Phase 3 seed-noise diagnostic below.

### Fixtures
All in `tests/test_scorer.py`; run with `python -I -m pytest -q`. 43 passed on 2026-10-26 (EV2 revision `8501643023cd2eb6`, fixture hash `8a0ffb8e64f4f88b`); the five EV2 fixtures fail on EV1 r5 (`9a1922c8898b90db`), which had 38.

| Fixture | Expected | Observed | Tolerance | Result |
|---|---|---|---|---|
| Worked example: records A (truth NNNSV, pred NNSSV) and B (truth NNSVV + one F beat; pred NVNVN, F predicted V). Units confusion [[3,1,1],[1,1,0],[1,0,2]]; F1 N 0.6, S 0.5, V 0.6667; macro 0.588889; accuracy 0.6; F beat reported but not scored; 1 class-specific false S and 1 false V flag in 1.0 h; N/S/V-restricted record-averaged S sensitivity 0.5 and V PPV 0.75; review burden 6 S-or-V flags, 2 normal flagged, 1 F flagged, 0 swaps, 2 missed ectopic per hour | as stated | as stated | 1e-6 relative | pass |
| Paper-compatible metrics (R2): truth N,S,V,F with predictions N,S,V,S gives N/S/V-restricted S PPV 1.0 but SVEB +P 0.5 (F->S is an S false positive), FPR 1/3; F->V, Q->V and Q->S are neither rewarded nor penalised | as stated | as stated | 1e-6 | pass |
| Known-good prediction | 1.0 | 1.0 | 1e-6 | pass |
| Deliberately poor prediction (all N) | 0.222222 | 0.222222 | 1e-6 relative | pass |
| Row order shuffled; class absent from truth and predictions (F1 = 1; with one false positive, F1 = 0) | as stated | as stated | exact | pass |
| Average precision, hand examples (0.8333; tie gives 0.5) | as stated | as stated | 1e-6 | pass |
| Malformed: missing unit, missing F beat, duplicate, extra ID, labels outside {N,S,V}, missing columns, missing probability column, null ID, non-finite probability, probabilities not summing to 1 | rejected | rejected (11 cases) | n/a | pass |
| Paired comparison: identical arms; perfect vs all-N and reversed (per-class and AUPRC CIs); small detectable regression is unfavorable; outcome reasons (a +0.01 delta with CI [+0.005, +0.015] is "no detectable change: detectable gain below the practical threshold") | as specified | as specified | n/a | pass |
| Interval levels (R4): headline primary CI 95%; S and V slice members at 98.75% with the slice rule (a consistent S gain below the practical threshold is a favorable slice while the primary outcome is no detectable change); low-data primary at 98.75% and equal to its slice member; secondary role has no slice block | as specified | as specified | n/a | pass |
| A gain carried by one record (removing it makes the delta negative) is not favorable; leave-one-record-out entry matches | not favorable | not favorable | exact | pass |
| Seed resampling widens the CI for seed-variable arms; reproducible; seed-averaged summary equals the mean of per-seed values; unequal seed counts rejected; extra rows rejected in compare | as specified | as specified | n/a | pass |
| Command checks (R5), synthetic ds2s: a file given five times, the same file in both arms, one run instead of five, duplicate seed ids, different seed indices across arms, a stale manifest hash and a wrong role/split are all refused before any label is read; a valid 5 x 5 headline runs and logs once; an identical rerun is accepted; a different headline is refused; a diagnostic runs with one file per arm | as specified | as specified | n/a | pass |
| Non-beat annotations (R1): `!`, `+`, `~`, `|` are dropped from beat positions and RR intervals | as specified | as specified | exact | pass |
| Lookahead check: causal feature passes; whole-record mean RR fails; 3 s window fails | as specified | as specified | n/a | pass |
| Confirmation command (R6), synthetic svdb: no reason gives refusal; `score` refuses svdb; a malformed one-run request is refused before logging; one `compare --role confirmation` logs exactly one access (with code revision, 10 prediction hashes and 10 artifact hashes) and emits every per-seed and seed-averaged secondary metric, per-record confusion and per-record 5 x 3 table; a second access without `--repair-reason` is refused; a repair with different model artifacts is refused (V003 S3); a repair with the same artifacts is accepted; a third is refused; confirmation before any headline is refused (V003 N2); the real confirmation labels are never opened | as specified | as specified | n/a | pass |
| Confirmation pre-checks (V003 S2): an unwritable output and a scorer crash (simulated) both fail before the access is logged and before labels are read | as specified | as specified | n/a | pass |
| Order on the test splits (V003 B1, M4, N1, N3, N4), synthetic ds2s: before the headline, `score`, `secondary`, low-data and non-reference diagnostics are refused without reading labels; references are accepted; the headline runs; `lowdata_k5` runs at 98.75% with its slice decision in the command output; an identical rerun with reordered paths is accepted; a different low-data run is refused; secondary and score run after the headline; an identical headline rerun is accepted after later entries; an `--out` equal to an input is refused; reference-only arms cannot be the headline; an earlier non-reference scoring blocks the headline | as specified | as specified | n/a | pass |
| Seed provenance (V003 S1): byte-identical model artifacts, mixed `config_id`s in one arm, and one `arm_id` for both arms are refused before label access | as specified | as specified | n/a | pass |
| Reduced-data subsets (V003 M3): the frozen file equals `units.draw_lowdata_subsets` on the DS1 units | as specified | as specified | exact | pass |
| EV2 D3: the same five runs per arm given in another order, and from another directory, give identical numbers (primary, slices, per class, AUPRC, leave-one-record-out, per-seed arms) | identical | identical | exact | pass |
| EV2 D4: after a headline, `lowdata_k5` is refused before label access for runs lacking the provenance fields, fitted on all DS1 records, fitted on the k11 subset, derived from another configuration, with arms swapped, or with the wrong refit scope; the correct runs are accepted and the fields appear in the output; the headline configurations of an old-format log entry are recovered from its logged files' manifests | as specified | as specified | n/a | pass |
| EV2 D5: `--out` naming a referenced model artifact, either ledger, a processed-data file or a directory is refused before label access; the artifact's bytes are unchanged | as specified | as specified | n/a | pass |
| EV2 D1, D2: a repair that swaps the arms with the same ten artifacts is refused before label access; a repair to the first report's path is refused; a legitimate repair to a new path archives a second report; both archived reports match their index hashes; the first `--out` file is unchanged | as specified | as specified | n/a | pass |
| EV2 D2, D6: a failure after the access is logged (simulated scorer failure on the real labels) is archived as a failed access with its error and counts against the cap | as specified | as specified | n/a | pass |
| Real data: current class totals and their difference from de Chazal Table II (R3); DS1 prediction set 50,964 with 50,542 units; no non-beat codes in the prediction sets; splits disjoint; 202 and paced records absent; released files label-free; `predict` recomputable from positions and record length; no SVDB labels outside `confirm/` | true | true | exact | pass |

## Scorecard
No weights are published, so equal weights are an *assumption*. Two gate rows must reach 3 before submission. Rated twice, separately, against these anchors.

| Criterion | Weight | Evidence that would convince the judges | 0 | 1 | 2 | 3 | Rated by |
|---|---|---|---|---|---|---|---|
| Performance relative to the comparable classical baseline | 25% | Headline EV1 paired delta (quantum-reservoir arm against matched ESN arm) on ds2s; SVDB confirmation; per-class, AUPRC and false-flag tables; pre-declared slices | No matched comparison, or a comparison with leakage or unequal tuning | Matched comparison run; outcome unfavorable or no detectable change, and not analysed further | No detectable change overall, but a member of the fixed four-member slice family whose 98.75% CI lower bound is > 0 (all four reported); or favorable on ds2s but not confirmed on SVDB | Favorable on ds2s under the full decision rule (including the 232 condition), and confirmed on SVDB (delta > 0, CI excluding 0) | two internal ratings |
| Ingenuity | 25% | Write-up: the limitation addressed (fixed, training-free feature maps that must generalise to unseen patients; low-power physical reservoirs), the literature gap, controls that isolate the quantum effect | Off-the-shelf quantum ML with no rationale | Standard quantum model with a generic rationale | Quantum component tied to a specific limitation of the classical approach, with the literature gap cited | As 2, plus a design that isolates what is quantum (classical-spin mean-field control, separable ablation) and a feasibility link to hardware (Braket run) | two internal ratings |
| Depth | 25% | Ablations, mechanism analysis, noise, shot and hardware evidence, per-class and per-patient analysis | One headline number | Per-class metrics plus one ablation | Ablations along at least 3 axes (entanglement, readout size, qubit count, shots or noise) with a mechanism explanation | As 2, plus device-noise simulation and a real-hardware subset, and an analysis of where and why quantum features help or fail (per patient and class, with a kernel or geometric diagnostic) | two internal ratings |
| Soundness | 25% | Patient-held-out split; equal tuning budgets; two-level uncertainty; pre-registered rules; passed lookahead checks; confirmation access log; limitations; verification report | Patient leakage, tuning on the test split, or claims without evidence | Patient-held-out but unequal tuning, or no uncertainty | Patient-held-out, equal tuning budget, record- and seed-level CIs, lookahead check passed, limitations stated | As 2, plus access-logged external confirmation, a published variant count, a verification PASS, and every claim traceable to an experiment ID | two internal ratings |
| Gate: deliverables complete | must reach 3 | Codebase with both approaches, comparative evaluation, explanation of problem, methods and quantum purpose, reproduction instructions (brief, "Prepare your submission") | Any item missing | (n/a) | (n/a) | All four present and checked in verification | verification |
| Gate: reproducible | must reach 3 | Clean environment from `requirements-lock.txt`; `scripts/download_data.py` with checksum check; one command regenerates the headline tables | Headline cannot be regenerated | Regenerates with manual steps | Regenerates with one command, but not from a clean environment | Regenerates from a clean environment and fresh download, checked in verification | verification |

- **Representativeness:** unverifiable against the judges before judging. The first external feedback is in the table below.

| Date | Who | What they said | Scorecard effect |
|---|---|---|---|
| 2026-10-28 ~18:00 | Independent progress review supplied by the author (`PROGRESS_REVIEW_2026-10-28.md`) | Rigorous, with useful controls. But the primary is inconclusive and mean-field reproduces the gain, so quantum value is not demonstrated. Equal weights and hardware-dependent top anchors are internal choices, not official rules. Prioritise the SVDB confirmation, a precise claim pass and complete delivery over more depth experiments | No anchor changed (anchors are part of the approved EV2). The internal scorecard is treated as a completion tracker, not the objective. Hardware and depth items are dropped for this deadline |

## Comparison procedure
- **Technical:**
  - **Units and dependence:** the evaluation units of the split. Beats within a record are dependent, so the record (patient) is the resampling unit.
  - **Paired signed delta and estimand:** both arms are scored on identical units. Delta = (mean over the candidate's 5 seeds of the per-seed macro-F1) − (the same for the baseline); positive means the candidate is better.
    - This is not the macro-F1 of a 5-model probability ensemble.
    - Its uncertainty is conditional on the fixed DS1 training cohort and the selected configurations.
    - Strict roles need exactly 5 distinct seeded runs per arm with run manifests (enforced before label access). Diagnostic comparisons may use fewer.
    - The demo uses the seed-0 model of the headline quantum arm. A seed ensemble, if ever shown, is labelled as such and is not the scored estimand.
  - **Uncertainty:** two-level bootstrap, B = 8,000 replicates, generator seed 20261026; one replicate set serves every interval of a comparison.
    - Records are resampled with replacement, jointly for both arms. Seeds are resampled with replacement, independently within each arm.
    - Primary interval: 95% percentile CI.
    - Slice-family intervals: 98.75% (Bonferroni over the fixed four-member family below). B = 8,000 leaves 50 draws in each tail.
    - Assumption: records are exchangeable draws of patients. With 21 records, one of which holds 77.5% of the S units, the CI is approximate and wide.
  - **Practical gain threshold:** +0.02 macro-F1, frozen now. No ds2s or diagnostic result changes it within EV1.
  - **Decision rule:**
    - *Favorable* if delta >= +0.02, the CI lower bound > 0, **and** the point delta with record 232 removed is > 0 (ds2s and ds2).
    - *Unfavorable* if the CI upper bound < 0.
    - Otherwise *no detectable change*, which means insufficient evidence, not equivalence.
    - The output records the reason: "CI includes 0", "detectable gain below the practical threshold" (e.g. +0.01 with CI [+0.005, +0.015]), or "gain disappears without the dominant record".
    - The output also records the outcome without the 232 condition, so a gain carried by 232 is visible and reported as such.
  - **Suspicious-gain threshold:** delta >= +0.05 macro-F1 queues an immediate verification.
  - **Seed-noise diagnostic (replaces the r3 "null calibration"):**
    - In Phase 3 the matched ESN arm (R0) with seed indices 0-4 is compared with R0 with seed indices 5-9 on pooled DS1 out-of-fold predictions (`compare --split ds1 --role diagnostic`; a proxy result that uses no test data).
    - It is a diagnostic, not a calibration: one draw cannot estimate CI coverage or a reliable noise floor, and a larger positive threshold could not fix an upper bound below zero.
    - It triggers if its CI excludes 0 or |delta| > 0.01. Then seeds, the implementation and interval behaviour are investigated, and the finding is logged in ANOMALIES.md, before any competitive ds2s evaluation. It does not change the practical threshold.
  - **Reported with every comparison:** per-class F1 deltas with CIs, S/V AUPRC deltas with CIs, and the leave-one-record-out delta table.
- **Matched-baseline rules (pre-registered; they define "comparable classical baseline"):**
  1. **Same pipeline:** identical prediction set and units, beat segmentation, filtering, downsampling, input encoding and RR features, the same readout model class and regularisation grid, the same class weighting and decision-rule procedure, and the same 5 seed indices (enforced in strict roles).
  2. **Readout dimension matched:** the classical reservoir block supplies exactly as many features to the readout as the quantum block (K_c = K_q). K counts every readout feature, including time-multiplexed snapshots and every Pauli observable.
     - K is fixed for the headline pair before tuning and declared with the search spaces in EXPERIMENTS.md. Every configuration in either headline search space yields exactly K reservoir features.
     - Configurations that change K (qubit count, observable set) are ablations, not members of the headline search.
  3. **Equal tuning budget:** each arm's realised count of DS1-CV configurations is the same N <= 40.
     - A configuration is one reservoir design point. The readout regularisation grid and the decision-rule procedure are fixed, identical in both arms, declared with the search spaces, and nested inside every configuration. They do not count separately toward N, and no other readout or threshold search is allowed.
     - The count covers every design variant of that arm: qubit count, Hamiltonian, encoding and observable set for the quantum arm; size, spectral radius, leak rate, input scaling and sparsity for the ESN.
     - Both search spaces are declared in EXPERIMENTS.md before the first tuning run. The ESN space includes standard settings (spectral radius 0.5-1.2, leak rate 0.1-1, input scaling 0.1-2).
     - Same random-search procedure and seed scheme. Tuning never reads ds2s, ds2 or svdb.
  4. **Headline pre-registered and immutable:**
     - The headline is the first non-reference scoring of the test splits: the first quantum-versus-matched-ESN pair evaluated on ds2s. It is named by experiment ID on its card before the run and run with `--role headline`. The command enforces this order (no other model may be scored on ds2s or ds2 before it) and refuses a different headline once one is logged.
     - R0 (the matched ESN arm) therefore gets its first ds2s score as the baseline arm of the headline comparison, in the same access.
     - Later ds2s-driven variants and newly invented slices are exploratory. They run with `--role secondary`; their ds2s intervals are descriptive after adaptive development; the write-up reports every one.
     - The r3 sequential correction (m = pairs evaluated so far) is withdrawn. A Bonferroni adjustment controls a family fixed in advance; it does not make adaptive test-set development valid. The author's approval or a larger m does not turn a later pair into a confirmatory one.
     - A frozen final pair (the headline, or a later variant) is assessed on SVDB. If it is not the headline, the write-up states that it was selected using ds2s.
  5. **Variant count:** every ds2s, ds2 or svdb scoring is appended automatically to `runs/full_eval_log.jsonl`, logged in EXPERIMENTS.md and reported in the write-up. At most 15 such full evaluations on EV1 without the author's approval. The minimal-reference re-scorings made for r4 before approval are diagnostics and do not count.
  6. **Measurement model:**
     - The headline quantum arm uses finite-shot readout: 1,024 shots per circuit per beat, Z-basis, simulated by sampling. Exact expectation values are an ablation only.
     - The headline classical reservoir is a leaky-tanh echo state network (ESN).
  7. **Further controls,** reported with the same procedure:
     - the classical-spin (mean-field, product-state) reservoir of the same Hamiltonian, after the matching rule of Kornjača et al. 2024 (`doi:10.48550/arxiv.2407.02553`);
     - a separable (non-interacting) quantum reservoir;
     - RR plus handcrafted features alone;
     - a strong classical reference for context only.
     - **Claim limits:**
       - The matched ESN is a controlled comparator. Equal feature dimension does not establish equal model capacity or a practical computational advantage.
       - The classical-spin comparison is a heuristic entanglement control (Kornjača et al. 2024). Bowles et al. 2024 (`arXiv:2403.07059`) support examining classical baselines and non-entangling variants.
       - Neither establishes an ECG advantage for this model.
- **Pre-declared slices and regimes** (secondary; each counts against the cap where it needs a new ds2s scoring).
  - **Slice family, fixed now (m = 4, level 98.75%):** the S-class and V-class F1 deltas of the headline comparison, and the macro-F1 deltas of the two reduced-data comparisons (k = 5, k = 11).
  - **Slice rule:** a slice counts as favorable only if its 98.75% CI lower bound is > 0. The slice decision does not use the practical threshold or the dominant-record condition of the primary outcome. The command reports it separately (`slices` in the output).
  - Every slice result is reported, whatever its outcome. A slice invented after any result is exploratory, reported as such, and never joins the family.
  - (a) per-class F1 deltas for S and V: slice-family members at 98.75% in the headline comparison; 95% descriptive intervals in every comparison;
  - (b) record 232 removed (in every compare output);
  - (c) **reduced-data refitting** (renamed from "low-data regime" in r4):
    - Both headline arms keep the configurations selected on full DS1 and are refitted on k ∈ {5, 11} DS1 records, then scored on ds2s with `--role lowdata_k5` / `--role lowdata_k11` (5 seeds per arm).
    - Refitted on the subset: every fitted quantity (input normalisation, readout weights, decision rule). Fixed from full DS1: the reservoir configuration.
    - This measures reduced-data refitting conditional on full-data model selection, not a method that needs only k labelled records. One subset per k leaves subset-selection uncertainty unmeasured.
    - Subsets, frozen before any model in `runs/data/processed/EV1/lowdata_subsets.json` (sha256 `6348bd6c817b057c55e885bcfefd3f041e3563d74a53de841f88bfde78d982f1`, written by `qhc.units` and listed in `manifest.json`): `units.draw_lowdata_subsets` uses numpy `default_rng(20261026)` and `rng.choice(sorted DS1 records, k, replace=False)`, for k = 5 then k = 11 from the same stream, redrawing until the subset has at least 10 S and 10 V units. Fixture `test_lowdata_subsets_are_reproducible` checks the frozen file against the function. The r4 draft drew the same subsets; only the rule text in the file changed.
      - k = 5: 101, 122, 209, 215, 223 (2 draws; units N 12,183 / S 462 / V 638).
      - k = 11: 106, 112, 115, 116, 119, 124, 205, 208, 209, 220, 223 (1 draw; units N 22,130 / S 589 / V 2,656).
  - (d) the SVDB confirmation;
  - (e) optional diagnostics: patient-grouped CV over the 44 non-paced MIT-BIH records in 43 subject groups (201 and 202 as one group), and the causal-only boundary.
    - Reported as diagnostics and never used for selection.
    - The grouped CV trains on ds2s labels, which the boundary rules forbid for any result that feeds a decision. It is therefore allowed only after the final pair is frozen and its SVDB confirmation has run, or not at all.
- **Rubric:** two separate internal ratings against the anchors.
  - A change counts only when both ratings move the same way on the claimed criteria.
  - The gap between the two ratings is disagreement: an internal consistency check, not an uncertainty estimate and not validation against the judges.
  - Rubric gains are internal assessments wherever reported.
- **Tradeoff rule:**
  - The two gate rows must reach 3, whatever else happens.
  - Otherwise the equal-weight sum decides, unless the author rules otherwise.
  - A soundness rating below 2 vetoes any submission claim of improved performance.
- **Hardware and noise tracks (pre-declared result types):**
  - **Device-noise simulation:** the quantum arm simulated with a noise model of the target QPU, scored on ds2s. A full result for a distinct, secondary candidate, counted against the cap.
  - **Real-hardware run on Amazon Braket:**
    - Result type: *diagnostic*. A stratified subset of about 100 ds2s beats, chosen by a seeded draw before any hardware run, is scored on hardware with a readout trained on simulated DS1 features.
    - Reported: per-beat agreement with the noiseless and finite-shot simulations, macro-F1 on the subset with a bootstrap CI, and feature correlation.
    - It cannot change the headline outcome.
    - Every task needs the author's approval with a cost estimate, within the USD 90 cap.

## Confirmation policy
- **Technical:** SVDB (`svdb`, 78 records, 184,286 units) is the confirmation set.
  - **Use:** it is never used for training, tuning, selection or diagnostics.
    - The final frozen pair (the exact DS1-trained artifacts, 5 seeded runs per arm with run manifests) is scored once with `qhc.evaluate compare --split svdb --role confirmation --confirm-reason "..."`.
    - That one command emits the complete report: primary delta and CI, per-class and AUPRC deltas, and every per-seed and seed-averaged secondary metric with the per-record confusions. No further label access is needed for reporting. `score` refuses svdb.
  - **Pass criterion, fixed now:** *confirmed* if the SVDB paired delta is > 0 and its 95% CI lower bound is > 0 (two-level bootstrap over the 78 records).
  - **Caveats:** absolute scores may differ from ds2s because of domain shift; the direction is unknown before evaluation. The bootstrap may be anti-conservative if records share subjects (A006).
  - **Guard (tested):**
    - Before any access: role and split, 5 distinct seeded runs per arm with valid manifests, and the predictions against the label-free prediction set.
    - Then the output file is checked: it must be new and writable (EV2, D2). The whole comparison is run once as a preflight on placeholder labels (cycling N/S/V, 20 replicates). This catches output and code errors before an access is logged (V003 S2). It cannot rule out failures that depend on the real labels or on resources; such a failure is recorded as a failed access and counts against the cap (EV2, D6).
    - Then the cap (2, counted from `runs/confirmation_access.jsonl`).
    - A second access also needs `--repair-reason`. It must score the same model artifacts as the first, **in the same roles and seeds**: candidate artifacts by seed and baseline artifacts by seed, so swapping the arms is a change (EV2, D1). A model or role change needs `--approved-model-change` recording the author's approval. It is then marked as a change, not a repair: the first result stands and is reported alongside (V003 S3, D1).
    - Then the access is logged with the code revision, every prediction-file hash and every model-artifact hash.
    - Only then is `confirm/labels_svdb.csv` read. The complete report of each access is archived immutably as `runs/confirmation_reports/access_<n>.json`. An index line in `runs/confirmation_reports/index.jsonl` records its sha256 and status (completed or failed, with the error). This happens before the `--out` copy is written, so the first result survives any repair (EV2, D2). A summary is printed.
  - **Access cap:** 2 project-wide (the final pair, plus one repair rerun).
  - **Repair:**
    - A second access is allowed only for a documented implementation correction (for example a resampling or file-assembly defect), never as another model-selection opportunity.
    - The first result and the repair reason are preserved, and results affected by the defect are invalidated.
    - The cap is a workflow safeguard; on its own it does not make a second access legitimate.
- **Access log** (appending here is bookkeeping and does not create a new version):

| Date | E### | Reason |
|---|---|---|
| 2026-10-26 | none | Data-card inspection (headers, label counts); no predictions scored |
| 2026-10-26 ~17:45 | none | **Incident, not a scoring access.** While testing the confirmation guard, a bug (the data path was bound when the function was defined, so the test's patched path was ignored) made `load_labels` open the real `confirm/labels_svdb.csv` inside a pytest run. Synthetic predictions failed beat-ID validation before any metric was computed. The only output was the error `qhc.scorer.PredictionError: 184389 prediction-set beats have no prediction, e.g. svdb:800:100002`, which reveals a beat ID (public positions) and the size of the prediction set, both already in the released positions file. No label values or scores were displayed or stored, and the real access log was not written. V002 judged the entry and the fix adequate. **To be disclosed in the write-up's limitations.** Fixed in `dd225b75db9a8c68`; the guard test now asserts the real file is never opened. Not counted against the cap. Recorded for transparency. |
| 2026-10-28 19:29:19 UAE | E018 (E003 vs E002) | **Confirmation access 1 of 2.** Pre-registered SVDB confirmation of the frozen headline pair; predictions from the exact DS1-trained artifacts via the A018 predict-only path, whose ds2s self-check reproduced all 10 logged headline hashes. Completed 20:01:41; report archived `runs/confirmation_reports/access_1.json` (sha256 `39c6b7e77a4353d6...`). Result: delta −0.0085 [−0.0476, +0.0274], **not confirmed**. |

- **Rubric:** none available before judging. The Phase 6 rehearsal is a readiness check, not confirmation.

## Runtime / resources
- **Full evaluation runtime and cost:** scoring under 10 s. A comparison (8,000 bootstrap replicates with AUPRC) takes 55 s for one run per arm on ds2s and about 5 min for 5 runs per arm (CPU). SVDB is about 4 times larger. Model runtime: the finite-shot 10-qubit reservoir simulates all 50,964 DS1 beats in under 1 s on one GPU. The per-run cap is 3 GPU-hours.
- **Demo build time:** n/a so far.

## Response to V001 (metric review, 2026-10-26)

| Finding | Change |
|---|---|
| B1: label leak through `is_unit` | `positions_*` now carry a label-free `predict` flag. Pipelines predict all beats in the prediction set, including F and Q. The scorer selects the units. A test recomputes the flag from positions and record length. |
| B2: the 1.0 s boundary contradicted post-RR | Boundary redefined as b_i = max(t_{i+1}, t_i + 1.0 s), one-beat lookahead. `qhc.leakcheck` is required before any full evaluation. The causal-only variant is pre-declared as optional. |
| B3: budget and selection loopholes | Equal realised N <= 40 per arm covering all design variants; search spaces declared in EXPERIMENTS.md before tuning; headline = first pair evaluated on ds2s, named before its run; replacements need the author's approval and a Bonferroni CI; ds2 counts against the cap. |
| S1: 232 dominance (77.5%) | Favorable now also requires the delta without 232 to be > 0. Leave-one-record-out table and per-class CIs in every comparison. |
| S2: seeds fixed | Two-level bootstrap (seeds resampled within each arm), plus the pre-declared null-calibration rule. |
| S3: operating point | Probabilities mandatory; S/V AUPRC deltas with paired-bootstrap CIs; decision-rule procedure identical across arms. |
| S4: review burden | False flags per hour and EC57 record-averaged sensitivity and PPV added. No per-record macro-F1. |
| S5: shot model | Headline quantum arm uses 1,024 Z-basis shots per circuit; exact expectations are an ablation; K counts every readout feature; headline classical reservoir = leaky-tanh ESN. |
| S6: confirmation guard | Validate first, enforce the cap, log, then read labels from `confirm/`. Pass criterion and SVDB lead and resampling fixed here. A6 caveat added. |
| S7: undeclared slices | Slices (a) to (e) declared above. |
| Minor | Extra rows rejected in compare; unequal seed counts rejected; F/Q prediction distribution reported; 44-record grouped CV and causal-only variant declared as optional diagnostics; suspicious threshold lowered to 0.05; 232 share corrected to 77.5%. |

## Response to V003 (re-check of r4, 2026-10-26; full report `runs/V003/report.md`)

| Finding | Change in r5 |
|---|---|
| B1: headline and low-data slices choosable after peeks | Order rules on ds2s and ds2 in `_check_order`: references only before the headline; diagnostics there limited to references; score, secondary and low-data wait for the headline; the headline refused after any earlier non-reference scoring; headline and low-data run once (content identity). Tested. |
| S1: copies pass as seeds | Distinct model-artifact content hashes within an arm; one `config_id` per arm; different `arm_id`s across arms. Tested. |
| S2: a failure after logging spends an access | Writability check and a scorer smoke test on placeholder labels before the access is logged; result printed first and written atomically with a fallback under `runs/`. Tested. |
| S3: a repair can change models | The second access must score the same set of model-artifact hashes, unless `--approved-model-change` records the author's approval. Tested. |
| M1: stale text | EC57 wording in the alternatives, runtime, headline definition corrected. |
| M2: identity depended on path spelling | Identity is per-arm sets of content hashes; headline repair rule stated (a corrected rerun needs a new approved version). |
| M3: subset rule ambiguous | `units.draw_lowdata_subsets` writes the file (exact `rng.choice` call named); reproducibility fixture. |
| M4: low-data levels tested only in the scorer | Command-level test of `lowdata_k5` (98.75%, slice decision in the output). |
| M5: diagnostic (e) trains on ds2s labels | Allowed only after the final pair and SVDB confirmation are frozen, or not at all. |
| M6: no per-record F/Q table | Per-record 5 x 3 paper-compatible tables in every arm summary. |
| Follow-up N1: a reference-only "headline" opened ds2s early | `--role headline` refuses reference-only arms; the headline-exists check counts only non-reference headlines. Tested. |
| Follow-up N2: SVDB before any headline | Confirmation refused until a non-reference ds2s headline is logged. Tested. |
| Follow-up N3: identical headline rerun refused after later entries | Once a headline is logged, an identical rerun is accepted at any time and a different one refused. Tested. |
| Follow-up N4: `--out` could overwrite an input | Refused. Tested. |
| Follow-up N5: no code guard for test labels outside the command | Procedural: pipeline code never reads test-split labels; verifications check it by code search. |
| Follow-up: serialization error at the final write | The smoke test serialises its result; `_write` also falls back on TypeError/ValueError. |

## Response to the independent review of r3 (`EV1_R3_REVIEW.md`, 2026-10-26)

| Item | Change in r4 |
|---|---|
| R1: flutter waves as beat positions | `!` removed from `BEAT_SYMBOLS`; beat selection factored into `units.select_beats` with a fixture of beat and non-beat codes. DS1 rebuilt: prediction set 51,436 -> 50,964, units 50,542 unchanged, folds unchanged; ds2s, ds2 and svdb byte-identical. DS1 rr_rule recomputed: 0.3924 -> 0.3920 (A007). |
| R2: "EC57-style" secondary metrics | Existing fields renamed `nsv_*` and described as N/S/V-restricted, with no EC57 claim. Paper-compatible gross VEB/SVEB Se, +P and FPR added on the full prediction set, following Table V. F->S fixture added. |
| R3: "exactly reproduces de Chazal" | Claim corrected in EVAL.md, PROBLEM_BRIEF.md and ANOMALIES.md; reconciliation table published; fixture renamed `test_units_match_current_dataset_counts` and checks the difference table. ds2 comparisons are labelled contextual (A008). |
| R4: multiplicity | Fixed four-member slice family; `compare` emits `primary` (95%) and `slices` (98.75%, slice rule) separately; `--n-comparisons` removed; roles validated before label access; headline immutable (enforced from the full-evaluation log); later variants descriptive. |
| R5: five copies of one file | Duplicate resolved paths refused in every role; strict roles need exactly 5 runs per arm with hash-bound run manifests, distinct seeds, artifacts and randomness, and the same seed indices in both arms. |
| R6: incomplete confirmation report | `compare` computes every per-seed and seed-averaged secondary metric and the per-record confusions in the same access; outputs carry the scorer identity; the confirmation log binds prediction and artifact hashes; `score` refuses svdb; a second access needs a repair reason. |
| Additional 1: null calibration | Replaced by a DS1 seed-noise diagnostic that never changes the threshold; practical threshold frozen. |
| Additional 2: low-data claim | Renamed reduced-data refitting; refitted versus fixed quantities stated; subsets frozen and hashed. |
| Additional 3: review burden | Total S-or-V flags, normal beats flagged, F/Q flagged, S<->V swaps and missed ectopic beats per hour added; class-specific rates keep their N/S/V scope in their names. |
| Additional 4: estimand and matching | Estimand stated (mean of per-seed macro-F1, not an ensemble); demo predictor named; K fixed before tuning; readout grid and decision rule nested in each configuration. |
| Additional 5: claims from controls | Claim limits added under matched-baseline rule 7. |
| Small corrections | Latency max(1 s, next RR); r4 scorer identity separated from historical reference provenance; 44 records in 43 subject groups; SVDB scores "may differ"; outcome reasons; lockfile without the absolute editable path. |

Not done here, as the review notes: no clean-environment reproduction, no bootstrap-coverage study, and no audit of the complete EC57 standard.

## Defects and change history

### Known defects of EV1 (approved r5): all fixed in EV2 (`8501643023cd2eb6`)
Source: independent audit of the final r5, `EV1_R5_RECHECK.md` (in the project from 2026-10-26 19:57, before the approval; read only at ~21:35, after the approval and after the headline had started). It checked the same revision `9a1922c8898b90db` and the same EVAL.md sha256 `f758910b...` that were approved. These are defects in the command's guards and in reproducibility, not in the metric, the split, the units or the beat set. The audit found no real comparison affected. Logging them here is bookkeeping; fixing them changes the evaluation code and needs the author's approval.

| ID | Defect (audit item) | Where | What it affects | Experiments affected | Restriction until fixed |
|---|---|---|---|---|---|
| D1 | A confirmation repair compares the union of both arms' model hashes, so swapping candidate and baseline passes as "the same models" (F1) | `evaluate.py` `_confirmation_access` | SVDB repair only | none (no confirmation access exists) | no SVDB access |
| D2 | A repair written to the first access's `--out` replaces the first report, which nothing else stores (F2) | `evaluate.py` `_check_writable`, `_write` | SVDB repair only | none | no SVDB access |
| D3 | Scoring keeps the supplied file order, and bootstrap seed weights follow that order. Reordering the same files gives a different Monte Carlo CI under the same logged identity (F3) | `evaluate.py` `cmd_compare`; `scorer.py` `compare` | any strict comparison whose files are not passed in seed order | none: the headline E003 vs E002 passed both arms in seed order 0-4 (shell glob of `pred_ds2s_seed*.csv`), the order the fix imposes (checked from the log entry, below) | strict comparisons are run with files in seed order 0-4 |
| D4 | `lowdata_k5` and `lowdata_k11` are not bound to the headline configurations or to the frozen subsets: any internally consistent arm is accepted (F4) | `evalspec.RUN_KEYS`; `evaluate.py` `check_runs`, `_check_order` | reduced-data slice members | none (not run) | no `lowdata_*` comparison |
| D5 | `--out` may name a referenced model artifact or a ledger and overwrite it; the temporary name `out + '.tmp'` is fixed (F5) | `evaluate.py` `_check_out`, `_write` | any command, accidental clobbering | none (the headline wrote a new file) | `--out` always a new file under `runs/E###/` |
| D6 | Wording: the placeholder smoke test is a preflight check, it cannot rule out failures that depend on the real labels or on resources; the command prints a summary, not the full report (documentation item) | this file, Confirmation policy | text only | none | none |

| Version | Date | Reason / defect | Approved by | Affected experiments |
|---|---|---|---|---|
| EV1 (draft r1) | 2026-10-26 ~17:29 | initial draft | not approved | none |
| EV1 (draft r2) | 2026-10-26 17:48 | V001 findings B1-B3, S1-S7 and minor fixed before approval; no experiment existed | not approved | none |
| EV1 (draft r3) | 2026-10-26 17:55 | V002 residuals: slice decision rule with Bonferroni, B scaled with m, paths anchored to project root, causal-only wording, cross-record fitting forbidden, incident error text | not approved (independent review requested changes) | none |
| EV1 (draft r4) | 2026-10-26 ~18:45 | Independent review of r3 (`EV1_R3_REVIEW.md`): R1 non-beat `!` removed from beat positions (DS1 rebuilt); R2 N/S/V-restricted metrics renamed, paper-compatible VEB/SVEB added; R3 de Chazal count claim corrected; R4 fixed slice family with separate 98.75% output, headline immutable, sequential correction withdrawn; R5 run manifests and duplicate-run refusal; R6 complete report in one confirmation access, repair rule; null calibration replaced by a DS1 seed-noise diagnostic; reduced-data claim narrowed and subsets frozen; review-burden measures; estimand and matching details; claim limits; small corrections | not approved (V003 requested changes) | none (no model existed; the DS1 rr_rule reference was rescored) |
| EV1 (draft r5) | 2026-10-26 ~19:00 (follow-up fixes ~19:10; revision hash made line-ending independent ~19:20) | Re-check V003 of r4 and its follow-up on r5 (N1-N4): order on the test splits enforced (references only before the headline; headline first; headline and low-data run once, identity by content); seed provenance (distinct artifact hashes, one config per arm, different arm ids); confirmation pre-checks (writable output, scorer smoke test) and repair restricted to the same models; atomic output with fallback; per-record 5 x 3 tables; subset generator in `units`; stale text; diagnostic (e) timing | pending | none (no model scored on any test split) |
| EV1 (approved, r5) | 2026-10-26 21:26 | The author's approval of draft r5 as presented (EVAL.md sha256 prefix `f758910b94defc3d`, evaluation revision `9a1922c8898b90db`); no change to the specification or code | author, 2026-10-26 21:26 UAE | none at approval; E002-E006 are the first experiments on EV1 |
| EV2 | 2026-10-26 22:14 UAE | Guard fixes for EV1 known defects D1-D6 (`EV1_R5_RECHECK.md` F1-F5): per-role repair identity (D1); immutable confirmation report archive and no overwrite (D2); canonical seed order (D3); low-data provenance bound to the headline configurations and frozen subsets (D4); protected output paths and a unique temporary file (D5); preflight wording (D6). Scorer, units, metric, split, thresholds unchanged | author, 2026-10-26 22:14 UAE | none invalidated. The EV1 headline is rerun under EV2 as its first scoring; numbers are expected to be identical because the EV1 run already passed both arms in seed order |
