"""V005 critic: regenerate E014-n6 ds2s predictions by retraining the readout on DS1 (the e014-final path of
qhc.p4.ablate, output redirected to runs/V005/E014), then compare with the scored files, manifests and the log.
Also apply the declared selection rule to the variant_results files. Reads no ds2s/ds2/svdb labels."""
import glob, hashlib, json, os, sys
import numpy as np
from qhc.evaluate import ROOT
from qhc.p4 import ablate as A
from qhc.pipe import run
from qhc.pipe.features import load_split
from qhc.pipe.readout import Readout

OUT = os.path.join(ROOT, "runs", "V005", "E014", "n6")
os.makedirs(OUT, exist_ok=True)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
cands = [json.load(open(os.path.join(ROOT, "runs", "E014", v, "variant_results.json"))) for v in ("n6", "n8", "n12")]
sel = max(cands, key=lambda r: (r["mean_macro_f1"], -r["n_qubits"]))
rep = {"rule_selects": f"n{sel['n_qubits']}", "lam": sel["selected_lam"],
       "means": {f"n{r['n_qubits']}": r["mean_macro_f1"] for r in cands}, "seeds": {}}
assert rep["rule_selects"] == "n6"
cfg = A.e003()
n, lam = 6, sel["selected_lam"]
d, y, _ = run.ds1_data()
keys, units = run.keys_of(d), y >= 0
ds = load_split("ds2s"); tkeys = run.keys_of(ds)
log = [json.loads(x) for x in open(os.path.join(ROOT, "runs", "full_eval_log.jsonl")) if x.strip()]
logged = {}
for e in log:
    for f, h in e.get("files", {}).items():
        if "E014" in f:
            logged[f] = h
for s in range(5):
    model = A.GQRC(n, **cfg, seed=s, shots=A.SHOTS, shot_seed=1000 + s)
    X = run.design(model.features(d[run.INPUT], keys), d)
    A.R._UNIF_CACHE.clear()
    ro = Readout(lam).fit(X[units], y[units])
    meta = {"arm": f"qrc_n{n}", "exp": "E014", "model_class": "p4.ablate.GQRC", "n_qubits": n, "readout": "Z+ZZ",
            "K": model.K, "config": cfg, "config_index": 15, "seed": s, "shot_seed": 1000 + s, "shots": A.SHOTS,
            "input": run.INPUT, "lam": lam, "code_revision": A.REV}
    A.save_model(os.path.join(OUT, f"model_seed{s}.npz"), meta, model, ro)
    f = A.write_ds2s(OUT, s, model, ro, ds, tkeys, {"arm_id": f"E014-qrc_n{n}", "config_id": f"E014-qrc-cfg15-n{n}",
                                                   "shot_seed": 1000 + s, "shots": A.SHOTS, "n_qubits": n,
                                                   "config": dict(cfg, n_qubits=n), "lam": lam})
    orig = os.path.join(ROOT, "runs", "E014", "n6", f"pred_ds2s_seed{s}.csv")
    man = json.load(open(os.path.splitext(orig)[0] + ".run.json"))
    zo, zn = np.load(os.path.join(ROOT, "runs", "E014", "n6", f"model_seed{s}.npz")), np.load(os.path.join(OUT, f"model_seed{s}.npz"))
    rel = f"runs/E014/n6/pred_ds2s_seed{s}.csv"
    rep["seeds"][s] = {"regen_sha256": sha(f), "scored_file_sha256": sha(orig), "manifest_prediction_sha256": man["prediction_sha256"],
                       "logged_sha256": logged.get(rel), "manifest_artifact_sha256_matches_file": man["model_artifact_sha256"] == sha(os.path.join(ROOT, rel.replace(f"pred_ds2s_seed{s}.csv", f"model_seed{s}.npz"))),
                       "artifact_arrays_equal": {k: bool(np.array_equal(zo[k], zn[k])) for k in ("lam", "mu", "sd", "W_readout", "b_readout", "res_couplings")}}
    r = rep["seeds"][s]
    r["match_all"] = r["regen_sha256"] == r["scored_file_sha256"] == r["manifest_prediction_sha256"] == r["logged_sha256"]
    print(s, r["match_all"], r["artifact_arrays_equal"], flush=True)
json.dump(rep, open(os.path.join(ROOT, "runs", "V005", "E014", "regen_report.json"), "w"), indent=1)
print("ALL MATCH", all(r["match_all"] for r in rep["seeds"].values()))
