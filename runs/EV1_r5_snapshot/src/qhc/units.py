"""Build the evaluation units from raw annotations.

For each split this writes, under runs/data/processed/EV1/:
  positions_<split>.csv  every beat annotation position, with a label-free `predict` flag (edge and first/last rules
                         only). Pipelines must output a prediction for every `predict` beat. This is what a QRS
                         detector would provide.
  records_<split>.csv    record, fs, sig_len, duration_s (label-free).
  labels_<split>.csv     the `predict` beats with their AAMI class and `is_unit` (class in N/S/V). Only the scorer reads
                         this for test splits; pipelines may read labels_ds1.csv (training split) only. The confirmation
                         split's labels are written to confirm/ and read only through the guarded scoring path.
plus ds1_folds.json (grouped CV folds for tuning) and manifest.json (hashes of inputs and outputs).
"""
import argparse
import hashlib
import json
import os

import numpy as np
import pandas as pd
import wfdb

from . import evalspec as E


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record_list(raw_root, db, records):
    if records is not None:
        return list(records)
    return open(os.path.join(raw_root, db, "RECORDS")).read().split()


def predict_flags(samples, fs, sig_len):
    """Label-free prediction-set rule: not the first or last beat annotation, and at least EDGE_SEC from either end."""
    samples = np.asarray(samples)
    edge = int(round(E.EDGE_SEC * fs))
    flag = (samples >= edge) & (samples <= sig_len - 1 - edge)
    if len(flag):
        flag[[0, -1]] = False
    return flag


def select_beats(samples, symbols):
    """Beat annotations only: (sample, symbol) rows whose symbol is a beat code. Non-beat annotations (rhythm, noise,
    flutter waves `!`, ...) are dropped, so they never act as beat positions or enter RR intervals."""
    rows = [(int(s), sym) for s, sym in zip(samples, symbols) if sym in E.BEAT_SYMBOLS]
    return pd.DataFrame(rows, columns=["sample", "symbol"])


def beats_for_record(raw_root, db, rec):
    path = os.path.join(raw_root, db, rec)
    hdr = wfdb.rdheader(path)
    ann = wfdb.rdann(path, "atr")
    df = select_beats(ann.sample, ann.symbol)
    df["aami"] = df["symbol"].map(E.AAMI).fillna("other")
    df["predict"] = predict_flags(df["sample"], hdr.fs, hdr.sig_len)
    df["is_unit"] = df["predict"] & df["aami"].isin(E.CLASSES)
    df.insert(0, "record", rec)
    df.insert(0, "db", db)
    df["fs"] = hdr.fs
    df["beat_id"] = db + ":" + rec + ":" + df["sample"].astype(str)
    info = {"record": rec, "fs": hdr.fs, "sig_len": hdr.sig_len, "duration_s": hdr.sig_len / hdr.fs}
    return df, info


def make_folds(labels_ds1, k, n_trials=20000, seed=E.BOOT_SEED):
    """Grouped folds over DS1 records (equal record counts up to one), chosen by seeded random search to minimise the
    worst relative deviation of any fold's S or V beat count from an even share."""
    counts = labels_ds1.groupby("record")["aami"].value_counts().unstack(fill_value=0)
    for c in E.CLASSES:
        if c not in counts:
            counts[c] = 0
    recs = counts.index.to_numpy()
    sv = counts[["S", "V"]].to_numpy(dtype=float)
    target = sv.sum(0) / k
    base = np.arange(len(recs)) % k
    rng = np.random.default_rng(seed)
    best, best_cost = None, np.inf
    for _ in range(n_trials):
        assign = rng.permutation(base)
        load = np.zeros((k, 2))
        np.add.at(load, assign, sv)
        cost = np.abs(load / target - 1).max()
        if cost < best_cost:
            best, best_cost = assign, cost
    return {f"fold{i}": sorted(recs[best == i].tolist()) for i in range(k)}


def draw_lowdata_subsets(units_ds1, seed=E.BOOT_SEED):
    """Seeded DS1 record subsets for the reduced-data slice: rng = np.random.default_rng(seed); for each k in LOWDATA_K,
    in order and from the same stream, draw rng.choice(sorted DS1 records, k, replace=False) until the subset holds at
    least LOWDATA_MIN_UNITS S and LOWDATA_MIN_UNITS V units."""
    cnt = units_ds1.groupby("record")["aami"].value_counts().unstack(fill_value=0)
    recs = sorted(cnt.index)
    rng = np.random.default_rng(seed)
    out = {}
    for k in E.LOWDATA_K:
        draws = 0
        while True:
            draws += 1
            sub = sorted(rng.choice(recs, k, replace=False).tolist())
            c = cnt.loc[sub].sum()
            if c.get("S", 0) >= E.LOWDATA_MIN_UNITS and c.get("V", 0) >= E.LOWDATA_MIN_UNITS:
                break
        out[f"k{k}"] = {"records": sub, "draws": draws, "units": {x: int(c.get(x, 0)) for x in E.CLASSES}}
    rule = (f"numpy default_rng({seed}) over sorted DS1 records; k=5 then k=11 from the same stream with "
            f"rng.choice(records, k, replace=False); redraw until the subset has >= {E.LOWDATA_MIN_UNITS} S and "
            f">= {E.LOWDATA_MIN_UNITS} V units")
    return {"rule": rule, "subsets": out}


def build(raw_root, out_dir, splits=None):
    """Build all splits, or only `splits`; in that case the other splits' outputs and manifest entries are kept as
    they are (used in EV1 r4 to rebuild the MIT-BIH splits without reopening the SVDB annotations)."""
    os.makedirs(out_dir, exist_ok=True)
    m_path = os.path.join(out_dir, "manifest.json")
    manifest = {"ev": E.EV, "edge_sec": E.EDGE_SEC, "inputs": {}, "outputs": {}, "splits": {}}
    if splits is not None:
        manifest = json.load(open(m_path))
        manifest.setdefault("partial_rebuilds", []).append(sorted(splits))
    for db in ("mitdb", "svdb"):
        sums = os.path.join(raw_root, db, "SHA256SUMS.txt")
        manifest["inputs"][f"{db}/SHA256SUMS.txt"] = sha256(sums)
    for split, (db, records, _) in E.SPLITS.items():
        if splits is not None and split not in splits:
            continue
        recs = record_list(raw_root, db, records)
        parts = [beats_for_record(raw_root, db, r) for r in recs]
        pos = pd.concat([p for p, _ in parts], ignore_index=True)
        rec_info = pd.DataFrame([i for _, i in parts])
        pred_set = pos[pos["predict"]]
        lab = pred_set[["beat_id", "db", "record", "sample", "symbol", "aami", "is_unit"]]
        label_dir = os.path.join(out_dir, "confirm") if split in E.CONFIRMATION_SPLITS else out_dir
        os.makedirs(label_dir, exist_ok=True)
        paths = {
            "positions": os.path.join(out_dir, f"positions_{split}.csv"),
            "records": os.path.join(out_dir, f"records_{split}.csv"),
            "labels": os.path.join(label_dir, f"labels_{split}.csv"),
        }
        pos[["beat_id", "db", "record", "sample", "fs", "predict"]].to_csv(paths["positions"], index=False)
        rec_info.to_csv(paths["records"], index=False)
        lab.to_csv(paths["labels"], index=False)
        for p in paths.values():
            manifest["outputs"][os.path.relpath(p, out_dir).replace(os.sep, "/")] = sha256(p)
        units = lab[lab["is_unit"]]
        manifest["splits"][split] = {
            "db": db,
            "records": recs,
            "hours": float(rec_info["duration_s"].sum() / 3600),
            "n_positions": int(len(pos)),
            "n_predict": int(len(pred_set)),
            "n_units": int(len(units)),
            "class_counts": {k: int(v) for k, v in units["aami"].value_counts().items()},
            "predicted_nonunit_by_aami": {k: int(v) for k, v in pred_set.loc[~pred_set["is_unit"], "aami"].value_counts().items()},
            "not_predicted_by_aami": {k: int(v) for k, v in pos.loc[~pos["predict"], "aami"].value_counts().items()},
        }
        if split == "ds1":
            folds = make_folds(units, E.N_CV_FOLDS)
            f_path = os.path.join(out_dir, "ds1_folds.json")
            with open(f_path, "w") as f:
                json.dump(folds, f, indent=1)
            manifest["outputs"]["ds1_folds.json"] = sha256(f_path)
            manifest["ds1_folds"] = {
                name: {c: int(units[units["record"].isin(recs_)]["aami"].eq(c).sum()) for c in E.CLASSES}
                for name, recs_ in folds.items()
            }
            s_path = os.path.join(out_dir, "lowdata_subsets.json")
            with open(s_path, "w") as f:
                json.dump(draw_lowdata_subsets(units), f, indent=1)
            manifest["outputs"]["lowdata_subsets.json"] = sha256(s_path)
    with open(m_path, "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", default="runs/data/raw")
    ap.add_argument("--out", default=f"runs/data/processed/{E.EV}")
    ap.add_argument("--splits", nargs="+", choices=sorted(E.SPLITS), help="rebuild only these splits (default: all)")
    a = ap.parse_args()
    m = build(a.raw, a.out, a.splits)
    for s, info in m["splits"].items():
        print(s, info["n_predict"], info["n_units"], info["class_counts"], "nonunit:", info["predicted_nonunit_by_aami"],
              "not predicted:", info["not_predicted_by_aami"])
    print("folds:", m.get("ds1_folds"))


if __name__ == "__main__":
    main()
