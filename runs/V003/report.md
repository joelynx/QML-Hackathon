# V003: critic re-check of EV1 draft r4

Saved verbatim by the coordinator from the critic's final message: the harness did not let the critic subagent write report files. Reviewed EVAL.md sha256 `4fed26458f2c63cd…`, code revision `a2439884ff2f1909`, fixtures `15f4ece17d6839a2` (33/33 pass). Probe script `runs/V003/probes.py`, output `runs/V003/probe_results.json`, scratch `runs/V003/probe_tmp/`. All probes were synthetic, with PROCESSED and both logs redirected to `probe_tmp`; no real test labels, `confirm/` or real logs were touched.

**Verdict: NEEDS-CHANGES.** r4 has one blocking gap: the rule that confirmatory results can't be swapped after seeing ds2s is only partly enforced. It also has three should-fix items. All are small code changes. The metric, the bootstrap and the R1-R3 data fixes are correct.

## Blocking

**B1. The headline and low-data slices can still be chosen after seeing ds2s results** (`evaluate.py:173-180`, `evalspec.py:63-70`). The check only refuses a second, different `--role headline` run.
- (a) Headline chosen after peeks (probe P1). On a fresh log, a quantum `score` on ds2s, a 5x5 `--role diagnostic` pair with no run manifests, and a `--role secondary` pair A were all accepted, and then a different pair B was accepted as the headline. `EVAL.md:304` defines the headline as "the first quantum-versus-matched-ESN pair evaluated on ds2s", and the code doesn't enforce that.
- (b) Low-data slices can be redrawn (probe P1b). Rerunning `lowdata_k5` with different files was accepted; its slice decision went from "no detectable change" to "favorable".
- Fix: run-once check for `lowdata_k5` and `lowdata_k11`; refuse the first headline if the log already holds any ds2s or ds2 entry other than the reference prediction hashes; limit `diagnostic` on ds2s and ds2 to the reference hashes; optionally refuse `score`, `secondary` and low-data runs on ds2s until a headline is logged.

## Should-fix

**S1. The five-seed check compares file paths, not contents, so copies pass** (`evaluate.py:143-152`). Five renamed copies of one prediction file and five byte-identical model files, with manifests claiming seeds 0-4, were accepted (P2). One arm with five different `config_id`s, and a baseline with the same `arm_id` as the candidate, were accepted (P2b). Fix: distinct `model_artifact_sha256` within an arm, one `config_id` per arm, different `arm_id`s for the two arms.

**S2. A failure after logging uses up a confirmation access** (`evaluate.py:263-275`, `214-218`). With an unwritable `--out`, the command failed after the access was logged and the labels were scored (P3). Fix: check writability and smoke-test the scorer before logging; write atomically with a fallback; print the primary result before writing.

**S3. A repair access can use different models** (`evaluate.py:195-200`). A second access with entirely different model artifacts was accepted (P4). Fix: require the same set of `model_artifact_sha256` on the second access, unless an explicit flag records the human's approval.

## Item table

| Item | Status | Evidence |
|---|---|---|
| R1 flutter `!` | resolved | r4 `positions_ds1` equals r3 minus exactly the 472 `!` rows of record 207; prediction set 50,964, units 50,542, folds unchanged; independent rr_rule DS1 0.391974 (r3 0.392390) |
| R2 paper-compatible metrics | resolved, minor text left | `scorer.py` matches de Chazal Table V term for term, including both TN definitions; `EVAL.md:125` still listed EC57 (M1) |
| R3 de Chazal counts | resolved | `EVAL.md:158-176`, fixture, A008 |
| R4 multiplicity | partly | levels, slice output and rule correct; B1 |
| R5 distinct seeds | partly | exact duplicate paths refused; S1 |
| R6 complete confirmation report | partly | normal path complete; S2, S3 |
| Additional 1-5 | resolved | |
| Six small corrections | resolved | clean environment not tested |
| Acceptance: rebuild, counts, F->S, one access, hashes, reference rerun | resolved | reference CI [+0.0225, +0.2443] at B = 8,000 matches; ds2s/ds2 reference predictions byte-identical to r3 |
| Acceptance: interval levels | resolved, minor | low-data levels tested only through the scorer (M4) |
| Acceptance: refuse duplicate or insufficient seeds | partly | S1 |

Regression checks that passed: a brute-force bootstrap (explicit record and seed resampling, same random stream) reproduces the macro-F1 CI and the S/V AUPRC CIs to about 1e-16; `decide` and `slice_decision` match EVAL.md; `seed_average` is a plain mean with None propagation and count tables kept per seed; every path validates predictions before reading labels, and the confirmation order is validate, cap, log, read.

## Minor
- M1. Stale text: `EVAL.md:125` (EC57), `EVAL.md:379` (2,000 replicates, under 1 min), `EVAL.md:304` (contradicts the code, B1).
- M2. Headline identity depends on path spelling and merges both arms; no headline repair path documented. Fix: per-arm hash comparison; document a headline repair rule.
- M3. Low-data subset rule ambiguous (`rng.choice` vs `permutation`); no generator saved. Fix: name the exact call or save the script.
- M4. The R4 command-level test covers only the headline. Add a `lowdata_k5` command test.
- M5. Optional diagnostic (e) trains on ds2s labels; allow it only after the final pair and SVDB run are frozen, or drop it.
- M6. The paper-compatible confusion is pooled only; add a per-record 5x3 table.
