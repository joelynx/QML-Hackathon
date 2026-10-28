# Phase 6: Deliver (open mode)

## Requires
An incumbent in `STATE.md` whose experiment has verification *pass* under the current approved evaluation version, and the deliverable list from the brief (repo, demo, video, slides, writeup, forms). Everything up to the submission itself can be done without authorization; the submission needs it, explicit or within the pre-authorized scope in the project settings.

## Goal
Turn the verified incumbent into the exact package the judges receive, rehearse it against the questions they will ask, and record what was submitted.

## Steps
1. Freeze the deliverable build from the verified revision in a clean environment: the demo, the repo at a tagged commit, the writeup, the slides. Record hashes. Any code change after this is a new candidate.
2. Run the demo from a clean checkout, on a machine other than the one it was built on if any is available, otherwise in a fresh environment. Record runtime, dependencies, and everything it needs (network, keys, data files), and whether the rules allow each.
3. **Record a fallback.** A screen recording of the working demo and a static version of every live chart. Live demos fail; the recording is what you show when yours does.
4. **Claims check.** Every number and claim in the pitch and writeup points to an experiment ID or a source in the brief. Remove or soften the ones that don't.
5. **Rehearsal.** Ask the critic, in a fresh session, for the ten hardest questions a judge would ask given the packet, the scorecard, and the anomaly facts. Rehearse the answers. Questions with no good answer go to `ANOMALIES.md` and into the pitch as stated limitations rather than being hidden.
6. Assemble the submission package exactly as the brief lists it: formats, lengths, forms, team information, licence files, the data card. Check every item against the rules' deliverable list.
7. Record the package as *ready to submit* in `STATE.md` under Submissions, with its paths and hashes. Submit only with authorization, then record where, when, and the receipt. If the judges' feedback or score arrives, log it, and log a gap from the scorecard's self-rating as an anomaly.
8. Keep the previous package; don't overwrite it.

## Done when
- The package matches the brief's deliverable list item by item.
- The fallback recording exists and the claims check is clean.
- The rehearsal questions and answers are recorded.
- The package is recorded as ready to submit, and, once authorized and submitted, the receipt is logged.

## Avoid
- Changing code or claims after the verified build. A PASS covers the release build and the claim set it was given; a changed deliverable is a new candidate, so decide whether the fallback recording is the better choice.
- Claims without an experiment ID behind them.
- Spending the verification and final-artifact reserve on one more feature.
