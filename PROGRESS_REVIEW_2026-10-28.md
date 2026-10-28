**Progress review and critique: distance to a prize-winning Quantum Healthcare submission**

Reviewed 28 October 2026, approximately 18:00 UAE (UTC+4). This assessment covers the files currently in this workspace. It distinguishes observed results, previously recorded verification, reviewer judgment, and proposed work. Recommendations below have not been executed as new experiments.

**The project has a credible scientific foundation, but its central competitive claim remains unproven.** It implements a real quantum-reservoir simulation, a reasonably matched classical reservoir, careful patient separation, uncertainty estimates, and unusually useful controls. Its strongest result is a ventricular-class improvement against the ESN. Its primary result is inconclusive, and a classically tractable mean-field model achieves nearly the same performance as the quantum model. The current evidence therefore supports a rigorous comparative study with a useful attribution finding. It does not yet support a compelling case that quantum integration improves healthcare performance beyond strong classical alternatives.

The most consequential gap is between the goal of *testing a quantum hypothesis fairly* and the competition's goal of *demonstrating a useful improvement from a purposeful quantum contribution*. More ablations and a hardware demonstration could deepen the study. They cannot, by themselves, close that gap.

**The benchmark for this review is the supplied competition brief, with an explicitly aspirational standard layered on top.** [hackathon_details.md](hackathon_details.md) asks for a functional classical/quantum comparison, a meaningful purpose for quantum integration, measurable gains, sound evaluation, and reproducibility. It lists performance, ingenuity, depth, and soundness without weights. It does not require a QPU run, a clinical trial, a website, or proof of asymptotic quantum advantage. The equal 25% weights and hardware-dependent top scores in [EVAL.md](EVAL.md) are the project's internal planning choices, not official judging rules.

I could not establish a public page for this exact event or a scored exemplar from this competition. There is no defensible numerical estimate of winning probability. For context, the LUMS account of a winning healthcare entry emphasizes a locally relevant TB dataset and a reported gain against a fair classical baseline, but supplies insufficient numerical detail to audit that gain. NYUAD's 2023 archive links a healthcare prize winner to both a repository and a presentation. These illustrate useful submission qualities; they do not establish a scientific performance threshold or this event's rules. [LUMS winner account](https://sbasse.lums.edu.pk/winners-of-national-quantum-hackathon), [NYUAD 2023 archive](https://hackathon.nyuad.nyu.edu/year/2023/).

**What is actually complete.** The latest project state records Phase 3 complete on 26 October at 23:55 UAE. The experiment index ends at E011; the shot, noise, qubit/readout-size, hardware, and geometric-analysis ideas remain in the backlog. The write-up still contains explicit placeholders. I found no later completed Phase 4 results in the inspected artifacts. [STATE.md](STATE.md), [EXPERIMENTS.md](EXPERIMENTS.md), [IDEAS.md](IDEAS.md), [WRITEUP.md](WRITEUP.md).

| Area | Evidence present | Assessment |
|---|---|---|
| Problem definition | Unseen-patient N/S/V heartbeat classification, with a Holter-review use case | Clear research task; clinical workflow benefit remains hypothetical |
| Dataset and splitting | DS1 training; ds2s removes record 202, which shares a subject with training record 201 | Strong and necessary methodological choice |
| Classical comparator | ESN, 30 configurations, common input/readout, five final seeds | Good architecture-matched comparator; insufficient evidence of a strong task-level baseline |
| Quantum implementation | Ten-qubit statevector simulation, 1,024-shot measurements, 220 reservoir features | Functional simulated quantum model; no device evidence |
| Controls | Mean-field, uncoupled circuit, RR-only, reduced-data refits, regularization checks | Valuable evidence, including evidence against the hoped-for attribution |
| Evaluation | Cluster/seed bootstrap, prespecified primary and slice rules, access ledgers | Substantial rigor; finite dataset and post-result development limits still apply |
| Reproduction | Locked environment, scripts, historical clean-build reports, matching prediction hashes | Strong existing evidence; release workflow needs consolidation |
| External confirmation | SVDB prepared; no confirmation-access log exists | Not completed |
| Presentation | Draft write-up and a static ECG prediction plot | Demonstration exists; judge-facing narrative and final package are unfinished |
| Submission | Local deadline recorded; submission table empty | Official form, final upload contents, and receipt remain unverified here |

**The numerical results establish a narrow success and several important limits.** Values below come from the saved evaluation outputs and experiment cards, without new test-set scoring. Differences are absolute F1 points, not relative percentage improvements.

| Comparison | Result | What can be concluded |
|---|---|---|
| QRC E003 vs ESN E002, primary macro-F1 | 0.7273 vs 0.7065; delta +0.0208, 95% CI [-0.0157, +0.0617] | Fails the prespecified favorable-result rule because the interval includes zero |
| V-F1, prespecified slice | 0.874 vs 0.805; delta +0.0688, 98.75% CI [+0.0207, +0.1543] | A supported V-class improvement against this ESN within the four-member slice family |
| S-F1, prespecified slice | 0.347 vs 0.370; delta -0.0231, 98.75% CI [-0.1456, +0.0978] | No detectable change; point estimate is worse |
| QRC vs mean-field E004 | 0.7273 vs 0.7234; delta +0.0039, 95% CI [-0.0028, +0.0115] | No demonstrated additional accuracy benefit from the full quantum simulation |
| Uncoupled E005 vs QRC | Macro-F1 delta -0.0009; V-F1 delta -0.0634, descriptive 95% CI [-0.1321, -0.0210] | Coupling affects the class trade-off; it does not establish an overall or quantum-specific benefit |
| RR-only E006 | Macro-F1 0.6997; S-F1 0.390 | Much of the predictive performance is already available from classical rhythm features |
| Five-patient readout refit | QRC-minus-ESN delta -0.0086 | No evidence of a low-data advantage |
| Eleven-patient readout refit | QRC-minus-ESN delta -0.0308 | No evidence of a low-data advantage |

Sources: [headline table](runs/tables/headline_ds2s.md), [mean-field comparison](runs/tables/secondary_E003_vs_E004_ds2s.md), [uncoupled comparison](runs/tables/secondary_E005_vs_E003_ds2s.md), [five-patient comparison](runs/tables/lowdata_k5_ds2s.md), [eleven-patient comparison](runs/tables/lowdata_k11_ds2s.md), [experiment index](EXPERIMENTS.md).

The positive leave-one-record-out deltas are reassuring about sensitivity to deleting one record. They do not supersede the primary confidence interval. Likewise, a favorable prespecified V slice is a legitimate result, but cannot retrospectively become a successful primary macro-F1 test.

**Several strengths deserve to survive every revision.** The project separates patients rather than randomly splitting correlated beats; excludes the documented 201/202 subject overlap; fits preprocessing/readouts on training data; matches input encoding, readout size, and declared tuning effort; reports uncertainty at the record and seed levels; and exposes the negative controls instead of hiding them. The regularization-grid extension also addresses a concrete baseline-fairness concern. The physical data source independently confirms that records 201 and 202 belong to the same subject. [PhysioNet MIT-BIH description](https://physionet.org/content/mitdb/1.0.0/).

These strengths are relevant to known weaknesses in the field. Bowles and colleagues found ordinary classical models competitive or superior across their benchmark and found that removing entanglement often did not harm performance. Pandey's small-system reservoir study similarly found that careful classical matching removed the apparent advantages in its examples. These are specific studies, not universal impossibility results; the project is right to take their benchmarking lessons seriously. [Bowles et al.](https://arxiv.org/abs/2403.07059), [Pandey](https://arxiv.org/abs/2607.09905).

**The goals need to become more demanding in the dimensions that matter to a judge.** The following is an aspirational standard for this project, not an invented official rubric.

| Current goal or implied promise | What a compelling submission would establish | Present gap |
|---|---|---|
| Compare a QRC fairly with an ESN | A practically meaningful, robust gain against the matched comparator, with context from strong classical alternatives | Primary comparison inconclusive; no strong non-reservoir comparison |
| Address unseen-patient generalization | A frozen model pair that transfers to a second dataset, with patient-level failure analysis | SVDB confirmation absent; one test patient dominates S beats |
| Make quantum integration purposeful | An experimentally supported mechanism or resource benefit that survives the relevant classical controls | Mean-field reproduces nearly all observed performance |
| Reduce review burden | Fewer false flags at a justified sensitivity target, or a clearly favorable clinical trade-off | Fewer flags accompany substantially more missed ectopic beats |
| Offer a training-free reservoir | An accurate description of what remains trained/tuned, plus measured inference/training resources | Reservoir weights are fixed, but the pipeline has supervised readout training and model selection |
| Demonstrate hardware feasibility | Representative circuits, shots, noise, feature/prediction fidelity, runtime and cost | Simulation only; no resource-quality trade-off measured |
| Produce a reproducible codebase | A portable frozen release, quick inspection path, and commands covering every central claim | Main reproduction command covers headline arms, not the complete control/analysis story |
| Show depth through many experiments | A compact chain of experiments that resolves the most important uncertainty | Backlog rewards breadth and internal scores more directly than clinical or quantum utility |

**The primary competitive blocker is the absence of demonstrated quantum-specific value.** Equal feature counts and equal numbers of configurations make the ESN comparison useful. They do not imply equal expressivity, equal optimization difficulty, or competitiveness with the best ordinary classifier on these inputs. The mean-field result makes this especially consequential: even without its own tuning budget, the classical approximation is within 0.0039 macro-F1 of the QRC.

A winner-level empirical claim need not prove exponential speedup or outperform every possible classical model. It should survive the obvious substitutes: a direct morphology-plus-RR linear readout, one suitable nonlinear classical model, and the existing mean-field control. A future comparison could use a DS1-tuned RBF SVM or tree-based model with a declared budget; a compact temporal model is another option if resources permit. The matched ESN should remain the original primary comparator. Additional models would provide explicitly secondary context, with selection based on DS1 and exposure disclosed.

The current rationale also stops one step short of the mechanism it needs. Avoiding quantum gradient training addresses training complexity, but both the ESN and mean-field reservoir already have fixed feature maps. It does not explain why this quantum circuit should generalize better between patients. Patient-relative morphology is a more direct response to that problem, and it is a shared classical preprocessing step. A useful next mechanism study would ask whether the discriminative structure comes from nonlinear classical feature expansion, pairwise products, the rhythm block, or genuinely nonclassical correlations.

**The clinical objective is not yet demonstrated by the chosen operating point.** On ds2s, the saved summary reports:

| Quantity per hour of recording | ESN | QRC | QRC-minus-ESN |
|---|---:|---:|---:|
| All S-or-V flags | 806 | 608 | -198 |
| Normal beats flagged | 374 | 217 | -157 |
| Missed ectopic beats | 57 | 93 | +36 |
| S sensitivity | 59.5% | 42.1% | -17.4 percentage points |
| V sensitivity | 95.3% | 94.9% | -0.4 percentage points |

These are seed-averaged descriptive values rounded in the [headline table](runs/tables/headline_ds2s.md), not estimates of minutes saved or patient outcomes. Reducing review flags by roughly one quarter is attractive, but the observed missed-ectopic rate is roughly 63% higher. The project has not established that this is an acceptable exchange. It must not market the flag reduction alone as clinical improvement.

A stronger future objective would compare false flags at a prospectively justified sensitivity target, or sensitivity at a fixed review budget, with the operating-point procedure fitted on DS1. The current primary metric should remain unchanged. Any new trade-off analysis should be labeled exploratory unless a new prospective evaluation is established. Calibration, an uncertain/abstain state, episode grouping, and actual reviewer time measurements would improve the workflow argument, but are not prerequisites for submitting an honest research prototype.

**The data support a benchmark claim with limited clinical reach.** The primary test has 47,129 scored beats but only 21 records. Many beats do not substitute for many independent patients. The existing A015 counts put 1,381 of 1,781 ds2s S beats in record 232: about 77.5%. The write-up's 75% appears to retain the less strict DS2 denominator. Report the exact denominator and retain the sensitivity analysis. Neither exclusion of 232 nor a different summary should be used to erase the observed failure on that patient. [ANOMALIES.md](ANOMALIES.md), [WRITEUP.md](WRITEUP.md).

MIT-BIH is a historical, deliberately enriched benchmark, not a representative contemporary wearable population. Its provenance supports studying classification; it does not support extrapolating the reported flags/hour to deployment prevalence. PhysioNet explicitly cautions against that population interpretation. [MIT-BIH provenance and usage notes](https://physionet.org/content/mitdb/1.0.0/).

The pipeline also receives expert-annotated beat positions. `beats_for_record()` reads annotation locations, and the demo consumes the released positions rather than detecting R peaks from raw ECG. This is a valid conditional beat-classification task, but it leaves detector errors and missed beats outside the evaluation. The decision boundary allows one-beat lookahead, with latency at least one second and sometimes longer; it is not an immediate alarm system. Noise, lead changes, calibration, patient subgroups, and operational failures remain untested. The present deliverable should describe an offline/latency-tolerant classification prototype. [units.py](src/qhc/units.py), [features.py](src/qhc/pipe/features.py), [demo.py](src/qhc/pipe/demo.py), [EVAL.md](EVAL.md).

SVDB is the most valuable remaining generalization check, but should be described accurately. It supplies 78 half-hour records selected to supplement supraventricular-arrhythmia examples. A positive result there would strengthen transfer evidence, while leaving modern-device validation and the project's unresolved subject-overlap question open. It cannot make the already inconclusive ds2s primary test significant. [SVDB source](https://physionet.org/content/svdb/1.0.0/), [confirmation policy](EVAL.md).

**Statistical rigor is strong, but some interpretations need tightening.**

- A CI crossing zero establishes neither equality nor equivalence. Say that the mean-field control achieves closely similar performance and that no added quantum benefit was detected. A claim of equivalence requires a justified margin and an appropriate test.
- QRC and mean-field V-F1 both round to 0.874, but their saved difference is -0.0001, with descriptive 95% CI [-0.0155, +0.0166]. They are not numerically identical. The uncertainty also limits any categorical statement that quantum correlations make no contribution whatsoever.
- The uncoupled control supports a class-level role for coupling in this configuration. Its macro-F1 is essentially unchanged and S-F1 has a higher point estimate. Thus coupling changes the class trade-off; it does not unambiguously improve all aspects of the task.
- The five-/eleven-patient experiments reuse hyperparameters selected with all DS1 patients. They measure reduced-data readout refitting conditional on those selections, not a complete learning procedure developed using only five or eleven patients. They also use fixed subsets rather than estimating variability across multiple patient subsets. [run.py, `cmd_lowdata`](src/qhc/pipe/run.py).
- The primary and four-member slice family have prespecified inference. The mean-field and uncoupled analyses are secondary/descriptive. Preserve that distinction when discussing their confidence intervals.
- Seven post-approval test scorings and a cap of fifteen are workflow controls, not a statistical guarantee against adaptive selection. Any new model choices informed by the seen ds2s results must be disclosed. The original headline must remain visible.
- The reported intervals concern this fixed training set, selected configurations, test records, and final seeds. They do not include all uncertainty from choosing a new training cohort or repeating the entire model-search process.

**Hardware feasibility is currently a promise, and the resource arithmetic matters.** The selected circuit uses four readout snapshots and 1,024 shots per snapshot: 4,096 circuit shots per beat. A straightforward QPU implementation would execute approximately 194.7 million shots for all 47,523 ds2s prediction rows, for one reservoir seed. At an illustrative 100,000 beats/day, that becomes 409.6 million shots and 400,000 logical snapshot circuits. These are arithmetic extrapolations from the implementation, not measured runtime or billing estimates. [reservoirs.py](src/qhc/pipe/reservoirs.py).

With the selected depth-two ten-qubit ring, the longest snapshot contains 80 logical ZZ interactions before native-gate compilation. Replaying the four prefixes entails 200 logical ZZ interactions across the four circuits per beat. Actual device costs depend on connectivity, compilation, batching, queueing, and shot execution; none has been established here. Eliminating parameter-shift training helps, but does not make inference intrinsically cheap. The current ten-qubit simulation has only 1,024 state amplitudes, so it supplies no computational advantage demonstration.

A useful hardware subset would preserve the actual circuit and readout, declare how beats were selected, compare measured features and predictions with simulation, report compilation and noise assumptions, and include full execution cost/latency. If independent copies are packed across a device, the exact placements and crosstalk assumptions need validation. A small selected subset is a feasibility experiment, not another reliable clinical-performance test. A QPU run cannot reverse the mean-field attribution result.

Consequently, hardware should remain optional for this deadline. The internal scorecard's reward for a Braket run is not sufficient reason to prioritize it over external confirmation and submission completion. Claims about low-power wearables, speed, or energy need measurements or should remain explicitly prospective.

**Code and release review found concrete issues beyond the already logged scientific limitations.** These findings do not invalidate the existing ds2s headline. They identify what should be checked or corrected before extending the claims.

| Finding | Evidence and scope | Recommended action |
|---|---|---|
| SVDB batch/demo shot keys use different sample coordinates | `build_split()` preserves native-sample beat IDs while resampling the signal; `keys_of()` hashes those IDs. `pipeline_fn()` instead builds IDs from the resampled positions passed by the demo. At 128-to-360 Hz, a native sample of 1280 becomes 3600, changing the finite-shot stream | Pass canonical beat IDs/native sample coordinates through both paths; compare batch and per-record predictions on label-free inputs before presenting an SVDB demo |
| Saved model loading is not fully self-contained | `load_artifact()` restores the readout, but regenerates the reservoir from configuration/seed, does not restore saved `res_*` arrays, and does not pass the saved shot count; the global default is used | Restore stored state and shot settings, or validate them and reject incompatible artifacts; this becomes material during shot sweeps or implementation changes |
| Automated suite concentrates on evaluation | The 43 cases are in `tests/test_scorer.py`; earlier simulator/readout validation is recorded in separate probes/reviews | Promote a small set of meaningful physics/readout and batch-invariance checks into the maintained suite if the implementation will change |
| Full scientific story lacks one reproduction entry point | `scripts/reproduce.py` rebuilds E002/E003 and the headline table; it does not recreate E004-E011, all central controls, or the demo | Provide explicit commands or a release manifest covering every central result; keep expensive runs separate from a quick inspection route |
| Fresh-run and audit modes need clearer packaging | `--check` needs the existing ledger and EV2 comparison JSON but refuses directories containing E002/E003 tuning outputs. A normal fresh run needs an appropriate fresh ledger | Document exactly which immutable reference files an audit copy needs; never tell a reviewer to delete the authoritative experiment history |
| Documentation overstates verification scope | WRITEUP says the critic reproduced predictions from a clean environment. V004 says the critic reran in the project venv and read the coordinator's separate clean-environment evidence | Attribute the two checks separately and preserve their actual scope |
| Preprocessing description has drifted | PROBLEM_BRIEF says band-pass filtering; current `load_signal()` performs loading, channel selection, nonfinite replacement and resampling, with no explicit band-pass stage | Describe the actual implemented pipeline; do not add preprocessing after the fact and treat old scores as unchanged |
| Portable release remains unproven | No Git repository is present; instructions mix Windows paths with shell continuation syntax; CUDA-pinned installation is documented more strongly than a tested CPU path | Ship a versioned, checksummed archive or repository with OS-specific commands, expected runtime, and a tested lightweight inspection/demo path |
| Public-facing package is incomplete | Draft placeholders remain; no final presentation or upload receipt was found in the inspected project files; code license is not stated in package metadata | Finish the write-up, provide a short presentation and evidence index, specify code/data attribution, and record submission receipt |

Sources: [run.py](src/qhc/pipe/run.py), [features.py](src/qhc/pipe/features.py), [reproduce.py](scripts/reproduce.py), [tests](tests/test_scorer.py), [VERIFICATIONS.md](VERIFICATIONS.md), [pyproject.toml](pyproject.toml).

The shot-key issue was additionally checked with a synthetic, label-free input using the selected QRC configuration: changing only the ID from native-coordinate `svdb:synthetic:1280` to resampled-coordinate `svdb:synthetic:3600` changed 210 of 220 feature values, with maximum absolute difference 0.09765625. This demonstrates the numerical consequence of the different keys. I did not test an actual SVDB patient's classification or measure its accuracy impact. The existing MIT-BIH headline uses the native 360 Hz rate and is not implicated by this resampling mismatch.

**The documentation needs a precise claim pass.** Alongside the table above, the following wording corrections would materially improve credibility:

| Current wording or implication | Better-supported wording |
|---|---|
| Quantum correlations do not contribute; mean-field is equivalent | No additional benefit from the full quantum model was detected against the mean-field control on this benchmark |
| Identical V-F1 | V-F1 values both round to 0.874; the saved difference is -0.0001 |
| Quantum improvement in healthcare performance | Prespecified V-F1 improvement against the matched ESN; primary macro-F1 inconclusive; clinical utility not established |
| Fewer alarms means less clinical work | Fewer beat flags at this operating point, accompanied by more missed ectopic beats; review time was not measured |
| Training-free model | Fixed reservoir with a supervised, tuned classical readout |
| Cheap forward pass / low-power wearable suitability | Four measured snapshot circuits per beat; hardware cost, latency and power remain unmeasured |
| No published quantum model beats a carefully matched model on real clinical data | The reviewed evidence does not establish a dependable quantum benefit; describe the actual search scope and date |

The last correction matters because the broad literature statement in PROBLEM_BRIEF exceeds what a finite search establishes. Gupta and colleagues' review found insufficient consistent evidence of performance benefits, scalability, and robustness; that is a more defensible claim than a universal statement about every published result. [Gupta et al. systematic review](https://www.nature.com/articles/s41746-025-01597-z).

One bibliographic correction is also concrete: WRITEUP identifies Greenwald's 1990 work as an MS thesis with a different title. PhysioNet identifies it as a Ph.D. thesis, *Improved detection and classification of arrhythmias in noise-corrupted electrocardiograms using contextual information*. Use the dataset provider's citation. [SVDB citation](https://physionet.org/content/svdb/1.0.0/).

**The submission story is currently more legible to an internal reviewer than to a competition judge.** The existing ECG PNG is readable and shows predictions clearly, but it presents only QRC outputs for one short interval. It cannot show that the system improves a clinical decision or that quantum processing caused a benefit. The many experiment IDs and verification phases provide traceability, but impose navigation work on a judge.

A finished presentation should make five points quickly: the unseen-patient task; the precisely matched experiment; the primary and V-class results together; the mean-field attribution finding; and the workload/missed-beat trade-off with external confirmation status. Put the main comparison and its control on the same figure. Include a representative success and failure example, with ground truth and comparator predictions only where permitted by the established data-access policy. Use a brief recorded walkthrough or reliable local demo, not a large new application. Keep the technical audit trail in an appendix. These are presentation recommendations, not additional official deliverables.

**The internal scorecard is useful for tracking completion but misleads if treated as the prize objective.** Its latest self-rating is Performance 2, Ingenuity 2, Depth 1, Soundness 2, with both completion gates awaiting final critic assessment. That is a fair description against its own anchors. It is not an official score, and V004's PASS covers baseline validity rather than a verified quantum improvement. [latest self-rating](runs/phase3/scorecard_selfrating_2026-10-26_2355.md), [V004 report](VERIFICATIONS.md).

The strategic problem is that the plan treats “Depth 1 is lowest” as the strongest reason to run more quantum diagnostics. A judge can still reject the value proposition after every depth box is filled: the primary endpoint is inconclusive, mean-field reproduces the gain, and clinical trade-offs remain unresolved. Optimize remaining effort for those unanswered questions and a complete delivery. The existing controls are a scientific achievement even though they weaken the original quantum-benefit story.

**The time plan must be reset immediately.** The supplied deadline is 28 October at 23:59 UAE. At this review's approximately 18:00 timestamp, about six hours remain, assuming no organizer extension. STATE's “48.1 h remaining,” 27 October checkpoints, and untouched 15:30 reserve are obsolete. The official form and any later announcements were not verified in this workspace; the supplied brief remains the authority available for this review.

The following sequence is realistic submission triage, with effort estimates rather than promises. It preserves the original experiment and does not assume a new positive result can be manufactured tonight.

| Priority | Action | Completion condition | Approximate effort |
|---|---|---|---|
| P0 | Verify the official submission instructions; freeze the current claim and artifact list | Upload format, required fields, deadline and a local release destination recorded | 15-30 min |
| P0 | Replace draft claims/placeholders and correct verification scope | A complete, internally consistent write-up with no implied overall or quantum-specific win | 45-75 min |
| P0 | Run the planned frozen-pair SVDB confirmation under the existing policy, after label-free pipeline preflight | An immutable report, access log, all class metrics, and honest interpretation whatever the sign | 60-120 min, dependent on compute |
| P0 | Make the saved results easy to inspect and reproduce | Evidence index, working commands, compact result figures/demo, preserved checksums | 45-75 min |
| P0 | Package, verify links/files, upload, and capture receipt | An actual submitted artifact and receipt | Protect at least the final 60-90 min |
| P1 | Add one strong classical contextual comparison only if it fits without threatening P0 work | DS1-only selection, fixed budget, all results labeled secondary, no primary replacement | Scope-dependent; stop if completion becomes uncertain |
| P2 | Small shot/noise diagnostic with a frozen configuration | A clearly labeled resource/robustness result | Optional; no broad sweep |
| Defer | New architecture search, dataset pivot, elaborate UI, broad qubit sweep, unprepared paid hardware run | Follow-up research plan | Beyond this submission window |

Do not postpone upload until the deadline to complete an optional experiment. If external confirmation fails operationally or scientifically, submit the honest limitation and available evidence rather than tuning on SVDB or concealing the failure. This review has not consumed the confirmation set or authorized new paid tasks.

**A longer research continuation would need a different success ladder.** First establish a clinically interpretable operating point and a strong classical baseline suite. Then identify a quantum contribution that survives mean-field and simple nonlinear controls. Next freeze the procedure and validate on additional independent patients/devices, with detector and signal-quality effects included where relevant. Finally measure the hardware cost/accuracy trade-off. Each stage should have a stop rule: if a cheaper classical method supplies the same utility, it becomes the practical recommendation while the quantum result remains an informative research finding.

The most defensible submission narrative available now is: *“We built a reproducible inter-patient ECG benchmark with matched quantum and classical reservoirs. A quantum-circuit feature map improved ventricular F1 against the ESN, but overall improvement was inconclusive and a classical mean-field model reproduced nearly all of the performance. We identify the operating-point trade-off and the limits of quantum attribution.”* Add the actual SVDB outcome if it is completed. This can be a strong, honest scientific entry. Whether that earns a prize depends on the judges and competing submissions; the current record does not justify describing it as a demonstrated quantum healthcare breakthrough.

**Review evidence and limits.** I read the competition brief, current state, problem/evaluation specifications, experiment and anomaly records, write-up, verification reports, saved comparison tables/JSON, reproduction scripts, and the feature/reservoir/readout/training/demo code. I inspected the existing demo image and checked selected primary research and dataset sources online. I did not run a new model search, rerun the full clean download/training pipeline, score a real test set, access SVDB confirmation labels, submit a QPU task, or change the evaluation/model code.

Checks performed during this review:

- Existing test suite: **43 passed, 3 deprecation warnings in 31.77 seconds**, using `.venv\Scripts\python.exe -B -m pytest -q -p no:cacheprovider --basetemp runs/progress_review_20261028/pytest_tmp`. An initial invocation had 11 setup errors because this review's temporary parent directory had not been created; creating that directory resolved them. This was a review-runner setup error, not an application defect.
- Evaluation revision recomputed as `8501643023cd2eb6`; pipeline revision as `55884b1fb66732b9`, matching the relevant recorded EV2/reproduction evidence.
- All **10/10** headline prediction-file SHA256 values match the logged original headline inputs. This validates artifact identity, not a fresh independent model reproduction.
- Both original tuning logs contain 30 configurations. The recorded selections are ESN configuration 28 and QRC configuration 15, consistent with the documentation.
- The evaluation ledger contains 12 entries including pre-approval references; the project records seven post-approval test scorings. The ledger SHA256 remained `5c1a366ed8c1f962598908f9eff7700f86b8ddb825de8ab79cc9b9b68baf9c15` across the inspected checks. No confirmation-access log exists.
- The synthetic resampled-key probe described above used generated inputs only.

Historical clean-environment evidence is recorded in [clean_build_EV2.md](runs/phase3/clean_build_EV2.md) and [reproduce_check_EV2.md](runs/phase3/reproduce_check_EV2.md). The latter ran the training/reproduction command with `--skip-data --check`; the fresh download/units build was tested separately. That is good cumulative evidence, with a narrower scope than a freshly audited, single uninterrupted end-to-end release run.

The report's priorities and aspirational winning standard are reviewer judgments. Missing items mean no supporting artifact was found in the inspected project, not proof that no team member has done work elsewhere. The numerical findings above trace to the saved artifacts; new experiments and official submission actions remain separate work.
