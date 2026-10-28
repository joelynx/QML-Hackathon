# E018 preparation summary (CPU A lane)

Label-free preparation of the pre-registered SVDB confirmation of the frozen headline pair E003 (QRC) vs E002 (ESN). Nothing was scored; no file under `runs/data/processed/EV1/confirm/` was opened; `runs/E002/` and `runs/E003/` were only read.

- **Code revision:** `eval 8501643023cd2eb6 / pipe 55884b1fb66732b9 / p4 predict 08dc4140d5d45b6b` (new module `src/qhc/p4/predict.py`; evaluation and pipeline code unchanged).
- **Self-check (ds2s, hashes only):** 10 of 10 logged headline prediction hashes reproduced from the saved artifacts.
- **SVDB predictions:** 5 per arm in `runs/E018/E003/` and `runs/E018/E002/`, label-free checks passed (check_runs, scorer.validate against the prediction set, --out check); compare preflight on placeholder labels passed.
- **Artifacts untouched:** 77 files in `runs/E002/` and `runs/E003/`, sha256 + size + mtime identical before and after: True.

## Confirmation command (for the coordinator)

Run from the project root. Bash:

```bash
CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 .venv/Scripts/python -I -m qhc.evaluate compare --split svdb --role confirmation --cand runs/E018/E003/pred_svdb_seed0.csv runs/E018/E003/pred_svdb_seed1.csv runs/E018/E003/pred_svdb_seed2.csv runs/E018/E003/pred_svdb_seed3.csv runs/E018/E003/pred_svdb_seed4.csv --base runs/E018/E002/pred_svdb_seed0.csv runs/E018/E002/pred_svdb_seed1.csv runs/E018/E002/pred_svdb_seed2.csv runs/E018/E002/pred_svdb_seed3.csv runs/E018/E002/pred_svdb_seed4.csv --cand-id E003 --base-id E002 --out runs/E018/confirm_svdb.json --confirm-reason "E018: pre-registered SVDB confirmation (EVAL.md, criterion fixed 2026-10-26) of the frozen headline pair E003 (QRC, candidate) vs E002 (ESN, baseline). Predictions from the exact DS1-trained artifacts runs/E003 and runs/E002 model_seed0-4.npz via the A018 predict-only path (qhc.p4.predict 08dc4140d5d45b6b); its ds2s self-check reproduced all 10 logged headline prediction hashes. Pass: delta above 0 and 95 percent CI lower bound above 0." 2>&1 | tee runs/E018/confirm_svdb_stdout.txt
```

PowerShell:

```powershell
$env:CUDA_VISIBLE_DEVICES='0'; $env:OMP_NUM_THREADS='8'; $env:MKL_NUM_THREADS='8'; .venv\Scripts\python.exe -I -m qhc.evaluate compare --split svdb --role confirmation --cand runs/E018/E003/pred_svdb_seed0.csv runs/E018/E003/pred_svdb_seed1.csv runs/E018/E003/pred_svdb_seed2.csv runs/E018/E003/pred_svdb_seed3.csv runs/E018/E003/pred_svdb_seed4.csv --base runs/E018/E002/pred_svdb_seed0.csv runs/E018/E002/pred_svdb_seed1.csv runs/E018/E002/pred_svdb_seed2.csv runs/E018/E002/pred_svdb_seed3.csv runs/E018/E002/pred_svdb_seed4.csv --cand-id E003 --base-id E002 --out runs/E018/confirm_svdb.json --confirm-reason "E018: pre-registered SVDB confirmation (EVAL.md, criterion fixed 2026-10-26) of the frozen headline pair E003 (QRC, candidate) vs E002 (ESN, baseline). Predictions from the exact DS1-trained artifacts runs/E003 and runs/E002 model_seed0-4.npz via the A018 predict-only path (qhc.p4.predict 08dc4140d5d45b6b); its ds2s self-check reproduced all 10 logged headline prediction hashes. Pass: delta above 0 and 95 percent CI lower bound above 0." | Tee-Object -FilePath runs/E018/confirm_svdb_stdout.txt
```

Order inside the command (src/qhc/evaluate.py, `cmd_compare` then `_confirmation_access`): role/split check; `check_runs` on both arms (5 seeded runs, manifests bound by hash to predictions and artifacts); cross-arm checks; `_check_out(..., new_file=True)`; `--confirm-reason` present; a logged ds2s headline; `scorer.validate` of all 10 files against the label-free prediction set; `_check_writable`; **`_smoke_test` (placeholder labels, 20 replicates)**; cap check (0 used of 2); **only then** the append to `runs/confirmation_access.jsonl`, then `runs/full_eval_log.jsonl`, then the label read, the archive `runs/confirmation_reports/access_1.json` + `index.jsonl`, and finally `--out`. After it runs, the access must be added to the EVAL.md access-log table (bookkeeping).

Preconditions now: headline logged True; `runs/confirmation_access.jsonl` exists False; `runs/confirmation_reports/` exists False; `runs/E018/confirm_svdb.json` exists False; evaluation revision `8501643023cd2eb6`; dominant record for svdb: None.

**Runtime estimate:** the same comparison on placeholder labels at 8000 replicates (184389 units) took 2019.4 s (33.7 min) on this machine; the smoke test adds 26.1 s. Expect about 35 min end to end.

## Self-check: logged vs reproduced (ds2s)

| Logged file | Logged sha256 | Reproduced sha256 | Match |
|---|---|---|---|
| `runs/E003/pred_ds2s_seed0.csv` | `b1450a4e6c69cc797f2cce40c34accf6ef861a34f403608f2e00d81cc931a363` | `b1450a4e6c69cc797f2cce40c34accf6ef861a34f403608f2e00d81cc931a363` | True |
| `runs/E003/pred_ds2s_seed1.csv` | `e76ac40d02f1eeb7473edef78a26e1a18c2c3f1fb4f3093205ec97bf06105272` | `e76ac40d02f1eeb7473edef78a26e1a18c2c3f1fb4f3093205ec97bf06105272` | True |
| `runs/E003/pred_ds2s_seed2.csv` | `24ea20f4a4bc91f1788a393598db1d5d2ce48e3a2a7c99c708ca9556308751ba` | `24ea20f4a4bc91f1788a393598db1d5d2ce48e3a2a7c99c708ca9556308751ba` | True |
| `runs/E003/pred_ds2s_seed3.csv` | `903d9d6f454e1c2010f1a07e72fc41fad646534333afad404b686a280f201ea3` | `903d9d6f454e1c2010f1a07e72fc41fad646534333afad404b686a280f201ea3` | True |
| `runs/E003/pred_ds2s_seed4.csv` | `ff2c09b9c6f382e70091a3f1203bf84493e0b5869c508daeccde41102cac6169` | `ff2c09b9c6f382e70091a3f1203bf84493e0b5869c508daeccde41102cac6169` | True |
| `runs/E002/pred_ds2s_seed0.csv` | `6996d03d8dddc1e2a6a0523f75ded867e2530c15461db81487b0d6b72c2ba7cc` | `6996d03d8dddc1e2a6a0523f75ded867e2530c15461db81487b0d6b72c2ba7cc` | True |
| `runs/E002/pred_ds2s_seed1.csv` | `8a70f0713e25c7b4b4aac42a13847c7bff8fe4e2a4d7ac1d8c29e63379089987` | `8a70f0713e25c7b4b4aac42a13847c7bff8fe4e2a4d7ac1d8c29e63379089987` | True |
| `runs/E002/pred_ds2s_seed2.csv` | `0cacdc4c2f47ea9347493a6fdd20a087456e5e5ad1a38a3a2e2d698fd1ddbbdc` | `0cacdc4c2f47ea9347493a6fdd20a087456e5e5ad1a38a3a2e2d698fd1ddbbdc` | True |
| `runs/E002/pred_ds2s_seed3.csv` | `cc2cfa437a2861ed79041e4a92474aef93183ab89f2a97013a0b36c4bb12fc91` | `cc2cfa437a2861ed79041e4a92474aef93183ab89f2a97013a0b36c4bb12fc91` | True |
| `runs/E002/pred_ds2s_seed4.csv` | `8511ccea894187a57660fc41628f233a4d689e998660c00f5f4b5289a6ab68ee` | `8511ccea894187a57660fc41628f233a4d689e998660c00f5f4b5289a6ab68ee` | True |

The reproduced manifests differ from the headline manifests only in `code_revision` (plus added provenance keys). Features: the existing `runs/features/EV1/ds2s.npz` (pipe `697d9992c5fe5811`); a fresh rebuild with the current pipeline into `runs/E018/features_ds2s_rebuild/` is array-identical: True. SVDB features were built by the same `features.build_split` into `runs/E018/features/svdb.npz`.

## Model artifacts (sha256 before / after)

| Artifact | sha256 before | after | unchanged |
|---|---|---|---|
| `runs/E002/model_seed0.npz` | `0f5b4333465d9e4800366ed27bfd0874f34e3e9ec1ae7559e1bacb57dcd70d0b` | `0f5b4333465d9e4800366ed27bfd0874f34e3e9ec1ae7559e1bacb57dcd70d0b` | True |
| `runs/E002/model_seed1.npz` | `58d5ede9934003b55d56352fed287eb239f00cdfe37eb9dc0772948da3318126` | `58d5ede9934003b55d56352fed287eb239f00cdfe37eb9dc0772948da3318126` | True |
| `runs/E002/model_seed2.npz` | `3d4a76f788c7f69a1a8ad0b28ce8491060d429b30e568e863d3c7d12eca7dca7` | `3d4a76f788c7f69a1a8ad0b28ce8491060d429b30e568e863d3c7d12eca7dca7` | True |
| `runs/E002/model_seed3.npz` | `ee95d1c4898ad238566bd1ba8ddf4c28b936c0e55c8a2139a3ba0758c1011fba` | `ee95d1c4898ad238566bd1ba8ddf4c28b936c0e55c8a2139a3ba0758c1011fba` | True |
| `runs/E002/model_seed4.npz` | `d3cf14e13e605dc952714547c7e2bc02dcb536f288b87512441c7baf0807d0f6` | `d3cf14e13e605dc952714547c7e2bc02dcb536f288b87512441c7baf0807d0f6` | True |
| `runs/E003/model_seed0.npz` | `a30c951215032d5bad94d6245f2e66edbce7a6a2cfaa7c62c9eb330d7f0b6039` | `a30c951215032d5bad94d6245f2e66edbce7a6a2cfaa7c62c9eb330d7f0b6039` | True |
| `runs/E003/model_seed1.npz` | `39a56b1b1b3e67de84af44c15f26f114903f4519c3643c218dda0ee30dc73808` | `39a56b1b1b3e67de84af44c15f26f114903f4519c3643c218dda0ee30dc73808` | True |
| `runs/E003/model_seed2.npz` | `cb005da3df5429ceb3a29c984b6faf2e473c75f78de65d8773d07e992e2e3c1b` | `cb005da3df5429ceb3a29c984b6faf2e473c75f78de65d8773d07e992e2e3c1b` | True |
| `runs/E003/model_seed3.npz` | `b23e1025d55cbe88a5b1268e18f0beb486e5b1245bed60ae93b2f87f7b100561` | `b23e1025d55cbe88a5b1268e18f0beb486e5b1245bed60ae93b2f87f7b100561` | True |
| `runs/E003/model_seed4.npz` | `bc5d6d49ead27e745b29f0ca2d9d647f0af53d75fc0273a61f387e3daa9bd2b5` | `bc5d6d49ead27e745b29f0ca2d9d647f0af53d75fc0273a61f387e3daa9bd2b5` | True |

Each artifact was read once into memory; the reservoir was rebuilt from its stored arm, configuration, seed, shot seed and shot count (QRC: 1,024 stored) and equals the saved `res_*` arrays exactly (QRC couplings; ESN W, W_in, b); the readout comes from the saved arrays. The artifacts' stored pipeline revision is `da67af87f8b8fd73`; the current pipeline `55884b1fb66732b9` reproduces their ds2s outputs byte for byte (table above).

## SVDB prediction files

Prediction set (label-free, `positions_svdb.csv` predict flag): 184389 beats of 184583 positions, 78 records.

| File | sha256 | rows | set equal | order = prediction set |
|---|---|---|---|---|
| `runs/E018/E003/pred_svdb_seed0.csv` | `f071f397ba3341e134c8bbbb1edbce726ddfff739f6ad50496aaf83b186b00c7` | 184389 | True | True |
| `runs/E018/E003/pred_svdb_seed1.csv` | `14011e86962486a4d2e7c4e9a70d4b01506404944868c91518a57386997a5a97` | 184389 | True | True |
| `runs/E018/E003/pred_svdb_seed2.csv` | `e700b93a46cff00c994dededd0608d4414bbf48a5fa935bf2c210b3018f9ddcd` | 184389 | True | True |
| `runs/E018/E003/pred_svdb_seed3.csv` | `abb18157e9d3a6e896a2e938af6ad5d8e45562237e843c2c20add3a5f6a4df6e` | 184389 | True | True |
| `runs/E018/E003/pred_svdb_seed4.csv` | `0c800968e0af2841ad4e4b2e5e0362d94ab9b8e848444addebedffd6ffb85050` | 184389 | True | True |
| `runs/E018/E002/pred_svdb_seed0.csv` | `55da4b6fd2233da1099351a6970697e6a2173be6b7182c9d36198f8c4c48698b` | 184389 | True | True |
| `runs/E018/E002/pred_svdb_seed1.csv` | `cf05f375de00fc73f37875f9fbff973b990d23fd642fc0a154336cc8ab1cad5b` | 184389 | True | True |
| `runs/E018/E002/pred_svdb_seed2.csv` | `a19b6a4376ff42447045c36c591deb0c40800325d5baa508c82b7c91f89f890e` | 184389 | True | True |
| `runs/E018/E002/pred_svdb_seed3.csv` | `ce9aa662eaeb29e914e9e28bef06b40df41a9b021769e9157a712f762329b7eb` | 184389 | True | True |
| `runs/E018/E002/pred_svdb_seed4.csv` | `59c7ebaf44b268eb401e19ed86f60e00dbc6012db8afd0f7c058d6ae9a4aee92` | 184389 | True | True |

## Timings

- Feature build svdb: 10.5 s (184389 beats).
- Feature build ds2s_rebuild: 3.2 s (47523 beats).
- Predict E003_ds2s: 24.7 s total for 5 seeds (per seed: 5.1, 4.8, 5.1, 4.6, 5.0 s).
- Predict E003_svdb: 116.8 s total for 5 seeds (per seed: 22.4, 20.6, 20.8, 28.7, 23.5 s).
- Predict E002_ds2s: 2.8 s total for 5 seeds (per seed: 0.8, 0.5, 0.4, 0.5, 0.4 s).
- Predict E002_svdb: 11.6 s total for 5 seeds (per seed: 2.1, 2.0, 1.9, 2.5, 1.7 s).
- Compare preflight (`_smoke_test`, placeholder labels): 26.1 s.
- Placeholder full comparison (8000 replicates): 2019.4 s.

## Notes

- A017: SVDB beat keys are the native 128 Hz beat IDs (batch path, `run.keys_of`), as in every scored file; `pipeline_fn` was not used.
- The selfcheck manifests in `runs/E018/selfcheck_ds2s/` carry split ds2s and point at the original artifacts; they are byte-identical copies of the headline inputs and are not to be scored.
- **Runtime caution:** the scoring is single-threaded CPU work of about 34 min. The access is logged about 1 min in (after the preflight). Run it in the background (not under a 10-minute foreground tool timeout) and do not interrupt it: an interrupted or failed run after logging counts as access 1 of 2. Start by about 21:05 UAE so it ends before the 21:45 hard stop.
- Pipeline revisions: the artifacts record `da67af87f8b8fd73`; predictions and SVDB features use the current `55884b1fb66732b9` (V004: the difference is `tables.py` and the `tune --lambdas` option in `run.py`; `features.py` and `reservoirs.py` unchanged). The 10/10 ds2s hash match and the identical ds2s feature rebuild confirm this for the MIT-BIH path; the SVDB-only branch (128 to 360 Hz `resample_poly`) has no earlier reference.
- `runs/E018/check_e018.py` reproduces every check above; `runs/E018/checks.json` holds the raw results.
