import hashlib, json, os
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
log = [json.loads(x) for x in open("runs/full_eval_log.jsonl") if x.strip()]
head = [e for e in log if e.get("role") == "headline" and e.get("split") == "ds2s"]
conf = [e for e in log if e.get("role") == "confirmation"][0]
acc = json.loads(open("runs/confirmation_access.jsonl").readline())
out = {"ds2s": {}, "svdb": {}}
for f, h in head[-1]["files"].items():
    exp, name = f.split("/")[1], f.split("/")[2]
    g = f"runs/V005/E018/selfcheck_ds2s/{exp}/{name}"
    out["ds2s"][f] = {"logged": h, "regen": sha(g), "match": sha(g) == h, "both_headline_entries_same": all(e["files"][f] == h for e in head)}
for f, h in conf["files"].items():
    exp, name = f.split("/")[2], f.split("/")[3]
    g = f"runs/V005/E018/{exp}/{name}"
    man = json.load(open(os.path.splitext(f)[0] + ".run.json"))
    gm = json.load(open(os.path.splitext(g)[0] + ".run.json"))
    diff = sorted(k for k in set(man) | set(gm) if man.get(k) != gm.get(k))
    out["svdb"][f] = {"logged_full_eval_log": h, "access_log": acc["prediction_sha256"][f], "on_disk": sha(f), "manifest": man["prediction_sha256"],
                      "regen": sha(g), "match_all": len({h, acc["prediction_sha256"][f], sha(f), man["prediction_sha256"], sha(g)}) == 1,
                      "manifest_artifact_sha_vs_access_log": man["model_artifact_sha256"] == acc["model_artifact_sha256"][f],
                      "artifact_on_disk_matches": sha(man["model_artifact"]) == man["model_artifact_sha256"],
                      "manifest_keys_differing_regen_vs_used": diff}
for k in ("ds2s", "svdb"):
    print(k, "all match:", all(v.get("match", v.get("match_all")) for v in out[k].values()), len(out[k]))
print("svdb manifest/artifact checks:", all(v["manifest_artifact_sha_vs_access_log"] and v["artifact_on_disk_matches"] for v in out["svdb"].values()))
print("manifest diffs:", {v_ for v in out["svdb"].values() for v_ in v["manifest_keys_differing_regen_vs_used"]})
fb = json.load(open("runs/V005/E018/features/build_svdb.json")); fo = json.load(open("runs/E018/features/build_svdb.json"))
print("svdb features arrays identical:", fb["arrays_sha256"] == fo["arrays_sha256"], "file sha same:", fb["file_sha256"] == fo["file_sha256"])
json.dump(out, open("runs/V005/E018/hash_report.json", "w"), indent=1)
