"""E016 label-free checks of the ds2s run set: check_runs, distinct artifacts, seed agreement. Prints JSON."""
import itertools
import json
import os
import sys

import numpy as np
import pandas as pd

from qhc.evaluate import ROOT, check_runs
from qhc.units import sha256

out = os.path.join(ROOT, "runs", "E016")
files = sorted(os.path.join(out, f"pred_ds2s_seed{s}.csv") for s in range(5))
runs = check_runs(sorted(files), "ds2s", "E016")
res = {"check_runs": "passed", "n_runs": len(runs),
       "seeds": [r["seed"] for r in runs], "config_id": runs[0]["config_id"], "arm_id": runs[0]["arm_id"],
       "prediction_sha256": {r["seed"]: r["prediction_sha256"] for r in runs},
       "model_artifact_sha256": {r["seed"]: r["model_artifact_sha256"] for r in runs}}
dfs = [pd.read_csv(f, dtype={"beat_id": str}) for f in files]
assert all((d["beat_id"].values == dfs[0]["beat_id"].values).all() for d in dfs)
preds = np.stack([d["pred"].to_numpy() for d in dfs])
probs = np.stack([d[["prob_N", "prob_S", "prob_V"]].to_numpy() for d in dfs])
res["n_beats"] = int(preds.shape[1])
res["distinct_prediction_hashes"] = len(set(res["prediction_sha256"].values()))
res["distinct_model_hashes"] = len(set(res["model_artifact_sha256"].values()))
res["all5_label_agreement"] = float((preds == preds[0]).all(0).mean())
pair = {f"{i}-{j}": float((preds[i] == preds[j]).mean()) for i, j in itertools.combinations(range(5), 2)}
res["pairwise_label_agreement"] = {"min": min(pair.values()), "mean": float(np.mean(list(pair.values()))),
                                   "max": max(pair.values())}
res["max_abs_prob_diff_vs_seed0"] = float(np.abs(probs - probs[0]).max())
res["pred_class_counts"] = {s: {c: int((preds[s] == c).sum()) for c in "NSV"} for s in range(5)}
print(json.dumps(res, indent=1))
with open(os.path.join(out, "ds2s_runset_check.json"), "w") as f:
    json.dump(res, f, indent=1)
