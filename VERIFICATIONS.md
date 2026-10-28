# Verifications (open mode)

One report per verification, written by the critic. The coordinator links each report from its experiment card. Metric reviews and rehearsal question sets are also recorded here, with verdict n/a.

## V001
- **Report type:** metric review
- **Experiment / candidate revision / comparison baseline / component parents / EV#:** none (no candidate exists). EV1 draft, code revision `f816fe79bf5f1fb4`, fixtures `70b4c33b861de1c0`. Reviewed 2026-10-26 by the critic in a fresh context.
- **Claim under review:** EV1 (draft) fits the user's decision and does not flatter either arm or hide an error a clinician would care about. EV1 consists of: macro-F1 over N/S/V on ds2s units; the paired record-cluster bootstrap; the decision rule and thresholds; the matched-baseline rules; and the SVDB confirmation policy.
- **Packet contents and raw evidence links:**
  - Read: CLAUDE.md, the 05-verification guide, PROBLEM_BRIEF.md ("Chosen problem (exact)"), EVAL.md, ANOMALIES.md, `src/qhc/{evalspec,units,scorer,evaluate}.py`, `tests/test_scorer.py`, `runs/data/processed/EV1/manifest.json`, `runs/EV1_reference/*.json`, and the ds1/ds2s positions and labels files.
  - Not read: IDEAS.md, `labels_svdb.csv`. Nothing was scored on svdb.
  - The critic's scripts are outside the repo: `check1.py` (independent rescoring and bootstrap) and `check2.py` (leak and lookahead counts), in the session scratchpad `C:\Users\admin\AppData\Local\Temp\claude\C--Users-admin-Desktop-Water-Hackathon-quantum-healthcare\2942d4c9-43db-4379-9b05-5a31d0d761be\scratchpad\v001\`.
- **Checks** (pass / fail / n/a (reason) / not run; one line of evidence each):
  1. Reproduce: **pass.**
     - `.venv/Scripts/python -I -m pytest -q` gives 24 passed.
     - The revision hash recomputes to `f816fe79bf5f1fb4`. The ds1/ds2s positions, labels and folds hashes equal `manifest.json`.
     - All 144 MIT-BIH record files present (48 records x .dat/.hea/.atr) match `SHA256SUMS.txt`, whose own hash is `b61158a9...`.
     - Independent code, no `qhc` import:
       - `const_n` on ds2s = 0.314736 (F1_N = 84,296/89,277 = 0.944207; S and V = 0).
       - `rr_rule` rebuilt from positions has 0 disagreements with `pred_rr_rule_ds2s.csv`: macro 0.454878, S Se 0.844, PPV 0.257.
       - Bootstrap with the same draw scheme: delta +0.14014, CI [+0.02196, +0.24239]. All equal EVAL.md.
  2. Comparison: **pass, with findings S2 and M1.**
     - `scorer.compare` is correctly paired: the same record weights apply to both arms, and seeds are averaged inside each replicate.
     - Seeds are held fixed in the CI, and the seed count is not enforced: 1 candidate file against 5 baseline files is accepted (tested on synthetic data).
  3. Leakage: **fail (evaluation defect, small magnitude).** `is_unit` in `positions_*.csv` is derived from labels, so test-patient F/Q beat locations are released to pipelines (B1).
  4. Lookahead: **fail (specification inconsistency).** The +1.0 s boundary contradicts the declared post-RR feature for 15.6% of ds2s units (B2). Enforcement is by code review only; no automated check exists.
  5. Metric and selection: **concerns.**
     - Selection and tuning-budget loopholes in matched-baseline rules 3-5 (B3).
     - Operating-point sensitivity of a hard-decision metric (S3).
  6. Validity (incl. data card complete, raw hash matches, licence allowed): **pass for MIT-BIH.**
     - Hashes match, and ODC-By 1.0 allows the use.
     - The data card is complete apart from items M2 and S6.
     - SVDB raw hashes were not rechecked, to avoid touching the confirmation data beyond what the rules allow.
  7. Robustness (applied to the metric, since there is no candidate): **concern** (S1).
     - On ds2s, record 232 holds 1,381 of 1,781 S units (77.5%). Without 232, record 222 holds 52.2% of the remaining 400.
     - V is spread more evenly: 233 holds 25.9% and 200 holds 25.8%.
     - 6 of 21 records have no S units, and 6 have no V units.
     - 34.0% of bootstrap replicates contain no record 232.
  8. Selection exposure: **n/a (no candidate).**
     - Confirmation log reviewed: one data-card inspection entry in EVAL.md, and no `runs/confirmation_access.jsonl` exists. This is consistent with "nothing scored on SVDB".
     - The guard has defects (S6).
  9. Blind rubric rating: **n/a** (metric review; no deliverables).

     | Criterion | Critic | Generator | Gap |
     |---|---|---|---|
     | n/a | | | |

  10. Claims check: **n/a for deliverables.** EVAL.md statements not matched by code or data:
      - "position files carry no labels (tested)": false (B1). The test checks only the `symbol`/`aami` column names.
      - "Each arm runs the same 5 seeds": not enforced (M1).
      - "Access cap: 2": not enforced (S6).
      - "one of which holds 75% of the S beats": 75.2% is the DS2 figure. On ds2s it is 77.5% (M2).
- **Findings, ranked by severity:**
  - **Blocking for approval.** All three are cheap to fix and change unit files or pre-registered rules, so they should land before EV1 is frozen.
    - **B1. Label leak through `is_unit`** (`units.py:47-52`, written at `:95`).
      - What leaks: interior beats of class F, Q or "other" get `is_unit=False`, so a pipeline reading `positions_ds2s.csv` can locate every F/Q beat of the test patients.
      - Size: 394 such beats in ds2s (362 in record 213), and 894 in ds1 (472 `!` flutter waves in 207, 374 F in 208).
      - Measured signal: in DS1, units next to such a beat are 35.8% V against 7.0% otherwise; in ds2s, 2.7% against 6.8%. The signal is learnable but transfers badly.
      - It favours neither arm by construction. But it is a label channel in test inputs, and it contradicts a stated soundness claim.
      - Fix:
        1. Make the prediction set label-free. Pipelines predict every beat annotation that passes the edge and first/last rules (computable from sample, fs and sig_len), F/Q included. The scorer selects the N/S/V units from labels.
        2. Drop `is_unit`, or replace it with an edge-only flag.
        3. Add a test that the released flag is a function of position only.
      - This also makes it possible to report F-beat predictions, which the brief promises.
    - **B2. The decision-time boundary contradicts the post-RR feature** (EVAL.md "Allowed inputs", which says up to t + 1.0 s; the brief allows lookahead "to the next R-peak").
      - 7,358 of 47,129 ds2s units (15.6%) have their next beat more than 1.0 s later, up to 5.87 s.
      - This includes 383 of 1,781 S units: 275 in 232 and 86 in 222.
      - A pipeline using the standard post-RR feature therefore breaks the written rule exactly where S-F1 is decided, and the rule cannot be tested as written.
      - Fix: pick one rule and write it down.
        - (a) One-beat lookahead: signal and positions up to the next beat annotation, with variable latency, and nothing beyond.
        - (b) Fixed latency of t + 1.0 s, with post-RR censored at 1.0 s plus an indicator.
      - Then add a runnable lookahead check: truncate test records at the boundary for a sample of beats and require identical predictions.
      - Also pre-declare the brief's causal-only (no post-RR) sensitivity analysis, or remove it from the brief.
    - **B3. The tuning-budget and headline-selection rules leave room for a flattering quantum claim** (matched-baseline rules 3-5).
      - Gaps:
        - (i) "At most 40" allows the two arms to end up with different realised budgets.
        - (ii) The budget is not stated to cover every design variant. The quantum side could try several Hamiltonians, encodings or observable sets with 40 configurations each while the classical side gets one search.
        - (iii) Rule 4 allows adaptive iteration: evaluate pair A on ds2s, see the result, design B, select B on DS1, evaluate B on ds2s, and promote B to headline. Every step is "selected on DS1", but the sequence adapts to ds2s, and with 15 allowed evaluations the headline becomes a best-of-many (Bowles et al.'s positivity bias).
        - (iv) The search spaces are not declared.
      - Fix:
        1. Equal realised count N <= 40 per arm. The count covers every DS1-CV configuration of every design variant of that arm.
        2. Declare both search spaces before the first tuning run. The ESN space must include standard settings.
        3. Pre-register the headline as the first quantum-versus-matched-classical pair evaluated on ds2s, named by experiment ID before the run.
        4. Later pairs are secondary unless the human approves a replacement. A replacement uses a 1 - 0.05/m CI for m such comparisons, and m is reported.
        5. ds2 scorings count toward the cap of 15.
  - **Should fix:**
    - **S1. One patient can carry the headline.**
      - For `rr_rule`, 77.3% of S true positives come from 232, and the delta falls from +0.140 to +0.049 without it. Macro delta is roughly (ΔF1_S + ΔF1_V)/3.
      - Fix:
        - "Favorable" headline wording also requires the excluding-232 delta to be > 0. Otherwise the wording is "favorable, carried by record 232".
        - Add a leave-one-record-out influence table, and per-class ΔF1 with CIs, to every compare output.
    - **S2. Seeds are fixed inside the CI.**
      - Reservoir draws are part of the claim "quantum vs classical reservoirs".
      - Fix: use a two-level bootstrap (seeds resampled within each arm, records jointly).
      - At minimum, pre-declare this: if the Phase 3 R0-against-R0 null comparison is not "no detectable change", or its |delta| exceeds 0.01, then seed resampling is added and the threshold becomes max(0.02, 2|null delta|), as a new version before any quantum run.
    - **S3. Operating point.**
      - Hard argmax F1 under prior shift (S prevalence 1.9% in DS1, 3.8% in ds2s, 6.6% in SVDB) can produce a delta from a threshold shift alone.
      - Fix:
        - Rule 1 makes the decision rule identical across arms, with any thresholds fitted inside the shared budget.
        - `prob_*` columns become mandatory for headline arms.
        - Pre-declare per-class AUPRC (S, V) with the same paired bootstrap as a threshold-free secondary.
    - **S4. Pooled F1 hides the review burden.**
      - `rr_rule` has S PPV 0.257, which is about 413 false S flags per hour across ds2s.
      - Fix:
        - Add EC57 record-averaged Se/PPV per class (over the records containing that class) and false flags per hour to the outputs.
        - Avoid per-record macro-F1: with the vacuous-class convention, one false flag in an S-free record flips S-F1 from 1 to 0.
    - **S5. The quantum arm's measurement model is undeclared.**
      - Exact expectation values amount to infinite shots, which flatters the quantum arm relative to hardware.
      - Fix:
        - Declare the headline shot model and add a finite-shot ablation.
        - State that K_q counts every readout feature, including time-multiplexed ones.
        - Name the headline classical reservoir (the ESN) explicitly.
    - **S6. Confirmation guard.**
      - `evaluate.py:69,81` log the access before the labels load and the predictions are validated, so a malformed file uses up one of the 2 accesses.
      - The cap is not enforced in code.
      - `scorer` functions can read `labels_svdb.csv` without logging.
      - Fix:
        - Validate the prediction IDs against positions before logging.
        - Refuse a third access.
        - Isolate `labels_svdb.csv` so that only the guarded path reads it.
      - Also put these in the confirmation policy before any access:
        - the SVDB pass criterion (same sign, CI excluding 0; currently stated only in the scorecard);
        - the SVDB lead and resampling choice, fixed without labels;
        - the caveat that the record bootstrap may be anti-conservative if records share subjects (A006).
    - **S7. Scorecard Performance anchor 2 credits "a pre-declared slice" but none is declared.** Fix: list the slices now. Otherwise slice choice will be post hoc.
  - **Minor:**
    - **M1. `compare` and `score` disagree.**
      - `scorer.compare` filters prediction rows to the units before validation (`scorer.py:124-127`), so it silently accepts non-unit rows that `score` rejects.
      - It also accepts unequal seed counts.
      - Fix: validate before filtering, and assert 5 distinct files per arm.
    - **M2. Wording and coverage.** EVAL says 75%; the ds2s figure is 77.5%. The brief's secondary analyses (grouped CV over 44 records; causal-only; F "reported") are missing from EVAL. Add them, or record why they are dropped.
    - **M3. Decision-rule labels.**
      - A gain that is detectable but below threshold (delta in (0, 0.02) with CI lower > 0) is labelled "no detectable change", while a detectable -0.001 is "unfavorable".
      - The asymmetry is conservative and acceptable. The write-up should say "below the practical threshold" for such gains.
    - **M4. Suspicious-gain threshold.** 0.08 is loose given that small differences are expected. 0.05 is suggested; this only changes urgency, since every candidate is verified anyway.
    - **M5. Clinical units.** Translate +0.02 into clinical units, for example about +0.06 S-F1, or so many fewer false S flags per hour.
    - **M6. Shared limitations.**
      - Oracle fiducials may encode the beat class (V placement), and `beat_id` exposes the record number (1xx random, 2xx selected for arrhythmia).
      - Both arms share these. Verification should check that no pipeline parses the record ID, and the limitations should be stated.
    - **M7. Recorded command.** The `command` field records the script path, not the `-m` invocation.
- **Alternatives considered and what each would change:**
  - **Pooled N/S/V macro-F1 (current):** comparable with the literature. One third of it is S, which is 77.5% one patient.
  - **EC57 record-averaged Se/PPV:** weights patients equally. `rr_rule` S Se is 0.859 averaged against 0.844 pooled, but PPV is unstable in records with few S beats. Secondary (S4).
  - **Macro-F1 without 232 as co-primary:** then 222 holds 52%, and power is lost. The sign-consistency rule (S1) is preferred.
  - **Per-class AUPRC:** separates feature quality from the operating point, but makes no committed decision. Secondary (S3).
  - **N/S/V/F macro-F1:** F on ds2s is 362 of 387 beats from record 213, a single-patient class, so excluding it from the primary is correct.
  - **False flags per hour plus sensitivity:** closest to the reviewer's burden. Secondary (S4).
  - **MCC or kappa:** similar ranking; no change expected.
  - **Grouped CV over the 44 records (from the brief):** more clusters, but more complex nested selection. Optional secondary.
- **Implementation and evaluation valid:** no, as drafted (B1, B2). Both are fixable before approval, and no experiment is affected.
- **Improvement claim supported:** n/a (metric review)
- **Verdict:** n/a (metric review)
- **Scope and limitations of verdict:**
  - No SVDB labels were read or scored. SVDB unit construction was checked by code reading only (the same function as MIT-BIH).
  - De Chazal's record lists were checked only through the reproduced published class totals.
  - Coverage of the cluster bootstrap with 21 skewed clusters was not simulated.
- **Evaluation defect found:** yes.
  - (1) `is_unit` in `positions_*.csv` releases label-derived F/Q locations of test patients (B1).
  - (2) The +1.0 s decision-time boundary is inconsistent with the declared post-RR feature for 15.6% of ds2s units (B2).
  - Affected experiments: none (draft, no runs). Recovery: fix both before approval.

## V002
- **Report type:** metric review re-check (of V001 findings)
- **Experiment / candidate revision / comparison baseline / component parents / EV#:** none. EV1 draft r2, code revision `dd225b75db9a8c68` (recomputed, matches), fixtures `ccbe3120d947a5a7` (matches EVAL.md). Reviewed 2026-10-26.
- **Claim under review:** EV1 draft r2 resolves V001 findings B1-B3 and S1-S7 and introduces no new defects.
- **Packet contents and raw evidence links:**
  - Read: EVAL.md r2 (including "Response to V001" and the access-log incident), `src/qhc/*.py` (including the new `leakcheck.py`), `tests/test_scorer.py`, the rebuilt `runs/data/processed/EV1/` files, and `runs/EV1_reference/compare_rr_vs_const_ds2s.json`.
  - Not opened: `confirm/labels_svdb.csv`. My scripts wrap `pd.read_csv` so that they fail on any path under `confirm/`.
  - For svdb, only the label-free `positions_svdb.csv` and `records_svdb.csv` were read.
  - Scripts: `check3.py` and `check4.py` in the V001 scratchpad folder. The guard probes ran on synthetic files in a temp directory.
- **Checks:**
  1. Reproduce: **pass.**
     - pytest: 28 passed.
     - All 13 manifest output hashes match their files (the `confirm/` file was not opened).
     - Units are unchanged: 47,129 ds2s units (42,148 / 1,781 / 3,200).
     - My own code reproduces const_n 0.314736 and rr_rule 0.454878, and rr_rule's S AUPRC of 0.2229 (EVAL.md: 0.223).
     - The reference compare JSON reproduces: delta +0.1401, CI [+0.0220, +0.2424]. Leave-one-record-out without 232 is +0.0494 and without 221 is +0.1530, both equal to my values.
  2. Comparison: **pass.**
     - The two-level bootstrap reproduces exactly against my explicit-duplication implementation using the same RNG order: CI [-0.03633, +0.12076] on synthetic 5-seed arms.
     - `_boot_f1` and `_boot_ap` equal F1 and AP recomputed on explicitly duplicated records and seeds (max abs diff 0.0).
     - `average_precision` equals my threshold-sweep AP on tie-heavy data.
  3. Leakage: **pass (B1 resolved).**
     - `positions_*` columns are now beat_id, db, record, sample, fs and predict. `records_*` columns are record, fs, sig_len and duration_s.
     - In all four splits, `predict` equals my own position-only rule.
     - check2 rerun: there are 0 interior non-predict beats (previously 394 in ds2s and 894 in ds1), so the adjacency signal is gone.
     - The ds2s prediction set includes F 387 and Q 7.
  4. Lookahead: **pass (B2 resolved).**
     - b_i = max(t_{i+1}, t_i + 1 s) is consistent with post-RR.
     - Probes of `check_lookahead`:
       - flagged: whole-record z-score 10/10, whole-record median 10/10, beats-per-record 9/10, second-next RR 9/10;
       - not flagged: post-RR 0/10 (allowed);
       - also not flagged: `len(signal)` 0/10. That is record metadata already in `records_*`, not a leak.
  5. Metric and selection: **pass, with one residual (R1).** Rules 3-5 now close the V001 loopholes.
  6. Validity: **pass.** SVDB lead (ECG1) and resampling are now fixed without labels.
  7. Robustness: **pass.** The 232 condition, leave-one-record-out table and per-class CIs are present in the output and tested.
  8. Selection exposure: **pass.**
     - Guard order checked on the compare path. A malformed baseline seed raises PredictionError with no log written. A good pair logs exactly once and writes `confirmed`. The cap is enforced in code.
     - `runs/confirmation_access.jsonl` does not exist in the project (no access so far).
  9. Blind rubric rating: **n/a** (metric review).
  10. Claims check: **pass.** EVAL r2 statements match the code and data; residuals R1-R4 below.
- **Per finding:**

  | Finding | Status | Evidence |
  |---|---|---|
  | B1 | resolved | Checks 3 and 1 |
  | B2 | resolved | Check 4 |
  | B3 | resolved | Rules 3-5: equal realised N covering all variants; headline = first pair, named before its run; Bonferroni on replacement; ds2 counted |
  | S1 | resolved | `decide` requires the delta without 232 > 0; the fixture shows a one-record gain is not favorable |
  | S2 | resolved | Two-level bootstrap verified; null rule pre-declared |
  | S3 | resolved | Probabilities mandatory; AUPRC verified |
  | S4 | resolved | False flags per hour and record-averaged Se/PPV; fixture hand-checked |
  | S5 | resolved | 1,024 Z-basis shots; ESN named; K counts every feature |
  | S6 | resolved | Order and cap verified; pass criterion is in the code (`confirmed`) |
  | S7 | partially | See R1 |
  | Minor | resolved | Extra rows and unequal seeds rejected (tested); suspicious threshold 0.05; 77.5% corrected |

- **Residual findings (none blocking):**
  - **R1 (should fix, text only): slices have no decision rule and no multiplicity control.**
    - Scorecard Performance level 2 can be earned by any of at least 4 slice tests (S-F1 delta, V-F1 delta, low-data k = 5, k = 11).
    - None of them has a decision rule or a multiplicity control.
    - Fix: a slice is favorable only if its CI lower bound > 0 at 1 - 0.05/m_slices, and all slices are reported.
  - **R2 (minor): wide Bonferroni levels need more replicates.** With B = 2,000, a level such as 1 - 0.05/10 rests on the 5th order statistic. Fix: scale B with m, for example B >= 2,000·m.
  - **R3 (minor): the cap ledger is a relative path.**
    - `ACCESS_LOG` and `PROCESSED` are relative to the working directory, so the cap counter is tied to running from the project root. Fix: anchor them to the package root.
    - The causal-only variant (b_i = t_i + 0.5 s) still sees post-RR whenever RR < 0.5 s. The wording "no post-RR" should be adjusted.
  - **R4 (minor): limits of the lookahead check, and two notes.**
    - The lookahead check is per record. It cannot detect statistics fitted across test records, which remains a code-review item for each verification.
    - A null comparison that is not "no detectable change" would also indicate a CI miscalibration, not only the need for a higher threshold.
    - Predictions of S or V on F/Q beats are reported separately, not as false flags.
- **SVDB incident (access log, ~17:45):** the log entry and the fix are adequate, and SVDB is **not compromised** as a confirmation set.
  - SVDB's confirmatory value depends on no training, tuning or selection decision being informed by its labels.
  - No model existed. Validation failed on beat IDs, which equal the public prediction set. By the coordinator's account, no class values or scores were displayed or stored.
  - The fix is verified: load paths are now resolved at call time, and the guard test plus my probes assert that the real file is never opened.
  - Limits and requests:
    - I cannot independently verify what the pytest run displayed. Please add the exact error text to the incident row.
    - Mention the incident in the write-up's confirmation section.
    - The code cap counts only the jsonl, so the EVAL.md log and the jsonl are two ledgers. Report both.
- **Implementation and evaluation valid:** yes, for EV1 draft r2 as a specification. No candidate exists yet.
- **Improvement claim supported:** n/a (metric review)
- **Verdict:** n/a (metric review re-check)
- **Scope and limitations of verdict:**
  - No SVDB labels were read and nothing was scored on svdb.
  - The guard was exercised only on synthetic files.
  - The incident account rests on the coordinator's statement.
- **Evaluation defect found:** no new defect. The V001 defects (B1, B2) are resolved in r2. R1 should be fixed before approval but is not blocking.

## Template (copy for V002 onward)
- **Report type:** candidate verification / validity-only (R0) / metric review / rehearsal questions
- **Experiment / candidate revision / comparison baseline / component parents / EV#:**
- **Claim under review:**
- **Packet contents and raw evidence links:**
- **Checks** (pass / fail / n/a (reason) / not run; one line of evidence each):
  1. Reproduce:
  2. Comparison:
  3. Leakage:
  4. Lookahead:
  5. Metric and selection:
  6. Validity (incl. data card complete, raw hash matches, licence allowed):
  7. Robustness:
  8. Selection exposure (variants in line / full evaluations on EV#; confirmation access logged?):
  9. Blind rubric rating (from packet.md alone, written down before opening packet-selfrating.md):

     | Criterion | Critic | Generator | Gap |
     |---|---|---|---|

  10. Claims check: <claims without an experiment ID or source>
- **Implementation and evaluation valid:** yes / no / undetermined
- **Improvement claim supported:** technical yes / no / undetermined; rubric yes / no / undetermined; n/a for validity-only or non-candidate reports
- **Verdict:** PASS / FAIL / NEEDS-MORE / n/a (metric review or rehearsal questions)
- **Scope and limitations of verdict:**
- **If FAIL:** defect and location. **If NEEDS-MORE:** single most informative next test, or the missing item.
- **Evaluation defect found:** no / yes (describe; triggers the recovery rule)

## V003
- **Report type:** metric review re-check (of EV1 draft r4 against the independent review `EV1_R3_REVIEW.md`)
- **Experiment / candidate revision / comparison baseline / component parents / EV#:** none (no candidate exists). EV1 draft r4, code revision `a2439884ff2f1909`, fixtures `15f4ece17d6839a2` (both recomputed and matched; 33/33 tests pass). Reviewed 2026-10-26 ~18:50-19:00 by a critic subagent in a fresh context.
- **Claim under review:** EV1 r4 resolves every item of the r3 review (R1-R6, additional changes, small corrections, acceptance checks) and introduces no new defect.
- **Packet contents and raw evidence links:** full report `runs/V003/report.md` (saved by the coordinator; the harness blocked the subagent from writing it); probes `runs/V003/probes.py`, results `runs/V003/probe_results.json`. All probes synthetic, with the processed-data path and both logs redirected; `confirm/`, raw SVDB annotations, real ds2s/ds2/svdb scoring and the real logs were not touched.
- **Checks:** R1, R2, R3, additional 1-5 and the small corrections resolved; independent brute-force bootstrap reproduces the CIs to ~1e-16; Table V formulas match term for term. R4, R5, R6 partly resolved.
- **Verdict:** NEEDS-CHANGES. Blocking B1 (headline and low-data slices could be chosen after ds2s peeks); should-fix S1 (copies pass as seeds), S2 (a failure after logging spends a confirmation access), S3 (a repair could change models); minor M1-M6.
- **Coordinator response:** all findings addressed in EV1 draft r5; table "Response to V003" in EVAL.md.
- **Follow-up re-check (same critic, ~19:00-19:05) of the intermediate r5** (revision `ba12ebc1e0ad903c`, fixtures `dc7b3985739aabe5`, 38/38 pass): **APPROVE-READY.** B1, S1-S3 and M1-M6 resolved (probes `runs/V003/r5/probes_r5.py`, results `runs/V003/r5/probe_results_r5.json`). New: should-fix N1 (a reference-only "headline" would open ds2s to other models early); minor N2 (SVDB before any headline), N3 (identical headline rerun refused after later entries), N4 (`--out` could overwrite an input), N5 (no code guard for test labels outside the command), and serialization errors at the final write.
- **Coordinator response to the follow-up:** N1-N4 and the write fallback fixed in the final r5 (revision `9a1922c8898b90db`, fixtures `7f323fb891968894`, 38 pass); N5 handled procedurally (verifications grep pipeline code for test-label reads). The final r5 was not re-checked by the critic; the changes are confined to `_check_order`, `_confirmation_access`, `_check_out`, `_smoke_test` and `_write`, each covered by a test.

## V004
- **Report type:** validity-only (R0)
- **Experiment / candidate revision / comparison baseline / component parents / EV#:** E002 (R0, matched leaky-tanh ESN arm). Artifacts produced with pipeline `da67af87f8b8fd73` (run manifests), tuning launched with `cf7bd4bd0a9634f8` (reconstruction in `runs/E002/pipe_at_tuning/`; its raw-bytes hash recomputes to `cf7bd4bd0a9634f8`). Pipeline on disk when this verification started (21:52 UAE): **`55884b1fb66732b9`**, not the `ad80a50e051c6820` the packet calls current (M1). Comparison baseline: none (first incumbent; comparison checks n/a). Component parents: none. EV1 approved r5, evaluation revision `9a1922c8898b90db` (recomputed), fixtures `7f323fb891968894` (recomputed). Reviewed 2026-10-26 21:52-22:15 UAE by a critic subagent in a fresh context.
- **Claim under review** (from `runs/E002/packet.md`):
  1. The E002 pipeline fits and selects on DS1 only, has no leakage or lookahead, and writes outputs the EV1 command accepts.
  2. Its ds2s macro-F1 0.7065 (mean of 5 seeded runs) comes from the approved evaluation command.
  3. The slice runs from a clean checkout, and its data provenance is recorded.
  4. Every claim in `README.md` "Result so far" has evidence.
- **Packet contents and raw evidence links:**
  - Read: CLAUDE.md, the 05-verification guide, `runs/E002/packet.md` (including "Clean-environment results", appended 21:58), EVAL.md (EV1 r5 with D1-D6), PROBLEM_BRIEF.md, README.md, `src/qhc/pipe/*.py`, `src/qhc/leakcheck.py`, the run and check parts of `src/qhc/evaluate.py` and `scorer.validate`, `scripts/reproduce.py`, `scripts/download_data.py`, the real-data fixtures in `tests/test_scorer.py`, the E002 artifacts, `runs/E003/compare_ds2s_headline.json`, `runs/full_eval_log.jsonl`, the EXPERIMENTS.md declarations and the E002/E003 card fields. `runs/E002/packet-selfrating.md` was opened only after my ratings were written (`runs/V004/blind_ratings.json`, with an addendum written before opening it).
  - Not read or hashed: IDEAS.md, `labels_ds2s.csv`, `labels_ds2.csv`, `runs/data/processed/EV1/confirm/`, `runs/data/raw/svdb/`. Not touched: `runs/E010/`, `runs/E011/`, and every existing `runs/E###/` directory except for reads.
  - Critic outputs and scripts, all in `runs/V004/`:
    - `pipe_snapshot/`: the exact pipeline code that ran (`55884b1fb66732b9`);
    - `driver.py`, `driver_stdout.txt`, `driver_log.json`: features rebuilt into `runs/V004/features/`, then `tune --arm esn`, `final` seeds 0-4 (`--oof --splits ds2s`) and 5-9 (`--oof`), and `leakcheck`, all with `--exp V004/R0` (outputs in `runs/V004/R0/`);
    - `compare_repro.py` / `compare_repro.json`: rerun vs E002 and vs the logged headline inputs;
    - `hashcheck.py` / `hashcheck.json`: fixtures, raw MIT-BIH, processed outputs, E002 manifests;
    - `probes.py` / `probes.json`: label-free probes P1-P5;
    - `headline_ds2s_regen.md`: the tables rebuilt from the logged comparison;
    - `blind_ratings.json`.
  - ds2s scoring by the critic: **none**. `runs/full_eval_log.jsonl` had 6 lines before and after, with an unchanged sha256 `5496347c...` (`runs/V004/full_eval_log_before.sha256`). `runs/confirmation_access.jsonl` does not exist.
- **Checks** (pass / fail / n/a (reason) / not run; one line of evidence each):
  1. Reproduce: **pass.**
     - Full retune from regenerated features on the current pipeline `55884b1fb66732b9`:
       - The ds1 and ds2s feature arrays are identical to `runs/features/EV1/`.
       - The 30 configurations equal the declared draw (`sample_configs`, seed 20261026).
       - The same λ is chosen in every line. The tuning scores are within 3.3e-4 of `runs/E002/tuning.jsonl`, which was computed with the float32 ESN code (M2).
       - Selected configuration 28 with λ 0.001; score 0.674487 against 0.674411.
     - `final`:
       - All 5 `pred_ds2s_seed*.csv` are byte-identical to the sha256 logged for the headline (`6996d03d...`, `8a70f071...`, `0cacdc4c...`, `cc2cfa43...`, `8511ccea...`).
       - All 10 `oof_ds1_seed*.csv` are byte-identical to E002's, so the seed-noise diagnostic's inputs are reproduced too.
       - All 10 model arrays are identical.
     - Independent numpy re-implementation (P1): rebuilding the ESN and readout from the saved arrays reproduces all 5 scored files to 5.0e-7 (the 6-decimal rounding), with 0 argmax disagreements.
     - Because the inputs are byte-identical, the logged headline score 0.7065 applies without a new ds2s access. Scorer determinism is covered by the fixtures (38 passed here) and V001-V003.
     - The packet's clean-environment run (fresh venv, fresh MIT-BIH download, pipeline `75e043aa`) reports the same byte-identity.
  2. Comparison: **n/a** (R0, no prior incumbent).
  3. Leakage: **pass.**
     - `grep -rn "labels_ds2\|confirm/" src/qhc/pipe` finds nothing in the sources. The only processed files the pipeline reads are `labels_ds1.csv`, `ds1_folds.json` and `lowdata_subsets.json`.
     - Folds: 22 DS1 records, disjoint, none in ds2s.
     - `cv_oof` fits standardisation and readout on the training folds only.
     - The final readout's `mu`/`sd` equal the DS1-unit statistics exactly (P5).
     - Per-record end-to-end predictions (raw signal to `pipeline_fn`) on ds2s records 232, 213 and 222 equal the scored batch file to 5.6e-7 (P3), so no statistic is shared across test records.
     - The beat key is used only for QRC shot streams; the ESN ignores it.
  4. Lookahead: **pass.**
     - Rerun `leakcheck`: 731 DS1 beats, 0 violations.
     - Additional label-free check on ds2s records 232 and 213 (first 150 s, 419 beats): 0 violations (P4).
     - Code review: the window ends at t + 0.45 s, the template and RR means are causal, post-RR is allowed by the one-beat boundary, and the ESN state is reset per beat.
  5. Metric and selection: **pass.**
     - The reported 0.7065 and every R0 number in the packet equal `runs/E003/compare_ds2s_headline.json`, written by the approved command: scorer `9a1922c8898b90db`, EV1, B = 8,000, labels sha256 prefix `bc99cc7493340d0a`, log entry 21:26:59.
     - The choice among the 30 complete configurations used the declared DS1 out-of-fold proxy. It is unchanged under the float64 code.
  6. Validity (incl. data card complete, raw hash matches, licence allowed): **pass.**
     - The 5 files validate against the label-free prediction set (47,523 rows each). `check_runs` passes (seeds 0-4, one `config_id`), and `pred` = argmax of the rounded probabilities.
     - Raw MIT-BIH: 144/144 files match `SHA256SUMS.txt`, and the sums file is `b61158a9...` as in the data card.
     - Processed data: 11 outputs match `manifest.json`; 3 label files were skipped unopened. `lowdata_subsets.json` = `6348bd6c...`.
     - Licence ODC-By 1.0. Compute < 0.1 GPU-h.
     - SVDB hashes not checked (constraint). Minor provenance item M4.
  7. Robustness: **n/a** (validity-only; no gain is claimed for R0). Fact: per-seed ds2s macro-F1 ranges from 0.7027 to 0.7162.
  8. Selection exposure (variants in line / full evaluations on EV#; confirmation access logged?): **pass.**
     - 30 configurations x 4 λ, selected on DS1 only. `selected_config.json` was written at 19:22, before the first non-reference ds2s scoring (headline 21:26:59).
     - Full evaluations on EV1: 1 (the headline). The 5 pre-approval reference re-scorings are diagnostics. The critic added none.
     - Confirmation: no access (no `runs/confirmation_access.jsonl`). The policy applies to the final frozen pair, so it is n/a for R0.
  9. Blind rubric rating (from packet.md alone, written before opening packet-selfrating.md): **done.** One build exists (the R0 slice), and no rubric change is claimed for R0. Gap = critic minus generator.

     | Criterion | Critic | Generator | Gap |
     |---|---|---|---|
     | Performance vs comparable classical baseline | 1 | 1 | 0 |
     | Ingenuity | 1 | 2 | -1 |
     | Depth | 1 | 1 | 0 |
     | Soundness | 2 | 2 | 0 |
     | Gate: deliverables complete | 0 | 0 | 0 |
     | Gate: reproducible | 2 | 1 | +1 |

     - Ingenuity: the generator credits the limitation and literature gap written in PROBLEM_BRIEF.md. The deliverable (README) states neither, so I rate 1.
     - Reproducible: `scripts/reproduce.py` (21:46) postdates the self-rating (21:43, "no single command yet"). I rate 2, not 3: the one-command path was not run end to end, README does not name it, the clean copy is an older pipeline revision with 37/38 fixtures, and I did not run the clean-environment build myself.
     - Both gates are below 3, as both raters agree.
  10. Claims check: **pass** (no number without a source). Items:
      - README "Result so far": 0.727, 0.707, +0.021 [-0.016, +0.062], V +0.069 [+0.021, +0.154] and S -0.023 [-0.146, +0.098] all match `runs/E003/compare_ds2s_headline.json`. "30 configurations each": both `tuning.jsonl` files have 30 lines on the same λ grid.
      - README mean-field and separable sentence: cites A012 but not the experiment IDs (E004, E005), and gives no numbers.
      - README "Reproduce": the demo command writes `runs/demo/qrc_100.png`, but the packaged demo is `runs/demo/qrc_E003_rec232.png`, and no listed command regenerates it. The one-command `scripts/reproduce.py` is not mentioned (M3).
      - Packet, "Current: `ad80a50e`": stale (M1).
      - E002 card / self-rating: "no single command yet" is superseded by `scripts/reproduce.py`. The DS1 tuning best 0.6744 comes from the float32 code; the current code gives 0.67449 (M2).
      - EVAL.md approval sha256 `f758910b...` cannot be recomputed, because bookkeeping lines were appended after the approval. The evaluation code and fixture hashes do recompute.
- **Implementation and evaluation valid:** yes (E002 as produced and as regenerated; no leakage, no lookahead, valid outputs, score from the approved command).
- **Improvement claim supported:** n/a (validity-only R0 report).
- **Verdict:** **PASS** (validity-only).
- **Scope and limitations of verdict:**
  - Covers the exact E002 artifacts: `pred_ds2s_seed0-4.csv` with the hashes logged for the headline, `model_seed0-9.npz`, configuration 28 with λ 0.001.
  - Regenerated on pipeline `55884b1fb66732b9` in the project's venv from the project's raw data. The clean-environment and fresh-download evidence is the coordinator's run (`75e043aa`), read, not rerun.
  - ds2s was not rescored. The score rests on byte-identity with the logged inputs and on the approved scorer.
  - The tuning-time code is a reconstruction. Only its hash was checked, not its identity with what ran.
  - SVDB not examined.
  - Rubric ratings are internal assessments. Agreement between raters is a consistency check, not validation against the judges.
  - The PASS says nothing about whether the ESN baseline is optimally tuned (A010: λ at the grid edge, under study in E010). That bears on the fairness of later comparisons, not on R0's validity.
- **If FAIL / NEEDS-MORE:** n/a.
- **Evaluation defect found:** no new defect. D1-D6 are not touched by E002's claim.
- **Findings:**
  - **M1 (minor, provenance):** the packet's "current" pipeline revision is stale.
    - Where: `runs/E002/packet.md`, "Candidate revision and artifacts".
    - At 21:52 the code hashes to `55884b1fb66732b9`: `tables.py` was added at 21:45, and `run.py` changed again at 21:49 (a `--lambdas` tune option and a `lambdas` field in tuning lines).
    - Reverse-applying the packet's diff does not give `75e043aa`.
    - No effect on validity: the retune on `55884b1f` reproduces E002 byte for byte. Record the revision the deliverable ships with.
  - **M2 (minor, provenance):** the scores in `runs/E002/tuning.jsonl` come from the float32 ESN code (`cf7bd4bd`), which exists now only as a reconstruction. The current code gives scores up to 3.3e-4 different, with the same selection. 7 distinct wrong `pipe_revision` values are disclosed on the card. Suggest the write-up cite the reproducible tuning scores or state the difference.
  - **M3 (should-fix before delivery; reproducible gate):** `README.md` "Reproduce" omits `scripts/reproduce.py`, and its demo command does not rebuild the packaged demo `runs/demo/qrc_E003_rec232.png`. `reproduce.py --check` was not exercised end to end here.
  - **M4 (minor, data provenance):** `scripts/download_data.py` (`get_db`) checks the files against a `SHA256SUMS.txt` fetched from the same mirror at run time. It never compares that sums file with the pinned hash in the data card (`b61158a9...` for MIT-BIH), so a mirror-side change would pass silently.
  - **M5 (scope note):** the clean copy passed 37/38 fixtures because SVDB was not built. The full README sequence builds SVDB, so 38 is expected but was not observed in a clean environment.

## V005
- **Report type:** final-submission verification. It covers the validity of E018 (the SVDB confirmation) and of the Phase 4 results (E012-E017, E019), the README claim set, and a blind scorecard rating including both gates.
- **Experiment / candidate revision / comparison baseline / component parents / EV#:**
  - E018: E003 (QRC) against E002 (ESN, R0). Frozen artifacts `runs/E00{2,3}/model_seed{0..4}.npz`, predicted through `p4 predict 08dc4140d5d45b6b`.
  - Phase 4 secondaries: E012, E014-n6 and E015-rigetti against E003; E003 and E002 against E016.
  - Revisions: evaluation `8501643023cd2eb6` (EV2), pipeline `55884b1fb66732b9`, Phase 4 ablate `f7fe9f52db014c44`, noise `8b1226919f8ca395`, boost `c2c2fc47c011e891`, kernels `647cb96976578b0d`, braket_hw `4a5dbce596f0a847`. All were recomputed on disk at about 20:25 and equal the packet.
  - No candidate for promotion; the incumbent stays E002 (R0).
  - Critic, fresh context, 2026-10-28 20:05-20:45 UAE.
- **Claim under review** (`runs/V005/packet.md`):
  1. E018 is a valid, pre-registered, access-logged confirmation, with the outcome *not confirmed*.
  2. The five Phase 4 ds2s secondaries and the DS1 and label-free results are valid and reported as descriptive.
  3. Every number and claim in `README.md` (sha256 prefix `f83bad2ffa7d7209`, unchanged during the check) and `docs/EVIDENCE.md` is traceable, and none is stronger than its evidence.
  4. Blind scorecard ratings, including both gates.
- **Packet contents and raw evidence links:**
  - Read:
    - instructions: CLAUDE.md, the 05 guide, the packet;
    - specifications: EVAL.md (EV2: scorecard, comparison procedure, confirmation policy, access log), the EXPERIMENTS.md index, declarations, E002, Phase 4 declarations and E012-E019, ANOMALIES.md A019, `hackathon_details.md`;
    - deliverables: README.md, docs/EVIDENCE.md, `.gitignore`;
    - code: the relevant parts of `src/qhc/p4/{predict,ablate,noise,boost}.py` and `scripts/{reproduce,download_data}.py`;
    - logged outputs: the 7 compare JSONs, `runs/full_eval_log.jsonl`, `runs/confirmation_access.jsonl`, `runs/confirmation_reports/`, `runs/E019/{approval.json,cost_ledger.jsonl,analysis.json}`.
  - Not read, opened, hashed or listed:
    - IDEAS.md, STATE.md;
    - `runs/data/processed/EV1/confirm/`;
    - every ds2, ds2s and svdb label file. The names, but not the contents, of three tracked r3-snapshot label files appeared in `git ls-files` (F4).
  - `packet-selfrating.md` was opened only after `runs/V005/blind_ratings.json` was complete (20:36).
  - The critic ran no `compare` or `score` on any split and made no Braket call. `runs/full_eval_log.jsonl` had 18 lines and `runs/confirmation_access.jsonl` 1 line, before and after.
  - Critic outputs, in `runs/V005/`:
    - `E018/`: `regen.sh`, `regen.log`, `compare_hashes.py`, `hash_report.json`;
    - `E014/`, `E015/`: `regen_e01x.py`, `regen.log`, `regen_report.json`;
    - `E016/`: `final_stdout.txt`;
    - `check_compares.py` and `compare_summary.json`; `per_record.py`;
    - `clean/`: `clean_repro.sh`, `clean_repro.log`, `compare_manifest.py`;
    - `blind_ratings.json`.
    - The regenerated CSV, model and feature copies (about 230 MB) were deleted after hashing.
- **Checks:**
  1. Reproduce: **pass.**
     - **E018** (predict-only path rerun into `runs/V005/E018/`, 20:08-20:11):
       - SVDB features rebuilt; arrays and file sha256 equal `runs/E018/features/build_svdb.json`.
       - ds2s self-check: **10 of 10** files identical to the hashes in both logged headline entries.
       - SVDB: **10 of 10** regenerated files identical to the scored files on disk, their manifests, the 19:29:19 `full_eval_log` entry and `confirmation_access.jsonl`.
       - Manifests differ only in the scratch `features_file` path. Every `model_artifact_sha256` equals the artifact on disk and the access log's `artifacts_by_seed`.
     - **E016:** full retrain of the final step (`qhc.p4.boost --out runs/V005/E016 final --splits ds2s` on the logged `tuning.jsonl`, 135 s). 5 of 5 ds2s files and 5 of 5 DS1 OOF files are byte-identical to the scored ones, their manifests and the log.
     - **E014-n6:** readouts retrained on DS1 through the `e014-final` code path redirected to scratch (58 s). 5 of 5 ds2s files are byte-identical. Every saved array (λ, mu, sd, readout weights and biases, couplings) is identical.
     - **E015-rigetti:** predictions from the saved noisy models (`noise.load_model`, 6.5 min). 5 of 5 ds2s files are byte-identical; the artifact hashes equal the manifests.
     - Limit: the DS1 selection runs were not rerun (the E016 capped search, the E014 variant and λ runs, the E015 DS1 OOF). Their logged outputs were reused as the inputs to selection.
  2. Comparison: **pass.**
     - In all 7 logged outputs (`compare_summary.json`), every delta, 95% CI and delta without record 232 equals the packet and the README.
     - Recomputing EVAL.md's decision rule from the stored numbers gives the logged outcome in every case: *no detectable change*, "CI includes 0".
     - The secondaries are marked `inference: descriptive`. E018's `confirmed: false` follows from the pass criterion: the delta is −0.0085 and the CI lower bound −0.0476.
     - Every output has scorer `8501643023cd2eb6`, B = 8,000 and boot seed 20261026, with files in seed order 0-4 in both arms (D3).
  3. Leakage: **pass.**
     - Phase 4 code reads labels only through `run.ds1_data()`. A grep of `src/qhc/p4/*.py` and `scripts/*.py` finds no `labels_ds2*`, `load_labels` or `confirm/`.
     - E016 fits each fold on its training units only, and the final models on DS1 units only.
     - E019's beat draw reads only the `pred` column of `runs/E003/pred_ds2s_seed0.csv`, so it is label-free.
     - E016's selection recomputes from `tuning.jsonl`: configuration 6 (0.6718), the best of 30.
  4. Lookahead: **pass.**
     - Lookahead reports for E012, E014/n6, E015/rigetti and E016 each show 731 beats and 0 violations.
     - E015's noise streams are per beat: Philox keyed by (beat key, shot seed + tag) (`noise.py:103-107, 203-211`). Batch invariance and the rates-0 bit-identity checks are in `runs/E015/mechanism_checks.json`.
     - E014's generalised simulator is bit-identical to `reservoirs.QRC` at n = 10.
  5. Metric and selection: **pass.**
     - All 6 Phase 4 and E018 outputs come from the approved `compare`.
     - E014: the declared DS1 rule, recomputed from the three `variant_results.json` files, selects n6 (0.6803 against 0.6673 and 0.6635).
     - E015 (Rigetti) and both E016 comparisons were fixed by declaration, not by results.
     - Nothing was selected on ds2s. The secondaries were logged at 19:29:53-19:31:33, before the SVDB result (20:01:41).
  6. Validity: **pass.**
     - The guard sequence holds:
       - the access line and the `full_eval_log` line are both stamped 19:29:19;
       - `access_1.json` sha256 recomputes to `39c6b7e7…2b75b2434`, equal to `index.jsonl` (completed 20:01:41);
       - the archive equals `confirm_svdb.json` on every key;
       - this was access 1 of a cap of 2, `repair_reason` is null, and the EVAL.md row is present.
     - Test-split count recomputed: 13 of 15 (the 18 log lines minus 5 pre-approval references).
     - Licences: ODC-By 1.0.
     - E019: the human's approval is recorded (1 task, cap USD 18). Ledger estimate USD 17.708. The first attempt was refused before any task was created (USD 0).
     - The raw SVDB and MIT-BIH hashes were verified by the fresh download in check 9.
  7. Robustness: **pass, except one wording item (F2).**
     - Recomputed from the logged per-record confusions (no label access):
       - V false positives: QRC 710 against ESN 1,324 per seed, with the largest drops in records 117, 222, 105, 111, 232 and 212;
       - V true positives: 3,036 against 3,051;
       - S true positives in record 232: 493 against 781, of 1,381.
       - These match A015 and README Section 5.
     - Leave-one-record-out ranges and deltas without record 232 all match: headline +0.0111 to +0.0460; SVDB −0.0157 to −0.0010; E014 without 232 +0.0004; E015 −0.0179; E016 −0.0869 and −0.1329.
     - Not supported: E016 "lead everywhere else" (F2).
  8. Selection exposure: **pass.** README Sections 4 and 6 and limitation 13 label every Phase 4 ds2s comparison as secondary, descriptive and post-hoc. Variant counts are published. SVDB is presented as the pre-registered confirmation and reported as not confirmed. One timing wording item remains (F6).
  9. Blind rubric rating: **done.** Gap = critic − generator; generator ratings are from `packet-selfrating.md`.

     | Criterion | Critic | Generator | Gap |
     |---|---|---|---|
     | Performance vs comparable classical baseline | 2 | 2 | 0 |
     | Ingenuity | 3 | 3 | 0 |
     | Depth | 3 | 3 | 0 |
     | Soundness | 2 | "3 if the critic passes, else 2" → 2 | 0 |
     | Gate: deliverables complete | 3 | 3 | 0 |
     | Gate: reproducible | 3 | "2 unless the critic checks clean env + fresh download" → 3 (checked) | 0 |

     - Performance:
       - Anchor 2 is met: the V_f1 slice's 98.75% lower bound is +0.0207 and all four slice members are reported.
       - Anchor 3 is not: the ds2s primary is not favorable and SVDB is not confirmed.
     - Soundness: anchor 3 needs a critic PASS on the claims, and that is withheld (F1-F3). It becomes 3 after the repair and a PASS.
     - **Reproducible, anchor 3, checked by the critic.** Fresh venv from the system Python 3.12.10 and `requirements-lock.txt`, then `pip install -e .`, in a copy outside the project (`%TEMP%\v005_clean`) with only the README's audit-mode files. Then `scripts/reproduce.py --check` was run as one command, without `--skip-data`. Timeline (UAE):
       - 20:07:46-20:12:25 (4.7 min): venv, lock and editable install. Torch 2.11.0+cu128, CUDA available.
       - 20:12:25-20:21:00 (about 8.5 min): fresh download.
         - MIT-BIH: 144 files verified.
         - SVDB: 234 files verified.
         - Both sums files matched the pinned hashes.
       - Units rebuilt with the recorded counts. The 16 output hash strings in the manifest equal the project's (manifest only).
       - 43 fixtures passed.
       - Selections were identical to the project's:
         - ESN: configuration 28, λ 0.001, score 0.67449;
         - QRC: configuration 15, λ 0.1, score 0.66689.
       - Both lookahead checks passed (731 beats, 0 violations).
       - **10 of 10 headline prediction files** were identical to the log, and `runs/tables/headline_ds2s.md` was byte-identical (sha256 `cdc15df3…`).
       - Exit 0 at 20:35:06: **27.3 min** wall-clock, no manual step beyond the README's copy.
       - The build created `confirm/`. It was deleted unopened, and the scratch copy was then removed.
     - Rubric ratings are internal assessments. Agreement between the two raters is a consistency check, not validation against the judges.
  10. Claims check: **fail** (F1-F3).
      - Every other README number checked against its logged source matches:
        - ds2s: headline, slices, per-class F1, AUPRC, review burden and S/V sensitivity;
        - controls and Phase 4: E004-E006 and E012-E019;
        - SVDB table: V sensitivity/PPV 0.600/0.544 against 0.763/0.463; 801 against 870 flags per hour; 133 against 111 missed ectopic beats per hour; 39.0 h.
      - References checked with paperfetch:
        - Gupta et al. 2025 (doi:10.1038/s41746-025-01597-z): the authors match and the quote is verbatim in the abstract.
        - Jaeger 2001: title, sole author and year confirmed by Semantic Scholar (`s2:8430c0b9afa478ae660398704b11dca1221ccf22`). "GMD Report 148" is not in that record.
        - de Chazal 2004: SVEB +P 38.5% is verbatim in the abstract.
        - Pandey 2026: the abstract supports the README's paraphrase.
      - For de Chazal, paperfetch also returned "Acquire manually using the SCH Protocol: Automated Access Blocked". Its `paper_url` points to an unofficial shadow-library mirror and is not reproduced here. No acquisition is needed, because the claim is verified from the abstract. A legitimate green open-access copy is listed at http://hdl.handle.net/2262/17623.
- **Implementation and evaluation valid:** **yes.**
  - E018 is reproduced 20 of 20 files.
  - E014-n6, E015-rigetti and E016 are reproduced byte-identically, 15 of 15 ds2s files.
  - There is no leakage or lookahead, selection followed the declarations, the scores come from the approved command, and the confirmation guard and archive are intact.
- **Improvement claim supported:** n/a (no improvement is claimed). **The README claim set is not supported as written:** one false statement (F1) and two overstatements (F2, F3).
- **Verdict:** **FAIL on the claim set** (question 2). Validity (question 1) **PASS**: checks 1-8 passed, check 9 is done, check 10 failed.
  - The repair is text-only. No rerun and no test-split or SVDB access is needed.
  - Re-verification is a diff check of the edited lines (plus F4/F5 in the commit).
- **Scope and limitations of verdict:**
  - Not rerun: the DS1 selection runs (E014 variants, E016 search, E015 DS1 OOF) and E013, E017, E019. Their logged inputs and outputs were read, not regenerated.
  - Not rescored: ds2s and SVDB. The scores rest on byte-identity with the logged inputs and on the approved scorer.
  - SVDB resampling branch: has no independent reference. The regeneration shows determinism, not correctness (disclosed on E018).
  - E019 numbers: checked against `analysis.json` only.
- **If FAIL / NEEDS-MORE:** apply F1-F3 (required for PASS) and F4-F5 (packaging), then send the README, EVIDENCE.md and EXPERIMENTS.md diff for a check.
- **Evaluation defect found:** none.
- **Findings, ranked by severity:**
  - **F1 (should-fix, required; false statement).**
    - Where: `README.md:10`, "The evaluation was pre-registered and human-approved before any model existed", and `README.md:87`, "fixed … before any model existed".
    - E002 and E003 were tuned and their artifacts and ds2s predictions written on 2026-10-26 at 19:11-19:21. Evidence: the `tuning.jsonl`, `model_seed0.npz` and `pred_ds2s_seed0.csv` file times, and EXPERIMENTS.md:30, "EV1 draft r5 … not yet approved".
    - The human approved EV1 at 21:26 and EV2 (guard fixes) at 22:14.
    - What is true: the metric, split, units, decision rule and slice family were fixed in the draft before tuning, and r5 was approved unchanged before any test-split scoring (headline 21:26:59).
    - Fix: "pre-registered before tuning (EVAL.md draft r5) and approved by the human, unchanged, before any test-split scoring; EV2's guard fixes (22:14) changed no metric, split or threshold".
  - **F2 (should-fix, required; overstatement).**
    - Where: `README.md:193`, "…and lead everywhere else (A019)", and EXPERIMENTS.md:428, "on every other record the boosted trees lead".
    - Per record (seed-averaged confusions, descriptive), E016 does not lead E003 on records 100, 123, 210 and 219, besides record 232. The supported fact is the pooled one: without 232 the delta is −0.0869 against E003 and −0.1329 against E002.
    - Fix: "and lead on the remaining 20 records pooled".
  - **F3 (minor, required; overstatement).**
    - Where: `README.md:19`, "Six qubits or a Z-only readout do as well as or better than ten qubits".
    - "Better" rests on DS1 proxy means (+0.013 and +0.011, with no interval; the E013 card puts DS1 uncertainty at about ±0.05). On ds2s, n6 shows no detectable change: +0.0078 [−0.0055, +0.0188].
    - Fix: "scored at least as high on DS1 (proxy, no interval); no detectable change on ds2s".
  - **F4 (should-fix, packaging; the brief's "repository excludes label files").**
    - Commit `fc69043` tracks `runs/EV1_r3_snapshot/processed_r3/labels_ds1.csv`, `labels_ds2.csv` and `labels_ds2s.csv`.
    - This contradicts `.gitignore`'s "Not redistributed" and README:310. The licence allows the files, and README:317 discloses the snapshot, so this is not an evaluation leak.
    - Fix: `git rm --cached runs/EV1_r3_snapshot/processed_r3/labels_*.csv` and add `**/labels_*.csv` to `.gitignore`, or have the human decide to keep them and say so in README Section 10.
  - **F5 (should-fix, packaging).**
    - Commit `fc69043` (20:09:24) captured the critic's in-progress scratch in `runs/V005/`: partial logs, a mid-run `clean/clean_repro.log`, and 20 selfcheck CSVs and manifests (about 22 MB) duplicating `runs/E018/selfcheck_ds2s/`.
    - Fix:
      - commit the final `runs/V005/` logs, JSON and scripts;
      - remove `runs/V005/E018/selfcheck_ds2s/*.csv` from the index, or keep them deliberately;
      - commit the modified `runs/V005/packet.md`.
  - **F6 (minor, wording).**
    - Where: `README.md:148` and EXPERIMENTS.md:320, "declared … ~18:50, before any run".
    - The E015 calibration fetch (18:45:52), E019 device search (18:45) and E018 SVDB feature build (18:48) came earlier. None is a model result or a selection input, so there is no effect.
    - Fix: "before any model run".
  - **F7 (minor, privacy).**
    - AWS account ID `<aws-account-id>` appears in tracked `runs/E019/cost_ledger.jsonl`, `fetch_stdout.txt` and `results/*.json`, while the E019 card redacts it.
    - It is not a credential: `git grep` finds no access keys, secrets or private keys. The human decides whether to redact.
  - **F8 (info).**
    - README:60 and EVIDENCE.md:33 say the clean-environment evidence was not rerun by a critic. V005 has now rerun it, so update both and fill `<!-- SLOT:VERIFICATION -->`.
    - EVIDENCE.md:88, Jaeger: cite the V005 check.
    - `runs/E019/analysis.json` `n_tasks` = 40 counts circuits; there was 1 program-set task, as the README says.
- **Re-check after the repair cycle** (critic, 2026-10-28 20:38-20:45 UAE; appended, the report above is unchanged):
  - **Inputs.**
    - `runs/V005/repair_diff_README.txt`. It equals `diff` of `git show HEAD:README.md` (sha256 prefix `f83bad2ffa7d7209`) against the working README (`c41d23713755ca46`), so it is the complete README change.
    - Staged diffs of EXPERIMENTS.md, docs/EVIDENCE.md, ANOMALIES.md and `.gitignore`.
    - VERIFICATIONS.md: additions only, so the V005 text above is unaltered.
    - Script: `runs/V005/recheck_numbers.py`, which reads logged outputs only. No `compare`/`score`, no `confirm/`, no label file.
  - **F1: fixed.**
    - The new text (Summary "Design", Section 4) matches the records: draft r1 with metric, split and decision rule at 17:29; the first models (E001 probe) at 18:53; r5 at ~19:00-19:10; tuning and predictions at 19:11-19:21; approval unchanged at 21:26; first counted test-split scoring at 21:26:59.
    - The 18:37 lines are const_n and rr_rule, which are fixed reference rules, as the new Section 4 text says.
  - **F2: fixed.** README Section 6.4 and the E016 card now say "pooled over the other 20 records … though not in every record" (the card names 100, 123, 210 and 219).
  - **F3: fixed.**
  - **F4: fixed in the index.** The three label CSVs are staged for deletion and ignored by `**/labels_*.csv`. They are still in commit `fc69043` (`git log --all` finds them), so the amend must land before the push. Check with `git log --all -- runs/EV1_r3_snapshot/processed_r3/labels_ds2s.csv`, which should return nothing.
  - **F5: fixed.** The selfcheck CSVs are ignored and none is tracked; the critic logs and reports are staged.
  - **F6: fixed in the README.** EXPERIMENTS.md:320 still says "before any E012+ run" (optional).
  - **F7:** the human decides.
  - **F8: done.** See R3 and R5 below for its wording.
  - **Rehearsal additions checked against logged outputs, all correct:**
    - Paper-compatible VEB and SVEB Se and +P, both arms (headline JSON `paper_compatible`).
    - SVDB V AUPRC 0.605 vs 0.677, −0.073 [−0.185, +0.041].
    - SVDB V-sensitivity gap 16.3 points (0.7635 − 0.6001).
    - The SVDB V-F1 interval includes +0.069.
    - E019 draw of 16 beats per class. Chance agreement is 1/3 exactly, because the shot-side classes are uniform.
    - Cost: 100,000 × 4,096 = 409.6 M shots, × USD 0.000425 = USD 174,080 (`runs/E019/pricing.json`, fetched 2026-10-28 14:45Z).
    - J range U[0.1, 1.5], and E005 DS1 0.6793 vs 0.6671 (A012).
    - Seed-0 vs 5-seed DS1 labels.
    - The 9 records with ≥ 10 V units; the QRC is higher in 5 of 9; record 105 −0.167 (41 V units).
    - The ANOMALIES E019 slot count: 40 × 5 − 192 = 8 unused.
    - The V005 row in EVIDENCE.md.
  - **Remaining items:**
    - **R1 (number disagrees with the logged outputs; required).**
      - Where: README.md:132 "four records are within ±0.001", from ANOMALIES.md:167 (A015).
      - From the logged per-record confusions (seed-mean or pooled), only record 214 is within ±0.001 (−0.0001). Records 200 (−0.0014) and 221 (−0.0013) are within ±0.0015.
      - Fix in both files: "three records (200, 214, 221) are within ±0.0015".
    - **R2 (overstatement; required).**
      - Where: README.md:152 "the J = 0 variant scored highest on DS1 (0.679 vs 0.667)".
      - E014-n6 scored 0.6803 on DS1, which is higher.
      - Fix: "scored higher on DS1 than the selected J (0.679 vs 0.667; E005, proxy)".
    - **R3 (description of this report; required).**
      - Where: README.md:110 "FAIL on three wording items".
      - V005 found one inaccurate statement and two overstatements.
      - Fix: "FAIL on one inaccurate statement (pre-registration timing) and two overstatements, corrected in this version". When this re-check is resolved, also state its outcome in the slot and update the Soundness rating there.
    - **R4 (source description; required).**
      - Where: README.md:342 Jaeger, "checked against the source".
      - The check was against the Semantic Scholar record, not the report.
      - Fix: "checked against the Semantic Scholar record".
    - **R5 (optional).** README.md:62 and EVIDENCE.md:34 say "no manual step". Precise: "no manual step beyond the README's audit-mode file copy".
    - **R6 (optional).** The ds2s V-sensitivity gap is 0.45 points unrounded (0.9533 − 0.9488). "0.4" matches the rounded table values; fine as is.
  - **Re-check verdict on the claim set: FAIL (narrow).**
    - One number disagrees with the logged outputs (R1), and three lines need small corrections (R2-R4).
    - Everything else in the repair is verified.
    - After R1-R4, a grep of those four lines (plus the F4 history check) is enough for PASS. No rerun is needed.
    - Validity (question 1) stays PASS.
- **Final check** (critic, 2026-10-28 20:56 UAE; README sha256 prefix `4e3f4606a6b15a97`, commit `87fd848`, clean working tree):
  - **R1: fixed.**
    - README.md:132 now reads "three records (200, 214, 221) are within ±0.0015 (A015)".
    - A015 (ANOMALIES.md:167) carries a dated correction note: "only 214 is within ±0.001; three records (200, 214, 221) are within ±0.0015". This matches the logged per-record confusions.
  - **R2: fixed.** README.md:152 now reads "scored higher on DS1 than the selected J (0.679 vs 0.667; E005, proxy)".
  - **R3: fixed.** The verification slot describes the first check (one inaccurate statement, two overstatements) and the re-check (one wrong number, three wording items). It points to V005 for the final status and gives Soundness as "3 once the corrected claim set passes".
  - **R4: fixed.** README.md:342 now reads "checked against the Semantic Scholar record".
  - **R5: fixed** (README.md:62 and EVIDENCE.md:34).
  - **F6: fixed** (EXPERIMENTS.md:320).
  - **F4: fixed.**
    - `git log --all` on the three r3 label CSVs returns nothing.
    - `git ls-files` lists no `labels_*` file.
    - The only commit is `87fd848`.
  - **F7: redacted, by the human's choice.**
    - `git log --all -p` contains 0 occurrences of the account ID, and `git grep` finds none.
    - The tracked files carry `<aws-account-id>`.
    - `runs/E019_unredacted/` is ignored and untracked.
  - **Claim set (question 2): PASS.**
    - Every item from F1-F8 and R1-R5 is resolved.
    - No number checked disagrees with the logged outputs.
    - No claim is stronger than its evidence: no quantum advantage is claimed, and the post-hoc secondaries are labelled descriptive.
  - **Validity (question 1):** PASS, as recorded above.
  - **Overall V005 verdict: PASS.**
  - **Scorecard:** Soundness anchor 3 is now met (critic PASS, access-logged confirmation, published variant count, every claim traceable), so the critic's rating is 3. The other ratings are unchanged: Performance 2, Ingenuity 3, Depth 3, both gates 3. These are internal ratings, not the judges'.
  - **Scope:** unchanged from the report above. Rubric agreement between the two raters is a consistency check, not validation against the judges.
