"""V005: per-record facts from logged compare outputs (5x3 confusions, rows N,S,V,F,Q; cols N,S,V). No label access."""
import json, numpy as np
def arm(path, which):
    d = json.load(open(path)); ps = d["arms"][which]["per_seed"]
    recs = sorted(ps[0]["per_record"])
    return {r: np.mean([np.array(p["per_record"][r]["confusion_true_by_pred"], dtype=float) for p in ps], axis=0) for r in recs}
def f1s(c):
    c = c[:3]  # N/S/V units only
    out = []
    for k in range(3):
        tp = c[k, k]; fp = c[:, k].sum() - tp; fn = c[k].sum() - tp
        out.append(1.0 if (2 * tp + fp + fn) == 0 else 2 * tp / (2 * tp + fp + fn))
    return out
H = "runs/E003/compare_ds2s_headline_EV2.json"
q, e = arm(H, "candidate"), arm(H, "baseline")
vfp = lambda a: {r: a[r][[0, 1], 2].sum() for r in a}
qv, ev = vfp(q), vfp(e)
print("V FP per seed total QRC %.0f ESN %.0f" % (sum(qv.values()), sum(ev.values())))
print("largest ESN-QRC V FP reductions:", sorted(((round(ev[r] - qv[r], 1), r) for r in qv), reverse=True)[:6])
print("V TP QRC %.0f ESN %.0f" % (sum(q[r][2, 2] for r in q), sum(e[r][2, 2] for r in e)))
print("S TP rec232 QRC %.0f ESN %.0f; S units 232 %.0f; total S TP QRC %.0f ESN %.0f" % (q["232"][1, 1], e["232"][1, 1], q["232"][1].sum(), sum(q[r][1, 1] for r in q), sum(e[r][1, 1] for r in e)))
# E016 vs E003: per-record pooled-confusion macro-F1 (descriptive), records where E016 leads
B = "runs/E016/compare_ds2s_secondary_E003_vs_E016.json"
c3, b16 = arm(B, "candidate"), arm(B, "baseline")
lead = []
for r in c3:
    m3, m16 = np.mean(f1s(c3[r])), np.mean(f1s(b16[r]))
    lead.append((r, round(m16 - m3, 3)))
print("E016 minus E003 per-record macro-F1 (seed-avg confusion; descriptive):", lead)
print("records where E016 does not lead:", [r for r, x in lead if x <= 0])
