"""V004 critic reproduction of E002 (R0) from features onward, into runs/V004/ only.

Features are rebuilt into runs/V004/features (the shared runs/features/EV1 is not touched), compared with the shared
copy, and then used for a full retune (--exp V004/R0), the final runs (seeds 0-4 with OOF and ds2s; seeds 5-9 OOF) and
the lookahead check. No test-split labels are read: the pipeline reads labels_ds1.csv only.
"""
import hashlib
import json
import os
import sys
import time

import numpy as np

import qhc.pipe.features as F

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "runs", "V004")
F.FEATURE_DIR = os.path.join(OUT, "features")

from qhc.pipe import run as R  # noqa: E402

log = {"pipe_revision_loaded": R.PIPE_REV, "steps": {}}


def step(name, fn):
    t = time.time()
    print(f"\n=== {name}", flush=True)
    res = fn()
    log["steps"][name] = {"seconds": round(time.time() - t, 1), "result": res}
    with open(os.path.join(OUT, "driver_log.json"), "w") as f:
        json.dump(log, f, indent=1, default=str)
    return res


def feats():
    out = {}
    for s in ("ds1", "ds2s"):
        p, n = F.build_split(s)
        a = np.load(p)
        b = np.load(os.path.join(ROOT, "runs", "features", "EV1", f"{s}.npz"))
        out[s] = {"n": n, "shared_pipe_revision": str(b["pipe_revision"]),
                  "identical": {k: bool(np.array_equal(a[k], b[k])) for k in ("beat_id", "record", "win", "rel", "rr")}}
    return out


if __name__ == "__main__":
    steps = sys.argv[1:] or ["features", "tune", "final04", "final59", "leakcheck"]
    if "features" in steps:
        step("features", feats)
    if "tune" in steps:
        step("tune", lambda: R.main(["tune", "--arm", "esn", "--exp", "V004/R0"]))
    if "final04" in steps:
        step("final04", lambda: R.main(["final", "--exp", "V004/R0", "--seeds", "0", "1", "2", "3", "4", "--oof",
                                        "--splits", "ds2s"]))
    if "final59" in steps:
        step("final59", lambda: R.main(["final", "--exp", "V004/R0", "--seeds", "5", "6", "7", "8", "9", "--oof"]))
    if "leakcheck" in steps:
        step("leakcheck", lambda: R.main(["leakcheck", "--exp", "V004/R0", "--seed", "0"]))
    print("done", flush=True)
