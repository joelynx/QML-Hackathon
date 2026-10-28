"""V003 synthetic probes of EV1 r4 (never touches real test labels, confirm/, or the real logs).

Run from the project root:  .venv/Scripts/python -I runs/V003/probes.py
Every probe builds its own synthetic split under runs/V003/probe_tmp/<name>/ and monkeypatches qhc.evaluate's
PROCESSED, ACCESS_LOG and FULL_EVAL_LOG to it.
"""
import json
import os
import shutil
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "src"))

import numpy as np
import pandas as pd

from qhc import evalspec as E
from qhc import evaluate as ev
from qhc import scorer
from qhc.units import sha256

TMP = os.path.join(ROOT, "runs", "V003", "probe_tmp")
REAL_CONFIRM = os.path.normcase(os.path.join(ROOT, "runs", "data", "processed", "EV1", "confirm"))
REAL_LOGS = {os.path.normcase(os.path.join(ROOT, "runs", n)) for n in ("confirmation_access.jsonl", "full_eval_log.jsonl")}

# Guard: refuse to read anything under the real confirm/ directory.
_orig_read_csv = pd.read_csv


def _guarded_read_csv(path, *a, **k):
    if os.path.normcase(os.path.abspath(str(path))).startswith(REAL_CONFIRM):
        raise RuntimeError(f"probe tried to read real confirmation data: {path}")
    return _orig_read_csv(path, *a, **k)


pd.read_csv = _guarded_read_csv
results = {}


def env(name, split, n_rec=8, seed=0, alphabet="NNNNNNSV"):
    d = os.path.join(TMP, name)
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "processed", "confirm"))
    rng = np.random.default_rng(seed)
    spec = {f"r{i}": "".join(rng.choice(list(alphabet), size=60)) for i in range(n_rec)}
    rows = [(f"x:{r}:{i}", r, c, c in E.CLASSES) for r, s in spec.items() for i, c in enumerate(s)]
    lab = pd.DataFrame(rows, columns=["beat_id", "record", "aami", "is_unit"])
    proc = os.path.join(d, "processed")
    lab.assign(sample=range(len(lab)), fs=128, predict=True)[["beat_id", "record", "sample", "fs", "predict"]].to_csv(
        os.path.join(proc, f"positions_{split}.csv"), index=False)
    pd.DataFrame({"record": sorted(spec), "fs": 128, "sig_len": 230400, "duration_s": 1800.0}).to_csv(
        os.path.join(proc, f"records_{split}.csv"), index=False)
    ldir = os.path.join(proc, "confirm") if split in E.CONFIRMATION_SPLITS else proc
    lab.to_csv(os.path.join(ldir, f"labels_{split}.csv"), index=False)
    ev.PROCESSED = proc
    ev.ACCESS_LOG = os.path.join(d, "access.jsonl")
    ev.FULL_EVAL_LOG = os.path.join(d, "full_eval.jsonl")
    assert os.path.normcase(ev.ACCESS_LOG) not in REAL_LOGS and os.path.normcase(ev.FULL_EVAL_LOG) not in REAL_LOGS
    return d, lab


def pred_frame(lab, preds):
    df = pd.DataFrame({"beat_id": lab["beat_id"].to_numpy(), "pred": list(preds)})
    for c in E.CLASSES:
        df[f"prob_{c}"] = (df["pred"] == c).astype(float)
    return df


def runs(d, lab, arm, preds, split, seeds=(0, 1, 2, 3, 4), config_ids=None, arm_ids=None, artifacts=None, shot=True):
    """Prediction file + model artifact + run manifest per seed. `artifacts` may supply shared artifact contents."""
    a = os.path.join(d, arm)
    os.makedirs(a, exist_ok=True)
    files = []
    for j, (s, p) in enumerate(zip(seeds, preds)):
        f, art = os.path.join(a, f"pred_seed{s}_{j}.csv"), os.path.join(a, f"model_seed{s}_{j}.npz")
        pred_frame(lab, p).to_csv(f, index=False)
        with open(art, "wb") as fh:
            fh.write(artifacts[j] if artifacts else f"{arm}-{s}-{j}".encode())
        man = {"arm_id": (arm_ids[j] if arm_ids else arm), "seed": s, "split": split,
               "config_id": (config_ids[j] if config_ids else "cfg"), "code_revision": "probe",
               "model_artifact": art, "model_artifact_sha256": sha256(art), "reservoir_seed": 100 + s,
               "shot_seed": (200 + s) if shot else None, "prediction_sha256": sha256(f)}
        with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
            json.dump(man, fh)
        files.append(f)
    return files


def cmp_args(split, role, cand, base, out, extra=()):
    return ["compare", "--split", split, "--role", role, "--cand", *cand, "--base", *base,
            "--cand-id", "Q", "--base-id", "C", "--out", out, *extra]


def attempt(argv):
    try:
        ev.main(argv)
        return "accepted"
    except SystemExit as e:
        return f"refused: {e}"
    except Exception as e:  # noqa: BLE001
        return f"error: {type(e).__name__}: {e}"


def noisy(lab, q, s):
    t = lab["aami"].to_numpy()
    t = np.where(np.isin(t, E.CLASSES), t, "N")
    return np.where(np.random.default_rng(s).random(len(lab)) < q, "N", t)


# ---- P1: headline can be chosen after ds2s peeks (score / diagnostic / secondary) ----
d, lab = env("p1_headline_after_peeks", "ds2s")
qA = runs(d, lab, "qA", [noisy(lab, 0.30, s) for s in range(5)], "ds2s")
eA = runs(d, lab, "eA", [noisy(lab, 0.20, 10 + s) for s in range(5)], "ds2s", shot=False)
qB = runs(d, lab, "qB", [noisy(lab, 0.05, 20 + s) for s in range(5)], "ds2s")
eB = runs(d, lab, "eB", [noisy(lab, 0.20, 30 + s) for s in range(5)], "ds2s", shot=False)
out = os.path.join(d, "o.json")
r = {
    "score_quantum_candidate_on_ds2s": attempt(["score", "--split", "ds2s", "--pred", qA[0], "--id", "qA", "--out", out]),
    "diagnostic_5x5_no_manifest_check_on_ds2s": attempt(cmp_args("ds2s", "diagnostic", qB, eB, out)),
    "secondary_pair_A_on_ds2s": attempt(cmp_args("ds2s", "secondary", qA, eA, out)),
    "headline_pair_B_after_seeing_A_and_B": attempt(cmp_args("ds2s", "headline", qB, eB, out)),
}
r["full_eval_log_entries"] = [(e["cmd"], e["role"]) for e in ev._log_lines(ev.FULL_EVAL_LOG)]
results["P1_headline_after_peeks"] = r

# ---- P1b: lowdata slice-family members are not immutable ----
d, lab = env("p1b_lowdata_rerun", "ds2s")
q1 = runs(d, lab, "q1", [noisy(lab, 0.30, s) for s in range(5)], "ds2s")
e1 = runs(d, lab, "e1", [noisy(lab, 0.20, 10 + s) for s in range(5)], "ds2s", shot=False)
q2 = runs(d, lab, "q2", [noisy(lab, 0.05, 20 + s) for s in range(5)], "ds2s")
e2 = runs(d, lab, "e2", [noisy(lab, 0.20, 30 + s) for s in range(5)], "ds2s", shot=False)
out = os.path.join(d, "o.json")
r = {"lowdata_k5_first": attempt(cmp_args("ds2s", "lowdata_k5", q1, e1, out))}
r["first_slice"] = json.load(open(out))["slices"]["members"]["lowdata_k5"]["decision"]
r["lowdata_k5_second_different_files"] = attempt(cmp_args("ds2s", "lowdata_k5", q2, e2, out))
r["second_slice"] = json.load(open(out))["slices"]["members"]["lowdata_k5"]["decision"]
results["P1b_lowdata_not_immutable"] = r

# ---- P2: five copies of one run pass the strict-role checks when copied under new names ----
d, lab = env("p2_copies", "ds2s")
one = noisy(lab, 0.1, 0)
same_art = [b"identical-model"] * 5
qc = runs(d, lab, "q_copies", [one] * 5, "ds2s", artifacts=same_art)  # same predictions, same artifact bytes
eb = runs(d, lab, "e", [noisy(lab, 0.2, 10 + s) for s in range(5)], "ds2s", shot=False)
out = os.path.join(d, "o.json")
r = {"headline_with_5_copies_of_one_run": attempt(cmp_args("ds2s", "headline", qc, eb, out))}
if r["headline_with_5_copies_of_one_run"] == "accepted":
    res = json.load(open(out))
    r["distinct_prediction_hashes"] = len(set(res["candidate_files"].values()))
    r["distinct_artifact_hashes"] = len({m["model_artifact_sha256"] for f, m in res["run_manifests"].items() if f in qc})
results["P2_copies_pass"] = r

# ---- P2b: one arm's 5 'seeds' may come from 5 different configurations; arms may share an arm_id ----
d, lab = env("p2b_configs", "ds2s")
qm = runs(d, lab, "q_mixed", [noisy(lab, 0.1, s) for s in range(5)], "ds2s", config_ids=[f"cfg{j}" for j in range(5)])
em = runs(d, lab, "e_same_id", [noisy(lab, 0.2, 10 + s) for s in range(5)], "ds2s", arm_ids=["q_mixed"] * 5, shot=False)
out = os.path.join(d, "o.json")
results["P2b_mixed_configs_and_shared_arm_id"] = {
    "secondary_with_5_configs_and_baseline_arm_id_equal_to_candidate": attempt(cmp_args("ds2s", "secondary", qm, em, out))}

# ---- P3: confirmation access is consumed when the output cannot be written ----
d, lab = env("p3_confirm_out", "svdb", n_rec=10, seed=3, alphabet="NNNNNSSVFQ")
qs = runs(d, lab, "q", [noisy(lab, 0.05, s) for s in range(5)], "svdb")
es = runs(d, lab, "e", [noisy(lab, 0.3, 10 + s) for s in range(5)], "svdb", shot=False)
blocker = os.path.join(d, "not_a_dir.txt")
open(blocker, "w").write("x")
bad_out = os.path.join(blocker, "confirm.json")  # parent is a file: cannot be created
r = {"confirmation_with_unwritable_out": attempt(cmp_args("svdb", "confirmation", qs, es, bad_out,
                                                          ["--confirm-reason", "final pair"]))}
r["access_log_entries_after"] = len(ev._log_lines(ev.ACCESS_LOG))
r["output_written"] = os.path.exists(bad_out)
# ---- P4: the 'repair' access may use entirely different models ----
q_other = runs(d, lab, "q_other", [noisy(lab, 0.01, 40 + s) for s in range(5)], "svdb")
good_out = os.path.join(d, "confirm2.json")
r["repair_access_with_different_model_artifacts"] = attempt(cmp_args(
    "svdb", "confirmation", q_other, es, good_out, ["--confirm-reason", "repair", "--repair-reason", "anything"]))
log = ev._log_lines(ev.ACCESS_LOG)
r["artifact_sets_equal_across_accesses"] = (
    len(log) == 2 and set(log[0]["model_artifact_sha256"].values()) == set(log[1]["model_artifact_sha256"].values()))
results["P3_P4_confirmation"] = r

# ---- P5: an identical headline rerun is refused when the same files are spelled differently ----
d, lab = env("p5_path_spelling", "ds2s")
qh = runs(d, lab, "q", [noisy(lab, 0.1, s) for s in range(5)], "ds2s")
eh = runs(d, lab, "e", [noisy(lab, 0.2, 10 + s) for s in range(5)], "ds2s", shot=False)
out = os.path.join(d, "o.json")
rel = lambda fs: [os.path.relpath(f, os.getcwd()) for f in fs]
results["P5_headline_rerun_path_spelling"] = {
    "first_headline_relative_paths": attempt(cmp_args("ds2s", "headline", rel(qh), rel(eh), out)),
    "identical_files_absolute_paths": attempt(cmp_args("ds2s", "headline", qh, eh, out)),
}

# ---- B1: brute-force check of the two-level bootstrap (F1) and the AUPRC bootstrap ----
rng = np.random.default_rng(7)
spec = {f"r{i}": "".join(rng.choice(list("NNNNNNSVVF"), size=int(rng.integers(20, 60)))) for i in range(9)}
rows = [(f"x:{r}:{i}", r, c, c in E.CLASSES) for r, s in spec.items() for i, c in enumerate(s)]
lab = pd.DataFrame(rows, columns=["beat_id", "record", "aami", "is_unit"])
t = np.where(lab["is_unit"], lab["aami"], "N")


def soft(seed, q):
    g = np.random.default_rng(seed)
    pr = np.where(g.random(len(lab)) < q, g.choice(list("NSV"), len(lab)), t)
    p = pred_frame(lab, pr)
    raw = g.random((len(lab), 3)) + 2 * np.stack([(pr == c) for c in E.CLASSES], 1)
    raw = np.round(raw, 1)  # create ties
    p[scorer.PROB_COLS] = raw / raw.sum(1, keepdims=True)
    return p


C = [soft(s, 0.2) for s in range(3)]
Bs = [soft(10 + s, 0.4) for s in range(3)]
B = 150
res = scorer.compare(C, Bs, lab, n_boot=B, seed=123)
recs = sorted(lab["record"].unique())
g = np.random.default_rng(123)
rdraw = g.integers(0, len(recs), size=B * len(recs)).reshape(B, len(recs))
cdraw = g.integers(0, 3, size=B * 3).reshape(B, 3)
bdraw = g.integers(0, 3, size=B * 3).reshape(B, 3)
units = lab[lab["is_unit"]].reset_index(drop=True)


def f1s(truth, pred):
    out = []
    for c in E.CLASSES:
        tp = np.sum((truth == c) & (pred == c)); fp = np.sum((truth != c) & (pred == c)); fn = np.sum((truth == c) & (pred != c))
        out.append(1.0 if 2 * tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn))
    return np.array(out)


def arm_rep(arm, b, sdraw):
    idx = np.concatenate([np.flatnonzero(units["record"].to_numpy() == recs[k]) for k in rdraw[b]])
    tr = units["aami"].to_numpy()[idx]
    f = np.mean([f1s(tr, arm[s].set_index("beat_id").loc[units["beat_id"]]["pred"].to_numpy()[idx]) for s in sdraw[b]], 0)
    aps = {}
    for c in ("S", "V"):
        vals = [scorer.average_precision(tr == c, arm[s].set_index("beat_id").loc[units["beat_id"]][f"prob_{c}"].to_numpy()[idx])
                for s in sdraw[b]]
        aps[c] = np.mean([0.0 if v is None else v for v in vals])
    return f, aps


dm, dS, dV = [], [], []
for b in range(B):
    fc, ac = arm_rep(C, b, cdraw)
    fb, ab = arm_rep(Bs, b, bdraw)
    dm.append((fc - fb).mean()); dS.append(ac["S"] - ab["S"]); dV.append(ac["V"] - ab["V"])
q = lambda x, lvl: [float(v) for v in np.quantile(x, [(1 - lvl) / 2, 1 - (1 - lvl) / 2])]
results["B1_bootstrap_bruteforce"] = {
    "macro_ci_scorer": res["primary"]["ci"], "macro_ci_bruteforce": q(dm, 0.95),
    "auprc_S_ci_scorer": res["auprc"]["S"]["ci"], "auprc_S_ci_bruteforce": q(dS, 0.95),
    "auprc_V_ci_scorer": res["auprc"]["V"]["ci"], "auprc_V_ci_bruteforce": q(dV, 0.95),
    "macro_match": bool(np.allclose(res["primary"]["ci"], q(dm, 0.95))),
    "auprc_match": bool(np.allclose(res["auprc"]["S"]["ci"], q(dS, 0.95)) and np.allclose(res["auprc"]["V"]["ci"], q(dV, 0.95))),
}

with open(os.path.join(ROOT, "runs", "V003", "probe_results.json"), "w") as f:
    json.dump(results, f, indent=1, default=str)
print(json.dumps(results, indent=1, default=str))
