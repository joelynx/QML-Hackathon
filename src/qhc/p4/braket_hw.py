"""E019 (I006): real-hardware diagnostic of E003's seed-0 QRC circuit on Amazon Braket -- main-venv part.

Builds everything that does not need the Braket SDK: the label-free beat draw, the ring packing on the device
connectivity, native OpenQASM 3 programs on physical qubits (verbatim boxes), the submission plan with its cost, the
exact/finite-shot reference features, and the analysis of hardware counts. Submission and the local-simulator check
run in the separate SDK venv (`scripts/braket_submit.py`, `.venv-braket`). No labels are read anywhere.

Circuit (reservoirs.QRC): 10 qubits on a ring, per step k: RY(in_scale u_{k,q}) on every qubit, then `depth` times
[exp(-i sum_e c_e Z_a Z_b), RX(h) on every qubit]. Snapshot k = Z-basis measurement after step k (one circuit each).
Logical qubit q sits on position q of a physical 10-cycle; ring edge e = (q, q+1 mod 10) uses coupling c_e.

Compilation: the circuit is a list of 1q unitaries and ZZ blocks; ZZ(theta = 2 c) = [RY(pi/2) on b, CZ, RX(theta) on b,
CZ, RY(-pi/2) on b]; consecutive 1q unitaries on a qubit are fused, Z rotations are tracked virtually (they commute with
CZ and with the final Z measurement) and dropped at the end. Each fused block U = RZ(a) RY(b) RZ(g):
  rigetti: rz(g) rx(pi/2) rz(b) rx(-pi/2)   (pending Z phase a)   -- only rx(+-pi/2), rz, cz
  iqm:     prx(b, pi/2 - g)                  (pending Z phase a+g) -- only prx, cz
Usage (main venv):  python -m qhc.p4.braket_hw prepare | plan --device rigetti --beats 24 | reference | analyse
"""
import argparse
import datetime
import hashlib
import json
import math
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "runs", "E019")
E003 = os.path.join(ROOT, "runs", "E003")
N, STEPS = 10, 4
DRAW_SEED = 20261026
SHOTS = 1024
CLASSES = ("N", "S", "V")
EDGE_ORDER = (0, 2, 4, 6, 8, 1, 3, 5, 7, 9)

# Pricing verified on https://aws.amazon.com/braket/pricing/ at 2026-10-28T14:45Z (18:45 UAE); unchanged from 10-26.
DEVICES = {
    "rigetti": dict(arn="arn:aws:braket:us-west-1::device/qpu/rigetti/Cepheus-1-108Q", region="us-west-1",
                    task_usd=0.30, shot_usd=0.000425, file="get_device_rigetti_cepheus.json"),
    "iqm": dict(arn="arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet", region="eu-north-1",
                task_usd=0.30, shot_usd=0.00145, file="get_device_iqm_garnet.json"),
}
HARD_USD_CAP = 35.0


def task_cost(dev, shots=SHOTS):
    d = DEVICES[dev]
    return d["task_usd"] + shots * d["shot_usd"]


# ----------------------------------------------------------------------------------------------- circuit parameters
def e003_config():
    cfg = json.load(open(os.path.join(E003, "selected_config.json")))["config"]
    z = np.load(os.path.join(E003, "model_seed0.npz"))
    return cfg, np.asarray(z["res_couplings"], dtype=float)


def beat_inputs(beat_ids):
    from qhc.pipe import features
    d = features.load_split("ds2s")
    idx = {b: i for i, b in enumerate(d["beat_id"])}
    rows = [idx[b] for b in beat_ids]
    return d, rows


# ------------------------------------------------------------------------------------------------------- beat draw
def draw_beats():
    """Label-free: stratified by the seed-0 E003 *predicted* class; nested 24 < 48 < 96 (first n/3 of each class)."""
    import csv
    ids = {c: [] for c in CLASSES}
    with open(os.path.join(E003, "pred_ds2s_seed0.csv")) as f:
        for r in csv.DictReader(f):
            ids[r["pred"]].append(r["beat_id"])
    rng = np.random.default_rng(DRAW_SEED)
    perm = {c: [ids[c][i] for i in rng.permutation(len(ids[c]))[:32]] for c in CLASSES}
    order = [perm[c][i] for i in range(32) for c in CLASSES]  # interleaved: any prefix of 3m is class-balanced
    out = dict(seed=DRAW_SEED, source="runs/E003/pred_ds2s_seed0.csv (column pred; no labels read)",
               stratified_by="seed-0 E003 predicted class", class_pool_sizes={c: len(ids[c]) for c in CLASSES},
               order=order, options={str(n): order[:n] for n in (24, 48, 96)},
               drawn_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
    json.dump(out, open(os.path.join(OUT, "beats.json"), "w"), indent=1)
    return out


# ----------------------------------------------------------------------------------------------------- ring packing
def device_graph(dev):
    caps = json.load(open(os.path.join(OUT, DEVICES[dev]["file"])))["deviceCapabilities_parsed"]
    std = caps["standardized"]
    f2 = {}
    for k, v in std["twoQubitProperties"].items():
        a, b = (int(x) for x in k.split("-"))
        fz = [g["fidelity"] for g in v["twoQubitGateFidelity"] if g["gateName"].upper() == "CZ"]
        if fz:
            f2[frozenset((a, b))] = float(fz[0])
    fro, f1 = {}, {}
    for k, v in std["oneQubitProperties"].items():
        for g in v["oneQubitFidelity"]:
            if g["fidelityType"]["name"] == "READOUT":
                fro[int(k)] = float(g["fidelity"])
            if "RANDOMIZED_BENCHMARKING" in g["fidelityType"]["name"] and int(k) not in f1:
                f1[int(k)] = float(g["fidelity"])
    graph = {int(a): [int(b) for b in bs] for a, bs in caps["paradigm"]["connectivity"]["connectivityGraph"].items()}
    return graph, f2, fro, f1


def ten_cycles(adj):
    """All simple 10-cycles (as node tuples starting at their smallest node, one direction)."""
    cyc = set()
    for s in sorted(adj):
        stack = [(s, (s,))]
        while stack:
            v, path = stack.pop()
            if len(path) == N:
                if s in adj[v] and path[1] < path[-1]:
                    cyc.add(path)
                continue
            for w in adj[v]:
                if w > s and w not in path:
                    stack.append((w, path + (w,)))
    return sorted(cyc)


def pack_rings(dev, min_f2=0.97, min_ro=0.90, restarts=200):
    graph, f2, fro, f1 = device_graph(dev)
    good = lambda a, b: f2.get(frozenset((a, b)), 0) >= min_f2
    adj = {a: [b for b in bs if good(a, b) and fro.get(b, 0) >= min_ro] for a, bs in graph.items() if fro.get(a, 0) >= min_ro}
    cycles = ten_cycles(adj)
    # error score per beat at snapshot 4: each ring edge carries 16 CZ, each qubit one readout
    def cost(c):
        return sum(-16 * math.log(f2[frozenset((c[i], c[(i + 1) % N]))]) for i in range(N)) + \
               sum(-math.log(fro[q]) for q in c)
    sc = {c: cost(c) for c in cycles}
    best = []
    rng = np.random.default_rng(0)
    order0 = sorted(cycles, key=sc.get)
    for r in range(restarts):
        order = order0 if r == 0 else [order0[i] for i in np.argsort(np.array([sc[c] for c in order0]) *
                                                                   rng.uniform(1, 1.6, len(order0)))]
        used, pick = set(), []
        for c in order:
            if not used.intersection(c):
                pick.append(c)
                used.update(c)
        key = (len(pick), -sum(sc[c] for c in pick))
        if not best or key > best[0]:
            best = [key, pick]
    rings = sorted(best[1], key=sc.get)
    info = []
    for c in rings:
        ef = [f2[frozenset((c[i], c[(i + 1) % N]))] for i in range(N)]
        info.append(dict(qubits=list(c), cz_fidelity=ef, readout=[fro[q] for q in c], score=sc[c],
                         fid_snap=[float(np.prod(np.array(ef) ** (4 * k))) for k in range(1, STEPS + 1)]))
    all_f2 = np.array(list(f2.values()))
    return dict(device=dev, n_cycles_found=len(cycles), P=len(rings), rings=info, min_f2=min_f2, min_ro=min_ro,
                median_cz_error_device=float(np.median(1 - all_f2)),
                median_cz_error_rings=float(np.median([1 - f for r in info for f in r["cz_fidelity"]])) if info else None,
                median_readout_rings=float(np.median([f for r in info for f in r["readout"]])) if info else None)


# ---------------------------------------------------------------------------------------------- native compilation
I2 = np.eye(2, dtype=complex)


def RX(t):
    return np.array([[math.cos(t / 2), -1j * math.sin(t / 2)], [-1j * math.sin(t / 2), math.cos(t / 2)]])


def RY(t):
    return np.array([[math.cos(t / 2), -math.sin(t / 2)], [math.sin(t / 2), math.cos(t / 2)]], dtype=complex)


def RZ(t):
    return np.diag([np.exp(-0.5j * t), np.exp(0.5j * t)])


def zyz(U):
    """U = e^{i phi} RZ(a) RY(b) RZ(g); returns (a, b, g)."""
    U = U / np.sqrt(np.linalg.det(U))
    b = 2 * math.atan2(abs(U[1, 0]), abs(U[0, 0]))
    if abs(U[0, 0]) < 1e-12:
        a, g = 2 * np.angle(U[1, 0]), 0.0
    elif abs(U[1, 0]) < 1e-12:
        a, g = -2 * np.angle(U[0, 0]), 0.0
    else:
        s, d = -np.angle(U[0, 0]), np.angle(U[1, 0])  # (a+g)/2, (a-g)/2
        a, g = s + d, s - d
    return float(a), float(b), float(g)


def logical_ops(cfg, coup, ang, k):
    """Gate list for snapshot k (1-based) of one beat: ('u', q, 2x2) and ('cz', a, b)."""
    ops = []
    for step in range(k):
        for q in range(N):
            ops.append(("u", q, RY(ang[step, q])))
        for _ in range(int(cfg["depth"])):
            for e in EDGE_ORDER:  # even edges, then odd edges: two parallel layers (the ZZ terms commute)
                a, b = e, (e + 1) % N
                ops += [("u", b, RY(math.pi / 2)), ("cz", a, b), ("u", b, RX(2 * coup[e])), ("cz", a, b),
                        ("u", b, RY(-math.pi / 2))]
            for q in range(N):
                ops.append(("u", q, RX(cfg["h"])))
    return ops


def compile_native(ops, phys, dev):
    """ops on logical qubits -> list of native gate strings on physical qubits (qubit q -> phys[q])."""
    pend_u = {q: I2.copy() for q in range(N)}  # fused 1q unitary not yet emitted
    zphase = {q: 0.0 for q in range(N)}  # virtual Z rotation applied *before* pend_u in time order (already emitted side)
    out = []
    fmt = lambda x: repr(float(x))

    def flush(q):
        U = pend_u[q] @ RZ(zphase[q])
        a, b, g = zyz(U)
        if abs(b) < 1e-12:
            zphase[q] = a + g
        elif dev == "rigetti":
            p = phys[q]
            if abs(g) > 1e-12:
                out.append(f"rz({fmt(g)}) ${p};")
            out.extend([f"rx({fmt(math.pi / 2)}) ${p};", f"rz({fmt(b)}) ${p};", f"rx({fmt(-math.pi / 2)}) ${p};"])
            zphase[q] = a
        else:
            out.append(f"prx({fmt(b)}, {fmt(math.pi / 2 - g)}) ${phys[q]};")
            zphase[q] = a + g
        pend_u[q] = I2.copy()

    for op in ops:
        if op[0] == "u":
            pend_u[op[1]] = op[2] @ pend_u[op[1]]
        else:
            flush(op[1]), flush(op[2])
            out.append(f"cz ${phys[op[1]]}, ${phys[op[2]]};")
    for q in range(N):
        flush(q)  # remaining Z phase is dropped (commutes with the Z measurement)
    return out


def program(blocks, dev):
    """blocks: list of (gate_lines, phys qubits). One verbatim box, then measure every ring qubit in ring order."""
    meas = [p for _, ph in blocks for p in ph]
    lines = ["OPENQASM 3.0;", f"bit[{len(meas)}] b;", "#pragma braket verbatim", "box{"]
    for gl, _ in blocks:
        lines += ["  " + g for g in gl]
    lines.append("}")
    lines += [f"b[{i}] = measure ${p};" for i, p in enumerate(meas)]
    return "\n".join(lines) + "\n"


def beat_angles(cfg, rel_row):
    return cfg["in_scale"] * np.asarray(rel_row, dtype=np.float32).reshape(STEPS, N).astype(np.float64)


def build_plan(dev, n_beats, packing=None, beats=None):
    cfg, coup = e003_config()
    beats = beats or json.load(open(os.path.join(OUT, "beats.json")))
    ids = beats["options"][str(n_beats)]
    d, rows = beat_inputs(ids)
    packing = packing or json.load(open(os.path.join(OUT, f"packing_{dev}.json")))
    rings = [r["qubits"] for r in packing["rings"]]
    P = len(rings)
    circuits = []
    for k in range(1, STEPS + 1):
        for c0 in range(0, len(ids), P):
            chunk = list(range(c0, min(c0 + P, len(ids))))
            blocks, slots = [], []
            for j, bi in enumerate(chunk):
                ang = beat_angles(cfg, d["rel"][rows[bi]])
                gl = compile_native(logical_ops(cfg, coup, ang, k), rings[j], dev)
                blocks.append((gl, rings[j]))
                slots.append(dict(beat_id=ids[bi], ring=j, phys=rings[j]))
            src = program(blocks, dev)
            cid = f"{dev}_b{n_beats}_k{k}_c{c0 // P:03d}"
            circuits.append(dict(circuit_id=cid, snapshot=k, slots=slots, qasm=src,
                                 n_cz=sum(g.startswith("cz") for bl in blocks for g in bl[0]),
                                 sha16=hashlib.sha256(src.encode()).hexdigest()[:16]))
    cost = len(circuits) * task_cost(dev)
    return dict(device=dev, arn=DEVICES[dev]["arn"], region=DEVICES[dev]["region"], n_beats=n_beats, P=P,
                shots=SHOTS, n_tasks=len(circuits), est_usd=round(cost, 4),
                price=dict(task_usd=DEVICES[dev]["task_usd"], shot_usd=DEVICES[dev]["shot_usd"],
                           source="https://aws.amazon.com/braket/pricing/", fetched_utc="2026-10-28T14:45Z"),
                circuits=circuits)


# ------------------------------------------------------------------------------------------ reference and analysis
def feats_from_probs(p):
    """p: (2^10,) probabilities with qubit q = bit q of the index -> 55 features (Z_q, then Z_q Z_r pairs)."""
    from qhc.pipe.reservoirs import _z_table
    return np.asarray(p, dtype=np.float64) @ _z_table(N).astype(np.float64)


def feats_from_counts(counts, measured, phys):
    """counts: {bitstring: n} where char i is measured[i]; returns 55 features of the ring `phys` (logical order)."""
    from qhc.pipe.reservoirs import PAIRS
    pos = [measured.index(p) for p in phys]
    tot, z = 0, np.zeros(N)
    zz = np.zeros(len(PAIRS))
    for s, n in counts.items():
        v = np.array([1.0 - 2.0 * int(s[i]) for i in pos])
        z += n * v
        zz += n * np.array([v[a] * v[b] for a, b in PAIRS])
        tot += n
    return np.concatenate([z, zz]) / tot


def reference(ids):
    """Exact (shots=None) and E003 finite-shot (1,024 shots, shot seed 1000) features and seed-0 readout predictions."""
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")
    from qhc.pipe import run as R
    from qhc.pipe.reservoirs import QRC, beat_key
    meta, model, ro = R.load_artifact(os.path.join(E003, "model_seed0.npz"))
    z = np.load(os.path.join(E003, "model_seed0.npz"))
    assert np.allclose(model.couplings, z["res_couplings"]), "regenerated couplings differ from the artifact"
    d, rows = beat_inputs(ids)
    win, rr = d["rel"][rows], d["rr"][rows]
    keys = np.array([beat_key(b) for b in ids], dtype=np.int64)
    exact = QRC(**model.cfg, seed=model.seed, shots=None, device="cpu").features(win)
    shot = model.features(win, keys)
    return dict(exact=exact, shot=shot, rr=rr, ro=ro, model=model)


def predict(ro, feats, rr):
    p = ro.predict_proba(np.c_[feats, rr])
    return np.array(CLASSES)[np.argmax(p, 1)], p


def analyse(results_dir=None, tag=""):
    results_dir = results_dir or os.path.join(OUT, "results")
    recs = [json.load(open(os.path.join(results_dir, f))) for f in sorted(os.listdir(results_dir))
            if f.endswith(".json") and not f.endswith(".task.json")]
    hw = {}
    for r in recs:
        for s in r["slots"]:
            hw.setdefault(s["beat_id"], {})[r["snapshot"]] = feats_from_counts(r["counts"], r["measured_qubits"], s["phys"])
    ids = sorted(b for b, v in hw.items() if len(v) == STEPS)
    if not ids:
        return dict(n_beats_complete=0)
    H = np.stack([np.concatenate([hw[b][k] for k in range(1, STEPS + 1)]) for b in ids])
    ref = reference(ids)
    out = dict(n_beats_complete=len(ids), devices=sorted({r["device"] for r in recs}), n_tasks=len(recs))
    for name in ("exact", "shot"):
        R_ = ref[name].astype(np.float64)
        corr = [float(np.corrcoef(H[:, j], R_[:, j])[0, 1]) if H[:, j].std() > 0 and R_[:, j].std() > 0 else float("nan")
                for j in range(H.shape[1])]
        mad = np.abs(H - R_).mean(0)
        out[f"vs_{name}"] = dict(
            mean_abs_diff=float(mad.mean()),
            mean_abs_diff_by_snapshot=[float(mad[55 * k:55 * (k + 1)].mean()) for k in range(STEPS)],
            mean_abs_diff_Z=float(np.mean([mad[55 * k:55 * k + 10].mean() for k in range(STEPS)])),
            mean_abs_diff_ZZ=float(np.mean([mad[55 * k + 10:55 * (k + 1)].mean() for k in range(STEPS)])),
            median_feature_corr=float(np.nanmedian(corr)),
            median_feature_corr_by_snapshot=[float(np.nanmedian(corr[55 * k:55 * (k + 1)])) for k in range(STEPS)],
            pooled_corr=float(np.corrcoef(H.ravel(), R_.ravel())[0, 1]),
            zz_shrink_slope=float(np.polyfit(R_[:, [55 * k + j for k in range(STEPS) for j in range(10, 55)]].ravel(),
                                             H[:, [55 * k + j for k in range(STEPS) for j in range(10, 55)]].ravel(), 1)[0]))
    ex_shot_mad = np.abs(ref["shot"] - ref["exact"]).mean()
    out["shot_vs_exact_mean_abs_diff"] = float(ex_shot_mad)
    ph, _ = predict(ref["ro"], H, ref["rr"])
    pe, _ = predict(ref["ro"], ref["exact"], ref["rr"])
    ps, _ = predict(ref["ro"], ref["shot"], ref["rr"])
    out["pred_agree_hw_vs_shot"] = float(np.mean(ph == ps))
    out["pred_agree_hw_vs_exact"] = float(np.mean(ph == pe))
    out["pred_agree_shot_vs_exact"] = float(np.mean(ps == pe))
    out["pred_counts"] = {n: {c: int(np.sum(p == c)) for c in CLASSES} for n, p in (("hw", ph), ("shot", ps), ("exact", pe))}
    np.savez(os.path.join(OUT, f"analysis_features{tag}.npz"), beat_id=np.array(ids), hw=H, exact=ref["exact"], shot=ref["shot"])
    json.dump(out, open(os.path.join(OUT, f"analysis{tag}.json"), "w"), indent=1)
    return out


def relabel(src, measured):
    """Map physical qubit ids to 0..n-1 in measurement order (for the local simulator only)."""
    import re
    m = {p: i for i, p in enumerate(measured)}
    return re.sub(r"\$(\d+)", lambda x: f"${m[int(x.group(1))]}", src)


def validate_prep(n_val=4):
    """Programs for the local-simulator check (relabelled to contiguous qubits) plus our exact features."""
    cfg, coup = e003_config()
    ids = json.load(open(os.path.join(OUT, "beats.json")))["order"][:n_val]
    ref = reference(ids)
    d, rows = beat_inputs(ids)
    items = []
    for dev in DEVICES:
        rings = [r["qubits"] for r in json.load(open(os.path.join(OUT, f"packing_{dev}.json")))["rings"]]
        for bi, b in enumerate(ids):
            ang = beat_angles(cfg, d["rel"][rows[bi]])
            for k in range(1, STEPS + 1):
                ring = rings[0]
                gl = compile_native(logical_ops(cfg, coup, ang, k), ring, dev)
                src = program([(gl, ring)], dev)
                items.append(dict(name=f"{dev}_single_{bi}_k{k}", device=dev, qasm=relabel(src, ring), n=N,
                                  slots=[dict(beat=bi, beat_id=b, pos=list(range(N)))], snapshot=k,
                                  n_cz=sum(g.startswith("cz") for g in gl), n_1q=sum(not g.startswith("cz") for g in gl),
                                  ref=[ref["exact"][bi, 55 * (k - 1):55 * k].tolist()]))
    # packed: rigetti rings 0 and 1 (and iqm needs P >= 2, so rigetti only), beats 0 and 1, snapshots 2 and 4
    rings = [r["qubits"] for r in json.load(open(os.path.join(OUT, "packing_rigetti.json")))["rings"]]
    for k in (2, 4):
        blocks = []
        for bi in (0, 1):
            ang = beat_angles(cfg, d["rel"][rows[bi]])
            blocks.append((compile_native(logical_ops(cfg, coup, ang, k), rings[bi], "rigetti"), rings[bi]))
        meas = rings[0] + rings[1]
        items.append(dict(name=f"rigetti_packed2_k{k}", device="rigetti", qasm=relabel(program(blocks, "rigetti"), meas),
                          n=2 * N, snapshot=k, slots=[dict(beat=bi, beat_id=ids[bi], pos=list(range(N * bi, N * bi + N)))
                                                      for bi in (0, 1)],
                          ref=[ref["exact"][bi, 55 * (k - 1):55 * k].tolist() for bi in (0, 1)]))
    os.makedirs(os.path.join(OUT, "validation"), exist_ok=True)
    json.dump(dict(items=items, beat_ids=ids, shot_ref=ref["shot"].tolist(), exact_ref=ref["exact"].tolist()),
              open(os.path.join(OUT, "validation", "validation_input.json"), "w"))
    return len(items)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prepare", "plan", "analyse", "validate-prep"])
    ap.add_argument("--device", choices=sorted(DEVICES), default="rigetti")
    ap.add_argument("--beats", type=int, default=24, choices=[24, 48, 96])
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.cmd == "prepare":
        if not os.path.exists(os.path.join(OUT, "beats.json")):
            draw_beats()
        for dev in DEVICES:
            pk = pack_rings(dev)
            json.dump(pk, open(os.path.join(OUT, f"packing_{dev}.json"), "w"), indent=1)
            print(dev, "P =", pk["P"], "cycles", pk["n_cycles_found"], "median CZ err device/rings",
                  pk["median_cz_error_device"], pk["median_cz_error_rings"])
    elif a.cmd == "plan":
        pl = build_plan(a.device, a.beats)
        f = os.path.join(OUT, f"plan_{a.device}_b{a.beats}.json")
        json.dump(pl, open(f, "w"), indent=1)
        print(f, "tasks", pl["n_tasks"], "P", pl["P"], "USD", pl["est_usd"])
    elif a.cmd == "validate-prep":
        print("validation items", validate_prep())
    else:
        print(json.dumps(analyse(), indent=1))


if __name__ == "__main__":
    main()
