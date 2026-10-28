# Phase 2: Data and Evaluation (open mode)

## Requires
A chosen problem in `PROBLEM_BRIEF.md` with no unresolved blocking questions. Requests for the human filed in Phase 1 either fulfilled, or worked around with the workaround stated.

## Goal
Data you can defend and an evaluation you can trust, approved before competitive building starts. In open mode the evaluation has two parts: a technical metric for the components that have one, and a rubric scorecard for everything the judges score. Both start as a **draft** and become **approved** (version `EV1`) when the human signs off. From then on, invariant 2 in the core instructions applies.

## Steps
1. **Acquire the data and write its data card** in `EVAL.md`: source and link, licence and whether the rules allow it, provenance (who collected it, how, when), size, fields, date range, known biases, what is missing, how you cleaned it and where the cleaning code is. Keep the raw download untouched under `runs/data/raw/` and record its hash. If a needed source requires the human (credentials, an application, a purchase, private data), file a request (core invariant 8) and state what you are doing meanwhile. Use the research tools listed in the project settings, following their notes under `docs/agent/tools/`, to find datasets cited in papers, and file a request for anything a tool reports it cannot get. If the deliverable uses no external dataset or predictive component, write "n/a" on the data card and the technical metric, say what the deliverable uses instead, and carry functional tests and user-task evidence on the scorecard.
2. **Check validity.** Does the data measure what the problem is about? Write down the gap between what the data contains and what the user's decision needs. Synthetic or simulated data is allowed only when declared; results on it are diagnostic unless the judges accept it.
3. **Define the task on the data:** prediction or decision unit, target, decision-time information boundary, and a split that mirrors how the system would be used (by time, group, or entity). Fit preprocessing inside the training portion; check duplicate and entity overlap.
4. **Justify the technical metric that Phase 1 declared.** Tie it to the user's decision: what an error costs them and which errors matter more. Write why this metric and not the obvious alternatives. A metric chosen after modeling tends to be the one your approach is good at, so ask the critic, in a fresh session, to review the choice before approval: does any choice in the metric, split, or units flatter a particular approach or hide an error the user would care about? Record the review ID in `EVAL.md`.
5. **Build the scorecard.** One row per rubric criterion: weight, the evidence that would convince the judges, a 0 to 3 scale with anchors, who rates it. Representativeness against the judges is unverifiable; record that, and log every external touchpoint (a mentor review, organiser feedback) as external feedback: useful, but not official judging unless the competition makes it so.
6. **Scorer correctness** for the technical part: a fixture set recorded in `EVAL.md` (the worked example, a known-good and a deliberately poor prediction, documented edge cases, malformed inputs such as missing or duplicate IDs, wrong shape, non-finite values), and one evaluation command that writes a machine-readable result (per-unit scores, aggregate, candidate ID, version) to a known path.
7. **Minimal reference** (a constant, a trivial rule) to exercise the metric; record its revision.
8. **Comparison procedure.** Technical part: matched units, paired signed delta with positive meaning better, uncertainty method and assumptions, practical gain threshold, decision rule, suspicious-gain threshold, all in metric units and written before any candidate exists. Rubric part: two raters, the generator and the critic rating blind against the anchors; a rubric change counts only when both move the same way on the claimed criteria; the inter-rater gap is disagreement, a consistency check, not an uncertainty estimate and not validation against the judges. Write a tradeoff rule for criteria that move in opposite directions. Label rubric gains as internal assessments wherever they are reported.
9. **Confirmation policy** for the technical part: reserve untouched examples as a confirmation set with its scoring command, an access rule with a project-wide cap on accesses, and an access log; or document why none can be reserved and what alternative is used. Fresh training seeds do not remove selection bias. For the rubric there is no confirmation available before judging; say so. The Phase 6 rehearsal is a readiness check, not confirmation.
10. Write `EVAL.md` and hand it to the human for approval. Record the approval and version. Preauthorizing Phase 3 does not approve the evaluation; a conditional approval recorded in advance does. Update `STATE.md`.

## Output
- Data under `runs/data/` with a data card and raw hash in `EVAL.md`.
- Evaluation code with a single entry command and fixtures for the technical part.
- `EVAL.md` with data card, metric justification and review, scorecard, comparison procedure, limitations, state, and version.

## Done when
- The data card is complete and the licence is confirmed allowed under the rules, or the card is marked n/a and says what the deliverable uses instead.
- The technical metric was declared before modeling and reviewed by the critic, or it is marked n/a and the scorecard carries functional tests and user-task evidence in its place.
- The scorecard covers every rubric criterion with evidence requirements and anchors.
- A human has approved a specific version.

## Changing the evaluation after approval
Create a new version with a reason and the approval record; rerun the reference, the incumbent, and any candidate still under consideration; mark experiments whose conclusion the change affects as invalidated; never compare scores across versions. A new version that reuses the same validation units inherits their selection exposure. Adding a data source after approval is a new version.

## Avoid
- Choosing the metric after seeing what the first model does well.
- Treating a self-score on the rubric as evidence without the critic's blind rating.
- Quietly substituting a reachable dataset for the right one. Say what changed and what it costs.
- Treating zero rerun variance as evidence of precision.
