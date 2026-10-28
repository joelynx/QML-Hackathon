"""Predict-only path from saved headline artifacts (E018; fix for ANOMALIES A018).

  python -I -m qhc.p4.predict predict --exp E003 --split ds2s --out runs/E018/selfcheck_ds2s/E003
  python -I -m qhc.p4.predict predict --exp E003 --split svdb --out runs/E018/E003 --features-dir runs/E018/features
  python -I -m qhc.p4.predict build-features --split svdb --features-dir runs/E018/features

For each seed, the saved artifact runs/<exp>/model_seed<s>.npz is read once into memory (never opened for writing;
its sha256 is taken from those bytes and again from disk afterwards). The reservoir is rebuilt from the artifact's own
metadata (arm, configuration, reservoir seed, shot seed and the stored shot count, not a module default) and must equal
the saved res_* arrays exactly (QRC: couplings; ESN: W, W_in, b) or the run stops. The readout is restored from the
saved arrays. Features follow the batch path of `run.cmd_final`: `load_split`, `keys_of`, `design`, input `rel`.
Predictions are written with `run.write_pred`; each run manifest is copied from the corresponding headline ds2s
manifest runs/<exp>/pred_ds2s_seed<s>.run.json with split, prediction_sha256 and code_revision updated, and keeps
model_artifact / model_artifact_sha256 pointing at the original artifact (checked before and after).

Features of a split not built yet (svdb) are built with `features.build_split` into --features-dir, so nothing is
written outside the output tree. No labels are read anywhere in this module.
"""
import argparse
import hashlib
import io
import json
import os
import time

import numpy as np

from .. import evalspec as E
from ..evaluate import ROOT
from ..pipe import features as F
from ..pipe import run as R
from ..pipe.readout import Readout
from . import code_revision

MODULE = "predict"
RES_KEYS = {"qrc": ("couplings",), "esn": ("W", "W_in", "b")}


def _sha(b):
    return hashlib.sha256(b).hexdigest()


def file_sha256(path):
    with open(path, "rb") as f:
        return _sha(f.read())


def _rel(path):
    return os.path.relpath(os.path.abspath(path), ROOT).replace(os.sep, "/")


def _abs(path):
    return path if os.path.isabs(path) else os.path.join(ROOT, path)


def _fail(msg):
    raise SystemExit(f"[qhc.p4.predict] STOP: {msg}")


def load_frozen(path):
    """Load one saved artifact read-only and rebuild its model exactly. Returns (meta, model, readout, check)."""
    with open(path, "rb") as f:
        raw = f.read()
    before = _sha(raw)
    z = np.load(io.BytesIO(raw), allow_pickle=False)
    meta = json.loads(str(z["meta"]))
    arm = meta["arm"]
    if arm not in RES_KEYS:
        _fail(f"{path}: arm {arm!r} is not a headline reservoir arm")
    if meta.get("input") != R.INPUT:
        _fail(f"{path}: input {meta.get('input')!r} differs from the pipeline input {R.INPUT!r}")
    saved = {k[4:]: z[k] for k in z.files if k.startswith("res_")}
    if set(saved) != set(RES_KEYS[arm]):
        _fail(f"{path}: saved reservoir arrays {sorted(saved)} != expected {sorted(RES_KEYS[arm])}")
    if arm in R.SHOT_ARMS:
        if not isinstance(meta.get("shots"), int) or meta.get("shot_seed") is None:
            _fail(f"{path}: finite-shot arm without a stored shot count or shot seed ({meta.get('shots')}, "
                  f"{meta.get('shot_seed')})")
        model = R.build_model(arm, meta["config"], meta["seed"], meta["shot_seed"], shots=meta["shots"])
        if model.shots != meta["shots"] or model.shot_seed != meta["shot_seed"]:
            _fail(f"{path}: rebuilt shots/shot seed {model.shots}/{model.shot_seed} != stored "
                  f"{meta['shots']}/{meta['shot_seed']}")
        regen = {"couplings": np.asarray(model.couplings)}
    else:
        if meta.get("shots") is not None or meta.get("shot_seed") is not None:
            _fail(f"{path}: classical arm with a stored shot count or shot seed")
        model = R.build_model(arm, meta["config"], meta["seed"])
        regen = {"W": model.W.cpu().numpy(), "W_in": model.W_in.cpu().numpy(), "b": model.b.cpu().numpy()}
    if model.seed != meta["seed"]:
        _fail(f"{path}: rebuilt reservoir seed {model.seed} != stored {meta['seed']}")
    cfg_rebuilt = {k: model.cfg[k] for k in meta["config"]}
    if set(model.cfg) != set(meta["config"]) or cfg_rebuilt != meta["config"]:
        _fail(f"{path}: rebuilt configuration {model.cfg} != stored {meta['config']}")
    arrays = {}
    for k in RES_KEYS[arm]:
        a, b = regen[k], saved[k]
        if a.shape != b.shape or a.dtype != b.dtype or not np.array_equal(a, b):
            diff = float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64)))) if a.shape == b.shape else None
            _fail(f"{path}: regenerated reservoir array {k} differs from the saved res_{k} "
                  f"(shape {a.shape} vs {b.shape}, dtype {a.dtype} vs {b.dtype}, max abs diff {diff})")
        arrays[k] = {"shape": list(b.shape), "dtype": str(b.dtype), "sha256": _sha(np.ascontiguousarray(b).tobytes()),
                     "equal": True}
    ro = Readout(float(z["lam"]))
    ro.mu, ro.sd, ro.W, ro.b = z["mu"], z["sd"], z["W_readout"], z["b_readout"]
    after = file_sha256(path)
    if after != before:
        _fail(f"{path}: artifact bytes changed while loading ({before} -> {after})")
    check = {"artifact": _rel(path), "sha256_before": before, "sha256_after_load": after, "arm": arm,
             "seed": meta["seed"], "shot_seed": meta["shot_seed"], "shots": meta["shots"], "lam": float(z["lam"]),
             "artifact_pipe_revision": meta.get("pipe_revision"), "reservoir_arrays": arrays,
             "readout_shapes": {k: list(z[k].shape) for k in ("mu", "sd", "W_readout", "b_readout")}}
    return meta, model, ro, check


def _check_against_manifest(meta, check, man, exp, seed):
    want = {"arm_id": f"{exp}-{meta['arm']}", "config_id": f"{exp}-{meta['arm']}-cfg{meta['config_index']}",
            "seed": seed, "reservoir_seed": meta["seed"], "shot_seed": meta["shot_seed"], "config": meta["config"],
            "lam": check["lam"], "model_artifact": f"runs/{exp}/model_seed{seed}.npz",
            "model_artifact_sha256": check["sha256_before"]}
    bad = {k: (man.get(k), v) for k, v in want.items() if man.get(k) != v}
    if bad:
        _fail(f"{exp} seed {seed}: headline manifest disagrees with the artifact: {bad}")


def features_digest(d):
    return {k: _sha(np.ascontiguousarray(v).tobytes()) for k, v in d.items()}


def cmd_build(a):
    F.FEATURE_DIR = _abs(a.features_dir)
    t = time.time()
    out, n = F.build_split(a.split)
    rec = {"split": a.split, "file": _rel(out), "n_beats": n, "seconds": round(time.time() - t, 1),
           "file_sha256": file_sha256(out), "arrays_sha256": features_digest(F.load_split(a.split)),
           "pipe_revision": R.PIPE_REV, "code_revision": code_revision(MODULE)}
    with open(os.path.join(F.FEATURE_DIR, f"build_{a.split}.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec))


def cmd_predict(a):
    out = _abs(a.out)
    src_dir = os.path.join(ROOT, "runs", a.exp)
    if os.path.normcase(os.path.realpath(out)).startswith(os.path.normcase(os.path.realpath(src_dir))):
        _fail(f"--out {a.out} lies inside the artifact directory runs/{a.exp}")
    os.makedirs(out, exist_ok=True)
    if a.features_dir:
        F.FEATURE_DIR = _abs(a.features_dir)
    rev = code_revision(MODULE)
    t0 = time.time()
    d = F.load_split(a.split)
    keys = R.keys_of(d)
    feat_file = os.path.join(F.FEATURE_DIR, f"{a.split}.npz")
    t_load = round(time.time() - t0, 1)
    log = {"exp": a.exp, "split": a.split, "out": _rel(out), "code_revision": rev, "features_file": _rel(feat_file),
           "features_file_sha256": file_sha256(feat_file), "features_arrays_sha256": features_digest(d),
           "n_beats": int(len(d["beat_id"])), "features_load_seconds": t_load, "runs": []}
    for seed in a.seeds:
        t = time.time()
        art = os.path.join(src_dir, f"model_seed{seed}.npz")
        src_man_path = os.path.join(src_dir, f"pred_ds2s_seed{seed}.run.json")
        with open(src_man_path, "rb") as fh:
            src_man_raw = fh.read()
        man = json.loads(src_man_raw)
        meta, model, ro, check = load_frozen(art)
        _check_against_manifest(meta, check, man, a.exp, seed)
        X = R.design(model.features(d[meta["input"]], keys), d)
        probs = ro.predict_proba(X)
        f = os.path.join(out, f"pred_{a.split}_seed{seed}.csv")
        if os.path.exists(f) and not a.overwrite:
            _fail(f"{f} exists (pass --overwrite to replace an E018 output)")
        R.write_pred(f, d["beat_id"], probs)
        art_after = file_sha256(art)
        if art_after != check["sha256_before"]:
            _fail(f"{art}: artifact hash changed during prediction")
        new = dict(man, split=a.split, prediction_sha256=file_sha256(f), code_revision=rev,
                   model_artifact=man["model_artifact"], model_artifact_sha256=check["sha256_before"],
                   predicted_by="qhc.p4.predict (predict-only from the saved artifact; A018 fix)",
                   source_manifest=_rel(src_man_path), source_manifest_sha256=_sha(src_man_raw),
                   source_code_revision=man["code_revision"], features_file=_rel(feat_file),
                   features_arrays_sha256=log["features_arrays_sha256"],
                   artifact_check={**{k: v for k, v in check.items() if k != "artifact"}, "sha256_after_predict": art_after})
        with open(os.path.splitext(f)[0] + ".run.json", "w") as fh:
            json.dump(new, fh, indent=1)
        rec = {"seed": seed, "file": _rel(f), "sha256": new["prediction_sha256"], "artifact": _rel(art),
               "artifact_sha256_before": check["sha256_before"], "artifact_sha256_after": art_after,
               "reservoir_arrays_equal": all(v["equal"] for v in check["reservoir_arrays"].values()),
               "shots": check["shots"], "seconds": round(time.time() - t, 1)}
        log["runs"].append(rec)
        print(f"{a.exp} {a.split} seed {seed}: {rec['sha256'][:16]} artifact {check['sha256_before'][:16]} "
              f"unchanged, reservoir arrays equal, {rec['seconds']}s", flush=True)
    log["total_seconds"] = round(time.time() - t0, 1)
    with open(os.path.join(out, f"predict_{a.split}.json"), "w") as fh:
        json.dump(log, fh, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description="predict-only path from saved headline artifacts (E018, A018)")
    sub = ap.add_subparsers(dest="cmd")
    b = sub.add_parser("build-features")
    b.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    b.add_argument("--features-dir", required=True)
    b.set_defaults(fn=cmd_build)
    p = sub.add_parser("predict")
    p.add_argument("--exp", required=True, choices=["E002", "E003"])
    p.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    p.add_argument("--out", required=True)
    p.add_argument("--features-dir", help="feature directory (default: the pipeline's runs/features/EV1)")
    p.add_argument("--seeds", type=int, nargs="+", default=list(range(E.N_SEEDS)))
    p.add_argument("--overwrite", action="store_true")
    p.set_defaults(fn=cmd_predict)
    a = ap.parse_args(argv)
    if a.cmd is None:
        ap.error("choose build-features or predict")
    a.fn(a)


if __name__ == "__main__":
    main()
