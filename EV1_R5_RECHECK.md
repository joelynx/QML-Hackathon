**EV1 review-response audit — draft r5**  
Reviewed 26 October 2026 against [the original r3 review](EV1_R3_REVIEW.md), the saved r3 source, and the current r5 implementation.

**Recommendation: make a small further revision before freezing EV1.** The data, literature and metric corrections are sound. The main remaining problems are in preserving the meaning and history of an evaluation: a confirmation repair can reverse the arms, its output can erase the first result, and an accepted identical rerun can produce different confidence intervals. The reduced-data roles also need stronger provenance checks. None of these findings establishes that an actual experiment used an invalid comparison.

The reviewed evaluation-code revision is **`9a1922c8898b90db`**; the fixture hash begins **`7f323fb891968894`**. `EVAL.md` SHA256 is `f758910b94defc3dbbbbb1c735c41d2611755b20ba578340cdd6de9c95a84be9`. This report covers the final r5 files, including changes made after the intermediate V003 follow-up.

**Disposition of every original review item**

| Original item | Assessment of the response |
|---|---|
| R1: non-beat flutter annotations | **Resolved.** `!` is excluded from beat positions. Current DS1 labels exactly equal the saved r3 labels with the 472 flutter entries removed: 50,964 predictions, 50,542 scored units. An independent reconstruction from raw DS1 annotations matches the released positions. Fold assignments are unchanged. Regenerated DS1 reference predictions match the saved r4 files; macro-F1 is 0.3169736910 for `const_n` and 0.3919742092 for `rr_rule`. |
| R2: paper-compatible secondary metrics | **Resolved.** The restricted primary metric remains explicit, and separately named gross VEB/SVEB metrics use the supplied paper's Table V denominators. I checked all 15 truth/prediction cells for both endpoints independently, including F→S, F→V and Q exclusions; all agree. Per-record 5×3 tables preserve the necessary counts. This is historical paper compatibility, not an audit of the complete EC57 standard. |
| R3: false exact count-match claim | **Resolved.** `EVAL.md`, `PROBLEM_BRIEF.md`, `ANOMALIES.md` and the renamed count fixture distinguish current annotations from Table II. The published differences are correct; the cause remains appropriately unverified. Labels were not changed to force agreement. Literature comparisons are described as contextual. |
| R4: multiplicity and headline replacement | **Substantially resolved, with two enforcement gaps below.** The dynamic sequential correction is gone. The primary headline uses 95% intervals, the fixed four-member slice family uses 98.75%, and secondary comparisons are descriptive. The command enforces headline-first ordering and refuses a different headline or a second distinct run for the same low-data role. However, accepted seed permutations change the intervals (F3), and the first low-data invocation is not bound to the specified refit (F4). |
| R5: five copies counted as five seeds | **Resolved at the declared provenance-check level.** Strict roles require five runs, reject repeated paths across arms, validate prediction and model hashes, require distinct seed IDs/artifact contents/randomness pairs, enforce one configuration per arm and matched seed indices, and allow identical predictions from independently declared runs. The pending E002 and E003 files each pass the five-run checks. This validates manifests and files; it cannot establish how an arbitrary artifact was actually trained. |
| R6: complete report in one confirmation access | **Reporting omission resolved; repair integrity remains incomplete.** One comparison now contains per-seed and seed-averaged secondary metrics, review burden, non-unit predictions and per-record confusion tables. Separate SVDB `score` calls are refused. The access log binds predictions and model hashes. F1 and F2 below concern the remaining repair and result-preservation requirements. |

**Changes still recommended**

**F1 — Preserve candidate/baseline identity during a confirmation repair. High priority.**

Locations: `src/qhc/evaluate.py:277–289`, especially the set comparison at lines 282–283; `EVAL.md:383–389`.

The repair check compares the **union** of model-artifact hashes from both arms. It loses which artifacts were the candidate and which were the baseline. Consequently, reversing the arms passes the “same models” check without `--approved-model-change`.

My isolated synthetic command sequence produced:

| Command | Delta | `confirmed` | Accepted? |
|---|---:|---|---|
| First confirmation, candidate versus baseline | −0.5722511685 | false | yes |
| Repair, baseline versus candidate, same ten artifacts | +0.5722511685 | true | yes |

The second command supplied a repair reason but no approved model change. The same external evidence therefore changed from failure to success solely by changing the comparison direction. This is a concrete gap in the guard, not evidence that the real pending pair has been reversed.

**Change:** record and compare model identities separately for the candidate and baseline, preferably keyed by seed and including the declared arm identity. Preserve those roles across an ordinary repair. An explicitly approved correction that changes the hypothesis must be identified as such, with the original result retained; it should not silently inherit the original confirmation interpretation. Add a fixture that swaps complete arms while retaining all ten artifacts and expects refusal before label access or logging. The existing different-artifact fixture cannot catch this.

**F2 — Archive the first confirmation result before accepting a repair. High priority.**

Locations: `src/qhc/evaluate.py:271`, `:286–289`, `:304–315`; `EVAL.md:389`.

`_check_writable` accepts an existing output file, and `_write` replaces it. A second confirmation may use the first command's `--out`. In the synthetic sequence above, the first negative report was replaced by the positive repair report. No other result JSON was created, and neither ledger stores the first metrics. Hashes and reasons alone cannot reconstruct the first report without another label-dependent computation.

The specification explicitly promises to preserve the first result. The current confirmation test also reuses the same output path for a repair but never checks preservation.

**Change:** store a complete, immutable report for each confirmation access under a unique access ID. Record its path and hash, completion/failure status, repair reason and any invalidation relationship in the audit trail. A user-selected output can be an additional copy. Refuse overwriting a prior confirmation report before accessing labels, or archive and verify it first. Test that both full reports remain readable after a legitimate repair to the same requested output path.

**F3 — Canonicalize seed order before bootstrapping. Medium priority.**

Locations: `src/qhc/evaluate.py:187–189`, `:346–371`; `src/qhc/scorer.py:280–293`; `tests/test_scorer.py:418`.

Request identity sorts hashes within each arm, but scoring preserves the supplied file order. Bootstrap seed weights are assigned to array positions. Reversing only the candidate's five input paths therefore produces a different Monte Carlo interval despite the same files, same declared seed IDs, same bootstrap seed, and same accepted log identity.

In my 8,000-replicate synthetic comparison, delta stayed **+0.0417618683**, but:

| Interval | Original order | Reversed candidate order |
|---|---|---|
| Primary 95% CI | [−0.04482723, +0.12839999] | [−0.04473419, +0.12637790] |
| S slice 98.75% CI | [−0.08091351, +0.16995337] | [−0.09105921, +0.16355954] |

This is Monte Carlo variation, not evidence that every interval is statistically invalid. It is nevertheless inconsistent with reproducible “identical reruns” and permits choosing among intervals by file ordering; a borderline result could change its decision. This particular probe did not change a decision.

**Change:** sort each strict arm by its validated seed ID before passing predictions to the scorer, keeping manifests and reported seed summaries aligned. Use a content-based stable order for diagnostics if identical reruns there are also promised. Extend the existing reordered-path fixture to require identical numerical outputs, including all CIs and decisions, after reordering or relocating unchanged files.

**F4 — Bind reduced-data roles to the headline configurations and frozen subsets. Medium priority; resolve before using these slice results.**

Locations: `src/qhc/evalspec.py` (`RUN_KEYS`); `src/qhc/evaluate.py:130–166`, `:234–238`, `:351–375`; `EVAL.md:345–351`.

The specification correctly narrows the claim to reduced-data refitting, freezes the subsets, and requires the headline configurations. However, the command checks only that each current arm has internally consistent manifests and that the role has not already been used with different predictions. It does not compare the first low-data request with the headline configurations or require training-subset provenance.

After a synthetic headline, `lowdata_k5` accepted an unrelated configuration named `unrelated_full_data_cfg` against the unchanged baseline files. No training-record list, subset hash or parent-headline configuration was supplied. The result was labeled a slice-family member. These were synthetic artifacts; the probe demonstrates missing validation, not actual full-data training being concealed.

**Change:** have the refitting pipeline emit a stable parent-configuration identity, the training-record list/subset hash, and the refit scope. Before labels are opened, check both arms against the named headline configurations and the frozen k-specific subset. Preserve those fields in the comparison output. A new artifact/configuration ID for a refit is reasonable; compare its explicit parent identity rather than requiring an identical artifact ID. Add negative fixtures for a full-data run, the wrong subset and a different parent configuration. Metadata still needs to be backed by review of the refitting code.

The subset-generation fix itself is correct: I reproduced both stored subsets, their draw counts and their class counts. Do not redraw them.

**F5 — Extend output collision protection to model artifacts and audit files. Lower priority, straightforward fix.**

Locations: `src/qhc/evaluate.py:202–206`, `:304–310`, `:349–357`.

The new guard protects prediction CSVs and their run manifests only. I passed a referenced model-artifact path as `--out` in an isolated synthetic comparison. Validation accepted its original hash, then the writer replaced that model with the report, leaving the manifest invalid. This is an accidental file-clobbering risk even when every evaluation rule is otherwise followed.

**Change:** protect all referenced model files, both evaluation ledgers, and dataset inputs; validate both the final destination and the temporary-file destination. A unique temporary file in the output directory also avoids collisions with the fixed `out + '.tmp'` name. Add a refusal test that verifies artifact bytes are unchanged. This recommendation concerns the normal CLI's path checks, not resistance to a malicious user with filesystem access.

**Remaining original recommendations and smaller corrections**

| Original recommendation | Assessment |
|---|---|
| Replace one-draw null calibration | **Resolved in the protocol.** It is now a DS1 out-of-fold seed-noise diagnostic, with investigation on a trigger and a fixed +0.02 practical threshold. It is correctly not claimed to estimate coverage or calibrate the threshold. |
| Narrow the low-data claim | **Resolved in wording and subset preparation.** Full-DS1 configuration selection is disclosed; all fitted quantities must be refitted on the subset, and subset-selection uncertainty is acknowledged. Execution/provenance still needs F4. |
| Clarify review burden | **Resolved.** Restricted class-specific errors are distinguished from total S-or-V flags, normal beats flagged, F/Q flags and S↔V confusions. These appear in comparison summaries. |
| Specify seed estimand and matching | **Resolved in the protocol.** Mean individual-seed F1 is distinguished from ensemble F1; conditioning on DS1 and configuration selection is explicit; the demo uses seed 0. K is fixed before tuning, and the shared nested readout search is specified. |
| Retain controls and limit quantum claims | **Resolved in the protocol.** ESN, mean-field, separable and no-reservoir comparisons remain, with a stronger classical reference required for context. Equal K is not presented as equal capacity or practical speed advantage. These requirements do not establish that all planned control experiments are already complete. |

All six small corrections were made: latency is `max(1 second, next-RR)`; historical scorer provenance is distinguished from the current revision; grouped CV uses 44 records in 43 subject groups; SVDB scores “may differ”; detectable gains below the practical threshold have a separate reason; and the absolute editable-install path was removed from the lockfile. A clean-environment reproduction remains unverified.

The subsequent V003 changes also provide useful protection: reference-only predictions cannot consume the headline role; model scoring waits for the headline; confirmation waits for a non-reference headline; copied artifacts and mixed configurations are rejected; and malformed inputs, basic output errors and a placeholder-label scorer failure are caught before confirmation logging. Later descriptive entries do not block an identical headline rerun. The remaining defects above qualify the stronger claims about repair identity, identical reruns and complete result preservation.

Two documentation adjustments should accompany the fixes:

- `EVAL.md:381` says the placeholder smoke test means an output error or scorer crash **cannot** spend an access. It catches useful classes of failures, but cannot rule out real-label-dependent failures, resource exhaustion during 8,000 replicates, or a later write failure. Describe it as a preflight check and document how failed attempts are retained and handled. Likewise, the command prints a summary before writing; it does not print the complete report.
- Refresh the project status notes' “none known” unresolved-defects and “ready for approval” statements after addressing this report. No approval or change to project state is implied by this audit.

**Verification and limits**

- **38 tests passed**, with three dependency/API deprecation warnings, using `.venv\Scripts\python.exe -I -B -m pytest -q -p no:cacheprovider --basetemp=runs/EV1_r5_review/pytest_tmp`.
- Reviewed the source changes from the saved r3 files across `evalspec.py`, `evaluate.py`, `scorer.py`, `units.py` and the fixtures; `leakcheck.py` and the package initializer are unchanged. Reviewed the revised evaluation rules, reconciliation/anomaly notes, V003 responses, reference artifacts and reproduction instructions.
- All **11 processed-output hashes checked in this audit** match the manifest. This excludes held-out label files. Comparing manifest entries with the r3 snapshot shows only DS1 positions/labels changed and the low-data subset file was added. The unchanged held-out-label hashes were compared as manifest text, not recomputed by reopening labels.
- Independently verified DS1 rebuilding, DS1 reference regeneration, subset reproducibility, Table V cell accounting and the five command-level findings above. Evidence: [recheck script](runs/EV1_r5_review/recheck.py), [machine-readable results](runs/EV1_r5_review/results.json), [source diff](runs/EV1_r5_review/source_changes.diff).
- Verified prediction/model manifests for the five pending E002 runs (`E002-esn-cfg28`) and five E003 runs (`E003-qrc-cfg15`), seed IDs 0–4. The pipeline label-access search finds the DS1 training-label read and no direct ds2s/ds2/confirmation-label read. This is contextual provenance checking, not a full validation of the new reservoir implementation or its performance.
- **No real candidate was scored on a held-out split.** New comparison probes used temporary synthetic datasets and isolated logs. The audit script rejects real held-out-label opens, including hashing, and raw SVDB annotation opens. The real full-evaluation ledger remains unchanged at five reference-only entries; no real confirmation-access ledger was created.
- This audit did not repeat the earlier literature search or reread held-out annotations. It uses the already inspected supplied de Chazal PDF and the original review's checked tables. It does not establish bootstrap coverage, independent SVDB subjects, clinical utility or clean-environment reproducibility.

The recommended work is concentrated in evaluation identity, result storage and low-data provenance. The evidence here does not call for another beat-set rebuild, a different primary metric, or retraining the existing full-DS1 E002/E003 models solely because of these findings. Preserve their current artifacts while completing the remaining checks, then record the new evaluation revision and fixture hashes.
