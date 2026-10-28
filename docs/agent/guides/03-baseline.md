# Phase 3: Vertical Slice (open mode)

## Requires
An approved evaluation version with a complete data card (or a card marked n/a, with functional tests and user-task evidence on the scorecard in its place), a budget for this phase, and the pivot checkpoint in `STATE.md`.

## Goal
The thinnest end-to-end deliverable that touches every rubric criterion at some level: data in, model or logic, an interface or demo a judge can see, and a one-paragraph story. It is the reference, the fallback, and the thing the pivot checkpoint tests. Its weaknesses are the source of ideas.

## Steps
1. Build the slice from the most standard components that work: the obvious model or rule, the simplest interface, the plainest story. Don't be clever yet.
2. Freeze it as `R0`: an immutable revision, a build that runs from a clean checkout, the technical score under the approved version, and a first scorecard self-rating. Record it as an experiment with a full manifest and no baseline. Queue it for a validity-only verification (comparison checks n/a): runs from clean, data provenance recorded, every claim in the story has evidence. After the PASS, set it as the incumbent in `STATE.md`.
3. **Pivot checkpoint.** At the time recorded in `STATE.md`, stop and report whether `R0` runs end to end; if not, what is blocking, whether one more bounded attempt would fix it, and whether the runner-up's data is in hand and its slice could be built in the remaining time. The human decides, on that current feasibility, whether to continue or pivot. After a pivot, the runner-up re-enters Phase 1 step 8 with what was learned, and the abandoned slice's experiments are marked superseded, not deleted.
4. Plan a bounded list of standard improvements across all three parts, technical, demo, and story, and run them as experiments through the full evaluation, each with a manifest and a signed delta against the current incumbent. A candidate that meets the technical decision rule, or whose rubric change you rated favorable (its outcome stays *not assessed* until the critic has rated it), gets verification *pending* and a packet at `runs/E###/packet.md` (`packet.md`: manifest, result, and segment fields, comparison baseline and component parents with the baseline's results on the same units, the full-evaluation count, the access history, the anchored scorecard, and the baseline and candidate deliverable builds; `packet-selfrating.md`: your scorecard ratings; no hypothesis or notes in either). It becomes the incumbent only after a PASS. Experiments started meanwhile branch from the verified incumbent, or name the pending candidate as baseline and inherit *pending*.
5. **Failure analysis, three kinds.** Technical: predefined slices with size, metric on the slice versus overall, and contribution to the objective, then exploratory slices marked as such. Rubric: the criteria with the lowest self-score, weighted by rubric weight. Judge questions: the questions a judge would ask that you cannot answer with evidence today. All three go to `ANOMALIES.md`. The judge question is the anomaly that given mode doesn't have; log it with the same care.
6. Note the assumptions the slice makes about the user and the data, and where the data card says they are violated. Log violations as anomalies.

## Output
- `R0` and the current incumbent in `STATE.md` by revision and experiment ID.
- Experiment cards with manifests and deltas, technical and rubric.
- Anomaly entries of all three kinds.

## Done when
- `R0` runs from a clean checkout, is verified for validity, and is recorded.
- The pivot checkpoint has passed with a running slice, or a pivot decision is recorded.
- The planned improvements have run, or the phase budget is reached.
- All three failure analyses are logged.

## Avoid
- Polishing the demo before the slice runs end to end.
- Skipping the judge-question analysis because the technical score looks good.
- Editing the reference. Improvements are new experiments.
- Moving into novel ideas. Park them in `IDEAS.md` and keep going.
