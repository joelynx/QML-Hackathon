"""Phase 4 ablations of the E003 quantum reservoir (EXPERIMENTS.md cards E012, E013, E014). src/qhc/pipe/ is untouched;
this module reuses its data loading, readout, prediction writer and lookahead pipeline.

  python -I -m qhc.p4.ablate e012                      exact expectations (reservoirs.QRC shots=None), cfg15, lambda 0.1
  python -I -m qhc.p4.ablate leakcheck --model runs/E012/model_seed0.npz --out runs/E012/leakcheck_seed0.json
  python -I -m qhc.p4.ablate e013 --shots 64 256 4096 1024   shot sweep, DS1 OOF only (1024 recomputes E003)
  python -I -m qhc.p4.ablate e014-check                n = 10 equivalence with reservoirs.QRC; dense-matrix check
  python -I -m qhc.p4.ablate e014 --variant n6         variants n6 n8 n12 (Z + ZZ) and z10 (Z only, K = 40)
  python -I -m qhc.p4.ablate e014-final                declared DS1 selection among n6/n8/n12, ds2s predictions

Common protocol (EXPERIMENTS.md "Phase 4 declarations"): E003's configuration cfg15; reservoir seed s, shot seed
1000 + s, s = 0..4; DS1 OOF by readout.cv_oof on the fixed folds; the ds2s readout is refitted on all DS1 units.
No ds2s, ds2 or svdb labels are read here.
"""
import argparse
import glob
import itertools
import json
import os
import time

import numpy as np
import pandas as pd
import torch

from .. import evalspec as E
from ..evaluate import ROOT, check_runs, load_positions
from ..leakcheck import check_lookahead
from ..scorer import f1_from_confusion
from ..units import sha256
from ..pipe import reservoirs as R
from ..pipe import run
from ..pipe.features import load_signal, load_split
from ..pipe.readout import LAMBDAS, Readout, cv_oof
from . import code_revision

NAME = "ablate"
REV = code_revision(NAME)  # the code this process loaded
SHOTS = run.SHOTS  # 1024, E003
LAM = 0.1  # E003's selected lambda
SEEDS = list(range(E.N_SEEDS))
VARIANTS = {"n6": 6, "n8": 8, "n12": 12, "z10": 10}


def odir(*parts):
    p = os.path.join(ROOT, "runs", *parts)
    os.makedirs(p, exist_ok=True)
    return p


def rel(path):
    return os.path.relpath(path, ROOT).replace(os.sep, "/")


def e003():
    with open(os.path.join(ROOT, "runs", "E003", "selected_config.json")) as f:
        b = json.load(f)
    assert b["arm"] == "qrc" and b["index"] == 15 and b["lam"] == LAM, b
    return b["config"]


def scores(y, p):
    """Pooled DS1 OOF macro-F1 and per-class F1 over the N/S/V units."""
    u = y >= 0
    cm = np.zeros((len(E.CLASSES),) * 2, dtype=np.int64)
    np.add.at(cm, (y[u], np.asarray(p)[u].argmax(1)), 1)
    f = f1_from_confusion(cm)
    return {"macro_f1": float(f.mean()), **{f"f1_{c}": float(f[i]) for i, c in enumerate(E.CLASSES)}}


def oof_eval(F, d, y, folds, lams):
    oof = cv_oof(run.design(F, d), y, d["record"], folds, lams)
    sc = {lam: scores(y, oof[lam]) for lam in lams}
    return oof, sc


def first_best(sc, lams):
    return max(lams, key=lambda lam: sc[lam]["macro_f1"])  # first maximum in grid order


def dump(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)


# ---------------------------------------------------------------- generalised n-qubit QRC (E014)

def edges_of(n, topology):
    e = [(q, q + 1) for q in range(n - 1)]
    return e + [(n - 1, 0)] if topology == "ring" else e


def z_table(n):
    """As reservoirs._z_table, for n qubits: (2^n, n + n(n-1)/2) eigenvalues of Z_q and Z_q Z_r; qubit q = bit q."""
    pairs = list(itertools.combinations(range(n), 2))
    b = np.arange(2 ** n)
    z = 1.0 - 2.0 * ((b[:, None] >> np.arange(n)[None, :]) & 1)
    zz = np.stack([z[:, q] * z[:, r] for q, r in pairs], 1)
    return np.concatenate([z, zz], 1).astype(np.float32), pairs


def resample_chunks(win, n):
    """(B, N_STEPS, n): each 10-sample chunk linearly resampled to n evenly spaced points (np.interp); identity at 10."""
    u = R._chunks(win)
    if n == R.N_IN:
        return u
    pos, xp = np.linspace(0, R.N_IN - 1, n), np.arange(R.N_IN, dtype=float)
    flat = u.reshape(-1, R.N_IN)
    out = np.empty((len(flat), n), dtype=np.float32)
    for i, row in enumerate(flat):
        out[i] = np.interp(pos, xp, row)
    return out.reshape(len(u), R.N_STEPS, n)


class GQRC:
    """reservoirs.QRC generalised to n qubits (logic copied): per step k, RY(in_scale * u_{k,q}) on qubit q, then
    `depth` times ZZ(J_e) on the ring and RX(h) on every qubit; couplings J * (1 + disorder * U[-1, 1]) from
    default_rng(seed) over the n ring edges; readout <Z_q> and all <Z_q Z_r> per snapshot; finite shots from the same
    per-beat Philox streams (reservoirs._uniforms)."""

    def __init__(self, n_qubits, in_scale, J, h, depth, topology, disorder, seed, shots=1024, shot_seed=None,
                 device=R.DEVICE):
        self.n = int(n_qubits)
        self.cfg = dict(in_scale=in_scale, J=J, h=h, depth=int(depth), topology=topology, disorder=disorder)
        self.seed, self.shots = int(seed), shots
        self.shot_seed = int(seed if shot_seed is None else shot_seed)
        self.device = device
        g = np.random.default_rng(self.seed)
        self.edges = edges_of(self.n, topology)
        self.couplings = J * (1 + disorder * g.uniform(-1, 1, len(self.edges)))
        ztab, self.pairs = z_table(self.n)
        zz_energy = sum(c * ztab[:, q] * ztab[:, r] for c, (q, r) in zip(self.couplings, self.edges))
        self.zz_phase = torch.tensor(np.exp(-1j * zz_energy), dtype=torch.complex64, device=device)
        self.obs = torch.tensor(ztab, device=device)
        c, s = np.cos(h / 2), np.sin(h / 2)
        self.rx = torch.tensor(np.array([[c, -1j * s], [-1j * s, c]]), dtype=torch.complex64, device=device)
        self.K = ztab.shape[1] * R.N_STEPS

    def _ry(self, psi, q, theta):
        n = psi.shape[0]
        v = psi.view(n, 2 ** (self.n - 1 - q), 2, 2 ** q)
        c, s = torch.cos(theta / 2).view(n, 1, 1), torch.sin(theta / 2).view(n, 1, 1)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        return torch.stack([c * a0 - s * a1, s * a0 + c * a1], 2).reshape(n, -1)

    def _rx_all(self, psi):
        n = psi.shape[0]
        c, ms = self.rx[0, 0], self.rx[0, 1]
        for q in range(self.n):
            v = psi.view(n, 2 ** (self.n - 1 - q), 2, 2 ** q)
            a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
            psi = torch.stack([c * a0 + ms * a1, ms * a0 + c * a1], 2).reshape(n, -1)
        return psi

    def _readout(self, psi, unif):
        p = psi.real ** 2 + psi.imag ** 2
        if self.shots is None:
            return (p.double() @ self.obs.double()).float()
        cdf = torch.cumsum(p.double(), 1)
        idx = torch.searchsorted(cdf, unif.double() * cdf[:, -1:]).clamp(max=p.shape[1] - 1)
        counts = torch.zeros_like(p).scatter_add_(1, idx, torch.ones_like(idx, dtype=p.dtype))
        return (counts / self.shots) @ self.obs

    @torch.no_grad()
    def features(self, win, keys=None, batch=8192):
        u_all = resample_chunks(win, self.n)
        if self.shots is not None and keys is None:
            raise ValueError("finite-shot readout needs one beat key per row")
        out = []
        for b0 in range(0, len(u_all), batch):
            u = torch.tensor(u_all[b0:b0 + batch], device=self.device)
            unif = None
            if self.shots is not None:
                unif = torch.tensor(R._uniforms(keys[b0:b0 + batch], self.shot_seed, R.N_STEPS * self.shots),
                                    device=self.device).view(-1, R.N_STEPS, self.shots)
            n = u.shape[0]
            psi = torch.zeros(n, 2 ** self.n, dtype=torch.complex64, device=self.device)
            psi[:, 0] = 1
            feats = []
            for k in range(R.N_STEPS):
                for q in range(self.n):
                    psi = self._ry(psi, q, self.cfg["in_scale"] * u[:, k, q])
                for _ in range(self.cfg["depth"]):
                    psi = self._rx_all(psi * self.zz_phase)
                feats.append(self._readout(psi, None if unif is None else unif[:, k]))
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out).astype(np.float32)


def dense_features(n, cfg, couplings, win):
    """Independent check: scipy.sparse Kronecker-product operators in complex128, exact expectations."""
    import scipy.sparse as sp
    I2 = sp.identity(2, format="csr", dtype=complex)
    Z = sp.csr_matrix(np.diag([1.0, -1.0]).astype(complex))

    def on(q, G):  # qubit q is bit q of the basis index: the rightmost Kronecker factor is qubit 0
        return sp.kron(sp.kron(sp.identity(2 ** (n - 1 - q), dtype=complex), sp.csr_matrix(G)),
                       sp.identity(2 ** q, dtype=complex), format="csr")

    Zs = [on(q, Z) for q in range(n)]
    H = sum(c * (Zs[a] @ Zs[b]) for c, (a, b) in zip(couplings, edges_of(n, cfg["topology"])))
    Uzz = sp.diags(np.exp(-1j * H.diagonal()))
    ch, sh = np.cos(cfg["h"] / 2), np.sin(cfg["h"] / 2)
    RX = np.array([[ch, -1j * sh], [-1j * sh, ch]])
    RXs = [on(q, RX) for q in range(n)]
    pairs = list(itertools.combinations(range(n), 2))
    xp = np.arange(R.N_IN, dtype=float)
    out = []
    for w in np.asarray(win, dtype=np.float32):
        psi = np.zeros(2 ** n, dtype=complex)
        psi[0] = 1
        feats = []
        for k in range(R.N_STEPS):
            chunk = w[k * R.N_IN:(k + 1) * R.N_IN].astype(float)
            u = chunk if n == R.N_IN else np.interp(np.linspace(0, R.N_IN - 1, n), xp, chunk)
            for q in range(n):
                t = cfg["in_scale"] * u[q]
                psi = on(q, np.array([[np.cos(t / 2), -np.sin(t / 2)], [np.sin(t / 2), np.cos(t / 2)]])) @ psi
            for _ in range(cfg["depth"]):
                psi = Uzz @ psi
                for q in range(n):
                    psi = RXs[q] @ psi
            ez = [np.vdot(psi, Zs[q] @ psi).real for q in range(n)]
            ezz = [np.vdot(psi, Zs[a] @ (Zs[b] @ psi)).real for a, b in pairs]
            feats += ez + ezz
        out.append(feats)
    return np.array(out)


# ---------------------------------------------------------------- artifacts, predictions, lookahead check

def save_model(path, meta, model, ro):
    st = ro.state()
    np.savez(path, meta=json.dumps(meta), lam=st["lam"], mu=st["mu"], sd=st["sd"], W_readout=st["W"],
             b_readout=st["b"], res_couplings=model.couplings)


def load_model(path):
    z = np.load(path)
    meta = json.loads(str(z["meta"]))
    ro = Readout(float(z["lam"]))
    ro.mu, ro.sd, ro.W, ro.b = z["mu"], z["sd"], z["W_readout"], z["b_readout"]
    kw = dict(meta["config"], seed=meta["seed"], shots=meta["shots"], shot_seed=meta["shot_seed"])
    model = R.QRC(**kw) if meta["model_class"] == "reservoirs.QRC" else GQRC(meta["n_qubits"], **kw)
    assert np.array_equal(model.couplings, z["res_couplings"]), "couplings do not match the artifact"
    return meta, model, ro


def write_ds2s(out, seed, model, ro, ds, tkeys, man_extra):
    f = os.path.join(out, f"pred_ds2s_seed{seed}.csv")
    run.write_pred(f, ds["beat_id"], ro.predict_proba(run.design(model.features(ds[run.INPUT], tkeys), ds)))
    R._UNIF_CACHE.clear()
    art = os.path.join(out, f"model_seed{seed}.npz")
    man = {"seed": seed, "split": "ds2s", "code_revision": REV, "model_artifact": rel(art),
           "model_artifact_sha256": sha256(art), "reservoir_seed": seed, "prediction_sha256": sha256(f), **man_extra}
    missing = [k for k in E.RUN_KEYS if k not in man]
    assert not missing, missing
    dump(os.path.splitext(f)[0] + ".run.json", man)
    return f


def leakcheck(model_path, out_path):
    t = time.time()
    meta, model, ro = load_model(model_path)
    pos = load_positions("ds1")
    report = {"model": rel(model_path), "model_sha256": sha256(model_path), "arm": meta["arm"], "seed": meta["seed"],
              "code_revision": REV, "records": {}}
    for rec in run.LEAK_RECORDS:
        g = pos[pos["record"] == rec].sort_values("sample")
        sig, fs, _ = load_signal("mitdb", rec)
        s = g["sample"].to_numpy()
        s = s[s < run.LEAK_SECONDS * fs]
        sig = sig[:int((run.LEAK_SECONDS + 10) * fs)]
        idx = range(1, len(s) - 1)
        fn = run.pipeline_fn(meta, model, ro, "mitdb", rec)

        def f(*args):
            r = fn(*args)
            R._UNIF_CACHE.clear()  # memory only; values do not depend on the cache
            return r

        bad = check_lookahead(f, sig, s, fs, idx)
        report["records"][rec] = {"beats_checked": len(idx), "violations": bad}
    report["beats_checked"] = sum(r["beats_checked"] for r in report["records"].values())
    report["n_violations"] = sum(len(r["violations"]) for r in report["records"].values())
    report["passed"] = report["n_violations"] == 0
    report["seconds"] = round(time.time() - t, 1)
    dump(out_path, report)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}), flush=True)
    return report


def cmd_leakcheck(a):
    leakcheck(os.path.join(ROOT, a.model), os.path.join(ROOT, a.out))


# ---------------------------------------------------------------- E012

def cmd_e012(a):
    cfg, out = e003(), odir("E012")
    d, y, folds = run.ds1_data()
    keys, units = run.keys_of(d), y >= 0
    ds = load_split("ds2s")
    tkeys = run.keys_of(ds)
    res = {"exp": "E012", "code_revision": REV, "config": cfg, "config_index": 15, "lam": LAM, "shots": None,
           "lambdas": list(LAMBDAS), "seeds": {}}
    for s in a.seeds:
        t = time.time()
        model = R.QRC(**cfg, seed=s, shots=None)
        F = model.features(d[run.INPUT], keys)
        t_feat = time.time() - t
        oof, sc = oof_eval(F, d, y, folds, LAMBDAS)
        run.write_pred(os.path.join(out, f"oof_ds1_seed{s}.csv"), d["beat_id"], oof[LAM])
        # mechanism checks: finite-shot E003 features of the same seed differ; prediction agreement with E003 OOF
        Ff = R.QRC(**cfg, seed=s, shots=SHOTS, shot_seed=1000 + s).features(d[run.INPUT], keys)
        R._UNIF_CACHE.clear()
        e3 = pd.read_csv(os.path.join(ROOT, "runs", "E003", f"oof_ds1_seed{s}.csv"), dtype={"beat_id": str})
        assert (e3["beat_id"].to_numpy() == d["beat_id"]).all()
        pred = np.array(E.CLASSES)[oof[LAM].argmax(1)]
        e3_probs = e3[[f"prob_{c}" for c in E.CLASSES]].to_numpy()
        ro = Readout(LAM).fit(run.design(F, d)[units], y[units])
        meta = {"arm": "qrc_exact", "exp": "E012", "model_class": "reservoirs.QRC", "n_qubits": 10, "config": cfg,
                "config_index": 15, "seed": s, "shot_seed": None, "shots": None, "input": run.INPUT, "lam": LAM,
                "code_revision": REV}
        save_model(os.path.join(out, f"model_seed{s}.npz"), meta, model, ro)
        f = write_ds2s(out, s, model, ro, ds, tkeys, {"arm_id": "E012-qrc_exact", "config_id": "E012-qrc-cfg15-exact",
                                                       "shot_seed": None, "shots": None, "config": cfg, "lam": LAM})
        res["seeds"][s] = {
            "oof_lam0.1": sc[LAM], "oof_by_lam": {str(k): v for k, v in sc.items()},
            "best_lam": first_best(sc, LAMBDAS), "best_lam_macro_f1": sc[first_best(sc, LAMBDAS)]["macro_f1"],
            "e003_oof": scores(y, e3_probs),
            "feature_mae_vs_1024shot": float(np.abs(F - Ff).mean()), "feature_maxabs_vs_1024shot": float(np.abs(F - Ff).max()),
            "features_identical_to_1024shot": bool(np.array_equal(F, Ff)),
            "pred_agreement_vs_E003_oof_all": float((pred == e3["pred"].to_numpy()).mean()),
            "pred_agreement_vs_E003_oof_units": float((pred[units] == e3["pred"].to_numpy()[units]).mean()),
            "ds2s_pred": rel(f), "seconds_features": round(t_feat, 1), "seconds": round(time.time() - t, 1)}
        print(f"E012 seed {s}: OOF lam0.1 {sc[LAM]['macro_f1']:.4f} (E003 {res['seeds'][s]['e003_oof']['macro_f1']:.4f})"
              f" agree {res['seeds'][s]['pred_agreement_vs_E003_oof_units']:.4f} {res['seeds'][s]['seconds']}s", flush=True)
        dump(os.path.join(out, "e012_results.json"), res)
    runs = check_runs(sorted(glob.glob(os.path.join(out, "pred_ds2s_seed*.csv"))), "ds2s", "E012")
    res["check_runs"] = {"passed": True, "n_runs": len(runs), "arm_id": runs[0]["arm_id"], "config_id": runs[0]["config_id"]}
    m = [res["seeds"][s]["oof_lam0.1"]["macro_f1"] for s in a.seeds]
    m3 = [res["seeds"][s]["e003_oof"]["macro_f1"] for s in a.seeds]
    res["mean_oof_lam0.1"], res["mean_e003_oof"] = float(np.mean(m)), float(np.mean(m3))
    res["mean_delta_vs_e003"] = float(np.mean(m) - np.mean(m3))
    dump(os.path.join(out, "e012_results.json"), res)
    print("E012 check_runs passed; mean OOF", res["mean_oof_lam0.1"], "E003", res["mean_e003_oof"], flush=True)


# ---------------------------------------------------------------- E013

def cmd_e013(a):
    cfg, out = e003(), odir("E013")
    d, y, folds = run.ds1_data()
    keys = run.keys_of(d)
    path = os.path.join(out, "e013_results.json")
    res = {"exp": "E013", "code_revision": REV, "config": cfg, "lam": LAM, "lambdas": list(LAMBDAS), "shots": {}}
    if os.path.exists(path):
        with open(path) as f:
            res = json.load(f)
        res["code_revision_resumed"] = REV
    exact0 = R.QRC(**cfg, seed=0, shots=None).features(d[run.INPUT], keys)
    zcols = np.array([k * R.K_SNAP + q for k in range(R.N_STEPS) for q in range(R.N_QUBITS)])
    zzcols = np.setdiff1d(np.arange(R.K), zcols)
    for n in a.shots:
        r = res["shots"].setdefault(str(n), {"seeds": {}})
        for s in a.seeds:
            if str(s) in r["seeds"]:
                continue
            t = time.time()
            F = R.QRC(**cfg, seed=s, shots=n, shot_seed=1000 + s).features(d[run.INPUT], keys)
            R._UNIF_CACHE.clear()
            t_feat = time.time() - t
            if s == 0:
                err = np.abs(F - exact0)
                r["feature_error_seed0"] = {"mae_all": float(err.mean()), "mae_Z": float(err[:, zcols].mean()),
                                            "mae_ZZ": float(err[:, zzcols].mean()), "max": float(err.max())}
            oof, sc = oof_eval(F, d, y, folds, LAMBDAS)
            f = os.path.join(out, f"oof_ds1_shots{n}_seed{s}.csv")
            run.write_pred(f, d["beat_id"], oof[LAM])
            best = first_best(sc, LAMBDAS)
            rs = {"oof_lam0.1": sc[LAM], "oof_by_lam": {str(k): v for k, v in sc.items()}, "best_lam": best,
                  "best_lam_macro_f1": sc[best]["macro_f1"], "oof_file": rel(f),
                  "seconds_features": round(t_feat, 1), "seconds": round(time.time() - t, 1)}
            if n == SHOTS:  # reproduction of E003's OOF files
                e3 = pd.read_csv(os.path.join(ROOT, "runs", "E003", f"oof_ds1_seed{s}.csv"), dtype={"beat_id": str})
                pe = e3[[f"prob_{c}" for c in E.CLASSES]].to_numpy()
                rs["e003_repro"] = {"max_abs_prob_diff": float(np.abs(pe - oof[LAM]).max()),
                                    "pred_agreement": float((e3["pred"].to_numpy()
                                                             == np.array(E.CLASSES)[oof[LAM].argmax(1)]).mean()),
                                    "e003_file_oof": scores(y, pe)}
            r["seeds"][str(s)] = rs
            print(f"E013 shots {n} seed {s}: lam0.1 {sc[LAM]['macro_f1']:.4f} best {best} {sc[best]['macro_f1']:.4f}"
                  f" {rs['seconds']}s", flush=True)
            dump(path, res)
        done = [r["seeds"][str(s)] for s in SEEDS if str(s) in r["seeds"]]
        r["mean_oof_lam0.1"] = float(np.mean([x["oof_lam0.1"]["macro_f1"] for x in done]))
        r["mean_best_lam"] = float(np.mean([x["best_lam_macro_f1"] for x in done]))
        r["n_seeds"] = len(done)
        dump(path, res)


# ---------------------------------------------------------------- E014

def variant_features(v, cfg, s, d, keys):
    n = VARIANTS[v]
    if v == "z10":  # Z-only readout: the first 10 of each 55-feature snapshot block of the E003 features
        F = R.QRC(**cfg, seed=s, shots=SHOTS, shot_seed=1000 + s).features(d[run.INPUT], keys)
        cols = np.array([k * R.K_SNAP + q for k in range(R.N_STEPS) for q in range(R.N_QUBITS)])
        F = F[:, cols]
    else:
        F = GQRC(n, **cfg, seed=s, shots=SHOTS, shot_seed=1000 + s).features(d[run.INPUT], keys)
    R._UNIF_CACHE.clear()
    return F


def cmd_e014_check(a):
    cfg, out = e003(), odir("E014")
    d, _, _ = run.ds1_data()
    keys = run.keys_of(d)
    idx = np.arange(0, len(keys), 16)  # 3,186 DS1 beats spread over every record
    rep = {"code_revision": REV, "n_beats": int(len(idx)), "beats": "every 16th DS1 prediction-set beat", "n10": {}}
    for s in (0, 3):
        for shots in (SHOTS, None):
            t = time.time()
            A = R.QRC(**cfg, seed=s, shots=shots, shot_seed=1000 + s).features(d[run.INPUT][idx], keys[idx])
            G = GQRC(10, **cfg, seed=s, shots=shots, shot_seed=1000 + s)
            B = G.features(d[run.INPUT][idx], keys[idx])
            R._UNIF_CACHE.clear()
            ref = R.QRC(**cfg, seed=s, shots=shots, shot_seed=1000 + s)
            rep["n10"][f"seed{s}_shots{shots}"] = {
                "bit_identical": bool(np.array_equal(A, B)), "max_abs_diff": float(np.abs(A - B).max()),
                "couplings_equal": bool(np.array_equal(ref.couplings, G.couplings)), "K": int(B.shape[1]),
                "seconds": round(time.time() - t, 1)}
            print("n10", s, shots, rep["n10"][f"seed{s}_shots{shots}"], flush=True)
    rep["dense"] = {}
    di = idx[:a.dense_beats]
    for n in (6, 8, 10, 12):
        t = time.time()
        G = GQRC(n, **cfg, seed=0, shots=None)
        A = G.features(d[run.INPUT][di])
        B = dense_features(n, cfg, G.couplings, d[run.INPUT][di])
        rep["dense"][f"n{n}"] = {"beats": int(len(di)), "K": int(A.shape[1]), "max_abs_diff": float(np.abs(A - B).max()),
                                 "seconds": round(time.time() - t, 1)}
        print("dense", n, rep["dense"][f"n{n}"], flush=True)
    rep["passed"] = all(x["max_abs_diff"] <= 1e-6 and x["couplings_equal"] for x in rep["n10"].values())
    dump(os.path.join(out, "mechanism_check.json"), rep)
    print("passed", rep["passed"])


def cmd_e014(a):
    cfg, v = e003(), a.variant
    out = odir("E014", v)
    d, y, folds = run.ds1_data()
    keys = run.keys_of(d)
    res = {"exp": "E014", "variant": v, "n_qubits": VARIANTS[v], "readout": "Z" if v == "z10" else "Z+ZZ",
           "code_revision": REV, "config": cfg, "shots": SHOTS, "lambdas": list(LAMBDAS), "seeds": {}}
    t = time.time()
    F = variant_features(v, cfg, 0, d, keys)
    res["K"] = int(F.shape[1])
    oof, sc = oof_eval(F, d, y, folds, LAMBDAS)
    lam = first_best(sc, LAMBDAS)
    res["selected_lam"], res["seed0_by_lam"] = lam, {str(k): x for k, x in sc.items()}
    run.write_pred(os.path.join(out, "oof_ds1_seed0.csv"), d["beat_id"], oof[lam])
    res["seeds"]["0"] = {**sc[lam], "seconds": round(time.time() - t, 1)}
    print(f"E014 {v} K {res['K']} seed 0: {json.dumps({k: round(x['macro_f1'], 4) for k, x in sc.items()})} -> lam {lam}",
          flush=True)
    dump(os.path.join(out, "variant_results.json"), res)
    for s in SEEDS[1:]:
        t = time.time()
        F = variant_features(v, cfg, s, d, keys)
        oof, sc = oof_eval(F, d, y, folds, (lam,))
        run.write_pred(os.path.join(out, f"oof_ds1_seed{s}.csv"), d["beat_id"], oof[lam])
        res["seeds"][str(s)] = {**sc[lam], "seconds": round(time.time() - t, 1)}
        print(f"E014 {v} seed {s}: {sc[lam]['macro_f1']:.4f} {res['seeds'][str(s)]['seconds']}s", flush=True)
        dump(os.path.join(out, "variant_results.json"), res)
    for k in ("macro_f1", *(f"f1_{c}" for c in E.CLASSES)):
        res[f"mean_{k}"] = float(np.mean([res["seeds"][str(s)][k] for s in SEEDS]))
    dump(os.path.join(out, "variant_results.json"), res)
    print(f"E014 {v}: mean {res['mean_macro_f1']:.4f}", flush=True)


def cmd_e014_final(a):
    cfg = e003()
    cands = []
    for v in ("n6", "n8", "n12"):
        with open(os.path.join(ROOT, "runs", "E014", v, "variant_results.json")) as f:
            r = json.load(f)
        assert len(r["seeds"]) == E.N_SEEDS, v
        cands.append(r)
    sel = max(cands, key=lambda r: (r["mean_macro_f1"], -r["n_qubits"]))  # ties to fewer qubits
    n, lam, v = sel["n_qubits"], sel["selected_lam"], f"n{sel['n_qubits']}"
    out = odir("E014", v)
    d, y, _ = run.ds1_data()
    keys, units = run.keys_of(d), y >= 0
    ds = load_split("ds2s")
    tkeys = run.keys_of(ds)
    rep = {"code_revision": REV, "rule": "highest 5-seed mean pooled DS1 OOF macro-F1 among n6/n8/n12, ties to fewer qubits",
           "means": {f"n{r['n_qubits']}": r["mean_macro_f1"] for r in cands}, "selected": v, "lam": lam, "seeds": {}}
    for s in SEEDS:
        t = time.time()
        model = GQRC(n, **cfg, seed=s, shots=SHOTS, shot_seed=1000 + s)
        X = run.design(model.features(d[run.INPUT], keys), d)
        R._UNIF_CACHE.clear()
        ro = Readout(lam).fit(X[units], y[units])
        meta = {"arm": f"qrc_n{n}", "exp": "E014", "model_class": "p4.ablate.GQRC", "n_qubits": n, "readout": "Z+ZZ",
                "K": model.K, "config": cfg, "config_index": 15, "seed": s, "shot_seed": 1000 + s, "shots": SHOTS,
                "input": run.INPUT, "lam": lam, "code_revision": REV}
        save_model(os.path.join(out, f"model_seed{s}.npz"), meta, model, ro)
        f = write_ds2s(out, s, model, ro, ds, tkeys, {"arm_id": f"E014-qrc_n{n}", "config_id": f"E014-qrc-cfg15-n{n}",
                                                       "shot_seed": 1000 + s, "shots": SHOTS, "n_qubits": n,
                                                       "config": dict(cfg, n_qubits=n), "lam": lam})
        rep["seeds"][s] = {"ds2s_pred": rel(f), "seconds": round(time.time() - t, 1)}
        print(f"E014 final {v} seed {s}: {rep['seeds'][s]['seconds']}s", flush=True)
    runs = check_runs(sorted(glob.glob(os.path.join(out, "pred_ds2s_seed*.csv"))), "ds2s", f"E014-qrc_n{n}")
    rep["check_runs"] = {"passed": True, "n_runs": len(runs), "arm_id": runs[0]["arm_id"], "config_id": runs[0]["config_id"]}
    dump(os.path.join(ROOT, "runs", "E014", "selection.json"), rep)
    print("check_runs passed", flush=True)
    rep["leakcheck"] = leakcheck(os.path.join(out, "model_seed0.npz"), os.path.join(out, "leakcheck_seed0.json"))["passed"]
    dump(os.path.join(ROOT, "runs", "E014", "selection.json"), rep)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Phase 4 QRC ablations (E012-E014)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("e012")
    p.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    p.set_defaults(fn=cmd_e012)
    p = sub.add_parser("leakcheck")
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_leakcheck)
    p = sub.add_parser("e013")
    p.add_argument("--shots", type=int, nargs="+", default=[64, 256, 4096, 1024])
    p.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    p.set_defaults(fn=cmd_e013)
    p = sub.add_parser("e014-check")
    p.add_argument("--dense-beats", type=int, default=8)
    p.set_defaults(fn=cmd_e014_check)
    p = sub.add_parser("e014")
    p.add_argument("--variant", required=True, choices=sorted(VARIANTS))
    p.set_defaults(fn=cmd_e014)
    p = sub.add_parser("e014-final")
    p.set_defaults(fn=cmd_e014_final)
    a = ap.parse_args(argv)
    print("code_revision", REV, flush=True)
    a.fn(a)


if __name__ == "__main__":
    main()
