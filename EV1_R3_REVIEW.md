**EV1, revision 3 — independent review and recommended changes**  
Reviewed 26 October 2026. Scope: [EVAL.md](EVAL.md), its implementation and fixtures, processed-data manifest, existing reference results, prior reviews, the competition brief, and primary literature.

**Recommendation: request a focused revision before approving EV1.** Keep the overall problem, primary metric and patient-separated comparison. However, r3 still contains a prediction-set error, two incorrect literature-comparability claims, and gaps in statistical and command-level enforcement. Passing the existing 28 tests does not establish that these requirements are satisfied. No trained candidate exists, so these corrections can be made before they affect model selection.

I recommend completing items R1–R6 below before approval. Their priority reflects their effect on the evaluation, not the size of a measured model-performance change. The review identifies no need to abandon C1 or replace macro-F1.

| Item | Priority | Recommended change |
|---|---|---|
| R1 | High | Remove non-beat flutter annotations from the beat/RR input stream. |
| R2 | High | Correct or rename the secondary metrics described as EC57-style. |
| R3 | Medium | Correct the claim that current counts exactly reproduce de Chazal's Table II. |
| R4 | High | Make the multiplicity policy coherent and executable, including headline replacements. |
| R5 | High | Enforce five distinct seeded runs for headline/confirmation results. |
| R6 | Medium | Produce all required diagnostics within the single confirmation access. |

**What I verified**

The reviewed source hash is `9c74cdcb7d673bc7`; the fixture hash is `ccbe3120d947a5a7`. Both match the recorded r3 identifiers. The SHA256 of the reviewed `EVAL.md` is `7bb9518db0a93e34e1664f5c7a29972c55fbeb0e3f407b71f75c764717032bf1`.

- All **28 existing tests passed**, with three dependency deprecation warnings. An initial test invocation failed to create its temporary directory because I had not yet created the parent review directory; after correcting that invocation, the suite passed without changes to project code.
- All **13 non-confirmation processed-output hashes** matched the manifest. All **144 MIT-BIH raw signal/header/annotation files** checked matched the downloaded checksum list. I did not reopen real SVDB labels or raw SVDB annotations, including for hashing.
- Independent confusion-count calculations reproduced `const_n = 0.3147357849` and `rr_rule = 0.4548782337` on ds2s.
- Rerunning the existing diagnostic reference comparison reproduced delta **+0.1401424488**, 95% CI **[+0.0219551964, +0.2423934047]**, and delta excluding record 232 **+0.0494296523**. This is a reference-scorer check, not evidence of quantum improvement.
- Additional synthetic probes reproduced the command and metric issues below. Real confirmation access remained unchanged.
- I read the supplied **11-page de Chazal paper**, including visual inspection of Tables I, II and V. PDF SHA256: `164df598535a1018dee8e3c7640b26159dd78cc831cb81e6e6712cfc5a64e940`.

The reproducible evidence is in [audit.py](runs/EV1_r3_review/audit.py), [audit_results.json](runs/EV1_r3_review/audit_results.json), and [the reproduced reference comparison](runs/EV1_r3_review/reference_compare_reproduced.json). Source code, evaluation rules, original fixtures and original reference outputs were not changed.

**R1 — Non-beat flutter waves are being used as beat positions**

Locations: `src/qhc/evalspec.py:17–19`, `src/qhc/units.py:49–57`, and `EVAL.md:42–46`.

`BEAT_SYMBOLS` includes `!`. PhysioNet explicitly categorizes `!`, a ventricular flutter wave, as a **non-beat annotation**. Its record directory also cautions that some tabulated totals include non-beats. [PhysioNet annotation definitions](https://physionet.org/static/lightwave/doc/annotations.html), [MIT-BIH record directory](https://archive.physionet.org/physiobank/database/html/mitdbdir/records.htm).

The current DS1 prediction set contains **472 `!` entries**, all in record 207, recorded as `aami=other`. Excluding them in an in-memory check changes the immediate pre-RR interval of **six scored beats** and post-RR interval of **six scored beats**. Rolling RR features or a reservoir that carries state across beats can be affected further; I have not measured a trained model's response.

This is not merely an extra unscored category: those positions are supplied to the model as if they were heartbeat fiducials. The existing test that recomputes `predict` from positions cannot detect an incorrect annotation-to-position rule.

**Change:** remove `!` from the beat-position whitelist, retain flutter information only in a separately documented annotation channel if ever needed, and rebuild affected artifacts and references. Add a fixture that supplies both genuine beat and non-beat annotation symbols and checks the resulting RR sequence. Confirm that DS1's prediction count falls from **51,436 to 50,964**, while its N/S/V unit count stays **50,542**. Recompute rather than assume the DS1 RR-reference score is unchanged. The primary ds2s files contain no such entries.

**R2 — “EC57-style” secondary precision is not the paper's definition**

Locations: `EVAL.md:90–106`; `src/qhc/scorer.py:48–50,108–140`; de Chazal, Section IV-H and Table V, printed pp. 1201–1202 / PDF pp. 6–7.

The scorer first removes every F/Q row and then computes all sensitivity, PPV and false-flag metrics from the remaining N/S/V confusion matrix. In the supplied paper, the S-class false-positive count includes **F → S** predictions. Its V-class definition excludes F → V and Q → V; its S-class definition excludes Q → S. These exclusions are not identical across classes. [Supplied paper](<papers/Automatic Classification of Heartbeats Using ECG.pdf>), [Table V formulas extracted for inspection](runs/EV1_r3_review/paper_page7_9_Im68.png).

A minimal example demonstrates the difference: truth `N,S,V,F`, predictions `N,S,V,S`. EV1 reports S PPV **1.0**; Table V's S PPV is **0.5**. EV1's primary macro-F1 is also 1.0, which is consistent with its explicitly restricted primary metric. The defect is claiming EC57 comparability for the secondary metrics without preserving their denominators.

**Change:** keep the N/S/V primary metric if desired. Add explicitly named paper-compatible S/V secondary metrics using the full prediction set, or rename the existing fields to **N/S/V-restricted record-averaged sensitivity and PPV** and remove claims of direct EC57 comparability. The former is preferable if literature comparison remains a goal. Add the F → S example as a fixture. The paper verifies these historical definitions; I have not audited the complete EC57 standard or its later revisions.

**R3 — The “exactly reproduces de Chazal” assertion is false**

Locations: `EVAL.md:139,182`; `tests/test_scorer.py:test_units_reproduce_de_chazal_counts`; related statements in `PROBLEM_BRIEF.md` and `ANOMALIES.md`.

Summing Table II's heartbeat types into the paper's AAMI classes gives the following counts. The current-data column reconstructs totals **before EV1's first/last-beat and edge exclusions**, so those exclusions do not explain this discrepancy.

| Split / class | Paper, Table II | Current downloaded annotations | Current minus paper |
|---|---:|---:|---:|
| DS1 N | 45,868 | 45,866 | −2 |
| DS1 S | 942 | 944 | +2 |
| DS1 V | 3,787 | 3,788 | +1 |
| DS1 F / Q | 415 / 8 | 415 / 8 | 0 / 0 |
| DS2 N | 44,258 | 44,259 | +1 |
| DS2 S / V | 1,837 / 3,221 | 1,837 / 3,221 | 0 / 0 |
| DS2 F / Q | 388 / 7 | 388 / 7 | 0 / 0 |

Source: [supplied paper](<papers/Automatic Classification of Heartbeats Using ECG.pdf>), printed p. 1197 / PDF p. 2, [visually checked Table II](runs/EV1_r3_review/paper_page2_1_Im2.png). The record lists and exclusions do match the paper. The present fixture checks hard-coded current counts against the manifest; it does not verify the historical table.

**Change:** retain the checksum-verified current annotations. Rename this fixture to a current-dataset count check, publish this reconciliation, and replace “reproduce de Chazal” with “use de Chazal's record split and class mapping, with the documented current-annotation count differences.” Annotation revisions are a possible explanation, but the precise cause is unverified. Do not alter labels merely to force agreement with a paper.

Also describe DS2 literature comparisons as contextual: EV1 removes edge beats, predicts only three classes, uses a specific lead policy and imposes a stricter temporal boundary. The paper's Section IV-D uses a whole-record average RR and a local average over surrounding intervals; copying those features verbatim would violate EV1. This is a reason to disclose the difference, not to loosen EV1's boundary.

**R4 — Multiplicity protection is incomplete**

Locations: `EVAL.md:205–208,228–245`; `src/qhc/evaluate.py:190–191`; `src/qhc/scorer.py:184–209,248–251`.

There are two separate issues.

First, the four slice tests require **98.75% CIs**, but the ordinary comparison command emits **95% per-class CIs** by default. My probe returned `ci_level=0.95, n_boot=2000`; manually passing `n_comparisons=4` returned `0.9875, 8000`. The same parameter changes the primary CI and every secondary CI, while its CLI help describes only headline replacement. There is no dedicated slice output or slice decision, and replacement count and slice count have different meanings. R3 therefore adds a written rule without providing an unambiguous reporting path for it.

**Change:** emit separately labeled primary and four-slice inference results, with the family size and level recorded in each. For the fixed headline, use the declared primary level and 98.75% slice CIs. The slice decision must use the slice CI rule, not the overall `outcome`, which additionally imposes the 0.02 threshold and dominant-record condition. Validate family sizes before accessing labels. Add an integration fixture verifying the levels and decisions in the normal command output.

Second, “number of pairs evaluated so far” is not a general correction for repeatedly replacing a headline or inventing new pairs after seeing ds2s. Bonferroni controls a specified family when the total allocated error is bounded; it does not automatically make adaptive test-set development valid. [NIST's Bonferroni definition](https://itl.nist.gov/div898/handbook/prc/section4/prc473.htm), [Cawley & Talbot on model-selection bias](https://www.jmlr.org/papers/v11/cawley10a.html).

For illustration, even independent valid null tests run successively at two-sided levels `0.05/i`, for `i=1,...,15`, have a **15.46%** probability of at least one rejection; the probability of at least one positive CI is **8.01%**. This is a mathematical counterexample to the sequential correction, **not an estimated false-positive rate for EV1**, whose practical-gain and record-232 conditions also matter.

**Recommended simple policy:** keep the first predeclared headline immutable; treat later ds2s-driven variants and newly invented slices as exploratory. A replacement can be reported, but its ds2s interval is descriptive after adaptive development; assess a frozen final pair on untouched SVDB with its stated provenance caveat. If multiple confirmatory ds2s hypotheses are essential, specify the fixed family or a valid sequential procedure before seeing results. Approval by the author and a larger `m` alone do not resolve adaptivity.

**R5 — Five seeds can mean five copies of one file**

Locations: `src/qhc/evaluate.py:66–73,118–129`; `src/qhc/scorer.py:189–195`; `EVAL.md:204,222`.

The expansion code accepts repeated paths and overlapping globs. Passing the same candidate file five times and the same baseline file five times produced a synthetic confirmation with:

```text
n_seeds: 5
distinct candidate files in output manifest: 1
distinct baseline files in output manifest: 1
warning emitted: false
confirmed: true
```

A single-file comparison also produced `confirmed=true`, with only a printed seed-count warning. Repetition creates no independent reservoir or shot-sampling runs and can suppress the seed-variation component the specification promises to measure. This is an enforcement gap; it is not evidence that any real experiment has exploited it.

**Change:** reject repeated resolved paths and duplicate seed IDs before scoring or confirmation access. Require exactly five distinct run manifests in headline/confirmation mode, including model-artifact identity, reservoir seed, and shot/readout randomness. Allow explicitly marked diagnostic references to use fewer seeds. Identical output hashes are not by themselves proof of invalid seeds: different valid runs can produce identical predictions. Validate run provenance rather than demanding different predictions.

**R6 — The authorized confirmation command cannot produce the required report**

Locations: `EVAL.md:90–95,144–146,264–270`; `src/qhc/evaluate.py:118–134`; `src/qhc/scorer.py:231–257`.

`compare` returns macro-F1, F1/AP deltas, intervals and leave-one-record-out deltas. It does **not** return per-class sensitivity/PPV, record-averaged sensitivity/PPV, false flags per hour, F/Q prediction distributions, or per-record confusion matrices. Those are supplied by the separate `score` path. This omission was reproduced through the synthetic SVDB command, including `confirmed=true`.

The specification requires these diagnostics for every scored arm but reserves one SVDB access for the final pair and one for a repair. Separate `score` calls for the five-seed arms would consume/exceed that budget. This is especially consequential because an aggregate improvement can coexist with worse S sensitivity or extra review burden.

**Change:** compute all per-seed arm summaries and clearly defined seed-averaged summaries during the same logged comparison access. Preserve the full per-record confusion data for later reporting without reopening labels. Include scorer/configuration identity in the output and bind the confirmation log to artifact/prediction hashes, not only free-form IDs.

Clarify that a repair is a documented implementation correction, not another model-selection opportunity. Preserve the first result and repair reason; invalidate affected earlier results when necessary. The existing guard is a useful workflow safeguard, but its cap alone does not establish that the second access is a legitimate repair.

**Additional changes worth making**

1. **Replace the null-calibration “fix” with a diagnostic escalation.** At `EVAL.md:217–219`, one ESN-vs-ESN comparison is used to choose a larger practical-gain threshold if the result is surprising. One draw cannot estimate CI coverage or a reliable noise floor. Increasing the positive-gain threshold cannot fix an upper CI below zero, which remains “unfavorable” under the existing rule. Keep the self-comparison as a diagnostic; investigate seeds, implementation and interval behavior when it triggers. Use DS1-based repetitions or synthetic checks for procedure development, and freeze the practical threshold before competitive ds2s evaluation. Do not describe a single null comparison as statistical calibration.

2. **Narrow the low-data claim.** At `EVAL.md:245`, configurations are selected using all DS1 labels, then retrained on 5 or 11 records. That measures reduced-data refitting conditional on full-data model selection, not an end-to-end method that needed only 5 or 11 labeled records. Label it accordingly, explicitly state which preprocessing parameters are refitted, and save the exact record subsets. For a genuine label-efficiency claim, all supervised tuning and fitted preprocessing must use only the permitted subset, with matched budgets. One subset per k also leaves subset-selection uncertainty unmeasured.

3. **Make review-burden labels precise.** Existing “false flags per hour” are class-specific errors restricted to N/S/V truth. They omit flags on F/Q and count S↔V confusion as an incorrect class flag even though the beat is still ectopic. Report total S-or-V flags/hour, normal beats flagged/hour, and F/Q flags separately if the intended workflow is general ectopic-beat review. Keep the original class-specific rates, but name their scope. Do not present a macro-F1 gain as proof that every clinically relevant error improved.

4. **Specify the seed estimand and matching details before implementation.** The current score averages five individual-model F1 values; it is not the F1 of a five-model probability ensemble. Its uncertainty is conditional on the fixed training cohort and selected configuration. State which predictor the demo uses. Also specify how equal feature dimension is maintained when configurations with different K are explored, and how readout regularization/threshold searches count toward the 40-configuration budget.

5. **Keep the controls but limit the resulting claims.** A matched ESN is a useful controlled comparator; retain the stronger classical reference, no-reservoir reference, separable reservoir and classical-spin control. Equal feature dimension alone does not establish equal model capacity or practical computational advantage. Kornjača et al. motivate the classical-spin comparison as a heuristic entanglement control; Bowles et al. support examining classical baselines and non-entangling variants. Neither establishes an ECG advantage for this proposed model. [Kornjača et al., methods and classical models](https://arxiv.org/html/2407.02553v1), [Bowles et al.](https://arxiv.org/abs/2403.07059).

**Small corrections**

| Location | Correction |
|---|---|
| `EVAL.md:112` | Latency is `max(1 second, next-RR)`, not “at most the next RR interval.” It exceeds next-RR when next-RR < 1 second. |
| `EVAL.md:140` | The scorer-command section still names `dd225b75db9a8c68`; distinguish historical reference provenance from the r3 scorer identity. |
| `EVAL.md:247` | Including both 201 and 202 gives **44 non-paced records in 43 subject groups**. Alternatively, explicitly define a 43-record dataset that excludes 202. |
| `EVAL.md:268` | Change “absolute scores will be lower” on SVDB to “may differ because of domain shift”; the direction is unknown before evaluation. |
| `scorer.decide` / outcome wording | A delta of +0.01 with CI [+0.005,+0.015] is labeled “no detectable change.” Preserve the three-way adoption rule if desired, but report a reason such as “detectable gain below practical threshold.” |
| `requirements-lock.txt` | Replace the absolute editable-install path with a portable installation step before claiming clean-environment reproducibility. That gate was not tested here. |

**What should stay**

Keep the exclusion of record 202 from the primary split: PhysioNet confirms that 201 and 202 share a subject. Keep MLII selection by lead name, grouped DS1 tuning, explicit oracle-beat/latency limitations, prediction coverage of F/Q, record-level resampling, the 232-exclusion check, finite-shot headline features, and transparent reporting of all variants. The core metric calculation and the existing diagnostic comparison reproduced. [MIT-BIH provenance and lead documentation](https://archive.physionet.org/physiobank/database/html/mitdbdir/intro.htm).

SVDB remains a useful external-database confirmation, with the already stated unknown-subject-overlap caveat. Its official description gives 78 recordings rather than a verified independent-patient count. This review provides no new evidence that the prior testing incident compromised it. [SVDB documentation](https://physionet.org/content/svdb/1.0.0/).

**Acceptance check for the next revision**

Rebuild affected DS1 artifacts after R1; reconcile paper counts without changing verified annotations; add the F → S metric fixture; test primary/slice interval levels; reject duplicate or insufficient headline seeds before label access; and run one synthetic confirmation command that emits the complete report while logging exactly one access. Then update revision hashes and affected documentation and rerun the existing fixtures and reference comparison. These checks do not require opening real SVDB labels or building the quantum model.

This is an evaluation review, not a candidate verification PASS. No training pipeline, quantum simulator, hardware run, clean-environment reproduction or new clinical-performance claim was evaluated. I inspected the current split construction and relevant data artifacts, but did not rebuild every raw-data artifact or independently measure bootstrap coverage.

**Literature access record — resolved**

A literature search initially reported for *Automatic Classification of Heartbeats Using ECG Morphology and Heartbeat Interval Features*: **“Acquire manually using the SCH Protocol: Automated Access Blocked”** ([paper link returned by the search](https://sci.bban.top/pdf/10.1109/tbme.2004.827359.pdf)). The author then supplied [the local PDF](<papers/Automatic Classification of Heartbeats Using ECG.pdf>), which I read and used for R2/R3. No manual-acquisition request remains. Other research used accessible PhysioNet documentation, the Kornjača paper, the locally cached Bowles paper, and the cited statistical sources.
