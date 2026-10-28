"""E009 (diagnostic, DS1 only): both headline arms at every lambda of the declared grid, pooled out-of-fold on the fixed
DS1 folds, seeds 0-4. Reports macro-F1, per-class F1 and false positives per class, to separate the reservoir features
from the readout regularisation (ANOMALIES A015). Run from the project root:
    .venv/Scripts/python -I runs/E009/matched_lambda.py
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
from qhc.pipe import pipe_revision  # noqa: E402
from qhc.pipe.readout import LAMBDAS, cv_oof  # noqa: E402
from qhc.pipe.run import INPUT, SHOT_ARMS, best_config, build_model, design, ds1_data, keys_of  # noqa: E402

OUT = os.path.join(os.path.dirname(__file__), "matched_lambda_ds1.json")


def counts(y, pred):
    u = y >= 0
    m = np.zeros((3, 3), int)
    np.add.at(m, (y[u], pred[u]), 1)
    f1 = [2 * m[k, k] / (m[k].sum() + m[:, k].sum()) for k in range(3)]
    return {"macro_f1": float(np.mean(f1)), "f1": dict(zip("NSV", map(float, f1))),
            "fp": {c: int(m[:, k].sum() - m[k, k]) for k, c in enumerate("NSV")},
            "tp": {c: int(m[k, k]) for k, c in enumerate("NSV")}}


d, y, folds = ds1_data()
keys = keys_of(d)
res = {"pipe_revision": pipe_revision(), "lambdas": list(LAMBDAS), "arms": {}}
for exp in ("E002", "E003"):
    best = best_config(exp)
    arm = best["arm"]
    res["arms"][exp] = {"arm": arm, "selected_lam": best["lam"], "by_lam": {str(l): [] for l in LAMBDAS}}
    for seed in range(5):
        model = build_model(arm, best["config"], seed, 1000 + seed if arm in SHOT_ARMS else None)
        X = design(model.features(d[INPUT], keys), d)
        oof = cv_oof(X, y, d["record"], folds, LAMBDAS)
        for lam in LAMBDAS:
            res["arms"][exp]["by_lam"][str(lam)].append(counts(y, oof[lam].argmax(1)))
        print(exp, seed, {lam: round(res["arms"][exp]["by_lam"][str(lam)][-1]["macro_f1"], 4) for lam in LAMBDAS}, flush=True)
for exp, a in res["arms"].items():
    for lam, runs in a["by_lam"].items():
        a.setdefault("mean", {})[lam] = {
            "macro_f1": float(np.mean([r["macro_f1"] for r in runs])),
            "f1": {c: float(np.mean([r["f1"][c] for r in runs])) for c in "NSV"},
            "fp": {c: float(np.mean([r["fp"][c] for r in runs])) for c in "NSV"},
            "tp": {c: float(np.mean([r["tp"][c] for r in runs])) for c in "NSV"}}
with open(OUT, "w") as f:
    json.dump(res, f, indent=1)
for exp, a in res["arms"].items():
    for lam, m in a["mean"].items():
        print(f"{exp} lam {lam:>6}: macro {m['macro_f1']:.4f} | F1 S {m['f1']['S']:.3f} V {m['f1']['V']:.3f} | "
              f"FP S {m['fp']['S']:.0f} V {m['fp']['V']:.0f} | TP S {m['tp']['S']:.0f} V {m['tp']['V']:.0f}")
