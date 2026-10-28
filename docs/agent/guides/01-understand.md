# Phase 1: Understand the Brief and Choose the Problem (open mode)

## Requires
The competition brief, theme, rubric or judging criteria, rules, timeline, and any resources the organisers provide. The research tools listed in the project settings.

## Goal
Choose a problem that is tractable in the time, has data you can actually get, fits the rubric, and is distinct from what most teams will build. Then define it precisely. Problem choice is the highest-leverage decision in an open competition, and it is made by the human from a shortlist you prepare.

## Steps
1. Read the brief, theme, rubric, rules, timeline, tracks, and prizes. Record each source with a link and access date. Mark each fact *official*, *forum*, or *assumption*, and state how conflicts are resolved.
2. Understand the judges: who they are, how long they see each team, what they see (demo, pitch, repo, writeup), and what the rubric weights. Past winners, where visible, show what is rewarded; note what they built and how it scored.
3. List constraints: team size, allowed tools and data, licensing, what must be built during the event, deliverable formats, deadlines with time zones. Mark fields that don't apply as "n/a".
4. Generate candidate problems, at most 8. One card each: the user and their pain, the decision the system would support, the deliverable, candidate data sources by name, rubric fit per criterion (low / medium / high), tractability in the time, distinctiveness (what most teams will build in this theme and whether this differs), and the main risk.
5. **No data, no problem.** Before a candidate stays on the shortlist (the top 3), obtain and inspect a sample of its data: download it, open it, check size, fields, licence, and date range. A source you cannot reach is not a source. If a source needs something only the human can do (an account, an application, a purchase, a private or gated dataset, a paywalled paper), file a request under Requests for the human in `STATE.md` (core invariant 8) and keep working on the other candidates meanwhile. A candidate whose data is blocked on a request goes on a marked watchlist, not the shortlist, until the data is in hand.
6. Use the research tools listed in the project settings for the hunt, following their notes under `docs/agent/tools/`. Papers show which datasets exist for a problem, what published baselines achieve, and the known failure modes. Record provenance for anything you take, and file a request for anything a tool reports it cannot get.
7. Shortlist and recommend: rank the candidates with a one-line reason each, name a recommended problem and a runner-up, and hand the decision to the human. Record what was rejected and why. The runner-up is the pivot target, so its data must already be in hand; a watchlisted candidate cannot be the runner-up. The human may still choose a watchlisted candidate, with a stated contingency for the case that the request is not fulfilled by the checkpoint.
8. Define the chosen problem precisely: the user, the decision supported, the input, the output and deliverable, the technical success criterion declared now before any model exists (Phase 2 justifies it), the rubric criteria it targets and how, and what information is available at decision time.
9. Propose a time plan against the budget in `STATE.md`, with a **pivot checkpoint**: a fraction of the time, 25 to 30 percent is a reasonable default, by which the vertical slice must run end to end. At the checkpoint the human decides, on current feasibility, whether to continue or switch to the runner-up; the checkpoint triggers the decision, not an automatic switch. Record the checkpoint and the runner-up in `STATE.md`.
10. List ambiguities and open questions with blocking or provisional status and an owner.

## Output
`PROBLEM_BRIEF.md` with the selection section filled. `STATE.md` with the pivot checkpoint, the runner-up, and any requests for the human. Surprises to `ANOMALIES.md`.

## Done when
- The human has chosen the problem from a shortlist in which every entry has an inspected data sample; blocked candidates are on the watchlist with their requests filed.
- The problem definition states user, decision, input, output, technical criterion, and rubric mapping.
- The pivot checkpoint and runner-up are recorded.
- Open questions are listed with status and owner, and blocking ones are flagged to the human.

## If the problem or the data is fixed
Skip what is given. A fixed problem collapses steps 4 to 7 to confirming that its data is reachable. Fixed data collapses step 5 to inspecting it. If the deliverable has no dataset or predictive component (a tool, a process, a design), say so in the brief; Phase 2 then marks the data card and the technical metric n/a and the scorecard carries functional and user-task evidence instead.

## Avoid
- Choosing a problem for its story before checking its data.
- Building anything. A sample download is inspection, not building.
- Letting the shortlist carry a candidate whose data is "probably available".
- Dropping a candidate silently because a resource was blocked. File the request and say so.
