"""V004: hash checks without opening test-split labels, confirm/ or raw SVDB files.

- fixture file hash (LF-normalised, first 16 hex; and raw)
- MIT-BIH raw files against the local SHA256SUMS.txt, and the hash of that sums file
- processed EV1 outputs against manifest.json, skipping labels_ds2s.csv, labels_ds2.csv and anything under confirm/
- E002 artifacts: prediction and model hashes against the run manifests and against the full-evaluation log entry
"""
import glob
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKIP = ("labels_ds2s.csv", "labels_ds2.csv")


def sha(p, lf=False):
    b = open(p, "rb").read()
    if lf:
        b = b.replace(b"\r\n", b"\n")
    return hashlib.sha256(b).hexdigest()


out = {}
t = os.path.join(ROOT, "tests", "test_scorer.py")
out["fixtures"] = {"lf16": sha(t, True)[:16], "raw16": sha(t)[:16]}

raw = os.path.join(ROOT, "runs", "data", "raw", "mitdb")
sums_path = os.path.join(raw, "SHA256SUMS.txt")
sums = {}
for line in open(sums_path):
    parts = line.split()
    if len(parts) == 2:
        sums[parts[1]] = parts[0]
recs = open(os.path.join(raw, "RECORDS")).read().split()
bad, n = [], 0
for r in recs:
    for ext in ("hea", "dat", "atr"):
        n += 1
        p = os.path.join(raw, f"{r}.{ext}")
        if not os.path.exists(p) or sha(p) != sums.get(f"{r}.{ext}"):
            bad.append(f"{r}.{ext}")
out["mitdb"] = {"records": len(recs), "files_checked": n, "mismatched": bad, "sums_file_sha256": sha(sums_path),
                "n_files_in_dir": len(os.listdir(raw))}

proc = os.path.join(ROOT, "runs", "data", "processed", "EV1")
man = json.load(open(os.path.join(proc, "manifest.json")))
res, skipped = {}, []
for rel, h in man["outputs"].items():
    if rel.startswith("confirm/") or os.path.basename(rel) in SKIP:
        skipped.append(rel)
        continue
    res[rel] = sha(os.path.join(proc, rel)) == h
out["processed"] = {"checked": res, "skipped_unopened": skipped, "manifest_sha256": sha(os.path.join(proc, "manifest.json")),
                    "lowdata_subsets_sha256": sha(os.path.join(proc, "lowdata_subsets.json"))}
out["manifest_inputs_keys"] = list(man.get("inputs", {}))[:5]

e2 = os.path.join(ROOT, "runs", "E002")
log = [json.loads(x) for x in open(os.path.join(ROOT, "runs", "full_eval_log.jsonl")) if x.strip()]
head = [e for e in log if e.get("role") == "headline"]
logged = head[-1]["files"] if head else {}
arts = {}
for s in range(5):
    p = os.path.join(e2, f"pred_ds2s_seed{s}.csv")
    m = json.load(open(os.path.join(e2, f"pred_ds2s_seed{s}.run.json")))
    arts[s] = {"pred_sha": sha(p), "manifest_pred_sha_ok": m["prediction_sha256"] == sha(p),
               "manifest_model_sha_ok": m["model_artifact_sha256"] == sha(os.path.join(ROOT, m["model_artifact"])),
               "logged_headline_ok": logged.get(f"runs/E002/pred_ds2s_seed{s}.csv") == sha(p),
               "code_revision": m["code_revision"], "config_id": m["config_id"]}
out["E002"] = arts
out["n_log_lines"] = len(log)
out["log_roles"] = [(e.get("time"), e.get("split"), e.get("role"), e.get("ids")) for e in log]
json.dump(out, open(os.path.join(ROOT, "runs", "V004", "hashcheck.json"), "w"), indent=1)
print(json.dumps(out, indent=1))
