# Current state

Read this first in every session. Update it last.

- **Updated:** 2026-10-28 21:10 UAE. **Phase 4 complete; Phase 5 V005 PASS (validity and claim set, after one repair cycle); Phase 6: package committed and pushed to the public repository `joelynx/QML-Hackathon` (see Submissions); the human submits the link through the official form.**
- **Session 2026-10-28 21:15-21:50 (presentation; the human asked to make the presentation "really good": README strengths, novelties and the Braket simulations, plus an easy-reading PDF in the style of `NSSC_Solution_Description.pdf`):**
  - **README:** tagline, PDF link, pipeline figure, new "Highlights" (At a glance, Strengths, What is new, Amazon Braket: simulations and real hardware); Section 6.6 expanded with the Braket LocalSimulator validation (`runs/E019/validation/localsim_report.json`, `runs/E019/summary.json`); forest and shots/noise figures in Sections 5 and 6.3; figure and PDF build commands in Sections 9-10; Section 3 cost line qualified "without beat packing". No result or claim of the V005-verified sections was changed otherwise.
  - **New files:** `QML_Hackathon_Solution_Description.pdf` (22 pages) built from `docs/report/report.html` by `scripts/build_report.py` (headless Chrome or Edge; no LaTeX on this machine, and downloading a TeX engine was blocked by the permission classifier); figures `docs/figures/fig_{pipeline,circuit,forest,review_burden,shots_noise,braket}.png` from `scripts/make_report_figures.py` (logged outputs only, no label access; every plotted number cross-checked against the README).
  - **Claim check (not a Phase 5 critic verification; V005 predates these texts):** a reviewer subagent checked the new README text and the report against the artifacts: 21 findings, all applied, PDF rebuilt. The main ones: the 24-beat LocalSimulator run was described as a program-set submit-fetch dry run (it ran each ring separately through `simplan`; the program-set format was checked with 2 executables); "160 CZ per circuit" is per beat snapshot (packed circuits carry up to 5 rings); the summary sentence overstated what SVDB and the QPU showed; "not as entanglement"; "approved before any test scoring" (reference rules were scored earlier); "first model scored" (first non-reference); IQM noise was DS1 only; the bit-order range; Cepheus reports 107 qubits; the cost guard works on estimates.
  - **Not committed or pushed:** awaiting the human's decision (the repository is public and is the submitted link). Optional: team names for the PDF byline (currently none).
- **Session 2026-10-28 18:36 (Phase 4 in parallel with delivery):**
  - **The human's answers at session start:** assumption 6 confirmed: the 6-probes-per-session limit is lifted for this session; 20 min per probe, 3 GPU-h per run and per-task Braket approval stay ("unless you ask me to lift them, which I will review before approving"). **Braket cap USD 35** (replaces USD 90); a cost estimate comes to the human before any task. GitHub: `gh` installed and authenticated. **Experiment freeze 22:00; push by 23:30.**
  - **Cards E012-E019 and their DS1-only selection rules written 18:50, before any run** (EXPERIMENTS.md, "Phase 4 declarations"). New code only in `src/qhc/p4/` (evaluation `8501643023cd2eb6` and pipeline `55884b1fb66732b9` untouched).
  - **Lanes (background subagents):** GPU0 E012/E013/E014; GPU1 E015; CPU A E018 (predict-only path, ds2s hash self-check, SVDB predictions; the coordinator runs the access); CPU B E016; CPU C E017; Braket E019 preparation (free calls only; cost estimate due ~19:20); delivery (README merge, claim pass, limitations, fixes, evidence index, figure, LICENSE, .gitignore). Only the coordinator scores on ds2s/svdb.
  - **Results (20:20):** E012-E017 completed (cards filled). **E018 SVDB confirmation: access 1 of 2 logged 19:29:19, completed 20:01:41: E003 vs E002 −0.0085 [−0.0476, +0.0274], NOT confirmed** (A022). Secondaries (EV2, ds2s): E012 +0.0005; E014-n6 +0.0078; E015-rigetti +0.0016 (V −0.053, CI excludes 0); E003 vs E016 +0.0057 (w/o 232 −0.087; E016 V F1 0.943); E002 vs E016 −0.0151. **E019:** first submission refused (missing Braket service-linked role, no task, USD 0); role created via API with the human's approval; one program-set task completed (est. USD 17.71); hardware features MAD 0.347 vs simulation, class agreement 41.7% (ceiling 87.5%) (A023). Anomalies A019-A023 logged.
  - **README:** merged write-up (delivery lane), slots filled by the coordinator; only `<!-- SLOT:VERIFICATION -->` remains (after V005). `docs/EVIDENCE.md` filled. Repository visibility: **public** (the human, ~19:20).
  - **Critic V005** launched ~20:15 on `runs/V005/packet.md` (self-rating `packet-selfrating.md`): claims check, validity of E018 and the secondaries, blind scorecard incl. a clean-environment + fresh-download reproduction for the reproducible gate.
  - **Verification (Phase 5):** V005 (critic, fresh context, 20:05-21:05): validity of E018 and the Phase 4 results PASS (E018 self-check and SVDB files regenerated byte for byte; 15/15 regenerated ds2s files of E014-n6, E015-rigetti, E016; all 7 logged outcomes match the rule); clean environment + fresh download reproduced the 10 headline files and table byte for byte (27.3 min). Claim set: FAIL (1 inaccurate statement, 2 overstatements) -> repaired -> re-check found 1 wrong number (A015 "four records within ±0.001") + 3 wording items -> repaired -> **PASS**. Blind ratings critic = generator: Performance 2, Ingenuity 3, Depth 3, Soundness 3, both gates 3 (internal ratings). Rehearsal V006 (`runs/V006/rehearsal.md`): ten judge questions; its README flags were applied in the repair cycle.
  - **Repository decisions by the human (~21:00):** AWS account ID redacted from all tracked files (originals in ignored `runs/E019_unredacted/`); repository name "QML Hackathon" -> `QML-Hackathon` (GitHub does not allow spaces); public.
  - **Timeline:** SVDB access not started after 21:45; Braket results by 21:30 or abandoned; freeze 22:00 (unfinished runs logged as aborted); results into README 22:00-22:30; critic (Phase 5) from ~21:30 on the SVDB report and headline claims, then the final README, one repair cycle; push by 23:30; the human submits the link.
- **Current phase:** **Phase 6 (deliver): package pushed and verified; awaiting the human's form submission.** Phase 4 ran 18:45-20:05 on 10-28 in parallel with delivery, authorized by the human. Previously: **reserve window (since 15:30 on 10-28): deliver, with verification (Phases 6 and 5).** **Phase 4 never ran.** No session ran between 10-26 23:55 and 10-28 18:06; no E012+ exists. **The human reinstated it at ~18:20** ("Don't drop the experiments. Use the compute we have to parallelize any tasks and accelerate work."). It runs in the next session, in parallel with delivery, and the reserve pays for it on the human's authorization (see "Next concrete action"). Phase 3 complete (closed 10-26 23:55). **Phase 4 authorized by the human 2026-10-26 ~23:21** ("Finish up phase 3, and moving on to phase 4 is approved."); it starts in a **new session**. Phase 3 was authorized ~18:25. EV1 r5 approved 21:26; headline at 21:27. **EV2 approved 22:14** ("Approved to both.": the D1-D6 guard fixes, and a full clean build with SVDB in a scratch copy). R0 = E002 is the incumbent (V004 PASS).
- **Evaluation:** **EV2 approved** (human, 2026-10-26 22:14 UAE): evaluation code `8501643023cd2eb6`, fixtures `8a0ffb8e64f4f88b` (43 pass). EV2 = EV1 r5 (`9a1922c8898b90db`, approved 21:26, snapshot `runs/EV1_r5_snapshot/`) plus the D1-D6 guard fixes; scorer, units, metric, split and thresholds unchanged. `evalspec.EV` still reads "EV1" (the unit set); outputs are tied to a version by `code_revision`.
- **Phase 3 progress (full results on ds2s under EV1/EV2):**
  - **Headline E003 vs E002:** +0.0208 [-0.0157, +0.0617], no detectable change. The EV2 rerun is identical.
  - **Slice family complete:** V_f1 +0.0688 [+0.0207, +0.1543] favorable; S_f1, lowdata_k5 (E007, -0.0086) and lowdata_k11 (E008, -0.0308) show no detectable change. These are the scorecard Performance anchor 2 conditions, pending the critic's rating.
  - **Controls (EV2 secondary, descriptive):**
    - QRC vs mean-field (E004): +0.0039 [-0.0028, +0.0115].
    - Separable vs QRC (E005): -0.0009; V F1 -0.063 [-0.132, -0.021].
    - RR only (E006): 0.6997.
    - So the V gain is not quantum-specific (A016).
  - **Diagnostics:** E009 (matched λ, DS1); E010/E011 (extended λ: the same selections, so A010 is resolved).
  - **Failure analyses:** technical A009-A012, A015, A016; rubric A013; judge questions A014.
  - **Deliverables:** tables `runs/tables/*.md`; README story with the limitation and literature gap; demo; `scripts/reproduce.py`; pivot-checkpoint report `runs/phase3/pivot_checkpoint_2026-10-27.md`.
  - **Close-out (23:21-23:55):**
    - **Write-up draft `WRITEUP.md`.** It covers the problem, the baseline, the quantum contribution and why, the fair evaluation, the results with experiment IDs, and limitations: A016, A001, A004, the 17:45 SVDB incident, A011, A008 and A006. Its Phase 4 and SVDB sections are marked *to be completed*.
    - **One-command reproduction** (`scripts/reproduce.py --skip-data --check`, fresh venv): exit 0. All 10 headline prediction files match the logged hashes and the headline table is byte-identical. No test-split scoring (`runs/phase3/reproduce_check_EV2.md`).
    - I001-I003 marked passed (run as E004-E006).
    - Self-rating `runs/phase3/scorecard_selfrating_2026-10-26_2355.md`: Depth 1 is the lowest; the conditions of both gates appear met, with the critic check pending (A013).
- **Reference R0:** E002 (ESN; ds2s macro-F1 0.7065 as the headline's baseline arm). **Verified for validity: V004 PASS (22:06).** Reproduces byte-for-byte with pipeline `55884b1fb66732b9` (critic) and `75e043aa9915baf2` (clean environment). Minimal references `const_n` and `rr_rule` rescored under r4 in `runs/EV1_reference_r4/`.
- **Incumbent:** **E002 (R0)**, since 2026-10-26 22:07 (V004 PASS); artifacts `runs/E002/` (final-run pipeline `da67af87f8b8fd73`, evaluation `9a1922c8898b90db`) | **Previous incumbent:** none
- **Deadline:** 2026-10-28 23:59 UAE (UTC+4) | **Verification and final-artifact reserve:** from 2026-10-28 15:30 UAE (~8.5 h); **not untouched: 2 h 36 min of it (15:30-18:06) passed with no work**; about 5.9 h remain at 18:06
- **Budget ledger** (one line per kind that matters: wall-clock, compute, money):
  - Wall-clock: total ~70 h (2026-10-26 01:30 to 2026-10-28 23:59 UAE), of which ~62 h before the reserve | used ~64.6 h (to 18:06 on 10-28) | **remaining ~5.9 h, all inside the reserve** | per-run cap 3 GPU-hours
  - Compute: local workstation (64 cores, 64 GB RAM, 2x RTX 6000 Ada), simulators, no total cap | used ~1.4 GPU-h plus ~1.5 CPU-h of bootstrap scoring (E002-E011, V004, clean builds, the 23:23 reproduction check of 26 min; largest single run ~21 min) | remaining n/a | per-run cap 3 GPU-hours
  - Money (QPU credits): USD 15 cash | used USD 0 | remaining USD 15 | per-job: human approves each job with a cost estimate
  - AWS credit applicable to Amazon Braket: USD 120. The human had to enable "advanced features", so usage beyond the credit is charged to the account. | used **USD 17.71 (estimate; 1 task, 2026-10-28 15:58 UTC; actual billing to be checked)** | spending cap **USD 35** (set by the human 2026-10-28 18:36; replaces the USD 90 cap of 2026-10-26) | remaining under cap USD 17.29 | per-task: human approves each task with a cost estimate
- **Full evaluations run on current EV#:** cumulative test-split scorings **13 of 15** (2026-10-28: SVDB confirmation logged 19:29:19 + 5 secondaries logged 19:29:53-19:31:33, outputs 19:40-19:42; the log's 18 lines = these 13 + 5 reference scorings of 2026-10-26 18:37 that do not count). Earlier: 7 of 15. EV1: 1 (headline, 21:26:59). EV2: 6 (identical headline rerun 22:15:23; secondary E003 vs E004; secondary E005 vs E003; `score` E006; `lowdata_k5` E007; `lowdata_k11` E008, all at 22:16). The planned secondary E011 vs E010 is not needed: the extended grid selected the same configurations, so its inputs are byte-identical to the headline's. `runs/full_eval_log.jsonl` (12 lines) is authoritative.
- **Evaluation-data reuse:** ds2s: minimal references (r3, r4 drafts); the headline pair (EV1 and an identical EV2 rerun); controls E004, E005, E006; low-data refits E007, E008. ds2: minimal references only. SVDB: **confirmation access 1 of 2 (E018, 2026-10-28 19:29:19; completed 20:01:41; not confirmed)**; logged in `runs/confirmation_access.jsonl` and the EVAL.md access log. A full clean build in a scratch copy (approved 22:14) reads SVDB annotations only to write that copy's `confirm/`; the agent does not open it.
- **Pending verification:** none. V005 (final package: E018, E012-E019, README claim set) PASS 2026-10-28 ~21:05; V004 (R0 validity) PASS, 2026-10-26 22:06; V001-V003 earlier.
- **Unresolved defects / evaluation issues:** none known. EV1 defects D1-D6 are fixed in EV2 (EVAL.md). Critic V004 minor findings M3 and M4 fixed; M5 closed: the full clean build with SVDB passes 43/43 fixtures and reproduces all 14 manifest hashes (`runs/phase3/clean_build_EV2.md`); its scratch `confirm/` was deleted unopened.
- **Open decisions for the human:**
  1. AWS Budgets alert on gross usage (the human will set it up later; see Requests).
  2. Open questions in `PROBLEM_BRIEF.md`: judges and organiser page, team size, submission format (submission format resolved ~18:20, item 3).
  3. (resolved ~18:20) Official submission form: **only a GitHub repository link is submitted.** All material goes in the repository, and the written content goes in a README. The rest of the form is team and individual details, which the human fills in.
  4. (resolved ~18:20) Licence: **MIT** for the code; the data stays ODC-By 1.0 with attribution. The repository is on GitHub (see Requests).
  5. (superseded: Phase 4 did not run) Confirm the assumption: the Phase 4 authorization (~23:21) replaces the 09:00 pivot checkpoint as the decision to continue with C1. If the human still wants a 09:00 review, Phase 4 proceeds on simulator-only work until then; none of it is irreversible.
  6. **Assumption to confirm at the start of the next session:** "parallelize any tasks" lifts the probe count limit (6 per session) for that session. The 20 min per probe, 3 GPU-h per run and per-task Braket approval with a cost estimate still apply.
- **Resolved decisions** (exact times not recorded in the conversation; reconstructed from file timestamps where possible):
  - Between 02:15 and 15:50: C1 chosen, C2 runner-up, Phase 2 authorized.
  - ~15:50: SVDB approved as external test data (download started 15:54).
  - ~17:00: Braket spending cap USD 90.
  - ~17:15: AWS credentials created by the human, verified by the agent 17:19.
  - 22:14: **EV2 approved** and a full clean build with SVDB in a scratch copy approved ("Approved to both.").
  - 21:26: **EV1 r5 approved** ("Approved.").
  - 2026-10-28 ~18:20 (the human, after the progress review):
    - "Don't drop the experiments. Use the compute we have to parallelize any tasks and accelerate work."
    - Submission is a GitHub repository link, with the written content in a README.
    - Licence MIT.
    - "Wait till I start the next session."
  - ~23:21: **Phase 4 authorized** ("Finish up phase 3, and moving on to phase 4 is approved."). Read as the pivot-checkpoint decision to **continue with C1**; this reading is an assumption, open decision 3.
  - ~18:25: independent review of EV1 r3 supplied (`EV1_R3_REVIEW.md`, recommendation: revise before approval); Phase 3 authorized; pivot checkpoint **2026-10-27 09:00 UAE confirmed** (the original 20:00 on 10-26 was missed).
- **Pivot checkpoint / runner-up (open mode):**
  - **Outcome (assumption, open decision 3):** passed with a running slice. The human authorized Phase 4 at ~23:21 on 10-26, which is read as the decision to continue with C1.
  - Checkpoint: **2026-10-27 09:00 UAE (confirmed by the human ~18:25 on 10-26; the original 2026-10-26 20:00 was missed)**. About 51% of the pre-reserve window, against the 25-30% default.
  - By then the vertical slice must run end to end: units, DS1 tuning, the matched classical reservoir arm (R0), a first quantum-reservoir arm, and a paired ds2s comparison with record-bootstrap CI.
  - At the checkpoint the human decides whether to continue or pivot.
  - Runner-up: **C2** (TCGA-BRCA data in `runs/data/samples/tcga_brca/`), confirmed by the human.
- **Progress review takeaways (2026-10-28 ~18:15; review supplied by the human; the decisions are the agent's within its rights, and the plan is proposed to the human):**
  - **Adopted.** All the review's factual findings were checked by the agent and hold:
    - the 232 denominator is 1,381 of 1,781 ds2s S units = 77.5% (the write-up says 75%, the DS2 figure);
    - the write-up overstates V004's scope: the critic reran in the project venv and read the coordinator's clean-environment evidence;
    - the Greenwald reference is wrong: PhysioNet lists a Ph.D. thesis, "... noise-corrupted electrocardiograms using contextual information", Harvard-MIT HST, 1990;
    - `PROBLEM_BRIEF.md` says "band-pass filtered", but no digital filter exists;
    - the SVDB shot-key mismatch (A017) and the artifact-loading gap (A018) are real.
  - **Adopted.** The submission narrative is the review's "most defensible narrative": the V-F1 slice gain against the matched ESN, the inconclusive primary, mean-field reproducing nearly all of the performance, the operating-point trade-off, and the SVDB outcome if run.
  - **Adopted.** A claim pass on `WRITEUP.md` and `README.md`:
    - "no added benefit of the full quantum model was detected against mean-field", not "equivalent" or "not from quantum correlations";
    - V-F1 "both round to 0.874; difference -0.0001 [-0.0155, +0.0166]";
    - "fixed reservoir with a supervised, tuned readout", not "training-free";
    - fewer flags come with +36 missed ectopic beats per hour (+63%) and S sensitivity -17.4 points; review time was not measured;
    - the hardware cost is prospective arithmetic: 4 snapshot circuits x 1,024 = 4,096 shots per beat, about 194.7 M shots for ds2s; nothing measured;
    - the literature claim is scoped to our search and its date (Gupta et al. 2025).
  - **New limitations to state:**
    - the task is conditional on reference beat positions (no QRS detector);
    - one-beat lookahead, so offline or latency-tolerant use only;
    - MIT-BIH is an enriched historical benchmark, so the rates per hour are not deployment prevalence;
    - 21 test patients;
    - the low-data refits reuse hyperparameters selected on all of DS1 and use fixed subsets;
    - the intervals are conditional on the fixed training set, the selected configurations and the seeds;
    - no strong non-reservoir classical model. The RR-only readout (0.700) already gives most of the performance.
  - **Overruled by the human (~18:20): the experiments are not dropped.** The agent had proposed dropping them, because the reserve never pays for experiments and the review agreed. The human authorized running them in parallel. They are:
    - the Phase 4 depth axes (I004, I005, I007), I008 and the Braket run (I006);
    - the review's P1, a strong classical context model. It is a post-hoc choice made after the ds2s results, so it is labelled secondary and disclosed;
    - the review's P2, the shot and noise diagnostics (covered by I004 and I005).
    - The review's caution still governs the write-up: these deepen the study, but none of them can turn the inconclusive primary or the mean-field attribution into a quantum-benefit claim.
  - **Kept, with a precondition:** the pre-registered SVDB confirmation of the frozen headline pair E003 vs E002, with a hard stop:
    - the precondition is the A018 predict-only path, whose ds2s hash self-check must reproduce the 10 logged hashes;
    - if the access has not completed by 21:15, the package goes out without it, stating that it was not run;
    - it runs in parallel with the experiments, which never change the frozen pair.
  - **Not adopted now:**
    - fixing A017 (no SVDB demo will be shown);
    - new automated physics tests;
    - extending `reproduce.py` to E004-E011. An evidence index with the per-card commands replaces it.
- **Superseded time plan (UAE time, revised 2026-10-26 17:55; obsolete since Phase 4 did not run):**
  - Phase 2: V001 review, then the human approves EV1, around 19:00-20:00 on 10-26.
  - Phase 3: vertical slice and R0, built overnight, from approval to about 08:00 on 10-27. Phase 3 must be authorized.
  - Pivot checkpoint: 09:00 on 10-27.
  - Phase 4: probes and full experiments, 09:00 on 10-27 to about 12:00 on 10-28.
    - Mid-point review around 20:00 on 10-27.
    - Device-noise simulation in Phase 4.
    - Braket hardware subset (every task approved) by the morning of 10-28.
  - Final pair frozen; ds2s full evaluation and SVDB confirmation by 15:30 on 10-28.
  - Reserve from 15:30: verification (Phase 5), one repair cycle, packaging (Phase 6). The human uploads before 23:59.
- **Running or aborted experiments:** none (all Phase 4 lanes completed before the 22:00 freeze; nothing aborted).
- **Last completed experiment:** E010/E011 (22:31); EV2 scorings of E003-E008 (22:16-22:28). Last completed check: the one-command reproduction (23:23-23:49), not an experiment.
- **Environment:**
  - Project venv `.venv` (Python 3.12.10), with numpy, pandas, wfdb, boto3, pytest, scipy, scikit-learn 1.9.1 and torch 2.11.0+cu128 (CUDA available, 2 GPUs; installed 2026-10-26 ~18:40). Lockfile regenerated without the absolute editable path; install the package with `pip install -e .`.
  - Code layout from r4: evaluation code is top-level `src/qhc/*.py` (its hash is the evaluation revision); pipeline and model code goes in `src/qhc/pipe/` and is hashed separately. Package `qhc` is installed editable from `src/`. Run code with `.venv/Scripts/python -I -m qhc.<module>` from the project root. Lockfile: `requirements-lock.txt`.
  - No git repository yet; revisions are recorded as sha256 of `src/qhc/*.py`. Initializing git is for the human to decide.
  - Raw data, untouched and SHA256-verified: `runs/data/raw/mitdb/` (48 records) and `runs/data/raw/svdb/` (78 records). Processed EV1 units are in `runs/data/processed/EV1/`.
  - Phase 1 samples are in `runs/data/samples/`.
  - Download from the PhysioNet AWS mirror `https://physionet-open.s3.amazonaws.com/`.
  - AWS profile `qhack` (us-west-1) is verified. Use Braket's free LocalSimulator for testing. A code-level device allowlist (Rigetti Cepheus-1-108Q, IQM Garnet), shot cap and cost ledger must exist before any hardware task.
- **Next concrete action (2026-10-28 21:05):** the human submits https://github.com/joelynx/QML-Hackathon through the official form before 23:59 UAE and fills in the team details; then records the receipt under Submissions. Optional before the 10-31 presentation: rehearse with `runs/V006/rehearsal.md`; edit the LICENSE copyright line with the team's names; check the actual Braket charge in AWS Billing. **The plan below is superseded (it was the plan for this session):**
  - **Compute:** 2 GPUs plus 64 cores. Every lane runs as background processes (`CUDA_VISIBLE_DEVICES` per GPU; CPU bootstraps in separate processes). Independent code lanes go to subagents (Agent tool). The coordinator writes the cards, the logs and the README. The Workflow tool only if the human explicitly asks for one.
  - **Test-split budget:** 8 of 15 scorings left. Up to 6 are planned for secondary ds2s comparisons; 2 stay spare. The SVDB confirmation has its own cap of 2.
  - **Rules for every experiment:**
    - its card and its DS1-only selection rule are written before any run (E012 onward);
    - every ds2s comparison is labelled secondary and descriptive;
    - post-hoc choices made after the ds2s results are disclosed;
    - nothing replaces the original headline.
  1. **18:30-18:50, setup:**
     - write the cards and the selection rules;
     - confirm assumption 6 with the human;
     - launch the lanes.
  2. **The lanes, in parallel, 18:50-21:00:**
     - **GPU0:**
       - I004: E003's configuration with exact expectations, then shots {64, 256, 1024, 4096}, on DS1 OOF;
       - I007: qubit count {6, 8, 12} and readout size. K changes, so these are ablations, not matched arms;
       - then a ds2s secondary for the exact-expectation arm and for one qubit-count variant, chosen by the DS1 rule (2 scorings).
     - **GPU1:** I005, a device-noise model of E003's configuration: readout error plus depolarising noise at published Rigetti Cepheus and IQM Garnet rates, by trajectories or a channel approximation. DS1 OOF first, then one ds2s secondary (1 scoring).
     - **CPU A:**
       - the A018 predict-only path;
       - its ds2s hash self-check against the 10 logged hashes;
       - SVDB features and predictions;
       - the confirmation preflight, then the SVDB confirmation (no access started after 21:15).
     - **CPU B:** the review's P1: one strong classical model (an RBF SVM or gradient boosting) on the same features, with a declared DS1 budget, then a ds2s secondary against E003 and E002 (1-2 scorings).
     - **CPU C:** I008: kernel-target alignment or geometric difference between the QRC, mean-field and ESN feature Gram matrices, per DS1 patient (diagnostic; no test labels).
     - **Braket (I006):**
       - a cost estimate goes to the human by about 19:00: 8-16 ds2s beats, 4 snapshot circuits each, several beats packed on disjoint qubits of a device;
       - after approval, the tasks are submitted with a device allowlist, a shot cap and a cost ledger;
       - the hardware features are compared with the simulated ones; this is label-free;
       - if results are not back by about 21:00, it is abandoned and reported.
     - **Agent:**
       - merge `WRITEUP.md` into `README.md` (the form requires the written content in a README);
       - the claim pass and the new limitations ("Progress review takeaways");
       - fix the 232 denominator, the V004 scope and the Greenwald reference;
       - the evidence index and the compact figure;
       - add `LICENSE` (MIT) and its `pyproject.toml` field;
       - `.gitignore`: exclude `runs/data/` (raw MIT-BIH and SVDB, the TCGA samples, which hold a file over 50 MB, and the processed units including `confirm/`), the venvs and `runs/*/pytest_tmp`;
       - `git init`, then the first commit.
  3. **Experiment freeze at 21:00.** Unfinished runs are logged as aborted with their artifact paths.
  4. **21:00-21:45:** the results go into the README, each with its ID and result type.
  5. **Critic verification (Phase 5), 21:00-22:15:**
     - it starts on the SVDB report and the headline claims as soon as they exist;
     - then it checks the final README's claims and both gates;
     - one repair cycle.
  6. **22:15-23:00:** push to the GitHub repository (see Requests). The human submits the link by about 23:15. The final 45 min are protected.
## Requests for the human
Things only the human can obtain: private or gated datasets, accounts and API applications, paywalled papers, purchases, credentials, licences. Filed the moment the need is found, repeated in the session report, never dropped silently. A research tool's manual-acquisition notice is copied here verbatim with its link.

| Date | Request | Blocking / optional | Why it matters | Where / how to obtain | Doing meanwhile | Status |
|---|---|---|---|---|---|---|
| 2026-10-28 | Official submission form: format, fields, file limits | blocking (packaging) | The package format depends on it | The organisers' Submissions panel | n/a | **resolved ~18:20:** a GitHub repository link only; written content in a README; team details in the form |
| 2026-10-28 | Code licence | optional | The package metadata named no licence | The human's choice | n/a | **resolved ~18:20:** MIT |
| 2026-10-28 | A GitHub repository the agent can push to | blocking (submission) | Only the repository link is submitted. `gh` is not installed here; `git` 2.52 is | Either (a) create an empty repository on github.com and give the agent its URL, pushing once with the Git Credential Manager browser sign-in, or (b) install the GitHub CLI and run `! gh auth login`. Public, or private with judge access, depending on what the organisers expect | The next session prepares the local repository (`.gitignore`, `LICENSE`, first commit) so the push is the last step | **resolved 2026-10-28 18:36:** `gh` installed and authenticated by the human; repository visibility to be confirmed before the push |
| 2026-10-26 | QPU access for a small real-hardware run | optional | Shows the quantum component on a QPU, not only in simulation | History: IBM Open Plan was suggested first (free, 10 QPU min / 28 days) but sign-up failed for the human. IQM Resonance Starter was checked as an alternative. Braket prices checked 2026-10-26 on https://aws.amazon.com/braket/pricing/: USD 0.30 per task plus per shot (Rigetti Cepheus 0.000425, IQM Garnet 0.00145, QuEra Aquila 0.01, IonQ Forte 0.08). | Local GPU simulators | **resolved 2026-10-26:** the human has USD 120 of AWS credit applicable to Braket; cap USD 90; every task approved with a cost estimate |
| 2026-10-26 | AWS credentials for Braket as a named profile, never in the repo | optional | Lets the agent submit approved tasks | IAM user `qhack-braket` with `AmazonBraketFullAccess`; access key in `~/.aws/credentials` under `[qhack]` | n/a | **resolved 2026-10-26 ~17:19:** verified with free STS and SearchDevices calls. QPUs ONLINE that day: Rigetti Cepheus-1-108Q (us-west-1), QuEra Aquila (us-east-1), IQM Garnet and IQM Emerald (eu-north-1), AQT IBEX Q1, IonQ Forte 1. Planned allowlist: Rigetti Cepheus-1-108Q (primary), IQM Garnet (secondary); IonQ and AQT blocked in code. |
| 2026-10-26 | AWS Budgets alert on gross usage | optional, strongly advised | With the credit applied the net bill stays at USD 0 until the credit runs out, so a normal alert only fires once the card is being charged | AWS console > Billing and Cost Management > Budgets > monthly cost budget, alerts at about USD 25 / 50 / 85; under advanced options, exclude credits. Also check the credit's expiry date on the Credits page. | Code-level caps and cost ledger (to be built before any hardware task) | open (the human will set it up later) |

## Submissions
| Date | Artifact path | Artifact hash | Revision | EV# | Local score | Official score | Receipt |
|---|---|---|---|---|---|---|---|
| 2026-10-28 20:58 UAE (pushed) | https://github.com/joelynx/QML-Hackathon (public; `main`) | commit `bd1d28b` (package; this STATE line is a later bookkeeping commit) | eval `8501643023cd2eb6`, pipe `55884b1fb66732b9`, p4 modules per V005 | EV2 | headline ds2s +0.0208 [−0.0157, +0.0617] (no detectable change); SVDB −0.0085 [−0.0476, +0.0274] (not confirmed) | n/a (judged) | **ready to submit; the human submits the link through the official form** (fresh clone verified 20:59: 127/127 logged prediction hashes match, 0 manifest mismatches, no label files, no account ID) |
