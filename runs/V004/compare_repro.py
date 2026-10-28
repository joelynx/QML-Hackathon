"""V004: compare the critic's retune and final runs (runs/V004/R0) with E002 and with the logged headline inputs.
Label-free: hashes, arrays and tuning lines only."""
import hashlib
import json
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
V, E2 = os.path.join(ROOT, "runs", "V004", "R0"), os.path.join(ROOT, "runs", "E002")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
out = {}

a = [json.loads(x) for x in open(os.path.join(V, "tuning.jsonl")) if x.strip()]
b = {x["index"]: x for x in (json.loads(y) for y in open(os.path.join(E2, "tuning.jsonl")) if y.strip())}
diffs = [abs(x["scores"][k] - b[x["index"]]["scores"][k]) for x in a for k in x["scores"]]
out["tuning"] = {"n_lines": len(a), "configs_equal": all(x["config"] == b[x["index"]]["config"] for x in a),
                 "best_lam_equal_all_lines": all(x["best_lam"] == b[x["index"]]["best_lam"] for x in a),
                 "max_abs_score_diff": max(diffs), "pipe_revisions": sorted({x["pipe_revision"] for x in a})}
sv, se = json.load(open(os.path.join(V, "selected_config.json"))), json.load(open(os.path.join(E2, "selected_config.json")))
out["selected"] = {"critic": sv, "same_index_config_lam": (sv["index"], sv["config"], sv["lam"]) == (se["index"], se["config"], se["lam"]),
                   "score_diff": sv["score"] - se["score"]}

log = [json.loads(x) for x in open(os.path.join(ROOT, "runs", "full_eval_log.jsonl")) if x.strip()]
logged = [e for e in log if e.get("role") == "headline"][-1]["files"]
out["ds2s_pred"] = {s: {"critic_sha": sha(os.path.join(V, f"pred_ds2s_seed{s}.csv")),
                        "equals_logged_headline_input": sha(os.path.join(V, f"pred_ds2s_seed{s}.csv")) == logged[f"runs/E002/pred_ds2s_seed{s}.csv"]}
                    for s in range(5)}
out["oof_ds1_identical"] = {s: sha(os.path.join(V, f"oof_ds1_seed{s}.csv")) == sha(os.path.join(E2, f"oof_ds1_seed{s}.csv"))
                            for s in range(10)}
arr = {}
for s in range(10):
    za, zb = np.load(os.path.join(V, f"model_seed{s}.npz")), np.load(os.path.join(E2, f"model_seed{s}.npz"))
    keys = sorted(k for k in za.files if k != "meta")
    arr[s] = {"same_keys": keys == sorted(k for k in zb.files if k != "meta"),
              "arrays_identical": all(np.array_equal(za[k], zb[k]) for k in keys)}
out["model_arrays"] = arr
out["leakcheck"] = json.load(open(os.path.join(V, "leakcheck_seed0.json")))
out["leakcheck"].pop("records", None)
json.dump(out, open(os.path.join(ROOT, "runs", "V004", "compare_repro.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
