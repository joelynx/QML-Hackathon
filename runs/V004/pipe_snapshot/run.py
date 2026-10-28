"""Tuning, training and prediction for the EV1 reservoir arms (matched-baseline rules 1-3 in EVAL.md).

  python -I -m qhc.pipe.run tune      --arm esn --exp E001      DS1 grouped-CV random search (proxy), resumable
  python -I -m qhc.pipe.run final     --arm esn --exp E001 --seeds 0 1 2 3 4 [--oof] [--splits ds2s]
  python -I -m qhc.pipe.run leakcheck --exp E001 --seed 0       full-pipeline lookahead check on DS1 records
  python -I -m qhc.pipe.run control   --exp E004 --kind mf --from-exp E003   controls of a tuned QRC (EVAL.md rule 7)
  python -I -m qhc.pipe.run rronly    --exp E006 --oof --splits ds2s          RR features alone (EVAL.md rule 7)
  python -I -m qhc.pipe.run lowdata   --exp E007 --from-exp E003 --k 5 --splits ds2s   reduced-data refit (EVAL.md slice c)

Both arms: reservoir input = the patient-relative beat window (features.relative_windows); readout input = the K = 220
reservoir features plus the shared rr block; readout = readout.Readout with the nested LAMBDAS grid; decision = argmax.
Tuning: N_CONFIGS configurations per arm drawn i.i.d. from SPACES with numpy default_rng(SEARCH_SEED), each evaluated
with reservoir seed TUNE_SEED (and shot seed TUNE_SEED) by pooled out-of-fold macro-F1 on the fixed DS1 folds; the
best (configuration, lambda) wins, ties to the lower index. Final runs: reservoir seed s and, for the quantum arm, shot
seed 1000 + s, for s in the 5 seed indices; readout refitted on all DS1 units.
"""
import argparse
import json
import os
import time

import numpy as np
import pandas as pd

from .. import evalspec as E
from ..evaluate import PROCESSED, ROOT, code_revision
from ..leakcheck import check_lookahead
from ..units import sha256
from . import pipe_revision
from .features import load_signal, load_split, record_features, L
from .readout import CLASS_IDX, LAMBDAS, Readout, cv_oof, oof_scores
from .reservoirs import beat_key, make

SPACES = {
    "esn": {"size": ("choice", [55, 110, 220]), "rho": ("uniform", 0.5, 1.2), "leak": ("uniform", 0.1, 1.0),
            "in_scale": ("loguniform", 0.1, 2.0), "density": ("uniform", 0.05, 1.0), "bias": ("uniform", 0.0, 1.0)},
    "qrc": {"in_scale": ("loguniform", 0.1, 2.0), "J": ("uniform", 0.1, 1.5), "h": ("uniform", 0.1, 1.5),
            "depth": ("choice", [1, 2, 3]), "topology": ("choice", ["chain", "ring"]),
            "disorder": ("uniform", 0.0, 1.0)},
}
N_CONFIGS = 30
SEARCH_SEED = E.BOOT_SEED
TUNE_SEED = 0
SHOTS = 1024
SHOT_ARMS = ("qrc", "mf")  # arms with finite-shot measurement sampling
INPUT = "rel"
LEAK_RECORDS, LEAK_SECONDS = ("207", "209", "114", "201"), 150
PIPE_REV = pipe_revision()  # the code this process loaded; files edited later do not change what it runs


def sample_configs(arm, n=N_CONFIGS, seed=SEARCH_SEED):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        cfg = {}
        for k, spec in SPACES[arm].items():
            if spec[0] == "choice":
                cfg[k] = spec[1][int(rng.integers(len(spec[1])))]
            elif spec[0] == "uniform":
                cfg[k] = float(rng.uniform(spec[1], spec[2]))
            else:
                cfg[k] = float(np.exp(rng.uniform(np.log(spec[1]), np.log(spec[2]))))
        out.append(cfg)
    return out


def ds1_data():
    d = load_split("ds1")
    lab = pd.read_csv(os.path.join(PROCESSED, "labels_ds1.csv"), dtype={"record": str, "beat_id": str})
    lab = lab.set_index("beat_id").loc[d["beat_id"]]
    y = np.where(lab["is_unit"].to_numpy(dtype=bool), lab["aami"].map(CLASS_IDX).fillna(-1).to_numpy(), -1).astype(int)
    with open(os.path.join(PROCESSED, "ds1_folds.json")) as f:
        folds = json.load(f)
    return d, y, folds


def keys_of(d):
    return np.array([beat_key(b) for b in d["beat_id"]], dtype=np.int64)


def build_model(arm, cfg, seed, shot_seed=None, shots=SHOTS):
    return make(arm, cfg, seed, **({"shots": shots, "shot_seed": shot_seed} if arm in SHOT_ARMS else {}))


def design(res_feats, d):
    return np.c_[res_feats, d["rr"]]


def exp_dir(exp):
    p = os.path.join(ROOT, "runs", exp)
    os.makedirs(p, exist_ok=True)
    return p


def _lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def cmd_tune(a):
    path = os.path.join(exp_dir(a.exp), "tuning.jsonl")
    done = {x["index"] for x in _lines(path)}
    d, y, folds = ds1_data()
    keys = keys_of(d)
    lams = tuple(a.lambdas) if a.lambdas else LAMBDAS
    for j, cfg in enumerate(sample_configs(a.arm, a.n)):
        if j in done:
            continue
        t = time.time()
        model = build_model(a.arm, cfg, TUNE_SEED, TUNE_SEED)
        X = design(model.features(d[INPUT], keys), d)
        scores = oof_scores(cv_oof(X, y, d["record"], folds, lams), y)
        best_lam = max(lams, key=lambda lam: scores[lam])  # first maximum in grid order
        rec = {"index": j, "arm": a.arm, "config": cfg, "scores": {str(k): v for k, v in scores.items()},
               "best_lam": best_lam, "best_score": scores[best_lam], "seconds": round(time.time() - t, 1),
               "tune_seed": TUNE_SEED, "input": INPUT, "lambdas": list(lams), "pipe_revision": PIPE_REV}
        with open(path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"{a.arm} cfg{j:02d} best {rec['best_score']:.4f} (lam {best_lam}) {rec['seconds']}s {cfg}", flush=True)
    best = best_config(a.exp)
    print("best:", best)


def best_config(exp):
    lines = _lines(os.path.join(ROOT, "runs", exp, "tuning.jsonl"))
    if not lines:  # a control: its configuration was fixed by `control`, not tuned
        with open(os.path.join(ROOT, "runs", exp, "selected_config.json")) as f:
            return json.load(f)
    b = max(lines, key=lambda x: (x["best_score"], -x["index"]))
    return {"index": b["index"], "arm": b["arm"], "config": b["config"], "lam": b["best_lam"], "score": b["best_score"],
            "n_configs": len(lines)}


def write_pred(path, beat_ids, probs):
    df = pd.DataFrame({"beat_id": beat_ids, "pred": np.array(E.CLASSES)[probs.argmax(1)]})
    for i, c in enumerate(E.CLASSES):
        df[f"prob_{c}"] = probs[:, i]
    df.to_csv(path, index=False, float_format="%.6f")


def save_artifact(path, arm, best, seed, shot_seed, model, ro):
    res = {"couplings": model.couplings} if arm in SHOT_ARMS else {"W": model.W.cpu().numpy(),
                                                               "W_in": model.W_in.cpu().numpy(),
                                                               "b": model.b.cpu().numpy()}
    meta = {"arm": arm, "config": best["config"], "config_index": best["index"], "seed": seed, "shot_seed": shot_seed,
            "shots": SHOTS if arm in SHOT_ARMS else None, "input": INPUT, "pipe_revision": PIPE_REV}
    st = ro.state()
    np.savez(path, meta=json.dumps(meta), lam=st["lam"], mu=st["mu"], sd=st["sd"], W_readout=st["W"],
             b_readout=st["b"], **{f"res_{k}": v for k, v in res.items()})


def load_artifact(path):
    z = np.load(path)
    meta = json.loads(str(z["meta"]))
    ro = Readout(float(z["lam"]))
    ro.mu, ro.sd, ro.W, ro.b = z["mu"], z["sd"], z["W_readout"], z["b_readout"]
    model = build_model(meta["arm"], meta["config"], meta["seed"], meta["shot_seed"])
    return meta, model, ro


def cmd_final(a):
    best = best_config(a.exp)
    arm = best["arm"]
    out = exp_dir(a.exp)
    d, y, folds = ds1_data()
    keys, units = keys_of(d), y >= 0
    targets = {s: load_split(s) for s in a.splits}
    tkeys = {s: keys_of(v) for s, v in targets.items()}
    for seed in a.seeds:
        shot_seed = 1000 + seed if arm in SHOT_ARMS else None
        t = time.time()
        model = build_model(arm, best["config"], seed, shot_seed)
        X = design(model.features(d[INPUT], keys), d)
        if a.oof:
            p = cv_oof(X, y, d["record"], folds, (best["lam"],))[best["lam"]]
            write_pred(os.path.join(out, f"oof_ds1_seed{seed}.csv"), d["beat_id"], p)
        ro = Readout(best["lam"]).fit(X[units], y[units])
        art = os.path.join(out, f"model_seed{seed}.npz")
        save_artifact(art, arm, best, seed, shot_seed, model, ro)
        for s, ds in targets.items():
            f = os.path.join(out, f"pred_{s}_seed{seed}.csv")
            write_pred(f, ds["beat_id"], ro.predict_proba(design(model.features(ds[INPUT], tkeys[s]), ds)))
            man = {"arm_id": f"{a.exp}-{arm}", "seed": seed, "split": s, "config_id": f"{a.exp}-{arm}-cfg{best['index']}",
                   "code_revision": f"eval {code_revision()} / pipe {PIPE_REV}",
                   "model_artifact": os.path.relpath(art, ROOT).replace(os.sep, "/"),
                   "model_artifact_sha256": sha256(art), "reservoir_seed": seed, "shot_seed": shot_seed,
                   "prediction_sha256": sha256(f), "config": best["config"], "lam": best["lam"]}
            with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
                json.dump(man, fh, indent=1)
        print(f"{a.exp} {arm} seed {seed}: {round(time.time() - t, 1)}s", flush=True)
    with open(os.path.join(out, "selected_config.json"), "w") as f:
        json.dump(best, f, indent=1)


CONTROLS = {
    "mf": "classical-spin (mean-field) reservoir of the same gates and couplings",
    "sep": "separable QRC: the same configuration with J = 0 (no entangling gates)",
}


def cmd_control(a):
    """Fix a control's configuration from a tuned QRC experiment (no tuning of its own), then train like `final`."""
    src = best_config(a.from_exp)
    if src["arm"] != "qrc":
        raise SystemExit("controls derive from a tuned QRC experiment")
    cfg = dict(src["config"], J=0.0) if a.kind == "sep" else dict(src["config"])
    best = {"index": src["index"], "arm": "mf" if a.kind == "mf" else "qrc", "config": cfg, "lam": src["lam"],
            "score": None, "n_configs": 0, "control_of": a.from_exp, "control": a.kind, "description": CONTROLS[a.kind]}
    with open(os.path.join(exp_dir(a.exp), "selected_config.json"), "w") as f:
        json.dump(best, f, indent=1)
    cmd_final(a)


def cmd_rronly(a):
    """Control: the shared readout on the 8 RR features alone. lambda chosen from LAMBDAS by DS1 OOF macro-F1 (the
    same procedure as the arms). Deterministic, so it is a single run (scored with `score`, not a 5-seed compare)."""
    out = exp_dir(a.exp)
    d, y, folds = ds1_data()
    units = y >= 0
    oof = cv_oof(d["rr"], y, d["record"], folds)
    scores = oof_scores(oof, y)
    lam = max(LAMBDAS, key=lambda v: scores[v])
    if a.oof:
        write_pred(os.path.join(out, "oof_ds1_seed0.csv"), d["beat_id"], oof[lam])
    ro = Readout(lam).fit(d["rr"][units], y[units])
    art = os.path.join(out, "model_seed0.npz")
    st = ro.state()
    np.savez(art, meta=json.dumps({"arm": "rr", "lam": lam, "pipe_revision": PIPE_REV}), lam=st["lam"], mu=st["mu"],
             sd=st["sd"], W_readout=st["W"], b_readout=st["b"])
    for s in a.splits:
        ds = load_split(s)
        f = os.path.join(out, f"pred_{s}_seed0.csv")
        write_pred(f, ds["beat_id"], ro.predict_proba(ds["rr"]))
        man = {"arm_id": f"{a.exp}-rr", "seed": 0, "split": s, "config_id": f"{a.exp}-rr", "lam": lam,
               "code_revision": f"eval {code_revision()} / pipe {PIPE_REV}",
               "model_artifact": os.path.relpath(art, ROOT).replace(os.sep, "/"), "model_artifact_sha256": sha256(art),
               "reservoir_seed": None, "shot_seed": None, "prediction_sha256": sha256(f)}
        with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
            json.dump(man, fh, indent=1)
    with open(os.path.join(out, "selected_config.json"), "w") as f:
        json.dump({"arm": "rr", "lam": lam, "scores": {str(k): v for k, v in scores.items()}}, f, indent=1)
    print(f"{a.exp} rr-only: DS1 OOF {scores} -> lambda {lam}")


def cmd_lowdata(a):
    """Reduced-data refitting (EVAL.md slice c): a headline arm keeps its full-DS1 configuration and lambda (the
    selected configuration) and its reservoir and shot seeds; the readout (normalisation and weights) is refitted on the
    units of the frozen k-record DS1 subset only. Writes runs/<exp>/<from-exp>/ with the run-manifest fields the
    low-data roles check: parent_config_id (the headline configuration id), train_records and refit_scope. A proxy:
    predictions for the DS1 records outside the subset (heldout_ds1_seed*.csv)."""
    best = best_config(a.from_exp)
    arm = best["arm"]
    with open(os.path.join(PROCESSED, "lowdata_subsets.json")) as f:
        subset = sorted(json.load(f)["subsets"][f"k{a.k}"]["records"])
    out = os.path.join(exp_dir(a.exp), a.from_exp)
    os.makedirs(out, exist_ok=True)
    d, y, _ = ds1_data()
    keys = keys_of(d)
    in_sub = np.isin(d["record"], subset)
    fit, held = in_sub & (y >= 0), ~in_sub
    targets = {s: load_split(s) for s in a.splits}
    parent = f"{a.from_exp}-{arm}-cfg{best['index']}"
    for seed in a.seeds:
        shot_seed = 1000 + seed if arm in SHOT_ARMS else None
        t = time.time()
        model = build_model(arm, best["config"], seed, shot_seed)
        X = design(model.features(d[INPUT], keys), d)
        ro = Readout(best["lam"]).fit(X[fit], y[fit])
        write_pred(os.path.join(out, f"heldout_ds1_seed{seed}.csv"), d["beat_id"][held], ro.predict_proba(X[held]))
        art = os.path.join(out, f"model_seed{seed}.npz")
        save_artifact(art, arm, best, seed, shot_seed, model, ro)
        for s, ds in targets.items():
            f = os.path.join(out, f"pred_{s}_seed{seed}.csv")
            write_pred(f, ds["beat_id"], ro.predict_proba(design(model.features(ds[INPUT], keys_of(ds)), ds)))
            man = {"arm_id": f"{a.exp}-{a.from_exp}-{arm}-k{a.k}", "seed": seed, "split": s,
                   "config_id": f"{parent}-k{a.k}", "code_revision": f"eval {code_revision()} / pipe {PIPE_REV}",
                   "model_artifact": os.path.relpath(art, ROOT).replace(os.sep, "/"),
                   "model_artifact_sha256": sha256(art), "reservoir_seed": seed, "shot_seed": shot_seed,
                   "prediction_sha256": sha256(f), "config": best["config"], "lam": best["lam"],
                   "parent_config_id": parent, "train_records": subset, "refit_scope": f"lowdata_k{a.k}",
                   "n_train_units": int(fit.sum())}
            with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
                json.dump(man, fh, indent=1)
        print(f"{a.exp} {a.from_exp} {arm} k{a.k} seed {seed}: {int(fit.sum())} units, {round(time.time() - t, 1)}s",
              flush=True)
    with open(os.path.join(out, "selected_config.json"), "w") as f:
        json.dump(dict(best, lowdata_k=a.k, train_records=subset, parent_config_id=parent), f, indent=1)


def pipeline_fn(meta, model, ro, db, rec):
    """The complete per-record pipeline f(signal, samples, fs) -> class probabilities, as qhc.leakcheck expects."""
    def f(signal, samples, fs):
        feats = record_features(signal, samples, fs)
        d = {"rel": feats[:, L:2 * L], "rr": feats[:, 2 * L:]}
        keys = np.array([beat_key(f"{db}:{rec}:{int(s)}") for s in samples], dtype=np.int64)
        return ro.predict_proba(design(model.features(d[INPUT], keys), d))
    return f


def cmd_leakcheck(a):
    meta, model, ro = load_artifact(os.path.join(ROOT, "runs", a.exp, f"model_seed{a.seed}.npz"))
    from ..evaluate import load_positions
    pos = load_positions("ds1")
    report = {"exp": a.exp, "seed": a.seed, "arm": meta["arm"], "pipe_revision": PIPE_REV, "records": {}}
    for rec in LEAK_RECORDS:
        g = pos[pos["record"] == rec].sort_values("sample")
        sig, fs, _ = load_signal("mitdb", rec)  # MIT-BIH is used at its native 360 Hz
        s = g["sample"].to_numpy()
        s = s[s < LEAK_SECONDS * fs]
        sig = sig[:int((LEAK_SECONDS + 10) * fs)]
        idx = range(1, len(s) - 1)
        bad = check_lookahead(pipeline_fn(meta, model, ro, "mitdb", rec), sig, s, fs, idx)
        report["records"][rec] = {"beats_checked": len(idx), "violations": bad}
    report["beats_checked"] = sum(r["beats_checked"] for r in report["records"].values())
    report["passed"] = all(not r["violations"] for r in report["records"].values())
    with open(os.path.join(ROOT, "runs", a.exp, f"leakcheck_seed{a.seed}.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}),
          {r: (v["beats_checked"], len(v["violations"])) for r, v in report["records"].items()})


def main(argv=None):
    ap = argparse.ArgumentParser(description="EV1 reservoir arms")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tune")
    t.add_argument("--arm", required=True, choices=sorted(SPACES))
    t.add_argument("--exp", required=True)
    t.add_argument("--n", type=int, default=N_CONFIGS)
    t.add_argument("--lambdas", type=float, nargs="+", help="readout grid (default: the declared LAMBDAS)")
    t.set_defaults(fn=cmd_tune)
    f = sub.add_parser("final")
    f.add_argument("--exp", required=True)
    f.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    f.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    f.add_argument("--oof", action="store_true", help="also write DS1 out-of-fold predictions (proxy)")
    f.set_defaults(fn=cmd_final)
    lk = sub.add_parser("leakcheck")
    lk.add_argument("--exp", required=True)
    lk.add_argument("--seed", type=int, default=0)
    lk.set_defaults(fn=cmd_leakcheck)
    c = sub.add_parser("control")
    c.add_argument("--exp", required=True)
    c.add_argument("--kind", required=True, choices=sorted(CONTROLS))
    c.add_argument("--from-exp", required=True)
    c.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    c.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    c.add_argument("--oof", action="store_true")
    c.set_defaults(fn=cmd_control)
    r = sub.add_parser("rronly")
    r.add_argument("--exp", required=True)
    r.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    r.add_argument("--oof", action="store_true")
    r.set_defaults(fn=cmd_rronly)
    lo = sub.add_parser("lowdata")
    lo.add_argument("--exp", required=True)
    lo.add_argument("--from-exp", required=True)
    lo.add_argument("--k", type=int, required=True, choices=list(E.LOWDATA_K))
    lo.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    lo.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    lo.set_defaults(fn=cmd_lowdata)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
