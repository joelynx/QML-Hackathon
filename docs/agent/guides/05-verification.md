# Phase 5: Verification (Critic Agent)

Run this in a separate context from the agent that produced the result.

## Input: the verification packet
You receive a packet, normally `runs/E###/packet.md`, written by the generator from its card's factual fields or assembled from those fields by the coordinator, and handed to you by the coordinator. It contains only facts:
- Experiment ID, candidate revision and artifact paths, the comparison baseline's revision and artifacts (normally the incumbent, sometimes a pending parent), and any component parents.
- Evaluation version, `EVAL.md`, `PROBLEM_BRIEF.md`.
- Exact commands, environment or lock file, configuration, data and split IDs, seeds.
- Raw results for candidate and incumbent on matched units, and the claimed delta.
- The precise claim under review, e.g. "E014 improves the full evaluation over incumbent E009 by the stated delta under EV2".
- Number of variants attempted in this line of work, the total number of full evaluations run on the current evaluation version (from `STATE.md`), and the confirmation-set access history.
- Segment results and any relevant anomaly observations as facts (slice, size, magnitude), without interpretation.
- In open mode: the anchored scorecard, the baseline and candidate deliverable builds (demo, pitch or writeup draft), and the data card. The generator's self-rating is in a separate file, `packet-selfrating.md`, which you open only after writing down your own rating.

Don't read `IDEAS.md`, the generator's hypothesis, or its notes. A persuasive explanation makes it easier to miss a bug. If the packet lacks something you need, the verdict is NEEDS-MORE naming the missing item; don't go looking for it in the generator's files.

## Goal
Answer two separate questions and record them separately:
1. Are the implementation and its evaluation valid (no leakage, correct metric, valid outputs)?
2. Is the improvement claim supported under the comparison procedure in `EVAL.md`?

Valid code can produce an inconclusive gain. A score increase does not establish valid code. Treat the claim as unproven, look for concrete defects, and give a clear verdict rather than open-ended doubt.

## Checks
Mark each as **pass**, **fail**, **n/a (reason)**, or **not run**. Work in order. A confirmed defect may justify stopping early, with the remaining checks marked not run.

1. **Reproduce.** Rerun the candidate's full pipeline from a clean state on the identified revision: training or inference, then the evaluation command. Scoring an existing predictions file only proves the scorer is deterministic. If retraining is beyond the verification budget, regenerate predictions from the recorded artifacts and state that limit in the verdict scope. Does the result match the packet within the stated tolerance?
2. **Comparison.** From the matched-unit results, compute the signed delta and uncertainty as `EVAL.md` specifies. Does it meet the decision rule? Rerun the incumbent too if its results aren't in the packet.
3. **Leakage.** Does any feature, parameter, or decision use information unavailable at decision time per the brief? Check target leakage, test data in training or tuning, shared groups across the split, and statistics computed on the full dataset. For a blend or stack, check that the out-of-fold predictions used to fit it come from the same split as the evaluation and that no component is scored on a fold it trained on.
4. **Lookahead.** For time-ordered problems: does anything use future data, including through resampling, normalisation, or fill logic?
5. **Metric and selection.** Does the reported score come from the approved evaluation, and was the choice among complete candidates made with it on the right data? Documented internal heuristics (a training loss, early stopping on a smooth surrogate, checkpoint choice by a proxy) are acceptable when the resulting candidate is then compared through the approved evaluation. Reject if the reported score is the surrogate, or if the choice among complete candidates used something other than the approved evaluation.
6. **Validity.** Would every output pass the official validator and constraints, including resource limits? In open mode, also: the data card is complete, the raw download hash matches, and the licence allows this use under the rules.
7. **Robustness.** Does the gain hold across segments, or come from a few units? If concentrated, is that consistent with the anomaly facts in the packet, or suspicious? This check costs nothing and runs before the confirmation set is touched.
8. **Selection exposure.** Given the variants attempted in this line and the total full evaluations on this version, is the gain consistent with selection on the validation units? Apply the confirmation policy from `EVAL.md` (confirmation set, fresh scenarios, or the documented alternative) and log the access at the moment it happens, whatever the eventual verdict. Fresh training seeds on the same validation examples do not address this. For a rubric-only claim this check is n/a; say so.
9. **Blind rubric rating (open mode).** From `packet.md` alone, rate the baseline and candidate deliverables on every scorecard criterion against the anchors, and write the ratings into your report. Only then open `packet-selfrating.md` and record the generator's ratings and the gap per criterion. The claim is supported when both raters moved the same way on the claimed criteria; opposite movements on different criteria are decided by the scorecard's tradeoff rule. Ratings are against the anchors, never relative to a previous critic.
10. **Claims check (open mode).** Every number and claim in the pitch or writeup points to an experiment ID or a source in the brief. List the ones that don't.

## Verdict rule
- **PASS:** every applicable check passed on the identified artifact, and the claim is supported.
- **FAIL:** a confirmed defect in the implementation or evaluation, or the comparison contradicts the claim. Name the defect and its location.
- **NEEDS-MORE:** any applicable check is unresolved, or a required input is missing. Name the single most informative next test or the missing item.

A valid implementation with an unsupported gain is NEEDS-MORE or FAIL on the claim, with the validity checks recorded as passed so that work isn't repeated.

For a validity-only report (R0) the improvement question is n/a and PASS means the validity checks passed. A PASS supports the recorded claim against its comparison baseline; whether the candidate replaces the current incumbent is the coordinator's promotion decision under core invariant 3.

## Output
Write a report in `VERIFICATIONS.md` as `V###` using the template. The coordinator links it from the experiment card and sets the experiment's verification field. If the defect is in the evaluation itself, say so explicitly; that triggers the evaluation recovery rule in the core instructions.

## After the verdict
- **Every verdict:** the coordinator sets the experiment's verification field and links the report, removes the experiment from the pending list in `STATE.md` (or keeps it there for NEEDS-MORE), and records any confirmation-set access in `EVAL.md` and the reuse line in `STATE.md` at the moment it happened, whatever the verdict.
- **PASS that promotes** (the comparison was against the current incumbent, or the human authorized a tradeoff): additionally, in this order, the candidate's card and index row in `EXPERIMENTS.md` (adoption incumbent); the previous incumbent's card and row (adoption superseded, or pooled if kept for an ensemble); the parent idea in `IDEAS.md` (promoted); `STATE.md` (incumbent, previous incumbent, full-evaluation count). A PASS that doesn't promote leaves adoption as candidate.
- **FAIL:** the defect goes back to the implementer as a concrete item. The fix is a new candidate revision and a new experiment, verified again. The original card and report are preserved.
- **NEEDS-MORE:** the named test or missing item is supplied, then verification resumes on the same report (appended, not rewritten).

## Other critic tasks (open mode)
Two more requests arrive in a fresh context and are answered as reports in `VERIFICATIONS.md` with verdict n/a:
- **Metric review**, before the evaluation is approved: given the chosen problem, the user's decision, and the proposed technical metric, does any choice in the metric, split, or units flatter a particular approach or hide an error the user would care about? Name the alternatives considered and what each would change.
- **Rehearsal**, a readiness check before delivery and not a confirmation of the rubric: given the packet, the scorecard, and the anomaly facts, write the ten hardest questions a judge would ask. Prefer questions about evidence, data provenance, and what breaks, over questions about ambition.

## Done when
Every check has a mark, both questions are answered, and a verdict with evidence is recorded.

## Avoid
- Fixing the code yourself. Report the defect; fixing it in the same context mixes roles.
- Vague doubt without a concrete check. Every concern should map to a test or a specific line of code.
- Issuing PASS because the checks you ran passed. Unrun applicable checks mean NEEDS-MORE.
