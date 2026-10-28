# Anomalies

Observations that don't fit expectations. Log liberally; ideation reads this first. Keep the observation separate from any explanation, and mark exploratory slices.

## Index
| ID | Observation (one line) | Slice | n | Metric on slice vs overall | Share of objective | Predefined / exploratory | Source | Status |
|---|---|---|---|---|---|---|---|---|
| A001 | One DS2 record (232) holds 75% of the S-class beats in the MIT-BIH inter-patient test set | MIT-BIH DS2, AAMI class S, by record | 1,382 of 1,837 S beats; 1 of 22 records | 75.2% of DS2 S beats from one record; the next two records hold 11.4% and 3.0% | Any S-class metric on DS2 (and macro-F1 over N/S/V, one third of which is S-F1) | exploratory (Phase 1 data inspection) | Phase 1, runs/phase1/inspect_samples.out | open |
| A002 | UCI SPECT has 39 fully duplicated rows and a 172:15 class imbalance in the official test file against 40:40 in train | UCI SPECT, all 267 rows | 267 | 39 duplicate rows (14.6%); 219 distinct feature patterns; overall 212 abnormal and 55 normal | Any SPECT metric | exploratory | Phase 1, runs/phase1/inspect_samples.out | open |
| A003 | TCGA-BRCA PAM50 subtype labels in the Xena clinical matrix (`PAM50Call_RNAseq`) are computed from the same RNA-seq data used as input | TCGA-BRCA, 956 samples with a PAM50 call | 956 | n/a (label provenance, not a metric) | Any PAM50-target experiment | exploratory | Phase 1, runs/phase1/inspect_samples.out | open |
| A004 | The standard MIT-BIH inter-patient split (de Chazal DS1/DS2) puts one subject in both train and test: record 202 "was taken from the same analog tape as record 201" | Records 201 (DS1) and 202 (DS2) | 1 subject; 202 has 2,061 N, 55 S, 19 V, 1 F beats | 202 contributes 3.0% of DS2 S beats | Any claim that DS1/DS2 is fully patient-disjoint | exploratory | Phase 1, 201.hea and 202.hea comments | open |
| A005 | MIT-BIH lead order is not fixed: record 114 stores V5 as channel 0 and MLII as channel 1; 40 of 48 records are MLII+V1 | MIT-BIH, lead configuration by record | 48 records | 1 non-paced record with MLII in channel 1 | Every beat of record 114 (DS1), if leads are chosen by index | exploratory | Phase 1, record headers | explained (database documentation: "Record 114 had its signals reversed") |
| A007 | 472 ventricular-flutter wave annotations (`!`, a PhysioNet non-beat code) were released as beat positions in EV1 r1-r3 | DS1 record 207 | 472 positions; 6 scored beats with a changed pre-RR and 6 with a changed post-RR | DS1 prediction set 51,436 -> 50,964 after the fix; N/S/V units unchanged (50,542); rr_rule DS1 macro-F1 0.3924 -> 0.3920 | DS1 training inputs of every pipeline (RR features, reservoir state carried across beats) | predefined (independent review R1) | EV1_R3_REVIEW.md R1; runs/data/processed/EV1/manifest.json | explained (fixed in EV1 r4 before any model was trained) |
| A009 | Raw beat morphology hurts inter-patient DS1 macro-F1 relative to RR alone; a patient-relative window recovers most of it | DS1 OOF, 50,542 units | 5 folds | RR only 0.637; window+RR 0.546; relative+RR 0.619; ESN(rel)+RR 0.634; QRC(rel)+RR 0.600 | Every arm (shared input encoding) | exploratory (E001) | runs/probes/P01_morphology/ | open |
| A010 | The declared readout λ grid's lower edge (0.001) binds for the ESN far more often than for the QRC | DS1 tuning, 30 configurations per arm | 30 + 30 | ESN: best λ = 0.001 in 15 of 30 configurations, including the selected one; QRC: 2 of 30 | Fairness of the matched comparison (the classical arm may be under-tuned on regularisation) | exploratory (E002, E003 tuning) | runs/E002/tuning.jsonl, runs/E003/tuning.jsonl | resolved (E010/E011: same selection with an extended grid) |
| A011 | float32 GPU matrix products made per-beat outputs depend on the batch, so the lookahead check flagged 2 of 141 beats on R0 | DS1 record 207, first 150 s | 2 beats | probability differences 1.8e-7 and 2.2e-8 (check tolerance 1e-6 relative), identical with or without the future signal replaced | Lookahead check of every pipeline | predefined (lookahead check) | runs/E002/leakcheck_seed0.json (first attempt, overwritten; numbers in E002 card) | explained (numerical; fixed with float64) |
| A012 | On DS1 the tuned QRC behaves like its classical mean-field model, and removing all couplings scores higher | DS1 OOF, 5 seeds per arm | 50,542 units | QRC 0.6671; mean-field 0.6671; separable (J = 0) 0.6793; ESN 0.6620; RR only 0.6367 | The quantum-advantage question itself | exploratory (E003-E006, proxy) | runs/E00{3,4,5,6}/oof_ds1_seed*.csv | open |
| A013 | Rubric failure analysis (self-rated; latest 23:55): Depth 1 is the lowest weighted criterion; Performance, Ingenuity and Soundness are 2; the conditions of both gates appear met, and the critic check is pending | Scorecard | 6 rows | 1 of 4 weighted criteria at 1 (was 2 of 4) | Judged score | exploratory | runs/phase3/scorecard_selfrating_2026-10-26_2355.md | open |
| A014 | Judge questions without evidence yet: quantum vs classical mechanism, baseline fairness, hardware, literature context, single-patient dependence, workload | Write-up | 6 questions | n/a | Judged score | exploratory | ANOMALIES A014 | open |
| A015 | Headline failure analysis (ds2s): the QRC arm's gain over the ESN is fewer false alarms (V false positives halved); it misses more S beats, almost all in record 232 | ds2s, per class and per record, seed-averaged | 21 records, 47,129 units | V FP per seed 709 vs 1,324 (V TP 3,036 vs 3,050); S FP 1,790 vs 2,886, S TP 750 vs 1,059 (232: 493 vs 781 of 1,381) | Headline delta +0.0208; V_f1 slice +0.0688 | predefined (per class, per record, 232) | runs/E003/failure_analysis_ds2s.txt, runs/E003/compare_ds2s_headline.json | open |
| A016 | On ds2s the QRC's gain over the ESN is reproduced by its classical mean-field model; the couplings matter for V, but classical couplings suffice | ds2s, EV2 secondary comparisons, 5 seeds per arm | 21 records, 47,129 units | QRC vs mean-field +0.0039 [-0.0028, +0.0115] (V F1 0.874 both); separable vs QRC -0.0009, V F1 -0.063 [-0.132, -0.021], S F1 +0.067 | The quantum-advantage question (headline V gain) | predefined controls (EVAL.md rule 7) | runs/E004/compare_ds2s_secondary_E003_vs_E004.json, runs/E005/compare_ds2s_secondary_E005_vs_E003.json | open |
| A008 | Current MIT-BIH annotation totals differ from de Chazal 2004 Table II | DS1 and DS2, AAMI classes, all beat annotations before edge exclusions | DS1 N -2, S +2, V +1; DS2 N +1; F and Q equal | n/a (provenance) | Literature comparability of DS1/DS2 counts only | predefined (independent review R3) | EV1_R3_REVIEW.md R3; tests/test_scorer.py::test_units_match_current_dataset_counts | open (cause unverified; labels not altered) |
| A006 | SVDB headers carry no demographics and name leads only ECG1/ECG2, so subject overlap with MIT-BIH and lead identity cannot be checked | SVDB, all 78 records | 78 records, 184,286 units | n/a (provenance) | Any SVDB confirmation claim | exploratory | Phase 2, SVDB headers and PhysioNet page | open |
| A017 | Finite-shot keys for SVDB beats differ between the batch path and the per-record path: the batch path hashes native 128 Hz beat IDs, while `pipeline_fn` (demo, leakcheck) hashes resampled 360 Hz positions | SVDB, any beat run through `pipeline_fn` | all SVDB beats; MIT-BIH is unaffected (native 360 Hz) | 210 of 220 QRC features changed on one synthetic beat, max abs diff 0.098 (review probe); prediction impact not measured | none on any scored result; an SVDB demo would disagree with the scored predictions | exploratory (progress review 2026-10-28) | PROGRESS_REVIEW_2026-10-28.md; `run.keys_of`, `run.pipeline_fn` | open |
| A018 | `load_artifact` rebuilds the reservoir from configuration and seed without checking the saved `res_*` arrays or the saved shot count, and no command predicts a new split from the saved artifacts (`final` refits and overwrites `model_seed*.npz`) | E002/E003 model artifacts, 5 seeds each | 10 artifacts | n/a (provenance) | the SVDB confirmation must score the exact DS1-trained artifacts (EVAL.md confirmation policy) | exploratory (progress review 2026-10-28; agent check) | PROGRESS_REVIEW_2026-10-28.md; `run.load_artifact`, `run.cmd_final` | open |

Status: open / explained / exploited / dismissed. Explained is not exploited; record both and the evidence.

## A001
- **Date:** 2026-10-26
- **Observation:** In DS2 (the 22 test records of the de Chazal 2004 inter-patient split, `doi:10.1109/tbme.2004.827359`), record 232 holds 1,382 of the 1,837 AAMI S-class (supraventricular ectopic) beats. Records 222 (209) and 202 (55) follow. In DS1, 944 S beats are spread over 16 records.
- **Slice definition and size:** MIT-BIH records in DS2, AAMI class S per record, mapped from reference annotations (N: N L R e j; S: A a J S; V: V E; F: F; Q: / f Q). Current DS1 and DS2 class totals: DS1 N 45,866 / S 944 / V 3,788 / F 415 / Q 8; DS2 N 44,259 / S 1,837 / V 3,221 / F 388 / Q 7. They differ from de Chazal's Table II by at most 2 beats per class (A008); the earlier note that they match exactly was wrong (corrected 2026-10-26, EV1 r4).
- **Evidence:** 232 has 75.2% of DS2 S beats. The 232.hea comment reads: sick sinus syndrome, sinus bradycardia, first-degree AV block, frequent ectopic atrial runs, pauses up to 6 s.
- **Candidate explanations (hypotheses, untested):** this is how the database was built, not an error. It means DS2 S sensitivity and PPV largely measure performance on one patient. Uncertainty estimates that treat beats as independent would be far too narrow.
- **Resolution and evidence:**
  - Phase 2 (2026-10-26) built EV1 around this: record-cluster bootstrap, an excluding-232 sensitivity analysis on every DS2 comparison, and SVDB as confirmation, where the largest record holds 14.9% of S beats.
  - Magnitude, measured with the minimal references in `runs/EV1_reference/`: the `rr_rule` reference beats `const_n` on ds2s by +0.140 macro-F1 [+0.022, +0.242], but by only +0.049 [+0.016, +0.093] when 232 is excluded. Most of a prematurity rule's S-class gain on DS2 comes from this one patient.
- **Linked ideas / experiments:** none yet
- **Status:** open

## A002
- **Date:** 2026-10-26
- **Observation:** SPECT.train (80 rows) is balanced 40/40, while SPECT.test (187 rows) is 172 abnormal to 15 normal. Of 267 rows, 39 are exact duplicates of another row, label included, and only 219 distinct 22-bit feature patterns occur.
- **Slice definition and size:** all 267 rows of UCI SPECT Heart (id 95).
- **Evidence:** pandas `duplicated()` over all 23 columns gives 39 rows.
- **Candidate explanations (hypotheses, untested):** the 22 binary features come from thresholding 44 continuous image features, so distinct patients collapse onto the same bit pattern. Duplicates across a split would inflate test scores, and the official test file has too few normals for a stable estimate.
- **Resolution and evidence:** none. Relevant only if candidate C4 is chosen.
- **Linked ideas / experiments:** none
- **Status:** open

## A003
- **Date:** 2026-10-26
- **Observation:** The column name `PAM50Call_RNAseq` indicates the subtype call was produced by the PAM50 classifier from the RNA-seq data. Predicting it from the same expression matrix means approximating a known deterministic function, not a clinical ground truth.
- **Slice definition and size:** 956 of 1,247 clinical-matrix rows have a PAM50 call (LumA 434, LumB 194, Basal 142, Normal 119, Her2 67).
- **Evidence:** column name and Xena provenance. Not yet confirmed against the Xena dataset description, because that page needs JavaScript.
- **Candidate explanations (hypotheses, untested):** n/a
- **Resolution and evidence:** none. If candidate C2 is chosen, prefer an independently measured target (ER status by IHC, n = 1,178 with Positive or Negative), or frame PAM50 explicitly as "reproduce the full-panel call from a reduced panel".
- **Linked ideas / experiments:** none
- **Status:** open

## A004
- **Date:** 2026-10-26
- **Observation:** The 202.hea comment says "This record was taken from the same analog tape as record 201". Both headers give the same subject (68 M, Digoxin, Hydrochlorthiazide, Inderal, KCl). Record 201 is in DS1 (train) and 202 in DS2 (test). The PhysioNet page lists 48 records from 47 subjects, consistent with one subject appearing twice.
- **Slice definition and size:** records 201 and 202. Record 202: N 2,061, S 55, V 19, F 1 (AAMI).
- **Evidence:** header comments, quoted above.
- **Candidate explanations (hypotheses, untested):** the standard split is record-disjoint, not strictly subject-disjoint. The effect on headline numbers is probably small (one of 22 test records), but it contradicts the "fully inter-patient" claim in much of the literature.
- **Resolution and evidence:** the database documentation confirms it: "Records 201 and 202 come from the same male subject" (mitdbdir intro, read 2026-10-26). EV1 (draft) makes the primary test split `ds2s` = DS2 without 202 (21 records). The published split is kept as the secondary `ds2` for literature comparability.
- **Linked ideas / experiments:** none
- **Status:** open

## A005
- **Date:** 2026-10-26
- **Observation:** Lead configurations across the 48 records are MLII+V1 (40), MLII+V5 (2), V5+V2 (2, paced records 102 and 104), MLII+V2 (2), MLII+V4 (1), and V5+MLII (1, record 114).
- **Slice definition and size:** 48 record headers.
- **Evidence:** `wfdb.rdheader` signal names.
- **Candidate explanations (hypotheses, untested):** n/a. Selecting leads by name (MLII) instead of channel index avoids feeding V5 for record 114. Paced records 102, 104, 107 and 217 are excluded under AAMI practice anyway.
- **Resolution and evidence:** none
- **Linked ideas / experiments:** none
- **Status:** open

## A006
- **Date:** 2026-10-26
- **Observation:**
  - All 78 SVDB headers have empty comment fields (no age, sex or medications), and the leads are named only `ECG1` and `ECG2`.
  - The PhysioNet page gives no subject count and no annotator description beyond "reference beat and signal quality annotations".
  - Sampling is 128 Hz, against 360 Hz for MIT-BIH.
- **Slice definition and size:** all 78 SVDB records (184,286 EV1 units).
- **Evidence:** `wfdb.rdheader` over all records; https://physionet.org/content/svdb/1.0.0/ (read 2026-10-26).
- **Candidate explanations (hypotheses, untested):** SVDB was assembled to supplement MIT-BIH's supraventricular examples (Greenwald 1990), so some subjects could also appear in MIT-BIH. This cannot be checked from the files.
- **Resolution and evidence:**
  - None possible from the data.
  - Consequences:
    - SVDB confirmation results carry the caveat "possible subject overlap with training data; leads unknown".
    - Both arms face the same domain shift, so the paired delta is the quantity confirmed, not absolute scores.
- **Linked ideas / experiments:** none
- **Status:** open

## A007
- **Observation:** EV1 r1-r3 treated `!` (ventricular flutter wave) as a beat code. PhysioNet lists `!` as a non-beat annotation. All 472 occurrences in the evaluation splits are in DS1 record 207, where they were released as beat positions with class "other".
- **Slice definition and size:** DS1 record 207, annotations with symbol `!`: 472. Removing them changes the pre-RR interval of 6 scored beats and the post-RR interval of 6 scored beats. Pipelines with state carried across beats (rolling RR, reservoirs) would be affected further.
- **Magnitude:** DS1 prediction set 51,436 -> 50,964; N/S/V units unchanged at 50,542; folds unchanged; rr_rule DS1 macro-F1 0.3924 -> 0.3920. ds2s, ds2 and svdb outputs are byte-identical.
- **Resolution and evidence:** fixed in EV1 r4 (`evalspec.BEAT_SYMBOLS`, `units.select_beats`, fixture `test_non_beat_annotations_are_not_beat_positions`). No model had been trained. Flutter information, if ever needed, would be a separately documented annotation channel.

## A008
- **Observation:** de Chazal 2004 Table II, summed into AAMI classes, gives DS1 N 45,868 / S 942 / V 3,787 / F 415 / Q 8 and DS2 N 44,258 / S 1,837 / V 3,221 / F 388 / Q 7. The checksum-verified current annotations give DS1 N 45,866 / S 944 / V 3,788 and DS2 N 44,259, with the other totals equal. The comparison is before EV1's edge and first/last exclusions, so those do not explain it.
- **Slice definition and size:** all beat annotations of the DS1 and DS2 records, AAMI mapping as in EVAL.md.
- **Magnitude:** at most 2 beats per class.
- **Resolution and evidence:** cause unverified (annotation revisions since 2004 are a possible explanation). Labels are not altered to force agreement. EV1 uses de Chazal's record split and class mapping with these documented differences, and literature comparisons on DS2 are contextual. Source: independent review EV1_R3_REVIEW.md R3, with the visually checked Table II at runs/EV1_r3_review/paper_page2_1_Im2.png.

## A009
- **Observation (exploratory, E001):** on DS1 grouped-CV out-of-fold predictions, a linear readout on the 8 RR features alone (macro-F1 0.637) beats every feature set that adds the raw beat window (window + RR 0.546; ESN + RR 0.522; QRC + RR 0.537). Subtracting the patient's causal running template from the window recovers most of the loss (relative window + RR 0.619; ESN(relative) + RR 0.634; QRC(relative) + RR 0.600, one untuned configuration each).
- **Slice definition and size:** DS1, 50,542 N/S/V units, 5 fixed record folds; pooled OOF macro-F1; seed 0.
- **Magnitude:** -0.09 macro-F1 from adding raw morphology to RR; the patient-relative input recovers about +0.07 to +0.11. Morphology raises V F1 (0.669 -> 0.703 with the ESN) and S sensitivity, but lowers S PPV (0.181 -> 0.146).
- **Interpretation (not yet tested):** absolute morphology is patient-specific and does not transfer across patients; deviations from the patient's own normal beat do. Consequence for the slice: neither reservoir may beat an RR-only readout, so an RR-only control must be reported next to the headline (EVAL.md rule 7, "RR plus handcrafted features alone").
- **Status:** open; the shared reservoir input was set to the relative window before tuning.

## A010
- **Observation (exploratory):** in DS1 tuning, the ESN's best λ sits at the lower edge of the shared, declared grid {0.001, 0.01, 0.1, 1} in 15 of 30 configurations, including the selected configuration 28. The QRC's does in 2 of 30 (it mostly selects 0.01 or 0.1).
- **Slice definition and size:** 30 configurations per arm, DS1 OOF macro-F1 per λ, `runs/E00{2,3}/tuning.jsonl`.
- **Magnitude:** unknown; the ESN might gain from λ < 0.001. The best ESN DS1 OOF score is 0.6744 against 0.6669 for the QRC.
- **Consequence:** the headline uses the pre-registered grid as declared. Any headline result is reported with this caveat, and a pre-declared secondary check is warranted: both arms refitted with an extended grid {1e-4, 1e-3, ...} chosen by DS1 OOF, as a `secondary` comparison after the headline.
- **Resolution (2026-10-26 22:31, E010/E011):** both arms were retuned over the same 30 configurations with λ ∈ {1e-5, 1e-4, 1e-3, 1e-2, 1e-1, 1}. Both select the same configuration and λ as before (ESN cfg28 λ 1e-3, an interior optimum: 1e-4 gives 0.6637 vs 0.6745; QRC cfg15 λ 0.1), and their predictions are byte-identical to E002 and E003. Under the extended grid, 5 of 30 ESN configurations prefer λ < 1e-3. The grid edge did not handicap the selected classical baseline.
- **Status:** resolved.

## A011
- **Observation:** the first full-pipeline lookahead check of R0 (E002, seed 0) flagged beats 48 and 65 of DS1 record 207. Their probabilities changed by 1.8e-7 and 2.2e-8 when the beat positions after the boundary were dropped, whether or not the signal was also replaced, which exceeds the check's 1e-6 relative tolerance.
- **Explanation:** float32 matrix products on the GPU (ESN state update) and in numpy (readout) round differently for different batch shapes. A genuine leak would change outputs by orders of magnitude more.
- **Consequence for the record:** E002's `tuning.jsonl` scores come from the float32 code. A float64 retune (clean environment, 2026-10-26) gives scores within 3.3e-4 of them, and the same λ in all 30 configurations and the same selected configuration 28.
- **Resolution:** the ESN state update and the readout's prediction step run in float64. The rerun check passes (731 beats, 0 violations) for E002 and E003. Earlier, the same issue was found and fixed in the QRC shot sampler (float64 CDF), and the RX gate is applied elementwise.
- **Status:** explained.

## A012
- **Observation (exploratory, proxy):** pooled DS1 out-of-fold macro-F1, mean over 5 seeds: QRC (E003) 0.6671; its classical-spin mean-field model (E004) 0.6671; the same QRC with J = 0, i.e. separable (E005), 0.6793; matched ESN (E002) 0.6620; RR only (E006) 0.6367. The QRC's tuned couplings are weak (J = 0.106 per layer, h = 0.159), at the low edge of the declared range J ~ U[0.1, 1.5].
- **Slice definition and size:** DS1, 50,542 N/S/V units, 5 fixed folds.
- **Magnitude:** mean-field minus QRC = -0.0000; separable minus QRC = +0.012 (S F1 +0.026, V F1 +0.014); QRC minus ESN = +0.005 (DS1 OOF CI [-0.044, +0.066], no detectable change).
- **Interpretation (to be tested on ds2s after the headline):** what the reservoirs contribute here comes from single-qubit nonlinear encoding (RY rotations read out as Z and products), not from entangling dynamics. Entangling interactions made the DS1 proxy slightly worse. For the write-up this is the central mechanism finding: an honest null for quantum correlations on this task.
- **Update 2026-10-26 22:30 (ds2s, EV2; A016):** the mean-field part holds on the test split (QRC vs mean-field +0.0039 [-0.0028, +0.0115]). The separable advantage does not: separable vs QRC -0.0009 overall, with V F1 lower (-0.063, CI excludes 0) and S F1 higher (+0.067, CI includes 0).
- **Status:** open.

## A013 (failure analysis: rubric)
- **Observation:** lowest self-rated criteria (`runs/phase3/scorecard_selfrating_2026-10-26.md`), weighted equally: Performance 0 (no ds2s comparison yet), Gate deliverables 0, Depth 1, Gate reproducible 1.
- **Slice / size:** six scorecard rows; internal generator rating only, not critic-rated.
- **Magnitude:** 2 of 4 weighted criteria at or below 1; both gates below 3.
- **Status:** open. Performance needs EV1 approval and the headline run. Depth needs ablation axes beyond entanglement.
- **Update 2026-10-26 21:43 (after the headline; `runs/E002/packet-selfrating.md`):** Performance 1 (no detectable change on the primary; V_f1 slice favorable, but anchor 2 needs all four family members reported, and the low-data pair waits for the D4 fix). Ingenuity 2, Depth 1, Soundness 2, Gate deliverables 0 (no write-up beyond one paragraph), Gate reproducible 1 (one-command script `scripts/reproduce.py` written; clean-environment run in progress). Lowest weighted: Performance and Depth at 1; both gates below 3.
- **Update 2026-10-26 23:55 (Phase 3 close-out; `runs/phase3/scorecard_selfrating_2026-10-26_2355.md`):**
  - Ratings: Performance 2 (complete slice family, V_f1 favorable), Ingenuity 2, **Depth 1**, Soundness 2.
  - The conditions of both gates appear met, and the critic check is pending:
    - Deliverables: all four items exist. The explanation is the `WRITEUP.md` draft.
    - Reproducible: `scripts/reproduce.py --check` ran as one command in a fresh venv and regenerated every headline input byte-identically (`runs/phase3/reproduce_check_EV2.md`).
  - The lowest weighted criterion is Depth. It needs at least two more ablation axes (readout size or qubit count, shots or noise) for anchor 2, and device noise, hardware and a kernel diagnostic for anchor 3. Phase 4 targets these.

## A014 (failure analysis: judge questions we cannot yet answer with evidence)
1. "Does the quantum reservoir do anything a classical model cannot?" Only DS1 proxy evidence so far (A012: the mean-field model matches it, and the separable variant beats it). ds2s secondary comparisons are needed. **Answered 22:30 (A016): no.** On ds2s the classical mean-field model matches it (+0.004 [-0.003, +0.012]); the gain over the ESN comes from the coupled spin-model feature map.
2. "Was the classical baseline handicapped?" The λ grid edge binds for the ESN (A010). An extended-grid secondary check is needed. **Answered 22:31 (E010/E011):** with the grid extended to 1e-5, both arms select the same configuration and λ, so the predictions are unchanged.
3. "Would this run on real hardware, and at what cost?" No noise simulation or Braket run yet (I005, I006).
4. "How does it compare with published inter-patient ECG classifiers?" No strong classical reference built (EVAL.md rule 7, last bullet). Paper-compatible VEB/SVEB metrics will allow contextual comparison.
5. "Is the result driven by one patient?" Answerable only after the headline (232 condition, leave-one-record-out table). **Answered 21:39 (E003 card, A015):** the leave-one-record-out delta is positive for every record (+0.011 to +0.046). Without 232 the delta rises to +0.046. The S-class loss is concentrated in 232.
6. "What does it mean for a clinician's workload?" Review-burden metrics exist in the scorer; none computed on test data yet. **Answered 21:39 (A015):** per hour of Holter, 608 vs 806 S-or-V flags and 217 vs 374 normal beats flagged, against 93 vs 57 missed ectopic beats (QRC vs ESN).
7. (new) "Is the V gain a regularisation artefact?" Partly answered on DS1 (E009, diagnostic): QRC features give fewer V false positives at every λ; the S-side reduction is mostly the QRC's stronger selected λ.
- **Status:** open for items 1-4; each maps to an idea or to a planned secondary comparison (E004, E005, E006, E010/E011).

## A015
- **Observation (predefined slices of the EV1 headline, from the logged output only; no further label access):** pooled over records, seed-averaged confusions (true x pred, N/S/V):
  - E003 (QRC): N [39,864, 1,653, 629]; S [950, 750, 80]; V [26, 137, 3,036].
  - E002 (ESN): N [38,209, 2,759, 1,179]; S [576, 1,059, 145]; V [21, 127, 3,050].
- **V:** the gain comes from false positives. V false positives per seed fall from 1,324 to 709 (-614): N->V in records with few or no V beats (117 -123, 222 -99, 105 -92, 111 -61, 212 -43) and S->V in 232 (-53). V true positives are unchanged (3,036 vs 3,050). Per-record V F1 (9 records with >= 10 V units): QRC better in 5 of 9; worst 105 (-0.167, 41 V units); four records within ±0.001 [**corrected 2026-10-28 (V005 re-check R1):** only 214 is within ±0.001; three records (200, 214, 221) are within ±0.0015].
- **S:** the QRC arm flags fewer S beats. S false positives fall by 1,096 per seed (213 -395, 233 -234, 210 -156, 212 -152, 219 -139), and S true positives fall by 310, of which 288 are in record 232 (493 vs 781 of 1,381). Per-record S F1 (7 records with >= 10 S units): QRC better in 4 of 7; 232 -0.196; the other two losses are small (222 -0.031, 200 -0.014).
- **Review burden per hour (seed-averaged, 10.5 h):** S-or-V flags 608 vs 806; normal beats flagged 217 vs 374; missed ectopic beats 93 vs 57.
- **Leave-one-record-out delta:** positive for every record left out, from +0.011 (without 213) to +0.046 (without 232).
- **Open question (exploratory):** whether the more conservative decision behaviour comes from the reservoir features or from the readout's regularisation. The selected λ differs: QRC 0.1, ESN 0.001 at the grid edge (A010).
- **E009 (diagnostic, DS1 OOF, both arms at every λ):**
  - the QRC features give fewer V false positives than the ESN at every λ (893-1,036 vs 942-1,474 per seed), so the V-side difference is not a regularisation artefact on DS1;
  - the S false-positive reduction appears mainly at the QRC's selected λ = 0.1 (2,446 vs the ESN's 3,303 at its own λ; 3,403 for the QRC at λ = 0.001), so on the S side regularisation explains much of it.
- **Status:** open.

## A016
- **Observation (predefined controls, full EV2 secondary comparisons on ds2s, descriptive):**
  - **E003 (QRC) vs E004 (classical mean-field model of the same gates, couplings and shot sampling):** 0.7273 vs 0.7234, **+0.0039 [-0.0028, +0.0115]**, no detectable change. Per class: N +0.001, S +0.011 [-0.000, +0.025], V -0.000. Seed-averaged V F1 is 0.874 for both; review burden is nearly equal (608 vs 615 S-or-V flags per hour).
  - **E005 (the same QRC with J = 0, separable) vs E003:** 0.7264 vs 0.7273, -0.0009 [-0.0444, +0.0319]. Per class: **V -0.063 [-0.132, -0.021]**; S +0.067 [-0.014, +0.131].
  - **E006 (RR features only, one run):** 0.6997. S F1 0.390, V F1 0.739.
- **Slice and size:** ds2s, 21 records, 47,129 N/S/V units; 5 seeds per arm (E006: one deterministic run).
- **Magnitude:** the headline gain over the ESN (+0.0208; V F1 +0.069) is matched by the mean-field model to within +0.004 overall and 0.000 on V F1.
- **Interpretation:** the V-class improvement over the matched ESN comes from the circuit's spin-model feature map: single-qubit rotations of the patient-relative window, coupled through ZZ interactions and read out as ⟨Z⟩ and ⟨ZZ⟩. It does not come from quantum correlations, because a product-state (mean-field) simulation of the same gates reproduces it. The couplings themselves matter: removing them costs V F1. Classical couplings suffice. This agrees with Bowles, Ahmed & Schuld 2024 (circuits without entanglement matched entangled ones) and with the weak couplings the tuner selected (J = 0.106).
- **Consequence for claims:** the write-up can claim a quantum-*circuit-inspired* feature map that beats a matched ESN on the V class (slice level). It cannot claim a quantum advantage. The mean-field model is a cheaper classical equivalent on this task.
- **Status:** open. The extended-λ fairness check E010/E011 is done (A010 resolved, same selections). Hardware or noise evidence would not change the attribution.

## A017
- **Date:** 2026-10-28 (raised by the human-supplied progress review; code path confirmed by the agent).
- **Observation:**
  - `features.build_split` keeps the native-sample beat IDs (for example `svdb:800:100002`, at 128 Hz) while it resamples the signal to 360 Hz, and `run.keys_of` hashes those IDs into each beat's finite-shot stream.
  - `run.pipeline_fn`, used by the demo and the lookahead check, builds the IDs from the resampled positions it receives instead.
  - For MIT-BIH, both give the same IDs, because the native rate is 360 Hz. For SVDB they differ: native 1280 becomes 3600.
- **Slice and size:** every SVDB beat that goes through `pipeline_fn`.
- **Magnitude:** on one synthetic, label-free beat with the selected QRC configuration, the review measured 210 of 220 features changed, with a maximum absolute difference of 0.098. The effect on predictions was not measured.
- **Consequence:**
  - No scored result is affected: every scored file comes from the batch path, and the lookahead check runs on MIT-BIH only.
  - The SVDB confirmation uses the batch path, which is self-consistent.
  - An SVDB demo built through `pipeline_fn` would not reproduce the scored SVDB predictions.
- **Action:** no SVDB demo is presented. The README discloses the mismatch. The fix (pass native coordinates through `pipeline_fn`) is deferred, because it changes pipeline code after the freeze for no scored benefit.
- **Status:** open.

## A018
- **Date:** 2026-10-28 (raised by the progress review; the missing predict path was found by the agent).
- **Observation:**
  - `run.load_artifact` restores the readout from the saved file, but it regenerates the reservoir from configuration and seed. It neither compares the result with the saved `res_*` arrays nor reads the saved shot count; the module default (1,024) is used.
  - No command predicts a new split from the saved artifacts. `final` refits the readout and rewrites `model_seed*.npz`, and the file bytes change because the stored metadata records the current pipeline revision.
- **Slice and size:** the 10 headline artifacts, E002 and E003 with seeds 0-4.
- **Consequence:** the confirmation policy requires the exact DS1-trained artifacts. Producing SVDB predictions with `final` would replace them: the arrays would be identical, by every reproduction check so far, but the file hashes would not.
- **Planned fix, before the confirmation:** a predict-only path that
  - loads each saved artifact;
  - checks that the regenerated reservoir equals the saved `res_*` arrays and that the shot count matches;
  - writes predictions and manifests without touching the artifact.

  Its self-check runs on ds2s from the saved artifacts and must reproduce the 10 logged headline hashes. That compares hashes only; nothing is scored.
- **Status:** open.

## A019
- **Date:** 2026-10-28 (E016, the post-hoc gradient-boosting context model; secondary, descriptive)
- **Observation:** the boosted trees on [patient-relative window | RR] tie both reservoir arms overall on ds2s (E003 vs E016 +0.0057 [−0.1389, +0.0676]; E002 vs E016 −0.0151 [−0.1896, +0.0766]), but the tie is carried by one record. Without record 232 the boosted trees lead by 0.087 (E003) and 0.133 (E002). Their V F1 is 0.943 against 0.874 (E003) and 0.805 (E002), with 95% CIs that exclude 0 (−0.068 [−0.159, −0.031]; −0.137 [−0.267, −0.067]); their S F1 is 0.246 against 0.347 and 0.370. They rarely predict S: 655 of 47,523 ds2s beats (label-free count, seed 0), against 2,585 (E003) and 3,923 (E002); DS1 OOF S sensitivity 0.268 (E003 0.614, E002 0.685).
- **Slice and size:** ds2s, 21 records, 47,129 units; record 232 holds 1,381 of 1,781 S units (A001).
- **Magnitude:** above.
- **Interpretation (exploratory):** a nonlinear learner on the same inputs is a stronger classical model than either reservoir arm on N and V; the reservoir arms' overall parity with it rests on S beats in one record. Untested cause of the S under-prediction: the trees fit the S morphology of a few training patients.
- **Consequence for claims:** the README states that the matched ESN is a controlled comparator, not the strongest classical model, and reports E016 with its 232 dependence. No claim that the quantum arm matches a strong classical model.
- **Status:** open (exploratory)

## A020
- **Date:** 2026-10-28 (E014 ablations; proxy, DS1 OOF)
- **Observation:** smaller readouts score higher on DS1 than E003 (K 220, 0.6671): n = 6 qubits (K 84) 0.6803, Z-only n = 10 (K 40) 0.6776; n = 8 0.6673; n = 12 (K 312) 0.6635. On ds2s (secondary) n = 6 vs E003 +0.0078 [−0.0055, +0.0188], without 232 +0.0004.
- **Slice and size:** DS1, 22 records, 5 seeds per variant.
- **Magnitude:** +0.013 and +0.010 on DS1, inside DS1's record-level uncertainty (about ±0.05).
- **Interpretation (exploratory):** dropping every ZZ correlator does not hurt DS1, consistent with A016 (correlations add little). The n = 6 variant also resamples each input chunk to 6 points, so qubit count and input resolution are confounded.
- **Status:** open (exploratory)

## A021
- **Date:** 2026-10-28 (E015 device-noise simulation)
- **Observation:** (1) the card's prediction failed on DS1: noise lowered V F1 below both E003 and the separable control (Rigetti 0.699, IQM 0.717; E003 0.742, E005 0.756). On ds2s (secondary) the noise-aware Rigetti arm trades V for S like the separable control: V −0.053 [−0.114, −0.020], S +0.058 [−0.036, +0.121], overall +0.0016 [−0.0331, +0.0248]. (2) Exploratory, seed 0: a readout trained on noiseless features and applied to noisy features collapses on DS1 OOF to 0.278 (Rigetti) and 0.498 (IQM), against 0.668.
- **Slice and size:** DS1 (22 records) and ds2s (21 records); 5 seeds; (2) one seed.
- **Magnitude:** above.
- **Consequence:** the V-class gain over the ESN (the headline's favorable slice) does not survive device noise at Rigetti's calibrated rates in this simulation, which omits idle decay and crosstalk (optimistic). For the hardware run (E019) the seed-0 readout trained on noiseless simulated features is expected to transfer badly; E019's class-agreement number must be read against (2).
- **Status:** open

## A022
- **Date:** 2026-10-28 (E018, the pre-registered SVDB confirmation; full, EV2)
- **Observation:** the frozen headline pair is not confirmed on SVDB: E003 0.6402 vs E002 0.6488, delta −0.0085 [−0.0476, +0.0274]; leave-one-record-out negative for every record (−0.0157 to −0.0010). The ds2s V-F1 gain (+0.069) is absent: SVDB V F1 0.570 vs 0.574 (−0.003 [−0.089, +0.073]). The QRC arm keeps the ds2s direction of trade-off on V (PPV 0.544 vs 0.463, sensitivity 0.600 vs 0.763) without the F1 gain, and its V AUPRC is lower (0.605 vs 0.677, CI includes 0).
- **Slice and size:** SVDB, 78 records, 184,286 units (S 12,193, V 9,933), 5 seeds per arm.
- **Magnitude:** above.
- **Interpretation:** the favorable ds2s V slice did not generalise to a second database with different sampling rate (128 Hz), lead and patient mix. Consistent with selection on one test split and with the fragility seen in E015 (noise) and E016 (strong classical model).
- **Status:** open (reported; no repair access: no implementation defect is known)

## A023
- **Date:** 2026-10-28 (E019, Rigetti Cepheus-1-108Q, 48 ds2s beats; diagnostic)
- **Observation:** hardware features differ from the simulation by a mean absolute 0.347 (shot noise alone 0.018) with pooled correlation 0.70 and a ZZ contraction slope 0.46; the seed-0 readout trained on noiseless features agrees with the finite-shot simulation on 41.7% of beats (ceiling 87.5%) and predicts S for 35 of 48. Snapshot 1 (the shallowest circuit) has the lowest median per-feature correlation (0.39), not the highest.
- **Slice and size:** 48 beats x 4 snapshots = 192 beat-snapshots (in 40 circuits of 5 rings; 8 ring slots unused), 1,024 shots each.
- **Interpretation:** the contraction and the S-skewed transfer agree with E015's step-5 result (A021). The low snapshot-1 correlation is unexplained; a candidate cause is the small spread of snapshot-1 features across beats (one weak input step), which makes correlation sensitive to readout error. Not investigated (freeze).
- **Status:** open (exploratory)
