"""E016: a strong classical context model, HistGradientBoostingClassifier on the reservoir arms' inputs plus RR.

  python -I -m qhc.p4.boost tune                       DS1 random search, N = 30, 20-minute wall-clock cap (proxy)
  python -I -m qhc.p4.boost final --splits ds2s        random states 0-4: DS1 OOF, refit on all DS1 units, predictions
  python -I -m qhc.p4.boost leakcheck --seed 0         full-pipeline lookahead check (features -> model)
  python -I -m qhc.p4.boost context                    DS1 OOF numbers next to E002, E003 and E006 (proxy)

Input: [patient-relative window (40) | RR block (8)] = np.c_[d["rel"], d["rr"]] from features.load_split. Training
units: DS1 beats with y >= 0 (N/S/V). Class-balanced sample weights n / (3 n_c), computed on each fit's own training
units like readout.Readout. HistGradientBoostingClassifier(early_stopping=False), random_state = the seed (it drives
the max_features feature subsampling, so seeds differ). Search space (EXPERIMENTS.md E016, in this key order), drawn
i.i.d. with numpy default_rng(20261026) like pipe.run.sample_configs. Each configuration is scored by pooled DS1 OOF
macro-F1 (readout.oof_scores) on the fixed folds ds1_folds.json with random state 0, in index order; the best wins,
ties to the lower index. No new configuration is launched after CAP_S seconds of search wall-clock; the rest are
recorded as not evaluated. Every fit uses THREADS OpenMP threads (fixed, so the tuning and final OOF agree exactly).
"""
import argparse
import datetime
import json
import os
import time

import joblib
import numpy as np
from joblib import Parallel, delayed
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

from .. import evalspec as E
from ..evaluate import ROOT
from ..units import sha256
from . import code_revision

EXP = "E016"
NAME = "boost"
ARM = "hgb"
SPACE = {
    "learning_rate": ("loguniform", 0.02, 0.3),
    "max_leaf_nodes": ("choice", [15, 31, 63, 127]),
    "min_samples_leaf": ("choice", [20, 50, 100, 200]),
    "l2_regularization": ("loguniform", 1e-3, 10.0),
    "max_iter": ("choice", [100, 200, 300]),
    "max_features": ("uniform", 0.5, 0.9),
}
N_CONFIGS = 30
SEARCH_SEED = 20261026
TUNE_SEED = 0
CAP_S = 20 * 60
THREADS = 4  # OpenMP threads per fit
FEATURES = "rel(40) | rr(8)"
LEAK_RECORDS, LEAK_SECONDS = ("207", "209", "114", "201"), 150


def out_dir(path=None):
    p = path or os.path.join(ROOT, "runs", EXP)
    os.makedirs(p, exist_ok=True)
    return p


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def sample_configs(n=N_CONFIGS, seed=SEARCH_SEED):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        cfg = {}
        for k, spec in SPACE.items():
            if spec[0] == "choice":
                cfg[k] = spec[1][int(rng.integers(len(spec[1])))]
            elif spec[0] == "uniform":
                cfg[k] = float(rng.uniform(spec[1], spec[2]))
            else:
                cfg[k] = float(np.exp(rng.uniform(np.log(spec[1]), np.log(spec[2]))))
        out.append(cfg)
    return out


def design(d):
    return np.c_[d["rel"], d["rr"]].astype(np.float32)


def class_weights(y):
    counts = np.bincount(y, minlength=len(E.CLASSES)).astype(np.float64)
    cw = np.where(counts > 0, len(y) / (len(E.CLASSES) * np.maximum(counts, 1)), 0.0)
    return cw[y]


def fit(X, y, cfg, seed, threads=THREADS):
    with threadpool_limits(limits=threads, user_api="openmp"):
        m = HistGradientBoostingClassifier(early_stopping=False, random_state=seed, **cfg)
        m.fit(X, y, sample_weight=class_weights(y))
    if list(m.classes_) != list(range(len(E.CLASSES))):
        raise RuntimeError(f"unexpected classes {m.classes_}")
    return m


def proba(m, X, threads=THREADS):
    with threadpool_limits(limits=threads, user_api="openmp"):
        return m.predict_proba(X)


def _task(kind, X, y, test, cfg, seed, threads):
    """kind 'fold': fit on the units outside `test`, return probabilities for every beat in `test`;
    kind 'full': fit on all units, return the model."""
    t = time.time()
    if kind == "fold":
        train = ~test & (y >= 0)
        p = proba(fit(X[train], y[train], cfg, seed, threads), X[test], threads)
        return p, round(time.time() - t, 2)
    units = y >= 0
    return fit(X[units], y[units], cfg, seed, threads), round(time.time() - t, 2)


def fold_masks(records, folds):
    return [np.isin(records, recs) for recs in folds.values()]


def load_ds1():
    from ..pipe.run import ds1_data  # imports torch; kept out of the worker processes
    d, y, folds = ds1_data()
    return d, y, folds


def score(p, y):
    from ..pipe.readout import oof_scores
    return oof_scores({0: p}, y)[0]


def per_class_f1(p, y):
    from ..scorer import f1_from_confusion
    u = y >= 0
    cm = np.zeros((len(E.CLASSES),) * 2, dtype=np.int64)
    np.add.at(cm, (y[u], p[u].argmax(1)), 1)
    return {c: float(v) for c, v in zip(E.CLASSES, f1_from_confusion(cm))}


def _lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def cmd_tune(a):
    out = out_dir(a.out)
    path = os.path.join(out, "tuning.jsonl")
    if os.path.exists(path):
        raise SystemExit(f"{path} exists; the capped search is not resumable")
    rev = code_revision(NAME)
    d, y, folds = load_ds1()
    X = design(d)
    masks = fold_masks(d["record"], folds)
    cfgs = sample_configs(a.n)
    meta = {"exp": EXP, "started": now(), "code_revision": rev, "n_declared": a.n, "search_seed": SEARCH_SEED,
            "tune_seed": TUNE_SEED, "cap_s": a.cap_s, "threads_per_fit": a.threads, "workers": a.workers,
            "features": FEATURES, "n_ds1_beats": int(len(y)), "n_ds1_units": int((y >= 0).sum()),
            "space": {k: list(v) for k, v in SPACE.items()}}
    done, t0 = [], time.time()
    with Parallel(n_jobs=a.workers, backend="loky") as par:
        for j, cfg in enumerate(cfgs):
            launch = time.time() - t0
            if launch >= a.cap_s:
                break
            t = time.time()
            res = par(delayed(_task)("fold", X, y, m, cfg, TUNE_SEED, a.threads) for m in masks)
            p = np.zeros((len(y), len(E.CLASSES)), dtype=np.float64)
            for m, (pm, _) in zip(masks, res):
                p[m] = pm
            rec = {"index": j, "arm": ARM, "config": cfg, "score": score(p, y), "per_class_f1": per_class_f1(p, y),
                   "fold_seconds": [s for _, s in res], "seconds": round(time.time() - t, 1),
                   "launched_at_s": round(launch, 1), "tune_seed": TUNE_SEED, "threads_per_fit": a.threads,
                   "code_revision": rev}
            with open(path, "a") as f:
                f.write(json.dumps(rec) + "\n")
            done.append(j)
            print(f"cfg{j:02d} {rec['score']:.4f} {rec['per_class_f1']} {rec['seconds']}s (launched {launch:.0f}s) "
                  f"{cfg}", flush=True)
    meta.update(finished=now(), search_seconds=round(time.time() - t0, 1), realised_n=len(done),
                not_evaluated=[j for j in range(a.n) if j not in done],
                not_evaluated_configs={j: cfgs[j] for j in range(a.n) if j not in done})
    best = best_config(out)
    meta["selected"] = best
    with open(os.path.join(out, "tuning_meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    print("realised N", len(done), "best:", best)


def best_config(out):
    lines = _lines(os.path.join(out, "tuning.jsonl"))
    b = max(lines, key=lambda x: (x["score"], -x["index"]))
    return {"index": b["index"], "arm": ARM, "config": b["config"], "score": b["score"], "n_configs": len(lines)}


def write_pred(path, beat_ids, probs):
    from ..pipe.run import write_pred as wp
    wp(path, beat_ids, probs)


def cmd_final(a):
    from ..pipe.features import load_split
    out = out_dir(a.out)
    best = best_config(out)
    rev = code_revision(NAME)
    d, y, folds = load_ds1()
    X = design(d)
    masks = fold_masks(d["record"], folds)
    targets = {s: load_split(s) for s in a.splits}
    tasks = [(s, k) for s in a.seeds for k in list(range(len(masks))) + ["full"]]
    t0 = time.time()
    res = Parallel(n_jobs=a.workers, backend="loky")(
        delayed(_task)("full" if k == "full" else "fold", X, y, None if k == "full" else masks[k], best["config"], s,
                       a.threads) for s, k in tasks)
    fits = dict(zip(tasks, res))
    timings = {}
    for s in a.seeds:
        p = np.zeros((len(y), len(E.CLASSES)), dtype=np.float64)
        for k, m in enumerate(masks):
            p[m] = fits[(s, k)][0]
        write_pred(os.path.join(out, f"oof_ds1_seed{s}.csv"), d["beat_id"], p)
        model, secs = fits[(s, "full")]
        timings[s] = {"full_fit_s": secs, "fold_fit_s": [fits[(s, k)][1] for k in range(len(masks))]}
        art = os.path.join(out, f"model_seed{s}.pkl")
        meta = {"exp": EXP, "arm": ARM, "config": best["config"], "config_index": best["index"], "random_state": s,
                "features": FEATURES, "classes": list(E.CLASSES), "threads_per_fit": a.threads, "code_revision": rev,
                "n_train_units": int((y >= 0).sum())}
        joblib.dump({"model": model, "meta": meta}, art)
        for split, ds in targets.items():
            f = os.path.join(out, f"pred_{split}_seed{s}.csv")
            write_pred(f, ds["beat_id"], proba(model, design(ds), a.threads))
            man = {"arm_id": f"{EXP}-{ARM}", "seed": s, "split": split, "config_id": f"{EXP}-{ARM}-cfg{best['index']}",
                   "code_revision": rev, "model_artifact": os.path.relpath(art, ROOT).replace(os.sep, "/"),
                   "model_artifact_sha256": sha256(art), "reservoir_seed": s, "shot_seed": None,
                   "prediction_sha256": sha256(f), "config": best["config"], "features": FEATURES,
                   "random_state": s, "note": "reservoir_seed carries the model's random_state (no reservoir)"}
            with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
                json.dump(man, fh, indent=1)
        print(f"{EXP} seed {s}: OOF {score(p, y):.4f} {per_class_f1(p, y)}", flush=True)
    with open(os.path.join(out, "selected_config.json"), "w") as f:
        json.dump(dict(best, final_seeds=list(a.seeds), final_seconds=round(time.time() - t0, 1), timings=timings,
                       code_revision=rev), f, indent=1)
    print(f"final {round(time.time() - t0, 1)}s")


def pipeline_fn(model):
    """f(signal, samples, fs) -> class probabilities, the complete per-record pipeline as qhc.leakcheck expects."""
    from ..pipe.features import L, record_features

    def f(signal, samples, fs):
        feats = record_features(signal, samples, fs)
        return proba(model, design({"rel": feats[:, L:2 * L], "rr": feats[:, 2 * L:]}))
    return f


def cmd_leakcheck(a):
    from ..evaluate import load_positions
    from ..leakcheck import check_lookahead
    from ..pipe.features import load_signal
    out = out_dir(a.out)
    art = os.path.join(out, f"model_seed{a.seed}.pkl")
    model = joblib.load(art)["model"]
    pos = load_positions("ds1")
    report = {"exp": EXP, "seed": a.seed, "arm": ARM, "model_artifact_sha256": sha256(art),
              "code_revision": code_revision(NAME), "records": {}}
    for rec in LEAK_RECORDS:
        g = pos[pos["record"] == rec].sort_values("sample")
        sig, fs, _ = load_signal("mitdb", rec)
        s = g["sample"].to_numpy()
        s = s[s < LEAK_SECONDS * fs]
        sig = sig[:int((LEAK_SECONDS + 10) * fs)]
        idx = range(1, len(s) - 1)
        bad = check_lookahead(pipeline_fn(model), sig, s, fs, idx)
        report["records"][rec] = {"beats_checked": len(idx), "violations": bad}
    report["beats_checked"] = sum(r["beats_checked"] for r in report["records"].values())
    report["passed"] = all(not r["violations"] for r in report["records"].values())
    with open(os.path.join(out, f"leakcheck_seed{a.seed}.json"), "w") as f:
        json.dump(report, f, indent=1)
    print(json.dumps({k: v for k, v in report.items() if k != "records"}),
          {r: (v["beats_checked"], len(v["violations"])) for r, v in report["records"].items()})


def _read_oof(path, beat_ids):
    import pandas as pd
    df = pd.read_csv(path, dtype={"beat_id": str}).set_index("beat_id").loc[beat_ids]
    return df[[f"prob_{c}" for c in E.CLASSES]].to_numpy(dtype=np.float64)


def cmd_context(a):
    """DS1 OOF (proxy) per seed: pooled macro-F1 and per-class F1, for E016 and the reference arms."""
    out = out_dir(a.out)
    d, y, _ = load_ds1()
    arms = {"E016": [os.path.join(out, f"oof_ds1_seed{s}.csv") for s in range(E.N_SEEDS)],
            "E003": [os.path.join(ROOT, "runs", "E003", f"oof_ds1_seed{s}.csv") for s in range(E.N_SEEDS)],
            "E002": [os.path.join(ROOT, "runs", "E002", f"oof_ds1_seed{s}.csv") for s in range(E.N_SEEDS)],
            "E006": [os.path.join(ROOT, "runs", "E006", "oof_ds1_seed0.csv")]}
    res = {}
    for arm, files in arms.items():
        per = []
        for f in files:
            p = _read_oof(f, d["beat_id"])
            per.append({"file": os.path.relpath(f, ROOT).replace(os.sep, "/"), "macro_f1": score(p, y),
                        "per_class_f1": per_class_f1(p, y)})
        res[arm] = {"seeds": per, "macro_f1_mean": float(np.mean([r["macro_f1"] for r in per])),
                    "macro_f1_sd": float(np.std([r["macro_f1"] for r in per], ddof=1)) if len(per) > 1 else None,
                    "per_class_f1_mean": {c: float(np.mean([r["per_class_f1"][c] for r in per])) for c in E.CLASSES}}
        print(f"{arm}: macro-F1 {res[arm]['macro_f1_mean']:.4f} (sd {res[arm]['macro_f1_sd']}) "
              f"per class {res[arm]['per_class_f1_mean']}")
    with open(os.path.join(out, "context_ds1_oof.json"), "w") as f:
        json.dump({"result_type": "proxy (DS1 OOF)", "n_ds1_units": int((y >= 0).sum()), "arms": res}, f, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="E016 gradient-boosting context model")
    ap.add_argument("--out", help="output directory (default runs/E016)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("tune")
    t.add_argument("--n", type=int, default=N_CONFIGS)
    t.add_argument("--cap-s", type=float, default=CAP_S)
    t.add_argument("--workers", type=int, default=5)
    t.add_argument("--threads", type=int, default=THREADS)
    t.set_defaults(fn=cmd_tune)
    f = sub.add_parser("final")
    f.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    f.add_argument("--splits", nargs="*", default=[], choices=sorted(E.SPLITS))
    f.add_argument("--workers", type=int, default=6)
    f.add_argument("--threads", type=int, default=THREADS)
    f.set_defaults(fn=cmd_final)
    lk = sub.add_parser("leakcheck")
    lk.add_argument("--seed", type=int, default=0)
    lk.set_defaults(fn=cmd_leakcheck)
    c = sub.add_parser("context")
    c.set_defaults(fn=cmd_context)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
