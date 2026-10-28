# Phase 4: Ideation and Probes

## Requires
An approved evaluation, a named incumbent in `STATE.md`, an `ANOMALIES.md` populated by the baseline failure analysis, and a probe budget for this session.

## Goal
Find where this specific problem differs from the textbook case, and test ideas that exploit it. A model's default suggestions are the most common good answers, which other competitors also receive. Ideas grounded in our own observations are the ones others are less likely to have. Novelty is a search strategy, not a selection rule: rank ideas by expected contribution under the actual constraints.

In open mode, ideas may target any part of the deliverable: data, model, demo, or story. Rank by rubric weight times the scorecard gap as well as by metric gain, and treat judge-question anomalies as first-class inputs.

## Session modes
- **Generate and probe:** one generation round, then probes.
- **Backlog only:** no generation; probe existing cards. Use this when the backlog already holds untested, well-rated ideas.

## Steps

### 1. Read before generating
Read `ANOMALIES.md`, recent `EXPERIMENTS.md` entries, and `IDEAS.md`. Ideas should start from these. Domain knowledge and standard approaches not yet tried are also legitimate sources, especially while the anomaly log is thin.

### 2. Generate (one round = at most 8 new ideas; a ceiling, not a quota)
Use these techniques; vary them across rounds:
- **Explain an anomaly.** Pick an anomaly and ask what would cause it and how to exploit it.
- **Find the violated assumption.** Take the baseline's assumptions; for each one this problem violates, ask what approach doesn't need it.
- **Exclude the obvious.** List the three approaches most competitors will use, then generate only ideas outside them and their variants. This is one exercise among several, not a filter on the whole backlog.
- **Borrow from another field.** Ask how a specialist in an adjacent area (SAT solving, game engines, logistics, signal processing, ecology) would attack it. Use the research tools listed in the project settings, following their notes under `docs/agent/tools/`, to see how adjacent fields attack the same structure; record provenance for anything you take.
- **Change the representation.** Recast the problem as a graph, search, game, compression, or estimation problem.
- **Invert or shrink.** Ask what would make the problem trivial and how close we can get; or solve tiny instances exactly and look for structure in the optimal solutions.

### 3. Write each idea as a card in `IDEAS.md`
- **Grounding:** anomaly ID, violated assumption, or "speculative".
- **Hypothesis:** the mechanism we think is at work and what it predicts.
- **Control:** what the probe is compared against (the incumbent, an ablation, a negative control).
- **Smallest informative experiment:** the cheapest test that can actually falsify the hypothesis, its result type (diagnostic / proxy / full), and the predeclared pass and stop criteria.
- **If pass / if fail:** what each outcome implies and what the next step would be.
- **Ratings** (low / medium / high): evidence strength, plausible gain, probability of success, total effort (the probe plus the implementation and verification it would lead to), informative value.

Some hypotheses can't be tested cheaply. Say so on the card rather than inventing a proxy that doesn't test the mechanism.

### 4. Triage
Pick the probes to run and write one line each on why. Prefer ideas with strong evidence and high informative value per unit of total effort. If the human has allowed a bounded share for speculative ideas, use it for the best of them; don't fill it just because it exists. Don't rank by a formula: the ratings are coarse judgments, and the written reason is what the next session needs.

### 5. Probe
Run the selected probes within the probe budget. Most will fail; that's expected and fine. Log each as an experiment with its result type and manifest, and update the idea's status. Before a null or unfavorable result marks an idea *failed*, confirm the mechanism actually executed: predictions differ from the control, the new feature or parameter takes non-trivial values, the flag is read. Record that check on the experiment card. A probe whose mechanism never ran has tested nothing.

### 6. Hand off
- A **diagnostic** or **proxy** pass authorises the next test on the card. It is not an improvement claim.
- A **full** result that meets the decision rule is a candidate: set verification to *pending*, adoption to *candidate*, and write its packet for the critic at `runs/E###/packet.md`: the card's manifest, result, and segment fields, the comparison baseline and component parents with the baseline's results on the same units, the full-evaluation count from `STATE.md`, and the confirmation access history. Leave out the hypothesis, idea links, and notes.
- In open mode, a rubric change you rate as favorable is queued the same way, with outcome *not assessed* until the critic has rated it. Its packet is two files: `packet.md` with the anchored scorecard, the baseline and candidate deliverable builds, and no scores or directional claim; and `packet-selfrating.md` with your ratings, which the critic opens only after recording its own.
- Any result above the suspicious-gain threshold is queued for verification immediately.
- New anomalies from probes go in `ANOMALIES.md`.

## Done when (per session)
- The chosen mode is complete: a generation round triaged, or the backlog probed.
- Probes within budget are run and logged with result types.
- Candidates are queued for verification and `STATE.md` is updated.
- Or: nothing feasible or informative remains within budget, and that is recorded with a reason.

## Avoid
- Generating more than one round without probing. Untested ideas pile up and add nothing.
- Building more than the smallest informative experiment before it has shown something. When no cheap faithful test exists, say so and get the budget approved.
- Promoting an idea because it's elegant. The probe decides.
- Treating a diagnostic pass as a metric gain.
