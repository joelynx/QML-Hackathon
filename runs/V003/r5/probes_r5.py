"""V003 re-check of EV1 r5: original probes P1-P5 adapted to the r5 order rules, plus new-hole probes N1-N5.
Synthetic only: PROCESSED, ACCESS_LOG, FULL_EVAL_LOG and (for N1) REFERENCE_PRED_SHA256 are redirected.
Run from the project root:  .venv/Scripts/python -I runs/V003/r5/probes_r5.py
"""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np
import pandas as pd

from qhc import evalspec as E
from qhc import evaluate as ev
from qhc.units import sha256

TMP = os.path.join(ROOT, "runs", "V003", "r5", "probe_tmp")
REAL_CONFIRM = os.path.normcase(os.path.join(ROOT, "runs", "data", "processed", "EV1", "confirm"))
REAL_LOGS = {os.path.normcase(os.path.join(ROOT, "runs", n)) for n in ("confirmation_access.jsonl", "full_eval_log.jsonl")}
_orig = pd.read_csv


def _guard(path, *a, **k):
    if os.path.normcase(os.path.abspath(str(path))).startswith(REAL_CONFIRM):
        raise RuntimeError(f"probe tried to read real confirmation data: {path}")
    return _orig(path, *a, **k)


pd.read_csv = _guard
REAL_REFS = set(E.REFERENCE_PRED_SHA256)
results = {}


def env(name, split, n_rec=8, seed=0, alphabet="NNNNNNSV"):
    d = os.path.join(TMP, name)
    shutil.rmtree(d, ignore_errors=True)
    proc = os.path.join(d, "processed")
    os.makedirs(os.path.join(proc, "confirm"))
    rng = np.random.default_rng(seed)
    spec = {f"r{i}": "".join(rng.choice(list(alphabet), size=60)) for i in range(n_rec)}
    rows = [(f"x:{r}:{i}", r, c, c in E.CLASSES) for r, s in spec.items() for i, c in enumerate(s)]
    lab = pd.DataFrame(rows, columns=["beat_id", "record", "aami", "is_unit"])
    lab.assign(sample=range(len(lab)), fs=128, predict=True)[["beat_id", "record", "sample", "fs", "predict"]].to_csv(
        os.path.join(proc, f"positions_{split}.csv"), index=False)
    pd.DataFrame({"record": sorted(spec), "fs": 128, "sig_len": 230400, "duration_s": 1800.0}).to_csv(
        os.path.join(proc, f"records_{split}.csv"), index=False)
    ldir = os.path.join(proc, "confirm") if split in E.CONFIRMATION_SPLITS else proc
    lab.to_csv(os.path.join(ldir, f"labels_{split}.csv"), index=False)
    ev.PROCESSED, ev.ACCESS_LOG, ev.FULL_EVAL_LOG = proc, os.path.join(d, "access.jsonl"), os.path.join(d, "full.jsonl")
    assert os.path.normcase(ev.ACCESS_LOG) not in REAL_LOGS and os.path.normcase(ev.FULL_EVAL_LOG) not in REAL_LOGS
    E.REFERENCE_PRED_SHA256 = set(REAL_REFS)
    return d, lab


def pred_frame(lab, preds):
    df = pd.DataFrame({"beat_id": lab["beat_id"].to_numpy(), "pred": list(preds)})
    for c in E.CLASSES:
        df[f"prob_{c}"] = (df["pred"] == c).astype(float)
    return df


def runs(d, lab, arm, preds, split, seeds=(0, 1, 2, 3, 4), artifacts=None, shot=True, cfg=None, arm_id=None):
    a = os.path.join(d, arm)
    os.makedirs(a, exist_ok=True)
    files = []
    for j, (s, p) in enumerate(zip(seeds, preds)):
        f, art = os.path.join(a, f"pred_seed{s}_{j}.csv"), os.path.join(a, f"model_seed{s}_{j}.npz")
        pred_frame(lab, p).to_csv(f, index=False)
        open(art, "wb").write(artifacts[j] if artifacts else f"{arm}-{s}-{j}".encode())
        man = {"arm_id": arm_id or arm, "seed": s, "split": split, "config_id": cfg[j] if cfg else "cfg", "code_revision": "probe",
               "model_artifact": art, "model_artifact_sha256": sha256(art), "reservoir_seed": 100 + s,
               "shot_seed": (200 + s) if shot else None, "prediction_sha256": sha256(f)}
        json.dump(man, open(os.path.splitext(f)[0] + ".run.json", "w"))
        files.append(f)
    return files


def cargs(split, role, cand, base, out, extra=()):
    return ["compare", "--split", split, "--role", role, "--cand", *cand, "--base", *base,
            "--cand-id", "Q", "--base-id", "C", "--out", out, *extra]


def attempt(argv):
    try:
        ev.main(argv)
        return "accepted"
    except SystemExit as e:
        return f"refused: {str(e)[:110]}"
    except Exception as e:  # noqa: BLE001
        return f"error: {type(e).__name__}: {str(e)[:110]}"


def noisy(lab, q, s):
    t = np.where(lab["is_unit"], lab["aami"], "N")
    return np.where(np.random.default_rng(s).random(len(lab)) < q, "N", t)


def arms4(d, lab, split="ds2s"):
    return (runs(d, lab, "qA", [noisy(lab, .3, s) for s in range(5)], split),
            runs(d, lab, "eA", [noisy(lab, .2, 10 + s) for s in range(5)], split, shot=False),
            runs(d, lab, "qB", [noisy(lab, .05, 20 + s) for s in range(5)], split),
            runs(d, lab, "eB", [noisy(lab, .2, 30 + s) for s in range(5)], split, shot=False))


# P1: peeks before the headline
d, lab = env("p1", "ds2s")
qA, eA, qB, eB = arms4(d, lab)
o = os.path.join(d, "o.json")
results["P1"] = {"score_quantum": attempt(["score", "--split", "ds2s", "--pred", qA[0], "--id", "q", "--out", o]),
                 "diagnostic_5x5": attempt(cargs("ds2s", "diagnostic", qB, eB, o)),
                 "secondary_A": attempt(cargs("ds2s", "secondary", qA, eA, o)),
                 "lowdata_A": attempt(cargs("ds2s", "lowdata_k5", qA, eA, o)),
                 "headline_B_first": attempt(cargs("ds2s", "headline", qB, eB, o)),
                 "headline_A_after_B": attempt(cargs("ds2s", "headline", qA, eA, o))}

# P1b: low-data run once (after a headline)
d, lab = env("p1b", "ds2s")
qA, eA, qB, eB = arms4(d, lab)
o = os.path.join(d, "o.json")
results["P1b"] = {"headline": attempt(cargs("ds2s", "headline", qA, eA, o)),
                  "lowdata_k5_first": attempt(cargs("ds2s", "lowdata_k5", qA, eA, o)),
                  "lowdata_k5_other_files": attempt(cargs("ds2s", "lowdata_k5", qB, eB, o)),
                  "lowdata_k5_identical": attempt(cargs("ds2s", "lowdata_k5", qA, eA, o))}

# P2 / P2b: copies and mixed configurations
d, lab = env("p2", "ds2s")
one = noisy(lab, .1, 0)
qc = runs(d, lab, "q_copies", [one] * 5, "ds2s", artifacts=[b"same"] * 5)
qid = runs(d, lab, "q_samepred", [one] * 5, "ds2s")  # identical predictions, distinct artifacts: allowed by design
qm = runs(d, lab, "q_mixed", [noisy(lab, .1, s) for s in range(5)], "ds2s", cfg=[f"c{j}" for j in range(5)])
eb = runs(d, lab, "e", [noisy(lab, .2, 10 + s) for s in range(5)], "ds2s", shot=False)
o = os.path.join(d, "o.json")
results["P2_P2b"] = {"copies_same_artifact": attempt(cargs("ds2s", "headline", qc, eb, o)),
                     "mixed_configs": attempt(cargs("ds2s", "headline", qm, eb, o)),
                     "same_arm_id_both_arms": attempt(cargs("ds2s", "headline", runs(d, lab, "e2", [noisy(lab, .1, 50 + s) for s in range(5)], "ds2s", arm_id="e"), eb, o)),
                     "identical_preds_distinct_artifacts": attempt(cargs("ds2s", "headline", qid, eb, o))}

# P3 / P4: confirmation failure paths and repair binding
d, lab = env("p3", "svdb", n_rec=10, seed=3, alphabet="NNNNNSSVFQ")
qs = runs(d, lab, "q", [noisy(lab, .05, s) for s in range(5)], "svdb")
es = runs(d, lab, "e", [noisy(lab, .3, 10 + s) for s in range(5)], "svdb", shot=False)
blocker = os.path.join(d, "file.txt")
open(blocker, "w").write("x")
r = {"unwritable_out": attempt(cargs("svdb", "confirmation", qs, es, os.path.join(blocker, "c.json"),
                                     ["--confirm-reason", "final"]))}
r["access_log_after_unwritable"] = len(ev._log_lines(ev.ACCESS_LOG))
r["first_access"] = attempt(cargs("svdb", "confirmation", qs, es, os.path.join(d, "c1.json"), ["--confirm-reason", "final"]))
q_other = runs(d, lab, "q_other", [noisy(lab, .01, 40 + s) for s in range(5)], "svdb")
r["repair_other_models"] = attempt(cargs("svdb", "confirmation", q_other, es, os.path.join(d, "c2.json"),
                                         ["--confirm-reason", "r", "--repair-reason", "x"]))
r["repair_same_models"] = attempt(cargs("svdb", "confirmation", qs, es, os.path.join(d, "c2.json"),
                                        ["--confirm-reason", "r", "--repair-reason", "x"]))
r["access_log_final"] = len(ev._log_lines(ev.ACCESS_LOG))
results["P3_P4"] = r

# P5: path spelling of an identical headline rerun
d, lab = env("p5", "ds2s")
qA, eA, _, _ = arms4(d, lab)
o = os.path.join(d, "o.json")
rel = lambda fs: [os.path.relpath(f, os.getcwd()) for f in fs]
results["P5"] = {"headline_relative": attempt(cargs("ds2s", "headline", rel(qA), rel(eA), o)),
                 "identical_absolute": attempt(cargs("ds2s", "headline", qA, eA, o)),
                 "arms_swapped": attempt(cargs("ds2s", "headline", eA, qA, o))}

# N1: a reference-only "headline" opens the post-headline gate (score/secondary/low-data) for a non-reference model
d, lab = env("n1", "ds2s")
const = ["N"] * len(lab)
rr = noisy(lab, .5, 99)
rc = runs(d, lab, "ref_const", [const] * 5, "ds2s", shot=False)   # five copies of one reference prediction
rb = runs(d, lab, "ref_rr", [rr] * 5, "ds2s", shot=False)
E.REFERENCE_PRED_SHA256 = set(REAL_REFS) | {sha256(rc[0]), sha256(rb[0])}  # simulate: these are the reference files
qA, eA, qB, eB = arms4(d, lab)
o = os.path.join(d, "o.json")
results["N1_reference_headline_opens_gate"] = {
    "headline_with_reference_copies": attempt(cargs("ds2s", "headline", rc, rb, o)),
    "score_quantum_before_real_headline": attempt(["score", "--split", "ds2s", "--pred", qA[0], "--id", "q", "--out", o]),
    "secondary_quantum_pair": attempt(cargs("ds2s", "secondary", qA, eA, o)),
    "lowdata_k5_quantum_pair": attempt(cargs("ds2s", "lowdata_k5", qA, eA, o)),
    "real_headline_afterwards": attempt(cargs("ds2s", "headline", qB, eB, o)),
}

# N2: SVDB confirmation is allowed before any headline exists
d, lab = env("n2", "svdb", n_rec=10, seed=3, alphabet="NNNNNSSVFQ")
qs = runs(d, lab, "q", [noisy(lab, .05, s) for s in range(5)], "svdb")
es = runs(d, lab, "e", [noisy(lab, .3, 10 + s) for s in range(5)], "svdb", shot=False)
results["N2_confirmation_before_headline"] = attempt(cargs("svdb", "confirmation", qs, es, os.path.join(d, "c.json"),
                                                           ["--confirm-reason", "early"]))

# N3: identical headline rerun after a later secondary
d, lab = env("n3", "ds2s")
qA, eA, qB, eB = arms4(d, lab)
o = os.path.join(d, "o.json")
results["N3_identical_rerun_after_secondary"] = {
    "headline": attempt(cargs("ds2s", "headline", qA, eA, o)),
    "secondary": attempt(cargs("ds2s", "secondary", qB, eB, o)),
    "identical_headline_rerun": attempt(cargs("ds2s", "headline", qA, eA, o))}

# N4: --out pointing at one of the input prediction files (non-confirmation path)
d, lab = env("n4", "ds2s")
qA, eA, _, _ = arms4(d, lab)
before = sha256(qA[0])
results["N4_out_overwrites_input"] = {"run": attempt(cargs("ds2s", "headline", qA, eA, qA[0])),
                                      "input_overwritten": sha256(qA[0]) != before}

# N5: test-split labels are not guarded outside the CLI
d, lab = env("n5", "ds2s")
try:
    ev.load_labels("ds2s")
    results["N5_load_labels_ds2s_direct"] = "readable without any order check"
except Exception as e:  # noqa: BLE001
    results["N5_load_labels_ds2s_direct"] = f"guarded: {e}"

E.REFERENCE_PRED_SHA256 = set(REAL_REFS)
json.dump(results, open(os.path.join(ROOT, "runs", "V003", "r5", "probe_results_r5.json"), "w"), indent=1)
print(json.dumps(results, indent=1))
