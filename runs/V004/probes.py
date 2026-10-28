"""V004 label-free probes of E002 (read-only on runs/E002; writes runs/V004/probes.json only).

P1  Independent numpy re-implementation of the ESN forward pass and the readout from the saved E002 model arrays,
    on the ds2s features; compared with the scored prediction files (all 5 seeds).
P2  Prediction files valid against the label-free prediction set (qhc.scorer.validate on qhc.evaluate.prediction_set)
    and the strict run checks (qhc.evaluate.check_runs); pred == argmax(prob).
P3  Per-record end-to-end path (raw signal -> pipeline_fn) on single ds2s records equals the batch predictions:
    no statistic is shared across test records.
P4  Lookahead check (qhc.leakcheck.check_lookahead) of the E002 seed-0 pipeline on ds2s records 232 and 213 (first
    150 s), label-free, in addition to the DS1 check of the packet.
P5  Readout normalisation: mu/sd stored in model_seed0.npz equal the DS1-unit statistics of the seed-0 design matrix.
"""
import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qhc.pipe.features as F  # noqa: E402

F.FEATURE_DIR = os.path.join(ROOT, "runs", "V004", "features")
from qhc.evaluate import check_runs, load_positions, prediction_set  # noqa: E402
from qhc.leakcheck import check_lookahead  # noqa: E402
from qhc.pipe import run as R  # noqa: E402
from qhc.scorer import validate  # noqa: E402

E2 = os.path.join(ROOT, "runs", "E002")
out = {}
ds = F.load_split("ds2s")


def esn_numpy(z, u):
    meta = json.loads(str(z["meta"]))
    a = meta["config"]["leak"]
    W, Win, b = z["res_W"].astype(np.float64), z["res_W_in"].astype(np.float64), z["res_b"].astype(np.float64)
    u = np.asarray(u, dtype=np.float32).reshape(len(u), 4, 10).astype(np.float64)
    h = np.zeros((len(u), W.shape[0]))
    feats = []
    for k in range(4):
        h = (1 - a) * h + a * np.tanh(h @ W.T + u[:, k] @ Win.T + b)
        feats.append(h[:, :55])
    return np.concatenate(feats, 1).astype(np.float32), meta


# P1
p1 = {}
for s in range(5):
    z = np.load(os.path.join(E2, f"model_seed{s}.npz"))
    res, meta = esn_numpy(z, ds["rel"])
    X = np.c_[res, ds["rr"]].astype(np.float32)
    zz = ((X.astype(np.float64) - z["mu"]) / z["sd"]) @ z["W_readout"].astype(np.float64) + z["b_readout"]
    zz -= zz.max(1, keepdims=True)
    p = np.exp(zz)
    p /= p.sum(1, keepdims=True)
    pred = pd.read_csv(os.path.join(E2, f"pred_ds2s_seed{s}.csv"), dtype={"beat_id": str})
    assert (pred["beat_id"].to_numpy() == ds["beat_id"]).all()
    q = pred[["prob_N", "prob_S", "prob_V"]].to_numpy()
    p1[s] = {"max_abs_prob_diff": float(np.abs(q - p).max()),
             "argmax_disagreements": int((np.array(list("NSV"))[p.argmax(1)] != pred["pred"].to_numpy()).sum()),
             "meta_seed": meta["seed"], "meta_config_index": meta["config_index"], "lam": float(z["lam"]),
             "res_W_shape": list(z["res_W"].shape)}
out["P1_numpy_reimplementation"] = p1

# P2
ps = prediction_set("ds2s")
files = [os.path.join("runs", "E002", f"pred_ds2s_seed{s}.csv") for s in range(5)]
p2 = {}
for f in files:
    pr = pd.read_csv(os.path.join(ROOT, f), dtype={"beat_id": str, "pred": str})
    validate(pr, ps)
    am = np.array(list("NSV"))[pr[["prob_N", "prob_S", "prob_V"]].to_numpy().argmax(1)]
    p2[f] = {"rows": len(pr), "valid": True, "pred_ne_argmax_rounded": int((am != pr["pred"].to_numpy()).sum()),
             "pred_counts": pr["pred"].value_counts().to_dict()}
cwd = os.getcwd()
os.chdir(ROOT)
runs = check_runs(files, "ds2s", "base")
os.chdir(cwd)
p2["check_runs"] = {"passed": True, "seeds": [r["seed"] for r in runs], "config_ids": sorted({r["config_id"] for r in runs})}
p2["prediction_set_size"] = len(ps)
out["P2_validity"] = p2

# P3 and P4
meta, model, ro = R.load_artifact(os.path.join(E2, "model_seed0.npz"))
pos = load_positions("ds2s")
pred0 = pd.read_csv(os.path.join(E2, "pred_ds2s_seed0.csv"), dtype={"beat_id": str}).set_index("beat_id")
p3, p4 = {}, {}
for rec in ("232", "213", "222"):
    g = pos[pos["record"] == rec].sort_values("sample")
    sig, fs, _ = F.load_signal("mitdb", rec)
    s = g["sample"].to_numpy()
    fn = R.pipeline_fn(meta, model, ro, "mitdb", rec)
    probs = fn(sig, s, fs)
    keep = g["predict"].to_numpy()
    ref = pred0.loc[g["beat_id"].to_numpy()[keep], ["prob_N", "prob_S", "prob_V"]].to_numpy()
    p3[rec] = {"beats": int(keep.sum()), "max_abs_diff_vs_scored_file": float(np.abs(probs[keep] - ref).max())}
    if rec in ("232", "213"):
        m = s < 150 * fs
        s2, sig2 = s[m], sig[:int(160 * fs)]
        idx = range(1, len(s2) - 1)
        bad = check_lookahead(R.pipeline_fn(meta, model, ro, "mitdb", rec), sig2, s2, fs, idx)
        p4[rec] = {"beats_checked": len(idx), "violations": bad}
out["P3_per_record_vs_batch"] = p3
out["P4_lookahead_ds2s"] = p4

# P5
d, y, folds = R.ds1_data()
X = R.design(model.features(d["rel"], R.keys_of(d)), d)
u = y >= 0
z = np.load(os.path.join(E2, "model_seed0.npz"))
out["P5_readout_norm"] = {"n_ds1_units": int(u.sum()), "mu_max_abs_diff": float(np.abs(X[u].mean(0) - z["mu"]).max()),
                          "sd_max_abs_diff": float(np.abs(X[u].std(0) + 1e-6 - z["sd"]).max())}
with open(os.path.join(ROOT, "runs", "V004", "probes.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
print(json.dumps(out, indent=1, default=str))
