"""V005 critic: regenerate E015-rigetti ds2s predictions from the saved models (noise.load_model rebuilds the noisy
reservoir from the artifact's metadata; readout from the saved arrays), write to runs/V005/E015, compare hashes with the
scored files, manifests and runs/full_eval_log.jsonl. Reads no ds2s/ds2/svdb labels."""
import hashlib, json, os, time
from qhc.evaluate import ROOT
from qhc.p4 import noise as N
from qhc.pipe import run as R
from qhc.pipe.features import load_split

OUT = os.path.join(ROOT, "runs", "V005", "E015", "rigetti"); os.makedirs(OUT, exist_ok=True)
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
log = [json.loads(x) for x in open(os.path.join(ROOT, "runs", "full_eval_log.jsonl")) if x.strip()]
logged = {f: h for e in log for f, h in e.get("files", {}).items() if "E015" in f}
ds = load_split("ds2s"); keys = R.keys_of(ds)
rep = {"seeds": {}}
for s in range(5):
    t = time.time()
    art = os.path.join(ROOT, "runs", "E015", "rigetti", f"model_seed{s}.npz")
    a0 = sha(art)
    meta, model, ro = N.load_model(art)
    f = os.path.join(OUT, f"pred_ds2s_seed{s}.csv")
    R.write_pred(f, ds["beat_id"], ro.predict_proba(R.design(model.features(ds[R.INPUT], keys), ds)))
    orig = os.path.join(ROOT, "runs", "E015", "rigetti", f"pred_ds2s_seed{s}.csv")
    man = json.load(open(os.path.splitext(orig)[0] + ".run.json"))
    rel = f"runs/E015/rigetti/pred_ds2s_seed{s}.csv"
    r = {"regen_sha256": sha(f), "scored_file_sha256": sha(orig), "manifest_prediction_sha256": man["prediction_sha256"],
         "logged_sha256": logged.get(rel), "artifact_sha256": a0, "manifest_artifact_sha256": man["model_artifact_sha256"],
         "artifact_unchanged": sha(art) == a0, "noise_meta": meta["noise"], "seconds": round(time.time() - t, 1)}
    r["match_all"] = r["regen_sha256"] == r["scored_file_sha256"] == r["manifest_prediction_sha256"] == r["logged_sha256"]
    r["artifact_match"] = r["artifact_sha256"] == r["manifest_artifact_sha256"]
    rep["seeds"][s] = r
    print(s, r["match_all"], r["artifact_match"], r["seconds"], flush=True)
json.dump(rep, open(os.path.join(ROOT, "runs", "V005", "E015", "regen_report.json"), "w"), indent=1)
print("ALL MATCH", all(r["match_all"] and r["artifact_match"] for r in rep["seeds"].values()))
