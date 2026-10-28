"""E015: device-noise simulation of the headline QRC (E003 cfg15) with stochastic Pauli trajectories.

  python -I -m qhc.p4.noise rates                         calibration medians -> runs/E015/rates.json
  python -I -m qhc.p4.noise check --n 4000                mechanism checks (i) and (ii)
  python -I -m qhc.p4.noise run --device rigetti [--splits ds2s] [--seeds 0 1 2 3 4]
                                                          lambda from seed-0 DS1 OOF, 5-seed DS1 OOF, ds2s predictions
  python -I -m qhc.p4.noise leakcheck --device rigetti --seed 0
  python -I -m qhc.p4.noise transfer --device rigetti --seed 0   readout trained noiseless, applied to noisy features
  python -I -m qhc.p4.noise report                        DS1 OOF tables vs E003 / E005

Noise model (declared on the E015 card):
  * depolarising error after every RY and every RX (one per gate): with probability q1 = 1.5 r1 a uniformly random
    non-identity Pauli on that qubit (r = average gate infidelity, q = r (d + 1) / d, d = 2);
  * each ZZ(theta) edge gate compiles to 2 native two-qubit gates (CZ); two 2q-depolarising events per edge per ZZ
    layer, each with probability q2 = 1.25 r2 of a uniformly random non-identity two-qubit Pauli on the edge (d = 4).
    The compiling single-qubit gates are ignored. The depolarising channel is unitarily covariant on its own pair, so
    both events can sit after the edge gate. Schedule: the ring's edges run in two parallel layers (even-index edges,
    then odd-index edges of reservoirs._edges); an even-layer error is applied after the full ZZ phase conjugated by
    the odd layer (U_odd E U_odd^dagger), which is exact for that schedule;
  * per-qubit readout assignment error on every sampled bit (P(0->1) = e01, P(1->0) = e10).
  1,024 shots per circuit per beat = T trajectories x (1024 / T) shots. Snapshot k is read from the trajectory's state
  after step k (one noise history per trajectory across the 4 snapshots; on hardware each snapshot is its own circuit,
  so marginal per-snapshot statistics agree but cross-snapshot noise correlations differ).
  Randomness per beat from Philox streams keyed by (beat_key, shot_seed): the shot uniforms are exactly the ones
  reservoirs.QRC uses; gate errors use key (beat_key, shot_seed + 2^32), readout flips (beat_key, shot_seed + 2^33).
  With all rates 0 and T = 1 the features equal reservoirs.QRC's finite-shot features exactly.
  Not modelled: idle T1/T2 decay, crosstalk, leakage, routing (a 10-qubit ring is assumed embeddable).
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd
import torch

from .. import evalspec as E
from ..evaluate import ROOT
from ..scorer import f1_from_confusion
from ..units import sha256
from ..pipe import run as R
from ..pipe.features import load_split
from ..pipe.readout import LAMBDAS, Readout, cv_oof, oof_scores
from ..pipe.reservoirs import N_QUBITS, N_STEPS, QRC, _edges, _uniforms, _z_table
from . import code_revision

OUT = os.path.join(ROOT, "runs", "E015")
EXP_CFG = os.path.join(ROOT, "runs", "E003", "selected_config.json")
DEVICES = {"rigetti": ("calibration_rigetti.json", "Rigetti Cepheus-1-108Q"),
           "iqm": ("calibration_iqm_garnet.json", "IQM Garnet")}
T_DEFAULT = 32
SHOTS = 1024
GATE_TAG, RO_TAG = 1 << 32, 2 << 32


# ---------------------------------------------------------------- calibration
def rates_from_calibration(device):
    """Median error rates from the standardized device properties of a saved Braket GetDevice response."""
    fn, name = DEVICES[device]
    with open(os.path.join(OUT, fn)) as f:
        raw = json.load(f)
    caps = json.loads(raw["deviceCapabilities"])
    sp = caps["standardized"]
    one, two = {}, {}
    for q, p in sp["oneQubitProperties"].items():
        for x in p.get("oneQubitFidelity", []):
            one.setdefault(x["fidelityType"]["name"], []).append(float(x["fidelity"]))
    for e, p in sp["twoQubitProperties"].items():
        for x in p.get("twoQubitGateFidelity", []):
            two.setdefault(f'{x["gateName"]}/{x["fidelityType"]["name"]}', []).append(float(x["fidelity"]))
    med = lambda v: float(np.median(v))
    fields = {}
    r1_key = "SIMULTANEOUS_RANDOMIZED_BENCHMARKING"  # gates run in parallel in the reservoir; present on both devices
    r1 = 1 - med(one[r1_key])
    fields["r1"] = f"1 - median over qubits of standardized.oneQubitProperties[*].oneQubitFidelity[{r1_key}] " \
                   f"(n = {len(one[r1_key])})"
    cz = [k for k in two if k.startswith("CZ/")]
    r2 = 1 - med(two[cz[0]])
    fields["r2"] = f"1 - median over edges of standardized.twoQubitProperties[*].twoQubitGateFidelity[{cz[0]}] " \
                   f"(n = {len(two[cz[0]])}); gate CZ"
    if "READOUT_ERROR_0_TO_1" in one:
        e01, e10 = med(one["READOUT_ERROR_0_TO_1"]), med(one["READOUT_ERROR_1_TO_0"])
        fields["readout"] = "median over qubits of oneQubitFidelity[READOUT_ERROR_0_TO_1] and [READOUT_ERROR_1_TO_0] " \
                            "(these entries hold error probabilities; asymmetric)"
    else:
        e01 = e10 = 1 - med(one["READOUT"])
        fields["readout"] = f"1 - median over qubits of oneQubitFidelity[READOUT] (n = {len(one['READOUT'])}); " \
                            "symmetric (no asymmetric fields published)"
    other = {k: {"n": len(v), "median": med(v), "min": min(v), "max": max(v)} for k, v in {**one, **two}.items()}
    return {"device": device, "device_name": name, "device_arn": raw.get("deviceArn"),
            "fetched_utc": raw["_fetched_utc"], "region": raw["_region"], "source": f"runs/E015/{fn}",
            "r1": r1, "r2": r2, "two_qubit_gate": "CZ", "e01": e01, "e10": e10,
            "q1": 1.5 * r1, "q2": 1.25 * r2, "fields": fields, "all_medians": other}


def load_rates(device):
    with open(os.path.join(OUT, "rates.json")) as f:
        return json.load(f)[device]


# ---------------------------------------------------------------- simulator
def _philox(keys, seed, n):
    out = np.empty((len(keys), n), dtype=np.float32)
    for i, k in enumerate(keys):
        out[i] = np.random.Generator(np.random.Philox(key=[int(k), int(seed)])).random(n, dtype=np.float32)
    return out


class NoisyQRC(QRC):
    def __init__(self, *args, q1=0.0, q2=0.0, e01=0.0, e10=0.0, traj=T_DEFAULT, **kw):
        super().__init__(*args, **kw)
        assert self.shots is not None and self.shots % traj == 0
        self.q1, self.q2, self.e01, self.e10, self.T = float(q1), float(q2), float(e01), float(e10), int(traj)
        self.S = self.shots // self.T
        edges = _edges(self.cfg["topology"])
        self.layer_a = [(i, e) for i, e in enumerate(edges) if i % 2 == 0]
        self.layer_b = [(i, e) for i, e in enumerate(edges) if i % 2 == 1]
        for lay in (self.layer_a, self.layer_b):
            qs = [q for _, e in lay for q in e]
            assert len(qs) == len(set(qs)), "edges of a layer must be disjoint"
        ztab = _z_table(N_QUBITS).astype(np.float64)
        eb = sum(self.couplings[i] * ztab[:, q] * ztab[:, r] for i, (q, r) in self.layer_b)
        self.phase_b = torch.tensor(np.exp(-1j * eb), dtype=torch.complex64, device=self.device)
        idx = torch.arange(2 ** N_QUBITS, device=self.device)
        self.bit = torch.stack([((idx >> q) & 1).bool() for q in range(N_QUBITS)])  # (n_qubits, 2^n)
        self.qs = torch.arange(N_QUBITS, device=self.device)
        self.n_edges = len(edges)
        self.n_loc = N_QUBITS + self.cfg["depth"] * (2 * self.n_edges + N_QUBITS)

    def noise_meta(self):
        return {"q1": self.q1, "q2": self.q2, "e01": self.e01, "e10": self.e10, "trajectories": self.T,
                "shots_per_trajectory": self.S}

    # Pauli X^x Z^z on qubit q for the rows of sub (global phases dropped: Y = i X Z)
    def _pauli(self, sub, q, x, z):
        m = sub.shape[0]
        flipped = sub.view(m, 2 ** (N_QUBITS - 1 - q), 2, 2 ** q).flip(2).reshape(m, -1)
        sub = torch.where(x.view(m, 1), flipped, sub)
        sign = torch.where(z.view(m, 1) & self.bit[q].view(1, -1), -1.0, 1.0)
        return sub * sign

    @staticmethod
    def _xz(code):
        return (code == 1) | (code == 2), (code == 2) | (code == 3)

    def _err1(self, psi, u, q):
        rows = torch.nonzero(u < self.q1).squeeze(1)
        if rows.numel() == 0:
            return psi
        code = (torch.floor(u[rows] / self.q1 * 3).clamp(max=2) + 1).long()
        x, z = self._xz(code)
        psi[rows] = self._pauli(psi[rows], q, x, z)
        return psi

    def _err2(self, psi, u, a, b, conj=None):
        rows = torch.nonzero(u < self.q2).squeeze(1)
        if rows.numel() == 0:
            return psi
        code = (torch.floor(u[rows] / self.q2 * 15).clamp(max=14) + 1).long()
        xa, za = self._xz(code % 4)
        xb, zb = self._xz(code // 4)
        sub = psi[rows]
        if conj is not None:
            sub = sub * conj.conj()
        sub = self._pauli(self._pauli(sub, a, xa, za), b, xb, zb)
        if conj is not None:
            sub = sub * conj
        psi[rows] = sub
        return psi

    def _sample(self, psi, unif_k, ro_k):
        """psi (n T, 2^n); unif_k (n, shots); ro_k (n, shots, n_qubits) or None -> (n, 55) feature block."""
        n = unif_k.shape[0]
        p = psi.real ** 2 + psi.imag ** 2
        cdf = torch.cumsum(p.double(), 1)
        u = unif_k.reshape(n * self.T, self.S)
        idx = torch.searchsorted(cdf, u.double() * cdf[:, -1:]).clamp(max=p.shape[1] - 1)
        if ro_k is not None:
            bits = (idx.unsqueeze(-1) >> self.qs) & 1
            thr = torch.where(bits == 1, self.e10, self.e01)
            flip = (ro_k.reshape(n * self.T, self.S, N_QUBITS) < thr).long()
            idx = idx ^ (flip << self.qs).sum(-1)
        idx = idx.reshape(n, self.shots)
        counts = torch.zeros(n, p.shape[1], dtype=p.dtype, device=p.device)
        counts.scatter_add_(1, idx, torch.ones_like(idx, dtype=p.dtype))
        return (counts / self.shots) @ self.obs

    @torch.no_grad()
    def features(self, win, keys=None, batch=2048):
        from ..pipe.reservoirs import _chunks
        u_all = _chunks(win)
        if keys is None:
            raise ValueError("finite-shot readout needs one beat key per row")
        noisy_gates = self.q1 > 0 or self.q2 > 0
        noisy_ro = self.e01 > 0 or self.e10 > 0
        T, depth, nq, ne = self.T, self.cfg["depth"], N_QUBITS, self.n_edges
        out = []
        for b0 in range(0, len(u_all), batch):
            kb = keys[b0:b0 + batch]
            u = torch.tensor(u_all[b0:b0 + batch], device=self.device)
            n = u.shape[0]
            unif = torch.tensor(_uniforms(kb, self.shot_seed, N_STEPS * self.shots),
                                device=self.device).view(n, N_STEPS, self.shots)
            ug = ro = None
            if noisy_gates:
                ug = torch.tensor(_philox(kb, self.shot_seed + GATE_TAG, T * N_STEPS * self.n_loc),
                                  device=self.device).view(n * T, N_STEPS, self.n_loc)
            if noisy_ro:
                ro = torch.tensor(_philox(kb, self.shot_seed + RO_TAG, N_STEPS * self.shots * nq),
                                  device=self.device).view(n, N_STEPS, self.shots, nq)
            ur = u.repeat_interleave(T, 0) if T > 1 else u
            psi = torch.zeros(n * T, 2 ** nq, dtype=torch.complex64, device=self.device)
            psi[:, 0] = 1
            feats = []
            for k in range(N_STEPS):
                for q in range(nq):
                    psi = self._ry(psi, q, self.cfg["in_scale"] * ur[:, k, q])
                if noisy_gates:
                    for q in range(nq):
                        psi = self._err1(psi, ug[:, k, q], q)
                for d in range(depth):
                    psi = psi * self.zz_phase
                    if noisy_gates:
                        base = nq + d * (2 * ne + nq)
                        for j, (_, (a, b)) in enumerate(self.layer_a):  # before layer b: conjugate by U_b
                            for r in range(2):
                                psi = self._err2(psi, ug[:, k, base + 2 * j + r], a, b, conj=self.phase_b)
                        off = base + 2 * len(self.layer_a)
                        for j, (_, (a, b)) in enumerate(self.layer_b):
                            for r in range(2):
                                psi = self._err2(psi, ug[:, k, off + 2 * j + r], a, b)
                    psi = self._rx_all(psi)
                    if noisy_gates:
                        base = nq + d * (2 * ne + nq) + 2 * ne
                        for q in range(nq):
                            psi = self._err1(psi, ug[:, k, base + q], q)
                feats.append(self._sample(psi, unif[:, k], None if ro is None else ro[:, k]))
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out).astype(np.float32)


def headline_cfg():
    with open(EXP_CFG) as f:
        return json.load(f)


def build(device, seed, traj=T_DEFAULT, rates=None):
    best = headline_cfg()
    r = load_rates(device) if rates is None else rates
    return NoisyQRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed, q1=r["q1"], q2=r["q2"],
                    e01=r["e01"], e10=r["e10"], traj=traj)


# ---------------------------------------------------------------- commands
def cmd_rates(a):
    os.makedirs(OUT, exist_ok=True)
    rates = {dev: rates_from_calibration(dev) for dev in DEVICES}
    with open(os.path.join(OUT, "rates.json"), "w") as f:
        json.dump(rates, f, indent=1)
    for dev, r in rates.items():
        print(dev, {k: r[k] for k in ("r1", "r2", "e01", "e10", "q1", "q2", "fetched_utc")})


def _blocks(F):
    """mean |<Z_q>| and mean |<Z_q Z_r>| per snapshot of a (n, 220) reservoir feature block."""
    out = {}
    for k in range(N_STEPS):
        s = F[:, 55 * k:55 * (k + 1)]
        out[k] = (float(np.abs(s[:, :N_QUBITS]).mean()), float(np.abs(s[:, N_QUBITS:]).mean()))
    return out


def cmd_check(a):
    best = headline_cfg()
    d, y, folds = R.ds1_data()
    rng = np.random.default_rng(20261028)
    sel = np.sort(rng.choice(len(d["beat_id"]), a.n, replace=False))
    keys = R.keys_of(d)[sel]
    win = d[R.INPUT][sel]
    rep = {"n_beats": int(a.n), "selection": "default_rng(20261028).choice(DS1 beats, n, replace=False), sorted",
           "code_revision": code_revision("noise")}
    for seed in a.seeds:
        t = time.time()
        ref = QRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed).features(win, keys)
        zero = NoisyQRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed, traj=1).features(win, keys)
        zero_b = NoisyQRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed, traj=1).features(
            win, keys, batch=333)
        rep[f"check_i_seed{seed}"] = {"exact_equal": bool(np.array_equal(ref, zero)),
                                      "max_abs_diff": float(np.abs(ref - zero).max()),
                                      "batch_invariant_equal": bool(np.array_equal(zero, zero_b)),
                                      "seconds": round(time.time() - t, 1)}
        print("check (i)", seed, rep[f"check_i_seed{seed}"], flush=True)
    seed = a.seeds[0]
    exact = QRC(**best["config"], seed=seed, shots=None).features(win)
    ref = QRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed).features(win, keys)
    base = {"exact": _blocks(exact), "noiseless_1024": _blocks(ref)}
    for dev in DEVICES:
        t = time.time()
        m = build(dev, seed)
        F = m.features(win, keys)
        F_b = m.features(win, keys, batch=500)
        nb = _blocks(F)
        r = load_rates(dev)
        # noiseless-only-readout and gates-only decompositions
        Fg = NoisyQRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed, q1=r["q1"], q2=r["q2"],
                      traj=T_DEFAULT).features(win, keys)
        rep[f"check_ii_{dev}"] = {
            "noisy": nb, "gates_only": _blocks(Fg),
            "shrink_Z_vs_noiseless_1024": {k: nb[k][0] / base["noiseless_1024"][k][0] for k in nb},
            "shrink_ZZ_vs_noiseless_1024": {k: nb[k][1] / base["noiseless_1024"][k][1] for k in nb},
            "shrink_Z_vs_exact": {k: nb[k][0] / base["exact"][k][0] for k in nb},
            "shrink_ZZ_vs_exact": {k: nb[k][1] / base["exact"][k][1] for k in nb},
            "batch_invariant_equal": bool(np.array_equal(F, F_b)), "seconds": round(time.time() - t, 1)}
        print("check (ii)", dev, json.dumps(rep[f"check_ii_{dev}"]), flush=True)
    rep["reference_blocks"] = base
    with open(os.path.join(OUT, "mechanism_checks.json"), "w") as f:
        json.dump(rep, f, indent=1)


def _scores(y, p):
    units = y >= 0
    cm = np.zeros((len(E.CLASSES),) * 2, dtype=np.int64)
    np.add.at(cm, (y[units], p[units].argmax(1)), 1)
    f1 = f1_from_confusion(cm)
    return {"macro_f1": float(f1.mean()), "f1": {c: float(v) for c, v in zip(E.CLASSES, f1)}}


def save_model(path, device, model, ro, rates, seed):
    best = headline_cfg()
    meta = {"arm": "qrc_noise", "device": device, "config": best["config"], "config_index": best["index"],
            "seed": seed, "shot_seed": 1000 + seed, "shots": SHOTS, "input": R.INPUT, "noise": model.noise_meta(),
            "rates": {k: rates[k] for k in ("r1", "r2", "e01", "e10", "q1", "q2", "two_qubit_gate", "fetched_utc",
                                            "source", "device_name", "fields")},
            "code_revision": code_revision("noise")}
    st = ro.state()
    np.savez(path, meta=json.dumps(meta), lam=st["lam"], mu=st["mu"], sd=st["sd"], W_readout=st["W"],
             b_readout=st["b"], res_couplings=model.couplings)


def load_model(path):
    z = np.load(path)
    meta = json.loads(str(z["meta"]))
    ro = Readout(float(z["lam"]))
    ro.mu, ro.sd, ro.W, ro.b = z["mu"], z["sd"], z["W_readout"], z["b_readout"]
    r = meta["rates"]
    model = NoisyQRC(**meta["config"], seed=meta["seed"], shots=meta["shots"], shot_seed=meta["shot_seed"],
                     q1=r["q1"], q2=r["q2"], e01=r["e01"], e10=r["e10"], traj=meta["noise"]["trajectories"])
    assert np.allclose(model.couplings, z["res_couplings"])
    return meta, model, ro


def cmd_run(a):
    out = os.path.join(OUT, a.device)
    os.makedirs(out, exist_ok=True)
    rates = load_rates(a.device)
    rev = code_revision("noise")
    d, y, folds = R.ds1_data()
    keys, units = R.keys_of(d), y >= 0
    targets = {s: load_split(s) for s in a.splits}
    log_path = os.path.join(out, "oof_scores.json")
    log = {"device": a.device, "code_revision": rev, "trajectories": a.traj, "rates": rates, "seeds": {}}
    lam = None
    for seed in a.seeds:
        t = time.time()
        model = build(a.device, seed, a.traj, rates)
        X = R.design(model.features(d[R.INPUT], keys), d)
        tf = round(time.time() - t, 1)
        if seed == a.seeds[0] and seed == 0:
            np.save(os.path.join(out, "feats_ds1_seed0.npy"), X)
        if lam is None:
            oof = cv_oof(X, y, d["record"], folds, LAMBDAS)
            sc = oof_scores(oof, y)
            lam = max(LAMBDAS, key=lambda v: sc[v])  # first maximum in grid order
            log["lambda_grid_seed0"] = {str(k): v for k, v in sc.items()}
            log["lam"] = lam
            p = oof[lam]
        else:
            p = cv_oof(X, y, d["record"], folds, (lam,))[lam]
        R.write_pred(os.path.join(out, f"oof_ds1_seed{seed}.csv"), d["beat_id"], p)
        log["seeds"][str(seed)] = {**_scores(y, p), "feature_seconds_ds1": tf}
        ro = Readout(lam).fit(X[units], y[units])
        art = os.path.join(out, f"model_seed{seed}.npz")
        save_model(art, a.device, model, ro, rates, seed)
        for s, ds in targets.items():
            t2 = time.time()
            f = os.path.join(out, f"pred_{s}_seed{seed}.csv")
            R.write_pred(f, ds["beat_id"], ro.predict_proba(R.design(model.features(ds[R.INPUT], R.keys_of(ds)), ds)))
            man = {"arm_id": f"E015-qrc_noise_{a.device}", "seed": seed, "split": s,
                   "config_id": f"E015-qrc-cfg15-{a.device}", "code_revision": rev,
                   "model_artifact": os.path.relpath(art, ROOT).replace(os.sep, "/"),
                   "model_artifact_sha256": sha256(art), "reservoir_seed": seed, "shot_seed": 1000 + seed,
                   "prediction_sha256": sha256(f), "config": headline_cfg()["config"], "lam": lam,
                   "noise": model.noise_meta(),
                   "rates": {k: rates[k] for k in ("r1", "r2", "e01", "e10", "q1", "q2", "two_qubit_gate",
                                                   "fetched_utc", "source")}}
            with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
                json.dump(man, fh, indent=1)
            log["seeds"][str(seed)][f"{s}_seconds"] = round(time.time() - t2, 1)
        log["seeds"][str(seed)]["total_seconds"] = round(time.time() - t, 1)
        with open(log_path, "w") as fh:
            json.dump(log, fh, indent=1)
        print(f"E015 {a.device} seed {seed}: lam {lam} OOF {log['seeds'][str(seed)]['macro_f1']:.4f} "
              f"{log['seeds'][str(seed)]['f1']} {round(time.time() - t, 1)}s", flush=True)
    f1s = [v["macro_f1"] for v in log["seeds"].values()]
    log["mean_macro_f1"] = float(np.mean(f1s))
    with open(log_path, "w") as fh:
        json.dump(log, fh, indent=1)
    print("mean", log["mean_macro_f1"])


def cmd_leakcheck(a):
    from ..evaluate import load_positions
    from ..leakcheck import check_lookahead
    from ..pipe.features import load_signal
    meta, model, ro = load_model(os.path.join(OUT, a.device, f"model_seed{a.seed}.npz"))
    pos = load_positions("ds1")
    report = {"exp": "E015", "device": a.device, "seed": a.seed, "arm": meta["arm"],
              "code_revision": code_revision("noise"), "records": {}}
    for rec in R.LEAK_RECORDS:
        g = pos[pos["record"] == rec].sort_values("sample")
        sig, fs, _ = load_signal("mitdb", rec)
        s = g["sample"].to_numpy()
        s = s[s < R.LEAK_SECONDS * fs]
        sig = sig[:int((R.LEAK_SECONDS + 10) * fs)]
        idx = range(1, len(s) - 1)
        bad = check_lookahead(R.pipeline_fn(meta, model, ro, "mitdb", rec), sig, s, fs, idx)
        report["records"][rec] = {"beats_checked": len(idx), "violations": bad}
        print(rec, len(idx), len(bad), flush=True)
    report["beats_checked"] = sum(r["beats_checked"] for r in report["records"].values())
    report["passed"] = all(not r["violations"] for r in report["records"].values())
    with open(os.path.join(OUT, a.device, f"leakcheck_seed{a.seed}.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}))


def cmd_transfer(a):
    """Hardware-run setting: readout (lambda of the headline, 0.1) trained on noiseless 1,024-shot features in each
    training fold, applied to the noisy features of the held-out fold."""
    best = headline_cfg()
    d, y, folds = R.ds1_data()
    keys = R.keys_of(d)
    seed = a.seed
    Xc = R.design(QRC(**best["config"], seed=seed, shots=SHOTS, shot_seed=1000 + seed).features(d[R.INPUT], keys), d)
    fp = os.path.join(OUT, a.device, f"feats_ds1_seed{seed}.npy")
    Xn = np.load(fp) if os.path.exists(fp) else R.design(build(a.device, seed).features(d[R.INPUT], keys), d)
    res = {"device": a.device, "seed": seed, "code_revision": code_revision("noise")}
    for lam in (best["lam"],):
        p_n = np.zeros((len(Xn), len(E.CLASSES)), dtype=np.float32)
        p_c = np.zeros_like(p_n)
        for recs in folds.values():
            test = np.isin(d["record"], recs)
            train = ~test & (y >= 0)
            ro = Readout(lam).fit(Xc[train], y[train])
            p_n[test] = ro.predict_proba(Xn[test])
            p_c[test] = ro.predict_proba(Xc[test])
        res[str(lam)] = {"noiseless_train_noisy_test": _scores(y, p_n), "noiseless_train_noiseless_test": _scores(y, p_c)}
        R.write_pred(os.path.join(OUT, a.device, f"transfer_oof_ds1_seed{seed}.csv"), d["beat_id"], p_n)
    with open(os.path.join(OUT, a.device, f"transfer_seed{seed}.json"), "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res))


def cmd_report(a):
    d, y, _ = R.ds1_data()
    rep = {}
    for name, pat in [("E003", "runs/E003/oof_ds1_seed{}.csv"), ("E005", "runs/E005/oof_ds1_seed{}.csv"),
                      ("E015-rigetti", "runs/E015/rigetti/oof_ds1_seed{}.csv"),
                      ("E015-iqm", "runs/E015/iqm/oof_ds1_seed{}.csv")]:
        rows = {}
        for s in range(E.N_SEEDS):
            p = os.path.join(ROOT, pat.format(s))
            if not os.path.exists(p):
                continue
            df = pd.read_csv(p).set_index("beat_id").loc[d["beat_id"]]
            rows[s] = _scores(y, df[[f"prob_{c}" for c in E.CLASSES]].to_numpy())
        if rows:
            rep[name] = {"seeds": rows, "mean_macro_f1": float(np.mean([v["macro_f1"] for v in rows.values()])),
                         "mean_f1": {c: float(np.mean([v["f1"][c] for v in rows.values()])) for c in E.CLASSES}}
    for name in ("E015-rigetti", "E015-iqm", "E005"):
        if name in rep and "E003" in rep:
            common = sorted(set(rep[name]["seeds"]) & set(rep["E003"]["seeds"]))
            dl = [rep[name]["seeds"][s]["macro_f1"] - rep["E003"]["seeds"][s]["macro_f1"] for s in common]
            rep[name]["paired_delta_vs_E003"] = {"per_seed": dl, "mean": float(np.mean(dl))}
    with open(os.path.join(OUT, "ds1_oof_report.json"), "w") as f:
        json.dump(rep, f, indent=1)
    for k, v in rep.items():
        print(k, round(v["mean_macro_f1"], 4), {c: round(x, 4) for c, x in v["mean_f1"].items()},
              v.get("paired_delta_vs_E003", {}).get("mean"))


def main(argv=None):
    ap = argparse.ArgumentParser(description="E015 device-noise simulation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("rates").set_defaults(fn=cmd_rates)
    c = sub.add_parser("check")
    c.add_argument("--n", type=int, default=4000)
    c.add_argument("--seeds", type=int, nargs="+", default=[0, 1])
    c.set_defaults(fn=cmd_check)
    r = sub.add_parser("run")
    r.add_argument("--device", required=True, choices=sorted(DEVICES))
    r.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    r.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    r.add_argument("--traj", type=int, default=T_DEFAULT)
    r.set_defaults(fn=cmd_run)
    lk = sub.add_parser("leakcheck")
    lk.add_argument("--device", required=True, choices=sorted(DEVICES))
    lk.add_argument("--seed", type=int, default=0)
    lk.set_defaults(fn=cmd_leakcheck)
    t = sub.add_parser("transfer")
    t.add_argument("--device", required=True, choices=sorted(DEVICES))
    t.add_argument("--seed", type=int, default=0)
    t.set_defaults(fn=cmd_transfer)
    sub.add_parser("report").set_defaults(fn=cmd_report)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
