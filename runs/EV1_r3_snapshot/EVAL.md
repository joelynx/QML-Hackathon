# Evaluation specification (open mode)

- **Version:** EV1 | **State:** draft (revision 3, after the critic's metric review V001 and re-check V002); ready for the human's approval
- **Approval:** pending (human).
  - Drafted 2026-10-26 ~17:29 UAE.
  - Critic metric review V001 (2026-10-26): 3 blocking, 7 should-fix and some minor findings.
  - All are addressed (see "Response to V001" at the end).
  - Critic re-check V002 (2026-10-26): every finding resolved except S7, which was partly fixed; no new blocking issue; the SVDB incident does not compromise the confirmation set.
  - The V002 residuals are closed in revision 3.
- **Brief version:** `hackathon_details.md` as read 2026-10-26. Problem C1, chosen by the human 2026-10-26 (PROBLEM_BRIEF.md).
- **Code revision:** no git repository yet.
  - Revision = first 16 hex of sha256 over `cat src/qhc/*.py`: `9c74cdcb7d673bc7`.
  - Compared with `dd225b75db9a8c68`, the only changes are data and log paths anchored to the project root and bootstrap draws scaled with m. Outputs for m = 1 are identical, so the reference results below, computed at `dd225b75db9a8c68`, stand.
  - Fixture tests `tests/test_scorer.py`: `ccbe3120d947a5a7`.
  - Environment: `requirements-lock.txt` (pip freeze, Python 3.12.10).
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
  - `python -I -m qhc.units` (revision `dd225b75db9a8c68`) writes to `runs/data/processed/EV1/`, with hashes in `manifest.json`:
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
- **Source and link:** https://physionet.org/content/svdb/1.0.0/. Files from the AWS mirror, downloaded 2026-10-26. Approved by the human 2026-10-26.
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
- **Secondary metrics, reported for every scored arm (none of them sets the outcome):**
  - per-class sensitivity, PPV and F1;
  - AAMI EC57-style record-averaged sensitivity and PPV, averaged over the records containing that class (or predicting it, for PPV);
  - false S and V flags per hour of recording;
  - per-class AUPRC for S and V (threshold-free), with the same paired bootstrap in comparisons;
  - how F and Q beats were classified.
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
    - **EC57 per-class sensitivity and PPV:** several numbers, no single decision rule. Reported as secondary.
    - **Matthews correlation:** sound, but not standard in this literature, where F1 is (e.g. Niu et al. 2020, `doi:10.1109/jbhi.2019.2942938`).
- **Declared before modeling on:** 2026-10-26 (PROBLEM_BRIEF.md, Phase 1); no model exists yet. **Critic review of the choice:** V001 (2026-10-26), findings addressed below; re-check requested.
- **Prediction unit, target, decision-time boundary:**
  - Unit: one prediction-set beat. Scored if it is an evaluation unit. Target: its AAMI class among N, S and V.
  - **Boundary:** for beat i at R-peak sample t_i, inputs may use the signal and beat positions of the same record up to b_i = max(t_{i+1}, t_i + 1.0 s), and all earlier data, plus parameters fitted on DS1.
    - This is one-beat lookahead, with latency at least 1 s and at most the next RR interval. The longest next-RR interval in ds2s is 5.87 s; 15.6% of ds2s units have a next beat more than 1 s away.
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
  | `ds1` | de Chazal DS1, 22 records | 51,436 | 50,542 (45,813 / 943 / 3,786) | All training and tuning, by grouped 5-fold CV on fixed folds (`ds1_folds.json`) |
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
    - DS1 and DS2 class totals reproduce de Chazal 2004 (tested).
- **Scorer revision / command / output:** revision `dd225b75db9a8c68`.
  - `python -I -m qhc.evaluate score --split ds2s --pred P.csv --id NAME --out runs/E###/score_ds2s.json`
  - `python -I -m qhc.evaluate compare --split ds2s --cand C_seed*.csv --base B_seed*.csv --cand-id X --base-id Y --out runs/E###/compare_ds2s.json [--n-comparisons m]`
  - Prediction file: CSV with `beat_id,pred,prob_N,prob_S,prob_V`, one row per prediction-set beat. Probabilities are mandatory.
  - Outputs:
    - Aggregate, per-class and secondary metrics, per-record confusion matrices, input hashes, version and command.
    - For `compare`: the delta, CI, outcome, per-class deltas with CIs, AUPRC deltas with CIs, the leave-one-record-out table, the delta without the dominant record, and per-seed scores.
- **Minimal reference used for the uncertainty estimate:** `runs/EV1_reference/` (revision `dd225b75db9a8c68`). References predict from positions only, with one-hot probabilities.
  - `const_n`: every beat N.
  - `rr_rule`: S when pre-RR < 0.85 x the mean of the previous 10 pre-RR intervals, else N; never V.

    | Reference | ds1 | ds2s | ds2 |
    |---|---|---|---|
    | `const_n` | 0.3170 | 0.3147 | 0.3153 |
    | `rr_rule` | 0.3924 | 0.4549 | 0.4526 |

  - `rr_rule` on ds2s:
    - S: sensitivity 0.844, PPV 0.257; record-averaged sensitivity 0.859, PPV 0.261; 412.9 false S flags per hour; AUPRC 0.223.
    - F beats were predicted N 384 / S 3.
  - Diagnostic comparison of `rr_rule` against `const_n` on ds2s:
    - Delta +0.1401, 95% CI [+0.0220, +0.2424].
    - Without 232: +0.0494; leave-one-record-out range +0.049 (232) to +0.153 (221).
    - Per-class delta: S +0.394 [+0.049, +0.681]; N +0.026 [−0.005, +0.066]; V 0.
    - Outcome "favorable", with the suspicious flag, as expected for a reference against a constant.
  - The noise floor for the real comparison is measured in Phase 3 (see the null rule below).

### Fixtures
All in `tests/test_scorer.py`; run with `python -I -m pytest -q`. 28 passed on 2026-10-26 (revision `dd225b75db9a8c68`).

| Fixture | Expected | Observed | Tolerance | Result |
|---|---|---|---|---|
| Worked example: records A (truth NNNSV, pred NNSSV) and B (truth NNSVV + one F beat; pred NVNVN, F predicted V). Units confusion [[3,1,1],[1,1,0],[1,0,2]]; F1 N 0.6, S 0.5, V 0.6667; macro 0.588889; accuracy 0.6; F beat reported but not scored; 1 false S and 1 false V flag in 1.0 h; record-averaged S sensitivity 0.5 and V PPV 0.75 | as stated | as stated | 1e-6 relative | pass |
| Known-good prediction | 1.0 | 1.0 | 1e-6 | pass |
| Deliberately poor prediction (all N) | 0.222222 | 0.222222 | 1e-6 relative | pass |
| Row order shuffled; class absent from truth and predictions (F1 = 1; with one false positive, F1 = 0) | as stated | as stated | exact | pass |
| Average precision, hand examples (0.8333; tie gives 0.5) | as stated | as stated | 1e-6 | pass |
| Malformed: missing unit, missing F beat, duplicate, extra ID, labels outside {N,S,V}, missing columns, missing probability column, null ID, non-finite probability, probabilities not summing to 1 | rejected | rejected (11 cases) | n/a | pass |
| Paired comparison: identical arms; perfect vs all-N and reversed (per-class and AUPRC CIs); small detectable regression is unfavorable | as specified | as specified | n/a | pass |
| A gain carried by one record (removing it makes the delta negative) is not favorable; leave-one-record-out entry matches | not favorable | not favorable | exact | pass |
| Seed resampling widens the CI for seed-variable arms; reproducible; unequal seed counts rejected; extra rows rejected in compare; Bonferroni level 1 − 0.05/m | as specified | as specified | n/a | pass |
| Lookahead check: causal feature passes; whole-record mean RR fails; 3 s window fails | as specified | as specified | n/a | pass |
| Confirmation guard (synthetic files): no reason gives refusal; a malformed file is rejected before logging; access logged; third access refused; the real confirmation labels are never opened | as specified | as specified | n/a | pass |
| Real data: totals = de Chazal 2004; splits disjoint; 202 and paced records absent; released files label-free; `predict` recomputable from positions and record length; no SVDB labels outside `confirm/` | true | true | exact | pass |

## Scorecard
No weights are published, so equal weights are an *assumption*. Two gate rows must reach 3 before submission. Rated by the generator and the critic independently and blind, against these anchors.

| Criterion | Weight | Evidence that would convince the judges | 0 | 1 | 2 | 3 | Rated by |
|---|---|---|---|---|---|---|---|
| Performance relative to the comparable classical baseline | 25% | Headline EV1 paired delta (quantum-reservoir arm against matched ESN arm) on ds2s; SVDB confirmation; per-class, AUPRC and false-flag tables; pre-declared slices | No matched comparison, or a comparison with leakage or unequal tuning | Matched comparison run; outcome unfavorable or no detectable change, and not analysed further | No detectable change overall, but a pre-declared slice whose delta CI lower bound is > 0 at level 1 − 0.05/m (m = number of slice tests; all reported); or favorable on ds2s but not confirmed on SVDB | Favorable on ds2s under the full decision rule (including the 232 condition), and confirmed on SVDB (delta > 0, CI excluding 0) | generator + critic |
| Ingenuity | 25% | Write-up: the limitation addressed (fixed, training-free feature maps that must generalise to unseen patients; low-power physical reservoirs), the literature gap, controls that isolate the quantum effect | Off-the-shelf quantum ML with no rationale | Standard quantum model with a generic rationale | Quantum component tied to a specific limitation of the classical approach, with the literature gap cited | As 2, plus a design that isolates what is quantum (classical-spin mean-field control, separable ablation) and a feasibility link to hardware (Braket run) | generator + critic |
| Depth | 25% | Ablations, mechanism analysis, noise, shot and hardware evidence, per-class and per-patient analysis | One headline number | Per-class metrics plus one ablation | Ablations along at least 3 axes (entanglement, readout size, qubit count, shots or noise) with a mechanism explanation | As 2, plus device-noise simulation and a real-hardware subset, and an analysis of where and why quantum features help or fail (per patient and class, with a kernel or geometric diagnostic) | generator + critic |
| Soundness | 25% | Patient-held-out split; equal tuning budgets; two-level uncertainty; pre-registered rules; passed lookahead checks; confirmation access log; limitations; verification report | Patient leakage, tuning on the test split, or claims without evidence | Patient-held-out but unequal tuning, or no uncertainty | Patient-held-out, equal tuning budget, record- and seed-level CIs, lookahead check passed, limitations stated | As 2, plus access-logged external confirmation, a published variant count, a critic PASS, and every claim traceable to an experiment ID | generator + critic |
| Gate: deliverables complete | must reach 3 | Codebase with both approaches, comparative evaluation, explanation of problem, methods and quantum purpose, reproduction instructions (brief, "Prepare your submission") | Any item missing | (n/a) | (n/a) | All four present and checked by the critic | critic |
| Gate: reproducible | must reach 3 | Clean environment from `requirements-lock.txt`; `scripts/download_data.py` with checksum check; one command regenerates the headline tables | Headline cannot be regenerated | Regenerates with manual steps | Regenerates with one command, but not from a clean environment | Regenerates from a clean environment and fresh download, checked by the critic | critic |

- **Representativeness:** unverifiable against the judges before judging. No external feedback yet.

| Date | Who | What they said | Scorecard effect |
|---|---|---|---|

## Comparison procedure
- **Technical:**
  - **Units and dependence:** the evaluation units of the split. Beats within a record are dependent, so the record (patient) is the resampling unit.
  - **Paired signed delta:** both arms are scored on identical units. Delta = (seed-averaged macro-F1 of the candidate) − (seed-averaged macro-F1 of the baseline); positive means the candidate is better. Each arm has exactly 5 seeds; equal counts are enforced, and a count other than 5 is warned.
  - **Uncertainty:** two-level bootstrap, B = 2,000, generator seed 20261026.
    - Records are resampled with replacement, jointly for both arms. Seeds are resampled with replacement, independently within each arm.
    - B = 2,000 x m (m = number of comparisons in the Bonferroni adjustment), so the tails keep enough draws.
    - 95% percentile CI, Bonferroni-adjusted to 1 − 0.05/m when the headline has been replaced (rule 4).
    - Assumption: records are exchangeable draws of patients. With 21 records, one of which holds 77.5% of the S units, the CI is approximate and wide.
  - **Practical gain threshold:** +0.02 macro-F1.
  - **Decision rule:**
    - *Favorable* if delta >= +0.02, the CI lower bound > 0, **and** the point delta with record 232 removed is > 0 (ds2s and ds2).
    - *Unfavorable* if the CI upper bound < 0.
    - Otherwise *no detectable change*, which means insufficient evidence, not equivalence.
    - The output also records the outcome without the 232 condition, so a gain carried by 232 is visible and reported as such.
  - **Suspicious-gain threshold:** delta >= +0.05 macro-F1 queues an immediate verification.
  - **Null calibration (pre-declared):**
    - In Phase 3 the matched ESN arm (R0) is compared with itself using two disjoint 5-seed sets on ds2s.
    - If that comparison is not "no detectable change", or its |delta| > 0.01, the practical threshold becomes max(0.02, 2|null delta|). This takes the form of EV2, approved by the human before any quantum full evaluation.
  - **Reported with every comparison:** per-class F1 deltas with CIs, S/V AUPRC deltas with CIs, and the leave-one-record-out delta table.
- **Matched-baseline rules (pre-registered; they define "comparable classical baseline"):**
  1. **Same pipeline:** identical prediction set and units, beat segmentation, filtering, downsampling, input encoding and RR features, the same readout model class and regularisation grid, the same class weighting and decision-rule procedure, and the same 5 seed indices.
  2. **Readout dimension matched:** the classical reservoir block supplies exactly as many features to the readout as the quantum block (K_c = K_q). K counts every readout feature, including time-multiplexed snapshots and every Pauli observable.
  3. **Equal tuning budget:** each arm's realised count of DS1-CV configurations is the same N <= 40.
     - The count covers every design variant of that arm: qubit count, Hamiltonian, encoding and observable set for the quantum arm; size, spectral radius, leak rate, input scaling and sparsity for the ESN.
     - Both search spaces are declared in EXPERIMENTS.md before the first tuning run. The ESN space includes standard settings (spectral radius 0.5-1.2, leak rate 0.1-1, input scaling 0.1-2).
     - Same random-search procedure and seed scheme. Tuning never reads ds2s, ds2 or svdb.
  4. **Headline pre-registered:**
     - The headline is the first quantum-versus-matched-ESN pair evaluated on ds2s. It is named by experiment ID on its card before the run.
     - Later pairs are secondary, unless the human approves a replacement. A replacement's decision uses a 1 − 0.05/m CI (m = number of quantum-vs-classical pairs evaluated on ds2s so far, passed as `--n-comparisons`), and the write-up reports m and every earlier pair.
  5. **Variant count:** every ds2s or ds2 scoring of any arm is logged in EXPERIMENTS.md and reported in the write-up. At most 15 such full evaluations on EV1 without the human's approval.
  6. **Measurement model:**
     - The headline quantum arm uses finite-shot readout: 1,024 shots per circuit per beat, Z-basis, simulated by sampling. Exact expectation values are an ablation only.
     - The headline classical reservoir is a leaky-tanh echo state network (ESN).
  7. **Further controls,** reported with the same procedure:
     - the classical-spin (mean-field, product-state) reservoir of the same Hamiltonian, after the matching rule of Kornjača et al. 2024 (`doi:10.48550/arxiv.2407.02553`);
     - a separable (non-interacting) quantum reservoir;
     - RR plus handcrafted features alone;
     - a strong classical reference for context only.
- **Pre-declared slices and regimes** (secondary; each counts against the cap where it needs a new ds2s scoring).
  - Slice decision rule: a slice counts as favorable only if its delta CI lower bound is > 0 at level 1 − 0.05/m, where m = 4 slice tests (S-class F1, V-class F1, low-data k = 5, low-data k = 11).
  - Every slice result is reported, whatever its outcome. Adding a slice after any result is seen raises m and must be disclosed.
  - (a) per-class F1 deltas for S and V (in every compare output);
  - (b) record 232 removed (in every compare output);
  - (c) **low-data regime:** both arms of the headline pair retrained on k ∈ {5, 11} DS1 records (seeded draw, seed 20261026), with the same configuration as selected on full DS1, then scored on ds2s;
  - (d) the SVDB confirmation;
  - (e) optional diagnostics: patient-grouped CV over the 43 non-paced MIT-BIH records with 201/202 as one group, and the causal-only boundary. These are reported as diagnostics and never used for selection.
- **Rubric:** two raters, the generator and the critic, rate blind against the anchors.
  - A change counts only when both raters move the same way on the claimed criteria.
  - The inter-rater gap is disagreement: an internal consistency check, not an uncertainty estimate and not validation against the judges.
  - Rubric gains are internal assessments wherever reported.
- **Tradeoff rule:**
  - The two gate rows must reach 3, whatever else happens.
  - Otherwise the equal-weight sum decides, unless the human rules otherwise.
  - A soundness rating below 2 vetoes any submission claim of improved performance.
- **Hardware and noise tracks (pre-declared result types):**
  - **Device-noise simulation:** the quantum arm simulated with a noise model of the target QPU, scored on ds2s. A full result for a distinct, secondary candidate, counted against the cap.
  - **Real-hardware run on Amazon Braket:**
    - Result type: *diagnostic*. A stratified subset of about 100 ds2s beats, chosen by a seeded draw before any hardware run, is scored on hardware with a readout trained on simulated DS1 features.
    - Reported: per-beat agreement with the noiseless and finite-shot simulations, macro-F1 on the subset with a bootstrap CI, and feature correlation.
    - It cannot change the headline outcome.
    - Every task needs the human's approval with a cost estimate, within the USD 90 cap.

## Confirmation policy
- **Technical:** SVDB (`svdb`, 78 records, 184,286 units) is the confirmation set.
  - **Use:** it is never used for training, tuning, selection or diagnostics. The final headline pair (the exact DS1-trained artifacts) is scored once with `qhc.evaluate compare --split svdb --confirm-reason "..."`.
  - **Pass criterion, fixed now:** *confirmed* if the SVDB paired delta is > 0 and its 95% CI lower bound is > 0 (two-level bootstrap over the 78 records).
  - **Caveats:** absolute scores will be lower for both arms (domain shift). The bootstrap may be anti-conservative if records share subjects (A006).
  - **Guard (tested):** the command validates the predictions against the label-free prediction set first, refuses a third access (cap 2, counted from `runs/confirmation_access.jsonl`), logs the access, and only then reads `confirm/labels_svdb.csv`.
  - **Access cap:** 2 project-wide (the final pair, plus one repair rerun).
- **Access log** (appending here is bookkeeping and does not create a new version):

| Date | E### | Reason |
|---|---|---|
| 2026-10-26 | none | Data-card inspection by the agent (headers, label counts); no predictions scored |
| 2026-10-26 ~17:45 | none | **Incident, not a scoring access.** While testing the confirmation guard, a bug (the data path was bound when the function was defined, so the test's patched path was ignored) made `load_labels` open the real `confirm/labels_svdb.csv` inside a pytest run. Synthetic predictions failed beat-ID validation before any metric was computed. The only output was the error `qhc.scorer.PredictionError: 184389 prediction-set beats have no prediction, e.g. svdb:800:100002`, which reveals a beat ID (public positions) and the size of the prediction set, both already in the released positions file. No label values or scores were displayed or stored, and the real access log was not written. V002 judged the entry and the fix adequate. **To be disclosed in the write-up's limitations.** Fixed in `dd225b75db9a8c68`; the guard test now asserts the real file is never opened. Not counted against the cap. Recorded for transparency. |

- **Rubric:** none available before judging. The Phase 6 rehearsal is a readiness check, not confirmation.

## Runtime / resources
- **Full evaluation runtime and cost:** scoring under 10 s; a comparison (2,000 bootstrap replicates with AUPRC) under 1 min on the CPU for ds2s. Model runtime is to be measured in Phase 3; the per-run cap is 3 GPU-hours.
- **Demo build time:** n/a so far.

## Response to V001 (critic metric review, 2026-10-26)

| Finding | Change |
|---|---|
| B1: label leak through `is_unit` | `positions_*` now carry a label-free `predict` flag. Pipelines predict all beats in the prediction set, including F and Q. The scorer selects the units. A test recomputes the flag from positions and record length. |
| B2: the 1.0 s boundary contradicted post-RR | Boundary redefined as b_i = max(t_{i+1}, t_i + 1.0 s), one-beat lookahead. `qhc.leakcheck` is required before any full evaluation. The causal-only variant is pre-declared as optional. |
| B3: budget and selection loopholes | Equal realised N <= 40 per arm covering all design variants; search spaces declared in EXPERIMENTS.md before tuning; headline = first pair evaluated on ds2s, named before its run; replacements need the human's approval and a Bonferroni CI; ds2 counts against the cap. |
| S1: 232 dominance (77.5%) | Favorable now also requires the delta without 232 to be > 0. Leave-one-record-out table and per-class CIs in every comparison. |
| S2: seeds fixed | Two-level bootstrap (seeds resampled within each arm), plus the pre-declared null-calibration rule. |
| S3: operating point | Probabilities mandatory; S/V AUPRC deltas with paired-bootstrap CIs; decision-rule procedure identical across arms. |
| S4: review burden | False flags per hour and EC57 record-averaged sensitivity and PPV added. No per-record macro-F1. |
| S5: shot model | Headline quantum arm uses 1,024 Z-basis shots per circuit; exact expectations are an ablation; K counts every readout feature; headline classical reservoir = leaky-tanh ESN. |
| S6: confirmation guard | Validate first, enforce the cap, log, then read labels from `confirm/`. Pass criterion and SVDB lead and resampling fixed here. A6 caveat added. |
| S7: undeclared slices | Slices (a) to (e) declared above. |
| Minor | Extra rows rejected in compare; unequal seed counts rejected; F/Q prediction distribution reported; 44-record grouped CV and causal-only variant declared as optional diagnostics; suspicious threshold lowered to 0.05; 232 share corrected to 77.5%. |

## Defects and change history
| Version | Date | Reason / defect | Approved by | Affected experiments |
|---|---|---|---|---|
| EV1 (draft r1) | 2026-10-26 ~17:29 | initial draft | not approved | none |
| EV1 (draft r2) | 2026-10-26 17:48 | V001 findings B1-B3, S1-S7 and minor fixed before approval; no experiment existed | not approved | none |
| EV1 (draft r3) | 2026-10-26 17:55 | V002 residuals: slice decision rule with Bonferroni, B scaled with m, paths anchored to project root, causal-only wording, cross-record fitting forbidden, incident error text | pending | none |
