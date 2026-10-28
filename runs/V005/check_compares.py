"""V005: read logged compare outputs (no scoring), recompute the decision-rule outcome from the stored numbers,
check file hashes against full_eval_log.jsonl and manifests, and print a summary."""
import hashlib, json, os, sys
R = os.getcwd()
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
log = [json.loads(x) for x in open("runs/full_eval_log.jsonl") if x.strip()]
J = ["runs/E003/compare_ds2s_headline_EV2.json", "runs/E018/confirm_svdb.json",
     "runs/E012/compare_ds2s_secondary_E012_vs_E003.json", "runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json",
     "runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json", "runs/E016/compare_ds2s_secondary_E003_vs_E016.json",
     "runs/E016/compare_ds2s_secondary_E002_vs_E016.json"]
def rule(p, split):
    d, (lo, hi) = p["delta"], p["ci"]
    w = p.get("delta_without_dominant_record")
    if d >= 0.02 and lo > 0 and (w is None or w > 0): return "favorable"
    if hi < 0: return "unfavorable"
    return "no detectable change"
out = {}
for j in J:
    d = json.load(open(j)); p = d["primary"]
    files = {**d["candidate_files"], **d["baseline_files"]}
    disk = {f: (sha(f) == h) for f, h in files.items()}
    man = {f: (json.load(open(os.path.splitext(f)[0] + ".run.json"))["prediction_sha256"] == h) for f, h in files.items()}
    ents = [e for e in log if e.get("files") and set(e["files"]) == set(files) and all(e["files"][k] == files[k] for k in files)]
    loro = d.get("leave_one_record_out_delta") or {}
    r = {"role": d["role"], "split": d["split"], "cand": d["candidate_id"], "base": d["baseline_id"],
         "cand_f1": round(p["candidate_macro_f1"], 4), "base_f1": round(p["baseline_macro_f1"], 4),
         "delta": round(p["delta"], 4), "ci": [round(x, 4) for x in p["ci"]], "ci_level": p["ci_level"],
         "without_232": None if p.get("delta_without_dominant_record") is None else round(p["delta_without_dominant_record"], 4),
         "outcome_logged": p["outcome"], "outcome_reason": p.get("outcome_reason"), "outcome_recomputed": rule(p, d["split"]),
         "inference": p.get("inference"), "per_class": {c: [round(v["delta"], 4), [round(x, 4) for x in v["ci"]]] for c, v in d["per_class_f1"].items()},
         "slices": d.get("slices"), "loro_min_max": [round(min(loro.values()), 4), round(max(loro.values()), 4)] if loro else None,
         "files_on_disk_match": all(disk.values()), "manifests_match": all(man.values()), "log_entries": [(e.get("time"), e.get("role")) for e in ents],
         "eval_rev": d["scorer"]["code_revision"], "n_boot": d["n_boot"], "time": d["time"], "confirmed": d.get("confirmed")}
    out[j] = r
    print(json.dumps({j: r}, default=str)); print()
json.dump(out, open("runs/V005/compare_summary.json", "w"), indent=1, default=str)
print("LOG LINES", len(log))
for e in log:
    print(e.get("time"), e.get("role"), e.get("split"), e.get("cand_id", e.get("candidate_id")), e.get("base_id", e.get("baseline_id")), e.get("code_revision", "")[:16] if isinstance(e.get("code_revision"), str) else "", len(e.get("files", {})))
