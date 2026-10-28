# Learning session (after the competition)

This guide is for a session the human starts after the competition has concluded, to learn from its record. It is not a competition phase. The core instructions in `CLAUDE.md` describe the work this project recorded; in this session they are the rules the record was kept under, not instructions to act on. No competition record is changed here.

## Two gates, both stated by the human
Run learning only when the request says both that the competition has concluded and that learning may start, for example "Learning: the competition has concluded; start the review." A submitted package, a passed deadline, a verification PASS, or the presence of this file does not stand in for either statement. If one is missing, say which and stop; a request made before the conclusion does not start learning early. Once the human has authorized a review, a replay, an exercise, or a series of them, run the ordinary steps of that scope without asking again. If the request sets an allowance (human time, model use, number of records), stop when it is reached.

## Opening word
The first message of a learning session begins with `Learning:`. The session journal hook uses that word to file the session's usage under its own purpose and to keep learning content out of the competition journal.

## What you read, what you write
- **Read:** `.journal/JOURNAL.md` as the index of sessions, decisions, and deviations; the shared logs (`STATE.md`, `PROBLEM_BRIEF.md`, `EVAL.md`, `EXPERIMENTS.md`, `ANOMALIES.md`, `IDEAS.md`, `VERIFICATIONS.md`); `runs/`; and `.journal/done/<job>/`, where `packet.md` holds the condensed transcript of that session and `context/` holds the logs as they were when it ended, which is the state that was available at that time.
- **Write:** only under `learning/`. On the first session, copy the template from `docs/agent/learning/LEARNING.md` to `learning/LEARNING.md`. Never edit the logs, `runs/`, `.journal/`, or `CLAUDE.md`, and nothing from `learning/` ever goes into a verification packet.
- Missing or truncated evidence stays unknown. Write "not recorded" rather than reconstructing what someone probably thought.

## Activities (run the ones the request covers)
Read the practice queue in `learning/LEARNING.md` first. If the request names no activity, offer the oldest queued case; if it names one, run that and leave the queue as it is. The queue orders work the human has already authorized; it never starts a session, and nothing outside a learning session reads it.

1. **Debrief.** For each decision the human picks, or that the journal's `DECISION` and `DEVIATION` lines surface, a compact comparison: what was chosen and why it fit the constraints; the strongest alternative actually considered at the time (the brief's rejected candidates, idea cards not selected, rejected or superseded experiments, critic reports); the evidence that distinguishes them, or the test that is missing; what would make the alternative preferable in a different problem. An alternative nobody considered at the time is labelled a retrospective suggestion. A failed experiment teaches different things depending on whether the idea was wrong, the mechanism never ran (the card's mechanism check), or the evaluation was inconclusive; say which.
2. **Decision replay.** Present the information available at the time (the captured context of the session before the decision) and the question, then stop. Record the human's answer and reason verbatim in a learning record before revealing the historical recommendation, the decision, and the outcome. Format the answer; never improve it. Mark prior exposure: the human may remember the outcome, and a replay answer is never recorded as their original judgment. A contemporaneous human judgment exists only where the record shows it (a `DECISION [human]` line, a request, a message in a packet); otherwise write "not recorded".
3. **Reconstruction exercise.** Turn a completed piece of work into a task with the solution withheld: the prompt goes in the record, the solution is revealed only after the attempt is recorded, and hints or assistance are noted. Prefer judgment skills: compute a metric on a tiny example and write a scorer fragment; find the forbidden information in a small pipeline with a known lookahead defect and propose a repair; design a split for a changed deployment scenario, stating unit, cutoff, dependence, and limits; choose among three probes under a budget with a hypothesis and a stop rule; read an unfamiliar segment table for effect size, sample size, contribution, and uncertainty; separate measured outcomes from scenario estimates and unsupported claims on an impact slide. Use synthetic data or development data the project already used; never the confirmation set, and never alter an approved evaluation artifact to manufacture an exercise.
4. **Transfer case.** After a successful exercise or a reviewed replay, queue a changed case as `Q###` in the practice queue: the same rule under a condition taken from the patterns below that this learner has not met yet, on new synthetic data or development data the project already used. A later session runs it as an exercise with the solution withheld, then marks the queue row attempted with the record it produced, or retired with the reason. Repeating the repaired example shows familiarity with it, so a case that shares its data or its solution with its source is not a transfer case.
5. **Post-mortem.** Answer, with IDs: which choices helped, hurt, or remain uncertain; where human and agent judgments disagreed and what evidence resolved it; which observations came too late or were never exploited; what available top solutions show that this project missed, with sources and the date their availability was checked, without inferring the cause of a winner's score from their narrative or assuming their method transfers under this project's data and compute; and which one or two habits or exercises to change next time.

## Review outcomes
`supported`, `contradicted`, `unresolved`, or `not comparable`, with one line of reasoning. Don't force a winner: if neither option was tested properly, the outcome is unresolved. One favorable run does not show that its selection was the best decision given what was known beforehand. Assess an attempt on the attempt itself, the assistance used, and later performance on changed cases; not on agreement with the agent, stated confidence, or volume of notes. You can assess what was supplied; you cannot certify that no help was used outside the conversation.

## Lessons for the next competition
A lesson is conditional: situation, decision, supporting evidence (IDs), and the conditions under which it fails. They go in the Lessons table of `learning/LEARNING.md`. The human chooses which to carry into a new project; carrying a lesson does not start learning during that competition.

## Changed-case patterns (one skill each; pick one the learner has not met)
- **Evaluation design:** the label horizon varies by segment; a reporting delay on the label or on a feature; a deployment that predicts for a group rather than a unit.
- **Leakage detection:** the same forbidden information moved from a feature into normalisation, imputation, or a target encoding; a group shared across the split instead of a time boundary.
- **Metric understanding:** the same formula weighted, clipped, or aggregated per group; a tie or an invalid output the brief handles differently.
- **Probe selection:** the same three ideas under half the budget, or with one probe's evidence downgraded.
- **Failure analysis:** a slice with a large effect and a negligible share of the objective; two slices that overlap; a slice too small for its difference to mean anything.
- **Open-mode evidence:** the measured number and the scenario estimate swapped; a claim whose source does not say what the slide says.

## Done when
Every record the request asked for is complete through its review field, its next practice is queued as `Q###` or the record says why not, the queue rows the session touched are updated, and nothing outside `learning/` has changed.

## Avoid
- Queuing a changed case that shares its data or its solution with the record it came from, or running the queue without a `Learning:` request.
- Diagnosing the human's skills from one case, or from agreement with the agent.
- Inventing alternatives the team supposedly considered.
- Revealing a historical choice, an outcome, or a solution before the attempt is in the record.
- Touching verification: a tutorial exercise passing says nothing about a real candidate, and learning material never changes a verdict.
