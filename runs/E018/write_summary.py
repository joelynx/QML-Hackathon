"""Compose runs/E018/summary.json and summary.md from the E018 logs and checks (no labels read)."""
import json
import os
import sys

from qhc import evaluate as V
from qhc.p4 import code_revision, module_revision

ROOT = V.ROOT
D = os.path.join(ROOT, "runs", "E018")
ENV = "CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8"
PY = ".venv/Scripts/python -I"
REASON = ("E018: pre-registered SVDB confirmation (EVAL.md, criterion fixed 2026-10-26) of the frozen headline pair "
          "E003 (QRC, candidate) vs E002 (ESN, baseline). Predictions from the exact DS1-trained artifacts runs/E003 "
          "and runs/E002 model_seed0-4.npz via the A018 predict-only path (qhc.p4.predict {rev}); its ds2s self-check "
          "reproduced all 10 logged headline prediction hashes. Pass: delta above 0 and 95 percent CI lower bound above 0.")


def load(name):
    p = os.path.join(D, name)
    return json.load(open(p)) if os.path.exists(p) else None


def main():
    checks = load("checks.json")
    rev = module_revision("predict")
    cand = [f"runs/E018/E003/pred_svdb_seed{s}.csv" for s in range(5)]
    base = [f"runs/E018/E002/pred_svdb_seed{s}.csv" for s in range(5)]
    reason = REASON.format(rev=rev)
    confirm = (f"{PY} -m qhc.evaluate compare --split svdb --role confirmation --cand {' '.join(cand)} "
               f"--base {' '.join(base)} --cand-id E003 --base-id E002 --out runs/E018/confirm_svdb.json "
               f"--confirm-reason \"{reason}\"")
    commands = {
        "build_svdb_features": f"{ENV} {PY} -m qhc.p4.predict build-features --split svdb --features-dir runs/E018/features",
        "build_ds2s_features_check": f"{ENV} {PY} -m qhc.p4.predict build-features --split ds2s "
                                     "--features-dir runs/E018/features_ds2s_rebuild",
        "selfcheck_ds2s": [f"{ENV} {PY} -m qhc.p4.predict predict --exp {e} --split ds2s --out runs/E018/selfcheck_ds2s/{e}"
                           for e in ("E003", "E002")],
        "predict_svdb": [f"{ENV} {PY} -m qhc.p4.predict predict --exp {e} --split svdb --out runs/E018/{e} "
                         "--features-dir runs/E018/features" for e in ("E003", "E002")],
        "checks": f"{ENV} {PY} runs/E018/check_e018.py --smoke --runtime",
        "confirmation_bash": f"{ENV} {confirm} 2>&1 | tee runs/E018/confirm_svdb_stdout.txt",
        "confirmation_powershell": "$env:CUDA_VISIBLE_DEVICES='0'; $env:OMP_NUM_THREADS='8'; $env:MKL_NUM_THREADS='8'; "
                                   + confirm.replace(".venv/Scripts/python", ".venv\\Scripts\\python.exe")
                                   + " | Tee-Object -FilePath runs/E018/confirm_svdb_stdout.txt",
    }
    pred = {f"{e}_{s}": load(f"{e}/predict_{s}.json") if s == "svdb" else load(f"selfcheck_ds2s/{e}/predict_{s}.json")
            for e in ("E003", "E002") for s in ("ds2s", "svdb")}
    builds = {"svdb": load("features/build_svdb.json"), "ds2s_rebuild": load("features_ds2s_rebuild/build_ds2s.json")}
    rt = load("runtime_estimate.json")
    artifacts = {}
    for k, v in pred.items():
        if v:
            for r in v["runs"]:
                a = artifacts.setdefault(r["artifact"], {"sha256_before": r["artifact_sha256_before"], "after": set()})
                a["after"].add(r["artifact_sha256_after"])
                if r["artifact_sha256_before"] != a["sha256_before"]:
                    a["after"].add("MISMATCH")
    artifacts = {k: {"sha256_before": v["sha256_before"], "sha256_after": sorted(v["after"]),
                     "unchanged": v["after"] == {v["sha256_before"]}} for k, v in artifacts.items()}
    summary = {"experiment": "E018", "lane": "CPU A", "code_revision": code_revision("predict"),
               "p4_predict_revision_now": rev, "commands": commands, "confirm_reason": reason,
               "selfcheck_all_match": checks["selfcheck_all_match"], "selfcheck": checks["selfcheck"],
               "ds2s_feature_rebuild_identical": checks.get("ds2s_rebuild_identical"),
               "artifacts": artifacts, "artifact_dirs_untouched": checks["artifacts_untouched"],
               "svdb_checks": checks.get("svdb"), "smoke_test": checks.get("smoke_test"),
               "preconditions": checks["preconditions"], "feature_builds": builds, "predict_logs": pred,
               "runtime_estimate": rt}
    with open(os.path.join(D, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1, default=str)

    L = []
    w = L.append
    w("# E018 preparation summary (CPU A lane)\n")
    w("Label-free preparation of the pre-registered SVDB confirmation of the frozen headline pair E003 (QRC) vs E002 "
      "(ESN). Nothing was scored; no file under `runs/data/processed/EV1/confirm/` was opened; `runs/E002/` and "
      "`runs/E003/` were only read.\n")
    w(f"- **Code revision:** `{summary['code_revision']}` (new module `src/qhc/p4/predict.py`; evaluation and pipeline code unchanged).")
    w(f"- **Self-check (ds2s, hashes only):** {sum(r['match'] for r in checks['selfcheck'])} of {len(checks['selfcheck'])} "
      "logged headline prediction hashes reproduced from the saved artifacts.")
    w(f"- **SVDB predictions:** 5 per arm in `runs/E018/E003/` and `runs/E018/E002/`, label-free checks passed "
      f"(check_runs, scorer.validate against the prediction set, --out check){'; compare preflight on placeholder labels passed' if checks.get('smoke_test') else ''}.")
    w(f"- **Artifacts untouched:** {checks['artifacts_untouched']['files_before']} files in `runs/E002/` and `runs/E003/`, "
      f"sha256 + size + mtime identical before and after: {checks['artifacts_untouched']['identical']}.\n")
    w("## Confirmation command (for the coordinator)\n")
    w("Run from the project root. Bash:\n")
    w("```bash\n" + commands["confirmation_bash"] + "\n```\n")
    w("PowerShell:\n")
    w("```powershell\n" + commands["confirmation_powershell"] + "\n```\n")
    w("Order inside the command (src/qhc/evaluate.py, `cmd_compare` then `_confirmation_access`): role/split check; "
      "`check_runs` on both arms (5 seeded runs, manifests bound by hash to predictions and artifacts); cross-arm checks; "
      "`_check_out(..., new_file=True)`; `--confirm-reason` present; a logged ds2s headline; `scorer.validate` of all 10 "
      "files against the label-free prediction set; `_check_writable`; **`_smoke_test` (placeholder labels, 20 "
      "replicates)**; cap check (0 used of 2); **only then** the append to `runs/confirmation_access.jsonl`, then "
      "`runs/full_eval_log.jsonl`, then the label read, the archive `runs/confirmation_reports/access_1.json` + "
      "`index.jsonl`, and finally `--out`. After it runs, the access must be added to the EVAL.md access-log table "
      "(bookkeeping).\n")
    pc = checks["preconditions"]
    w(f"Preconditions now: headline logged {pc['headline_logged']}; `runs/confirmation_access.jsonl` exists "
      f"{pc['access_log_exists']}; `runs/confirmation_reports/` exists {pc['confirmation_reports_dir_exists']}; "
      f"`runs/E018/confirm_svdb.json` exists {checks.get('svdb', {}).get('out_check', {}).get('exists')}; "
      f"evaluation revision `{pc['eval_code_revision']}`; dominant record for svdb: {pc['dominant_record_svdb']}.\n")
    if rt:
        w(f"**Runtime estimate:** the same comparison on placeholder labels at {rt['n_boot']} replicates "
          f"({rt['units']} units) took {rt['seconds']} s ({rt['seconds'] / 60:.1f} min) on this machine; "
          f"the smoke test adds {checks.get('smoke_test', {}).get('seconds')} s. Expect about "
          f"{(rt['seconds'] + (checks.get('smoke_test') or {}).get('seconds', 0)) / 60 + 1:.0f} min end to end.\n")
    w("## Self-check: logged vs reproduced (ds2s)\n")
    w("| Logged file | Logged sha256 | Reproduced sha256 | Match |")
    w("|---|---|---|---|")
    for r in checks["selfcheck"]:
        w(f"| `{r['logged_file']}` | `{r['logged_sha256']}` | `{r['reproduced_sha256']}` | {r['match']} |")
    w("\nThe reproduced manifests differ from the headline manifests only in `code_revision` (plus added provenance keys). "
      "Features: the existing `runs/features/EV1/ds2s.npz` (pipe `697d9992c5fe5811`); a fresh rebuild with the current "
      f"pipeline into `runs/E018/features_ds2s_rebuild/` is array-identical: {checks.get('ds2s_rebuild_identical')}. "
      "SVDB features were built by the same `features.build_split` into `runs/E018/features/svdb.npz`.\n")
    w("## Model artifacts (sha256 before / after)\n")
    w("| Artifact | sha256 before | after | unchanged |")
    w("|---|---|---|---|")
    for k, v in sorted(artifacts.items()):
        w(f"| `{k}` | `{v['sha256_before']}` | `{', '.join(v['sha256_after'])}` | {v['unchanged']} |")
    w("\nEach artifact was read once into memory; the reservoir was rebuilt from its stored arm, configuration, seed, "
      "shot seed and shot count (QRC: 1,024 stored) and equals the saved `res_*` arrays exactly (QRC couplings; ESN W, "
      "W_in, b); the readout comes from the saved arrays. The artifacts' stored pipeline revision is `da67af87f8b8fd73`; "
      "the current pipeline `55884b1fb66732b9` reproduces their ds2s outputs byte for byte (table above).\n")
    if checks.get("svdb"):
        w("## SVDB prediction files\n")
        ps = checks["svdb"]["prediction_set"]
        w(f"Prediction set (label-free, `positions_svdb.csv` predict flag): {ps['prediction_set_rows']} beats of "
          f"{ps['positions_rows']} positions, {ps['records']} records.\n")
        w("| File | sha256 | rows | set equal | order = prediction set |")
        w("|---|---|---|---|---|")
        for f, v in checks["svdb"]["validate"].items():
            w(f"| `{f}` | `{v['sha256']}` | {v['rows']} | {v['set_equal']} | {v['order_equals_prediction_set']} |")
        w("")
    w("## Timings\n")
    for k, b in builds.items():
        if b:
            w(f"- Feature build {k}: {b['seconds']} s ({b['n_beats']} beats).")
    for k, v in pred.items():
        if v:
            w(f"- Predict {k}: {v['total_seconds']} s total for 5 seeds (per seed: "
              f"{', '.join(str(r['seconds']) for r in v['runs'])} s).")
    if checks.get("smoke_test"):
        w(f"- Compare preflight (`_smoke_test`, placeholder labels): {checks['smoke_test']['seconds']} s.")
    if rt:
        w(f"- Placeholder full comparison ({rt['n_boot']} replicates): {rt['seconds']} s.")
    w("\n## Notes\n")
    w("- A017: SVDB beat keys are the native 128 Hz beat IDs (batch path, `run.keys_of`), as in every scored file; "
      "`pipeline_fn` was not used.")
    w("- The selfcheck manifests in `runs/E018/selfcheck_ds2s/` carry split ds2s and point at the original artifacts; "
      "they are byte-identical copies of the headline inputs and are not to be scored.")
    w("- **Runtime caution:** the scoring is single-threaded CPU work of about 34 min. The access is logged about 1 min "
      "in (after the preflight). Run it in the background (not under a 10-minute foreground tool timeout) and do not "
      "interrupt it: an interrupted or failed run after logging counts as access 1 of 2. Start by about 21:05 UAE so it "
      "ends before the 21:45 hard stop.")
    w("- Pipeline revisions: the artifacts record `da67af87f8b8fd73`; predictions and SVDB features use the current "
      "`55884b1fb66732b9` (V004: the difference is `tables.py` and the `tune --lambdas` option in `run.py`; "
      "`features.py` and `reservoirs.py` unchanged). The 10/10 ds2s hash match and the identical ds2s feature rebuild "
      "confirm this for the MIT-BIH path; the SVDB-only branch (128 to 360 Hz `resample_poly`) has no earlier reference.")
    w("- `runs/E018/check_e018.py` reproduces every check above; `runs/E018/checks.json` holds the raw results.")
    with open(os.path.join(D, "summary.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print("wrote summary.md / summary.json")


if __name__ == "__main__":
    sys.exit(main())
