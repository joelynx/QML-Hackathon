# V005 verification packet: the final submission (README claim set, SVDB confirmation, Phase 4 results, gates)

Assembled by the coordinator 2026-10-28 ~20:12 UAE from the cards' factual fields. Facts only.

## What is under review
1. **Validity of the SVDB confirmation E018** (full, EV2, `--role confirmation`, access 1 of 2): E003 (QRC, candidate) vs E002 (ESN R0, baseline), the frozen headline pair, predicted from the saved artifacts by the predict-only path `src/qhc/p4/predict.py`. Recorded outcome: delta −0.0085 [−0.0476, +0.0274], **not confirmed**.
2. **Validity of the Phase 4 secondary ds2s comparisons** (EV2, `--role secondary`, descriptive): E012 vs E003; E014-n6 vs E003; E015-rigetti vs E003; E003 vs E016; E002 vs E016. And the label-free hardware diagnostic E019, the DS1 proxies E013/E014/E015 and the DS1 diagnostic E017.
3. **The claim set of the submission `README.md`** (sha256 prefix at assembly `f83bad2ffa7d7209`, may differ by the verification slot only) and `docs/EVIDENCE.md`: every number and claim traceable to an experiment ID or a source; no claim stronger than the evidence.
4. **Scorecard ratings (blind)** on all six rows of the scorecard in `EVAL.md` ("Scorecard"), including both gates. Gate "reproducible" anchor 3 needs a critic check of regeneration from a clean environment and fresh download.

There is no candidate for promotion: the incumbent stays E002 (R0, V004 PASS). The headline E003 vs E002 outcome is *no detectable change* (EV1, rerun identically under EV2).

## Revisions and environment
- Evaluation code `8501643023cd2eb6` (EV2, approved 2026-10-26 22:14; top-level `src/qhc/*.py`, LF-normalised hash); fixtures 43.
- Pipeline `55884b1fb66732b9` (`src/qhc/pipe/*.py`, not edited this session). The 10 headline artifacts record pipeline `da67af87f8b8fd73` (final runs 2026-10-26).
- Phase 4 modules `src/qhc/p4/` (hash per module, `qhc.p4.module_revision`): predict `08dc4140d5d45b6b`, ablate `f7fe9f52db014c44`, noise `8b1226919f8ca395`, boost `c2c2fc47c011e891`, kernels `647cb96976578b0d`, braket_hw `4a5dbce596f0a847`. Run manifests record `eval / pipe / p4 <module> <hash>`.
- Project venv `.venv` (Python 3.12.10, `requirements-lock.txt`); Braket SDK only in `.venv-braket`. GPUs: 2x RTX 6000 Ada.
- Data: `runs/data/raw/` (MIT-BIH 48 records, SVDB 78 records, SHA256-verified), processed units `runs/data/processed/EV1/`. **Never open `runs/data/processed/EV1/confirm/`** or any test-label file directly; the scorer is the only reader of labels.

## Specifications
- `EVAL.md` (EV2): metric, split, units, comparison procedure, decision rule, slice family, confirmation policy, access log, hardware and noise tracks, scorecard.
- `PROBLEM_BRIEF.md`, `hackathon_details.md` (the brief and judging criteria).
- `EXPERIMENTS.md`: cards E002-E019 and the "Phase 4 declarations" section (written ~18:50 UAE on 2026-10-28, before any E012+ run).
- `ANOMALIES.md` (facts: A001, A004, A006, A015-A023).

## Access history (facts)
- `runs/full_eval_log.jsonl`: 18 lines. Test-split scorings: 7 before this session (EV1 headline 2026-10-26 21:26:59; EV2: headline rerun, E003 vs E004, E005 vs E003, E006 `score`, lowdata_k5, lowdata_k11), then on 2026-10-28: SVDB confirmation (19:29:19), and the 5 secondaries (access lines 19:29:53-19:31:33; outputs written 19:40:06-19:42:35). 13 of 15; the other 5 lines are the 2026-10-26 18:37 reference scorings, which do not count (EVAL.md rule 5).
- `runs/confirmation_access.jsonl`: 1 line (19:29:19). `runs/confirmation_reports/access_1.json` (sha256 `39c6b7e77a4353d67e97bfc7150dd42d8dc372c1088e517ae0bee952b75b2434`), `index.jsonl` (completed 20:01:41). EVAL.md access-log row added (bookkeeping). Earlier incident 2026-10-26 ~17:45 recorded in the EVAL.md access log (V002).

## Commands (exact; verbatim lists on the cards)
- E018 self-check and predictions: `runs/E018/summary.md` ("Confirmation command", self-check table); `runs/E018/check_e018.py` reruns the label-free checks.
- E018 access: `python -I -m qhc.evaluate compare --split svdb --role confirmation --cand runs/E018/E003/pred_svdb_seed{0..4}.csv --base runs/E018/E002/pred_svdb_seed{0..4}.csv --cand-id E003 --base-id E002 --out runs/E018/confirm_svdb.json --confirm-reason "..."`.
- Secondaries: `python -I -m qhc.evaluate compare --split ds2s --role secondary --cand <5 files> --base <5 files> --cand-id <id> --base-id <id> --out <json>`; outputs `runs/E012/compare_ds2s_secondary_E012_vs_E003.json`, `runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json`, `runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json`, `runs/E016/compare_ds2s_secondary_E003_vs_E016.json`, `runs/E016/compare_ds2s_secondary_E002_vs_E016.json` (each with `_stdout.txt`).
- Per-experiment training/prediction commands: `runs/E0xx/summary.json` (`commands`), and the cards.
- Hardware: `scripts/braket_submit.py` (`.venv-braket`), `python -I -m qhc.p4.braket_hw analyse`; ledger `runs/E019/cost_ledger.jsonl`, approval `runs/E019/approval.json`, results `runs/E019/results/`, `analysis.json`.
- One-command reproduction of the headline: `scripts/reproduce.py` (README Section 9, audit mode `--check`).

## Raw results (as logged; see the JSON files)
- **E018 (SVDB, 78 records, 184,286 units):** E003 0.6402 vs E002 0.6488; delta −0.0085 [−0.0476, +0.0274]; per class N +0.004, S −0.026, V −0.003; LORO −0.0157 to −0.0010.
- **E012 vs E003:** 0.7278 vs 0.7273, +0.0005 [−0.0058, +0.0081].
- **E014-n6 vs E003:** 0.7351 vs 0.7273, +0.0078 [−0.0055, +0.0188]; without 232 +0.0004.
- **E015-rigetti vs E003:** 0.7289 vs 0.7273, +0.0016 [−0.0331, +0.0248]; V F1 −0.0530 [−0.114, −0.020].
- **E003 vs E016:** 0.7273 vs 0.7216, +0.0057 [−0.1389, +0.0676]; without 232 −0.0869; V F1 −0.068 [−0.159, −0.031].
- **E002 vs E016:** 0.7065 vs 0.7216, −0.0151 [−0.1896, +0.0766]; without 232 −0.1329.
- **Headline (E003 vs E002, ds2s):** 0.7273 vs 0.7065, +0.0208 [−0.0157, +0.0617]; slice V_f1 +0.0688 [+0.0207, +0.1543] (98.75%).
- **E019 (48 beats, Rigetti Cepheus-1-108Q, 1 program-set task, 40 circuits x 1,024 shots):** feature MAD vs exact 0.347 (shot vs exact 0.018); pooled corr 0.70; class agreement with finite-shot simulation 41.7% (ceiling 87.5%).
- DS1 proxies: E013 table (`runs/E013/table.csv`), E014 (`runs/E014/table.csv`), E015 (`runs/E015/summary.json`), E016 (`runs/E016/summary.json`), E017 diagnostic (`runs/E017/summary.json`).

## Variant counts
- Headline line: 30 configurations per arm (E002, E003) + controls E004-E006 + E007/E008 + E010/E011 fairness reruns (no test scoring).
- Phase 4: E012 (1 arm), E013 (3 shot counts), E014 (4 variants; 1 to ds2s by a declared DS1 rule), E015 (2 device models; Rigetti to ds2s by declaration), E016 (30 configurations; 1 selected), E017 (diagnostic), E019 (1 hardware task). Every ds2s comparison in Phase 4 was chosen after the ds2s headline and control results were seen.

## Deliverables (brief: codebase with both approaches, comparative evaluation, explanation of problem/methods/quantum purpose, reproduction instructions)
- `README.md` (the written submission; the form takes a GitHub link only), `docs/EVIDENCE.md`, `docs/figures/ds2s_per_class_f1.png` (+ `scripts/make_figure.py`), `LICENSE` (MIT), `.gitignore` (raw/processed data excluded; `scripts/download_data.py` rebuilds), `src/`, `scripts/`, `tests/`, `runs/` (outputs).
- Clean-environment evidence so far: `runs/phase3/clean_build_EV2.md`, `runs/phase3/reproduce_check_EV2.md` (produced by the coordinator, 2026-10-26).
