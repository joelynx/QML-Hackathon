"""E017: kernel diagnostic of the reservoir feature maps on DS1 (diagnostic only: DS1 labels, no test split is read).

  python -I -m qhc.p4.kernels --out runs/E017 [--cache <features.npz>]

Feature maps: seed-0 final-run settings (reservoir seed 0, shot seed 1000) of E003 (QRC, 1,024 shots), the exact QRC
(E003 configuration, shots=None; the E012 setting), E004 (mean-field), E005 (separable QRC, J = 0) and E002 (ESN), plus
RR only (8 features). Reference maps (added for calibration, not on the E017 card): the QRC with shot seed 1001
(shot-noise floor), the QRC seed-1 final-run setting (reservoir seed 1, shot seed 1001), the exact mean-field model and
the ESN with reservoir seed 1. Inputs d["rel"] of every DS1 beat; analyses use the DS1 evaluation units (N/S/V) only.
Columns are standardised on the DS1 units exactly as the readout does: (x - mean) / (sd + 1e-6). Blocks: "res" = the
K = 220 reservoir features alone; "res_rr" = the reservoir block with the 8 standardised RR features appended (what the
readout sees). All kernels are linear (the readout is linear): K = Z Z^T.

1. Linear CKA (Kornblith et al. 2019): CKA(X, Y) = ||Yc^T Xc||_F^2 / (||Xc^T Xc||_F ||Yc^T Yc||_F), columns centred
   over the rows used (= HSIC-based CKA with linear kernels, biased estimator, as in the paper).
2. Centred kernel-target alignment (Cortes, Mohri & Rostamizadeh 2012): rho(K, K') = <Kc, K'c>_F / (||Kc||_F ||K'c||_F),
   Kc = H K H, H = I - 11^T/n. With K = X X^T and K' = Y Y^T this equals CKA(X, Y), Y the target (one-hot N/S/V, or a
   one-column indicator for V-vs-rest and S-vs-rest).
3. Geometric difference (Huang et al. 2021, eq. 5 and the regularised form of their Supplementary Information):
   g(K_C || K_Q) = sqrt( || sqrt(K_Q) sqrt(K_C) (K_C + lam I)^-2 sqrt(K_C) sqrt(K_Q) ||_inf ), spectral norm, kernels
   trace-normalised to Tr(K) = N. Computed as the largest singular value of diag(sqrt q) U_Q^T U_C diag(sqrt(c) / (c + lam)),
   K_C = U_C diag(c) U_C^T and K_Q = U_Q diag(q) U_Q^T from thin SVDs of the standardised feature matrices.
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

from . import code_revision
from ..evaluate import ROOT
from ..pipe import run
from ..pipe.reservoirs import K as K_RES

SEED = 20261026            # stratified subsample for CKA / pooled KTA (np.random.default_rng(SEED))
N_PER_CLASS = 2000         # per class, or all units of the class if fewer
GEO_SEEDS = (20261026, 20261027, 20261028)  # uniform subsamples of DS1 units for the geometric difference
N_GEO = 2000
GEO_LAMS = (1e-5, 1e-4, 1e-3, 1e-2, 0.025, 0.05, 0.1, 1.0)  # Huang et al. SI eq. L10 grid, plus 1.0
G_TRA_MAX = 0.045  # Huang et al. SI eqs. F20 / L9: report g_gen at the largest lam with g_tra < 0.045
MIN_CLASS = 10             # per-record KTA: >= MIN_CLASS units of the class in question (and of the rest)
SD_EPS = 1e-6              # as readout.Readout
CLASSES = ("N", "S", "V")
DECLARED = ("qrc", "qrc_exact", "mf", "sep", "esn", "rr")
REFERENCE = ("qrc_shot1001", "qrc_res1", "mf_exact", "esn_res1")
CLASSICAL_FOR_G = ("mf", "esn", "sep", "qrc_exact", "rr", "qrc_shot1001", "qrc_res1", "mf_exact", "esn_res1")


FORMULAS = {
    "linear_cka": "Kornblith et al. 2019 eqs. 3-4: HSIC(K,L) = tr(KHLH)/(n-1)^2, CKA = HSIC(K,L)/sqrt(HSIC(K,K) HSIC(L,L)); "
                  "linear kernels: ||Yc^T Xc||_F^2 / (||Xc^T Xc||_F ||Yc^T Yc||_F), columns centred over the rows used "
                  "(biased estimator, as in the paper)",
    "centred_kta": "Cortes, Mohri & Rostamizadeh 2012 Definition 4 / Lemma 1: rho(K,K') = <Kc,K'c>_F/(||Kc||_F ||K'c||_F), "
                   "Kc = [I - 11^T/m] K [I - 11^T/m]; target kernel Y Y^T (paper: y y^T for scalar labels; the one-hot "
                   "N/S/V target is our multiclass extension); equals CKA(X, Y) for K = X X^T",
    "geometric_difference": "Huang et al. 2021 main-text eq. 5 g(K1||K2) = sqrt(||sqrt(K2) K1^-1 sqrt(K2)||_inf), Tr K = N; "
                            "rank-deficient linear kernels need the regularised form of the SI (arXiv:2011.01938v2 eqs. "
                            "F19-F20, L8-L10): g_gen(K_C||K_Q) = sqrt(||sqrt(K_Q) sqrt(K_C)(K_C+lam I)^-2 sqrt(K_C) "
                            "sqrt(K_Q)||_inf), g_tra = lam sqrt(||sqrt(K_Q)(K_C+lam I)^-2 sqrt(K_Q)||_inf); resid = lim "
                            "lam->0 g_tra^2 (K_Q outside K_C's span). Paper: grid lam in {1e-5,1e-4,1e-3,0.01,0.025,0.05,"
                            "0.1}, report g_gen at the largest lam with g_tra < 0.045 (min over classical kernels); "
                            "engineered datasets: g_tra^2 s_Q <= 0.002. Caveat: pdftotext loses Greek letters and radicals; "
                            "the formula was reconstructed from equation structure, the stated lam = 0 limit and "
                            "s_C <= g^2 s_Q, and checked numerically against dense sqrtm/inv code (1e-9).",
}
REFERENCES = [
    {"cite": "Kornblith, S., Norouzi, M., Lee, H. & Hinton, G. Similarity of Neural Network Representations Revisited. "
             "Proceedings of the 36th International Conference on Machine Learning, PMLR 97, 3519-3529 (2019). arXiv:1905.00414.",
     "checked": "eqs. 3-4 from the arXiv v4 PDF via paperfetch (doi:10.48550/arxiv.1905.00414); venue and pages from "
                "proceedings.mlr.press/v97/kornblith19a.html"},
    {"cite": "Cortes, C., Mohri, M. & Rostamizadeh, A. Algorithms for Learning Kernels Based on Centered Alignment. "
             "Journal of Machine Learning Research 13(28):795-828 (2012). arXiv:1203.0550.",
     "checked": "Definition 4 and Lemma 1 from the arXiv v3 PDF via paperfetch (doi:10.5555/2503308.2188413; the arXiv "
                "header has a placeholder volume); volume and pages from jmlr.org/papers/v13/cortes12a.html"},
    {"cite": "Huang, H.-Y., Broughton, M., Mohseni, M., Babbush, R., Boixo, S., Neven, H. & McClean, J. R. Power of data "
             "in quantum machine learning. Nature Communications 12, 2631 (2021). doi:10.1038/s41467-021-22539-9.",
     "checked": "eq. 5 from the Europe PMC full text (PMC8113501); regularised eqs. F19-F20, L8-L10 and App. G from the "
                "arXiv:2011.01938v2 PDF (includes the SI) via paperfetch; volume and article number from Crossref"},
]
DEVIATIONS = [
    "four reference maps added (qrc_shot1001, qrc_res1, mf_exact, esn_res1) to calibrate 'near 1'",
    "CKA and KTA also on all DS1 units, besides the declared stratified subsample",
    "geometric difference: the paper's lam grid plus 1.0; g_tra and the out-of-span residual added (the regularised "
    "g_gen alone is misleading for rank-deficient kernels); extra noiseless pair qrc_exact vs mf_exact",
]
INTERPRETATION = (
    "Diagnostic, DS1 only; cannot show quantum advantage. Supports A016 at the representation level: the mean-field map "
    "is as close to the QRC as the QRC is to itself re-measured with another shot seed or rebuilt with another reservoir "
    "seed (CKA, g_gen at every lam, g_tra, residual), and in the noiseless limit the kernels nearly coincide. The QRC's "
    "per-record KTA edge over mean-field matches its edge over its own seed-1 draw. Does not support: any quantum "
    "advantage (these are linear kernels on measured expectations, not Tr(rho rho')); predictions of trained-readout F1 "
    "from KTA (unweighted kernel dominated by top PCs; separable has the highest KTA yet lower ds2s V F1 per A016); "
    "any test-patient claim."
)


def _cfg(exp):
    with open(os.path.join(ROOT, "runs", exp, "selected_config.json")) as f:
        return json.load(f)


def map_specs():
    c2, c3, c4, c5 = (_cfg(e) for e in ("E002", "E003", "E004", "E005"))
    assert c3["arm"] == "qrc" and c4["arm"] == "mf" and c2["arm"] == "esn" and c5["arm"] == "qrc"
    assert c4["config"] == c3["config"], "E004 must use E003's configuration"
    assert c5["config"] == dict(c3["config"], J=0.0), "E005 must be E003's configuration with J = 0"
    q, m, s, e = c3["config"], c4["config"], c5["config"], c2["config"]
    return {
        "qrc": ("E003 QRC, 1,024 shots, reservoir seed 0, shot seed 1000", lambda: run.build_model("qrc", q, 0, 1000)),
        "qrc_exact": ("exact QRC (shots=None), E003 configuration, reservoir seed 0",
                      lambda: run.build_model("qrc", q, 0, 1000, shots=None)),
        "mf": ("E004 mean-field, 1,024 shots, reservoir seed 0, shot seed 1000", lambda: run.build_model("mf", m, 0, 1000)),
        "sep": ("E005 separable QRC (J = 0), 1,024 shots, reservoir seed 0, shot seed 1000",
                lambda: run.build_model("qrc", s, 0, 1000)),
        "esn": ("E002 ESN, reservoir seed 0", lambda: run.build_model("esn", e, 0)),
        "qrc_shot1001": ("reference: E003 QRC, reservoir seed 0, shot seed 1001 (shot-noise floor)",
                         lambda: run.build_model("qrc", q, 0, 1001)),
        "qrc_res1": ("reference: E003 QRC seed-1 final-run setting (reservoir seed 1, shot seed 1001)",
                     lambda: run.build_model("qrc", q, 1, 1001)),
        "mf_exact": ("reference: exact mean-field (shots=None), reservoir seed 0",
                     lambda: run.build_model("mf", m, 0, 1000, shots=None)),
        "esn_res1": ("reference: E002 ESN, reservoir seed 1", lambda: run.build_model("esn", e, 1)),
    }


def provenance_check(models):
    """The regenerated seed-0 reservoirs equal the saved final-run artifacts."""
    out = {}
    for name, exp in (("qrc", "E003"), ("mf", "E004"), ("sep", "E005")):
        z = np.load(os.path.join(ROOT, "runs", exp, "model_seed0.npz"))
        out[name] = bool(np.array_equal(z["res_couplings"], models[name].couplings))
    z = np.load(os.path.join(ROOT, "runs", "E002", "model_seed0.npz"))
    m = models["esn"]
    out["esn"] = bool(np.array_equal(z["res_W"], m.W.cpu().numpy()) and np.array_equal(z["res_W_in"], m.W_in.cpu().numpy())
                      and np.array_equal(z["res_b"], m.b.cpu().numpy()))
    return out


def standardise(X, units):
    X = np.asarray(X, dtype=np.float64)
    mu, sd = X[units].mean(0), X[units].std(0) + SD_EPS
    return (X[units] - mu) / sd


def lin_cka(A, B):
    A = A - A.mean(0)
    B = B - B.mean(0)
    return float(np.linalg.norm(B.T @ A) ** 2 / (np.linalg.norm(A.T @ A) * np.linalg.norm(B.T @ B)))


def targets(y):
    oh = np.eye(3)[y]
    return {"onehot_NSV": oh, "V_vs_rest": oh[:, [2]], "S_vs_rest": oh[:, [1]]}


def eligible(y, target):
    """Per-record eligibility: >= MIN_CLASS units of the class in question and of the rest; for the one-hot target,
    >= MIN_CLASS units in at least two classes."""
    cnt = np.bincount(y, minlength=3)
    if target == "onehot_NSV":
        return int((cnt >= MIN_CLASS).sum()) >= 2
    c = 2 if target == "V_vs_rest" else 1
    return cnt[c] >= MIN_CLASS and len(y) - cnt[c] >= MIN_CLASS


def stratified(y, seed=SEED, n=N_PER_CLASS):
    rng = np.random.default_rng(seed)
    idx = [rng.choice(np.flatnonzero(y == c), min(n, int((y == c).sum())), replace=False) for c in range(3)]
    return np.sort(np.concatenate(idx))


def thin_eig(Z):
    """Eigen-decomposition of the trace-normalised linear kernel K = N Z Z^T / Tr(Z Z^T) from the thin SVD of Z:
    K = U diag(c) U^T with U (N, rank) orthonormal; the zero eigenvalues are dropped (they contribute nothing below)."""
    U, s, _ = np.linalg.svd(Z, full_matrices=False)
    c = s ** 2 * (len(Z) / (s ** 2).sum())
    keep = c > 1e-12 * c.max()
    return c[keep], U[:, keep]


def geo_diff(eC, eQ, lams):
    """Huang et al. 2021, Supplementary Information (arXiv:2011.01938v2) eqs. F19-F20 / L8-L9, with K_C the kernel
    that has to represent functions of K_Q:
      g_gen(lam) = sqrt(|| sqrt(K_Q) sqrt(K_C) (K_C + lam I)^-2 sqrt(K_C) sqrt(K_Q) ||_inf)   (= g(K_C || K_Q))
      g_tra(lam) = lam * sqrt(|| sqrt(K_Q) (K_C + lam I)^-2 sqrt(K_Q) ||_inf)                 (training-error factor)
    From thin eigendecompositions K_C = U_C diag(c) U_C^T, K_Q = U_Q diag(q) U_Q^T, G = U_Q^T U_C:
      g_gen = || diag(sqrt q) G diag(sqrt(c) / (c + lam)) ||_2
      g_tra^2 = lambda_max( diag(sqrt q) [G diag(lam^2 / (c + lam)^2) G^T + (I - G G^T)] diag(sqrt q) )
    (exact; I - G G^T is the part of K_Q's span outside K_C's span, which K_C cannot fit at any lam).
    Returns {lam: (g_gen, g_tra)} and g_tra^2 in the limit lam -> 0+ (the out-of-span residual)."""
    c, Uc = eC
    q, Uq = eQ
    G = Uq.T @ Uc
    sq = np.sqrt(q)
    A = sq[:, None] * G
    P = np.eye(len(q)) - G @ G.T
    out = {}
    for lam in lams:
        g_gen = float(np.linalg.norm(A * (np.sqrt(c) / (c + lam)), 2))
        M = (G * (lam / (c + lam)) ** 2) @ G.T + P
        g_tra = float(np.sqrt(max(np.linalg.eigvalsh(sq[:, None] * M * sq[None, :])[-1], 0.0)))
        out[lam] = (g_gen, g_tra)
    resid = float(max(np.linalg.eigvalsh(sq[:, None] * P * sq[None, :])[-1], 0.0))
    return out, resid


def main(argv=None):
    ap = argparse.ArgumentParser(description="E017 kernel diagnostic (DS1 only)")
    ap.add_argument("--out", default=os.path.join("runs", "E017"))
    ap.add_argument("--cache", help="optional npz of the DS1 feature maps (written if absent, read if present)")
    a = ap.parse_args(argv)
    out = os.path.join(ROOT, a.out) if not os.path.isabs(a.out) else a.out
    os.makedirs(out, exist_ok=True)
    T, t0 = {}, time.time()
    rev = code_revision("kernels")

    d, y_all, _ = run.ds1_data()
    units = y_all >= 0
    y = y_all[units]
    rec = d["record"][units]
    keys = run.keys_of(d)
    specs = map_specs()

    feats, provenance = {}, None
    if a.cache and os.path.exists(a.cache):
        z = np.load(a.cache)
        feats = {k: z[k] for k in specs}
        assert np.array_equal(z["beat_id"], d["beat_id"])
        provenance = json.loads(str(z["provenance"]))
        T["features_s"] = {"cached": a.cache}
    else:
        models, T["features_s"] = {}, {}
        for name, (_, build) in specs.items():
            t = time.time()
            models[name] = build()
            feats[name] = models[name].features(d[run.INPUT], keys)
            assert feats[name].shape == (len(keys), K_RES)
            T["features_s"][name] = round(time.time() - t, 1)
            print(f"features {name}: {T['features_s'][name]}s", flush=True)
        provenance = provenance_check(models)
        if a.cache:
            np.savez(a.cache, beat_id=d["beat_id"], provenance=json.dumps(provenance), **feats)
    print("provenance (regenerated seed-0 reservoirs == saved artifacts):", provenance, flush=True)

    Zrr = standardise(d["rr"], units)
    Z = {"res": {k: standardise(v, units) for k, v in feats.items()}}
    Z["res"]["rr"] = Zrr
    Z["res_rr"] = {k: (v if k == "rr" else np.c_[v, Zrr]) for k, v in Z["res"].items()}
    names = list(DECLARED) + list(REFERENCE)

    # ---- 1. linear CKA ------------------------------------------------------------------------------------------
    t = time.time()
    sub = stratified(y)
    sub_counts = {c: int((y[sub] == i).sum()) for i, c in enumerate(CLASSES)}
    cka = {}
    for blk in ("res", "res_rr"):
        for scope, idx in (("subsample", sub), ("all_units", np.arange(len(y)))):
            M = pd.DataFrame(np.eye(len(names)), index=names, columns=names)
            for i, p in enumerate(names):
                for q in names[i + 1:]:
                    M.loc[p, q] = M.loc[q, p] = lin_cka(Z[blk][p][idx], Z[blk][q][idx])
            M.to_csv(os.path.join(out, f"cka_{scope}_{blk}.csv"), float_format="%.4f")
            cka[f"{scope}/{blk}"] = M
    perm = np.random.default_rng(SEED + 1).permutation(len(sub))
    cka_null = {f"{p}_vs_{q}_rows_permuted/{blk}": lin_cka(Z[blk][p][sub], Z[blk][q][sub][perm])
                for blk in ("res", "res_rr") for p, q in (("qrc", "mf"), ("qrc", "esn"))}
    T["cka_s"] = round(time.time() - t, 1)
    print(f"CKA done {T['cka_s']}s", flush=True)

    # ---- 2. centred kernel-target alignment -----------------------------------------------------------------------
    t = time.time()
    rows = []
    for blk in ("res", "res_rr"):
        for scope, idx in (("subsample", sub), ("all_units", np.arange(len(y)))):
            tg = targets(y[idx])
            for m in names:
                for tn, Y in tg.items():
                    rows.append({"block": blk, "scope": scope, "map": m, "target": tn,
                                 "kta": lin_cka(Z[blk][m][idx], Y)})
    kta_pooled = pd.DataFrame(rows)
    kta_pooled.pivot_table(index=["block", "map"], columns=["target", "scope"], values="kta", sort=False).to_csv(
        os.path.join(out, "kta_pooled.csv"), float_format="%.4f")

    rows = []
    for r in sorted(np.unique(rec)):
        idx = np.flatnonzero(rec == r)
        yr = y[idx]
        cnt = np.bincount(yr, minlength=3)
        tg = targets(yr)
        for tn, Y in tg.items():
            if not eligible(yr, tn):
                continue
            for blk in ("res", "res_rr"):
                row = {"record": r, "target": tn, "block": blk, "n_units": len(idx), "n_N": int(cnt[0]),
                       "n_S": int(cnt[1]), "n_V": int(cnt[2])}
                for m in names:
                    row[m] = lin_cka(Z[blk][m][idx], Y)
                rows.append(row)
    kta_rec = pd.DataFrame(rows)
    kta_rec.to_csv(os.path.join(out, "kta_per_record.csv"), index=False, float_format="%.4f")

    wins = []
    for (tn, blk), g in kta_rec.groupby(["target", "block"], sort=False):
        for p, q in (("qrc", "esn"), ("qrc", "mf"), ("qrc", "sep"), ("qrc", "qrc_exact"), ("mf", "esn"),
                     ("sep", "esn"), ("qrc", "rr"), ("qrc", "qrc_res1"), ("esn", "esn_res1")):
            dlt = (g[p] - g[q]).to_numpy()
            nz = dlt[dlt != 0]
            wins.append({"target": tn, "block": blk, "a": p, "b": q, "records": len(g), "a_gt_b": int((dlt > 0).sum()),
                         "a_lt_b": int((dlt < 0).sum()), "median_a_minus_b": float(np.median(dlt)),
                         "mean_a_minus_b": float(dlt.mean()), "min": float(dlt.min()), "max": float(dlt.max()),
                         "wilcoxon_p_descriptive": float(wilcoxon(nz).pvalue) if len(nz) >= 6 else None})
    kta_wins = pd.DataFrame(wins)
    kta_wins.to_csv(os.path.join(out, "kta_per_record_wins.csv"), index=False, float_format="%.4g")
    T["kta_s"] = round(time.time() - t, 1)
    print(f"KTA done {T['kta_s']}s", flush=True)

    # ---- 3. geometric difference -----------------------------------------------------------------------------------
    t = time.time()
    rows, spectra = [], []
    for gs in GEO_SEEDS:
        gidx = np.sort(np.random.default_rng(gs).choice(len(y), N_GEO, replace=False))
        gcounts = {c: int((y[gidx] == i).sum()) for i, c in enumerate(CLASSES)}
        for blk in ("res", "res_rr"):
            E = {m: thin_eig(Z[blk][m][gidx]) for m in ["qrc"] + list(CLASSICAL_FOR_G)}  # includes qrc_exact, mf_exact
            for m, (w, _) in E.items():
                spectra.append({"geo_seed": gs, "block": blk, "map": m, "rank_1e-12": int(len(w)),
                                "participation_ratio": float(w.sum() ** 2 / (w ** 2).sum()),
                                "top_eig": float(w.max())})
            for kq, m in [("qrc", m) for m in CLASSICAL_FOR_G] + [("qrc_exact", "mf_exact")]:
                self_g, _ = geo_diff(E[kq], E[kq], GEO_LAMS)
                gcq, res_cq = geo_diff(E[m], E[kq], GEO_LAMS)
                gqc, res_qc = geo_diff(E[kq], E[m], GEO_LAMS)
                for lam in GEO_LAMS:
                    rows.append({"geo_seed": gs, "block": blk, "K_Q": kq, "K_C": m, "lam": lam,
                                 "g_gen_C_given_Q": gcq[lam][0], "g_tra_C_given_Q": gcq[lam][1],
                                 "g_gen_Q_given_C": gqc[lam][0], "g_tra_Q_given_C": gqc[lam][1],
                                 "g_gen_Q_given_Q_selfref": self_g[lam][0], "g_tra_Q_given_Q_selfref": self_g[lam][1],
                                 "resid_C_given_Q": res_cq, "resid_Q_given_C": res_qc,
                                 "top_eig_Q": float(E[kq][0].max()),
                                 "n": N_GEO, "n_N": gcounts["N"], "n_S": gcounts["S"], "n_V": gcounts["V"]})
        print(f"geo seed {gs} done {round(time.time() - t, 1)}s", flush=True)
    geo = pd.DataFrame(rows)
    geo.to_csv(os.path.join(out, "geodiff.csv"), index=False, float_format="%.5g")
    pd.DataFrame(spectra).to_csv(os.path.join(out, "spectra.csv"), index=False, float_format="%.5g")
    T["geo_s"] = round(time.time() - t, 1)
    T["total_s"] = round(time.time() - t0, 1)

    geo_mean = geo.groupby(["block", "K_Q", "K_C", "lam"])[["g_gen_C_given_Q", "g_tra_C_given_Q", "g_gen_Q_given_C",
                                                      "g_tra_Q_given_C", "g_gen_Q_given_Q_selfref"]].agg(["mean", "min", "max"])
    sel = []
    for (gs, blk, kq, m), g in geo.groupby(["geo_seed", "block", "K_Q", "K_C"]):
        for direction in ("C_given_Q", "Q_given_C"):
            ok = g[g[f"g_tra_{direction}"] < G_TRA_MAX]
            r = ok.loc[ok["lam"].idxmax()] if len(ok) else None
            sel.append({"geo_seed": gs, "block": blk, "K_Q": kq, "K_C": m, "direction": direction,
                        "lam_selected": None if r is None else float(r["lam"]),
                        "g_gen": None if r is None else float(r[f"g_gen_{direction}"]),
                        "g_tra": None if r is None else float(r[f"g_tra_{direction}"]),
                        "min_g_tra_on_grid": float(g[f"g_tra_{direction}"].min()),
                        "resid_lam0": float(g[f"resid_{direction}"].iloc[0])})
    geo_sel = pd.DataFrame(sel)
    geo_sel.to_csv(os.path.join(out, "geodiff_paper_rule.csv"), index=False, float_format="%.5g")
    summary = {
        "experiment": "E017", "result_type": "diagnostic (DS1 only; no test labels)",
        "command": "CUDA_VISIBLE_DEVICES=0 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 .venv/Scripts/python -I -m qhc.p4.kernels "
                   + " ".join(argv if argv is not None else __import__("sys").argv[1:]),
        "code_revision": rev,
        "maps": {k: v[0] for k, v in specs.items()} | {"rr": "RR only (8 features, d['rr'])"},
        "declared_maps": list(DECLARED), "reference_maps_added": list(REFERENCE),
        "provenance_seed0_reservoirs_match_saved_artifacts": provenance,
        "ds1": {"beats": int(len(units)), "units": int(units.sum()),
                "class_counts": {c: int((y == i).sum()) for i, c in enumerate(CLASSES)},
                "records": int(len(np.unique(rec)))},
        "standardisation": "per column on DS1 units: (x - mean) / (sd + 1e-6), population sd (as readout.Readout)",
        "subsample_cka_kta": {"seed": SEED, "rng": "numpy.random.default_rng(seed).choice per class N, S, V in order, "
                              "without replacement", "per_class_max": N_PER_CLASS, "counts": sub_counts},
        "geo": {"seeds": list(GEO_SEEDS), "n": N_GEO, "draw": "uniform without replacement over DS1 units",
                "lams": list(GEO_LAMS), "trace_normalised_to_N": True, "g_tra_max_paper_rule": G_TRA_MAX},
        "per_record_rule": f">= {MIN_CLASS} units of the class and of the rest (one-hot: >= {MIN_CLASS} in >= 2 classes)",
        "cka": {k: v.round(4).to_dict() for k, v in cka.items()},
        "cka_null_rows_permuted": cka_null,
        "kta_pooled": kta_pooled.to_dict(orient="records"),
        "kta_per_record_wins": kta_wins.to_dict(orient="records"),
        "kta_records_eligible": kta_rec[kta_rec.block == "res"].groupby("target").size().to_dict(),
        "geodiff_paper_rule": geo_sel.to_dict(orient="records"),
        "geodiff_mean_min_max_over_seeds": {f"{b}|{kq}|{m}|{lam}": {f"{c[0]}_{c[1]}": float(v) for c, v in r.items()}
                                            for (b, kq, m, lam), r in geo_mean.iterrows()},
        "timings_s": T,
        "formulas": FORMULAS, "references_verified": REFERENCES, "deviations_from_card": DEVIATIONS,
        "interpretation": INTERPRETATION,
        "note": "summary.md could not be written by the CPU C lane (subagent harness blocks .md files); this JSON carries "
                "everything it would hold.",
    }
    with open(os.path.join(out, "summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    print(json.dumps({"timings": T, "code_revision": rev}), flush=True)


if __name__ == "__main__":
    main()
