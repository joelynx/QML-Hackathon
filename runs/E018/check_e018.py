"""E018 label-free checks (CPU A lane). Reads no labels and nothing under runs/data/processed/EV1/confirm/.

  .venv/Scripts/python -I runs/E018/check_e018.py [--smoke] [--runtime]

1. Self-check: the 10 reproduced ds2s files (runs/E018/selfcheck_ds2s/) against the 10 hashes logged in the headline
   entry of runs/full_eval_log.jsonl (hashes only; nothing is scored).
2. SVDB prediction files: qhc.evaluate.check_runs per arm, the cross-arm checks of cmd_compare, scorer.validate against
   the label-free prediction set (positions_svdb.csv, predict flag), the --out check of cmd_compare (new file).
3. Preconditions of the confirmation access: a logged headline, no access log, no archived report.
4. --smoke: the compare preflight evaluate._smoke_test (placeholder labels cycling N/S/V, 20 replicates), timed.
   --runtime: the same placeholder comparison at the full N_BOOT replicates, timed (runtime estimate only; its
   numbers are meaningless and are not stored).
5. runs/E002 and runs/E003 untouched: every file's sha256, size and mtime against the snapshot taken before E018.
Writes runs/E018/checks.json (and runtime_estimate.json with --runtime).
"""
import argparse
import glob
import hashlib
import json
import os
import sys
import time

import numpy as np
import pandas as pd

from qhc import evalspec as E
from qhc import evaluate as V
from qhc import scorer

ROOT = V.ROOT
OUT = "runs/E018/confirm_svdb.json"
EXPS = (("E003", "candidate"), ("E002", "baseline"))


def sha(path):
    with open(os.path.join(ROOT, path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def snapshot():
    out = {}
    for d in ("runs/E002", "runs/E003"):
        for f in sorted(glob.glob(os.path.join(ROOT, d, "**", "*"), recursive=True)):
            if os.path.isfile(f):
                st = os.stat(f)
                out[os.path.relpath(f, ROOT).replace(os.sep, "/")] = {"sha256": sha(f), "size": st.st_size,
                                                                     "mtime_ns": st.st_mtime_ns}
    return out


def selfcheck():
    log = [json.loads(x) for x in open(os.path.join(ROOT, "runs", "full_eval_log.jsonl")) if x.strip()]
    head = [e for e in log if e.get("role") == "headline" and e.get("split") == "ds2s"]
    files = head[-1]["files"]
    assert all(e["files"] == files for e in head), "headline entries disagree"
    rows = []
    for f, h in files.items():
        exp, name = f.split("/")[1], f.split("/")[2]
        rep = f"runs/E018/selfcheck_ds2s/{exp}/{name}"
        got = sha(rep) if os.path.exists(os.path.join(ROOT, rep)) else None
        man = json.load(open(os.path.join(ROOT, os.path.splitext(rep)[0] + ".run.json")))
        src = json.load(open(os.path.join(ROOT, os.path.splitext(f)[0] + ".run.json")))
        changed = sorted(k for k in src if src[k] != man.get(k))
        rows.append({"logged_file": f, "logged_sha256": h, "reproduced_file": rep, "reproduced_sha256": got,
                     "match": got == h, "manifest_keys_changed_vs_headline": changed,
                     "headline_entries": [e["time"] for e in head]})
    return rows


def svdb_files():
    return {exp: sorted(glob.glob(os.path.join(ROOT, "runs", "E018", exp, "pred_svdb_seed*.csv"))) for exp, _ in EXPS}


def svdb_checks(files):
    res = {}
    runs = {}
    for exp, arm in EXPS:
        r = V.check_runs([os.path.relpath(f, ROOT) for f in files[exp]], "svdb", arm)
        runs[arm] = r
        res[f"check_runs_{arm}"] = {"passed": True, "seeds": [x["seed"] for x in r], "arm_id": r[0]["arm_id"],
                                    "config_id": r[0]["config_id"],
                                    "artifacts": {x["seed"]: [x["model_artifact"], x["model_artifact_sha256"]] for x in r}}
    c, b = runs["candidate"], runs["baseline"]
    assert c[0]["arm_id"] != b[0]["arm_id"], "same arm_id in both arms"
    assert sorted(x["seed"] for x in c) == sorted(x["seed"] for x in b), "seed indices differ"
    res["cross_arm"] = {"distinct_arm_ids": True, "same_seeds": True}
    pos = V.load_positions("svdb")
    pset = V.prediction_set("svdb")
    want = set(pset["beat_id"])
    res["prediction_set"] = {"positions_rows": int(len(pos)), "predict_true": int(pos["predict"].sum()),
                             "prediction_set_rows": int(len(pset)), "records": int(pset["record"].nunique())}
    per_file = {}
    preds = {}
    for exp, arm in EXPS:
        for f in files[exp]:
            p = V._read_pred(f)
            scorer.validate(p, pset)  # raises on any defect
            per_file[os.path.relpath(f, ROOT).replace(os.sep, "/")] = {
                "rows": int(len(p)), "set_equal": set(p["beat_id"]) == want, "duplicates": int(p["beat_id"].duplicated().sum()),
                "order_equals_prediction_set": bool((p["beat_id"].to_numpy() == pset["beat_id"].to_numpy()).all())
                if len(p) == len(pset) else False,
                "pred_counts": {k: int(v) for k, v in p["pred"].value_counts().items()}, "sha256": sha(f)}
            preds.setdefault(arm, []).append(p)
    res["validate"] = per_file
    cf = [r["_file"] for r in c]
    bf = [r["_file"] for r in b]
    V._check_out(OUT, cf + bf, c + b, new_file=True)
    res["out_check"] = {"out": OUT, "exists": os.path.exists(os.path.join(ROOT, OUT)), "passed": True}
    return res, preds, cf, bf


def preconditions():
    log = V._log_lines(V.FULL_EVAL_LOG)
    return {"headline_logged": bool(V._headline_entries(log)), "access_log_exists": os.path.exists(V.ACCESS_LOG),
            "confirmation_reports_dir_exists": os.path.exists(V.CONFIRM_REPORTS),
            "access_1_report_exists": os.path.exists(V._report_paths(1)[0]),
            "dominant_record_svdb": E.DOMINANT_RECORD.get("svdb"), "cap": E.CONFIRMATION_CAP,
            "eval_code_revision": V.code_revision()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--runtime", action="store_true")
    a = ap.parse_args()
    os.chdir(ROOT)
    out = {"time": pd.Timestamp.now(tz="Asia/Dubai").isoformat(timespec="seconds")}
    out["selfcheck"] = selfcheck()
    out["selfcheck_all_match"] = all(r["match"] for r in out["selfcheck"])
    fa = np.load(os.path.join(ROOT, "runs", "features", "EV1", "ds2s.npz"))
    fb = np.load(os.path.join(ROOT, "runs", "E018", "features_ds2s_rebuild", "ds2s.npz"))
    out["ds2s_rebuild_identical"] = all(fa[k].dtype == fb[k].dtype and np.array_equal(fa[k], fb[k])
                                        for k in ("beat_id", "record", "win", "rel", "rr"))
    print("self-check:", sum(r["match"] for r in out["selfcheck"]), "of", len(out["selfcheck"]), "match")
    files = svdb_files()
    if all(len(v) == E.N_SEEDS for v in files.values()):
        res, preds, cf, bf = svdb_checks(files)
        out["svdb"] = res
        print("svdb: check_runs, validate and out-check passed for both arms")
        if a.smoke:
            t = time.time()
            V._smoke_test("svdb", [V._read_pred(f) for f in cf], [V._read_pred(f) for f in bf])
            out["smoke_test"] = {"passed": True, "seconds": round(time.time() - t, 1)}
            print("smoke test passed", out["smoke_test"])
        if a.runtime:
            pset = V.prediction_set("svdb")
            fake = pset.assign(aami=np.array(E.CLASSES)[np.arange(len(pset)) % len(E.CLASSES)], is_unit=True)
            t = time.time()
            scorer.compare(preds["candidate"], preds["baseline"], fake, hours=V.load_hours("svdb"),
                           role="confirmation", dominant_record=E.DOMINANT_RECORD.get("svdb"))
            rt = {"n_boot": E.N_BOOT, "seconds": round(time.time() - t, 1), "units": int(len(fake)),
                  "note": "placeholder labels (cycling N/S/V, every prediction-set beat a unit); results discarded"}
            json.dump(rt, open(os.path.join(ROOT, "runs", "E018", "runtime_estimate.json"), "w"), indent=1)
            print("runtime estimate", rt)
    out["preconditions"] = preconditions()
    before = json.load(open(os.path.join(ROOT, "runs", "E018", "snapshot_E002_E003_before.json")))
    now = snapshot()
    out["artifacts_untouched"] = {"files_before": len(before), "files_after": len(now), "identical": before == now,
                                  "differences": sorted(k for k in set(before) | set(now) if before.get(k) != now.get(k))}
    with open(os.path.join(ROOT, "runs", "E018", "checks.json"), "w") as f:
        json.dump(out, f, indent=1, default=str)
    print(json.dumps({k: out[k] for k in ("selfcheck_all_match", "preconditions", "artifacts_untouched")}, default=str))


if __name__ == "__main__":
    sys.exit(main())
