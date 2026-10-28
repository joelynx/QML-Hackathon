"""V005 re-check: numbers added in the repair, from logged outputs only (no label access)."""
import json, numpy as np
H = json.load(open("runs/E003/compare_ds2s_headline_EV2.json"))
S = json.load(open("runs/E018/confirm_svdb.json"))
def pc(d, a): return d["arms"][a]["seed_average"]["per_class"]
for name, d in (("ds2s", H), ("svdb", S)):
    q, e = pc(d, "candidate"), pc(d, "baseline")
    print(name, "V Se QRC %.4f ESN %.4f gap %.1f pts" % (q["V"]["sensitivity"], e["V"]["sensitivity"], 100 * (e["V"]["sensitivity"] - q["V"]["sensitivity"])))
print("SVDB V AUPRC", S["auprc"]["V"])
for a in ("candidate", "baseline"):
    p = H["arms"][a]["seed_average"]["paper_compatible"]
    print("paper_compatible", a, json.dumps(p)[:400])
# per-record V F1 (records with >= 10 V units); two conventions
def per_record(d, a):
    ps = d["arms"][a]["per_seed"]
    recs = sorted(ps[0]["per_record"])
    out = {}
    for r in recs:
        cms = [np.array(p["per_record"][r]["confusion_true_by_pred"], float) for p in ps]
        def f1v(c):
            tp = c[2, 2]; fp = c[:, 2].sum() - tp; fn = c[2].sum() - tp
            return 1.0 if 2 * tp + fp + fn == 0 else 2 * tp / (2 * tp + fp + fn)
        out[r] = (cms[0][2].sum(), float(np.mean([f1v(c) for c in cms])), f1v(np.mean(cms, axis=0)))
    return out
q, e = per_record(H, "candidate"), per_record(H, "baseline")
rows = [(r, int(q[r][0]), round(q[r][1] - e[r][1], 4), round(q[r][2] - e[r][2], 4)) for r in q if q[r][0] >= 10]
print("records with >=10 V units:", len(rows))
for x in sorted(rows, key=lambda t: t[2]): print("  rec %s V units %d dF1(mean of seeds) %+.4f dF1(pooled conf) %+.4f" % x)
print("QRC higher (mean-of-seeds):", sum(x[2] > 0 for x in rows), " within +-0.001:", sum(abs(x[2]) <= 0.001 for x in rows))
print("QRC higher (pooled):", sum(x[3] > 0 for x in rows), " within +-0.001:", sum(abs(x[3]) <= 0.001 for x in rows))
a = json.load(open("runs/E019/analysis.json"))["pred_counts"]
hw, sh = a["hw"], a["shot"]; n = sum(hw.values())
print("E019 chance agreement", sum(hw[c] / n * sh[c] / sum(sh.values()) for c in hw), "shot counts", sh)
print("cost/day", 100000 * 4096, 100000 * 4096 * 0.000425)
