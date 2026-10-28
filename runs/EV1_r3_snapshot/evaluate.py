"""EV1 evaluation command.

  python -m qhc.evaluate score     --split ds2s --pred P.csv --id NAME --out runs/E###/score_ds2s.json
  python -m qhc.evaluate compare   --split ds2s --cand C_seed*.csv --base B_seed*.csv --cand-id X --base-id Y --out ...
  python -m qhc.evaluate reference --split ds2s --rule const_n --out runs/EV1_reference/pred_const_n_ds2s.csv

Prediction files are CSV with columns beat_id, pred (N/S/V), prob_N, prob_S, prob_V, with one row per beat whose
`predict` flag is set in positions_<split>.csv. Only N/S/V beats enter the metric.
Scoring the confirmation split (svdb) requires --confirm-reason. The predictions are validated first, then the
project-wide cap is checked, then the access is appended to runs/confirmation_access.jsonl, and only then are the
labels read.
"""
import argparse
import datetime
import glob
import json
import os
import sys

import numpy as np
import pandas as pd

from . import evalspec as E
from . import scorer
from .units import sha256

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (src/qhc/..)
PROCESSED = os.path.join(ROOT, "runs", "data", "processed", E.EV)
ACCESS_LOG = os.path.join(ROOT, "runs", "confirmation_access.jsonl")


def load_positions(split, processed=None):
    processed = processed or PROCESSED
    return pd.read_csv(os.path.join(processed, f"positions_{split}.csv"), dtype={"record": str})


def load_hours(split, processed=None):
    processed = processed or PROCESSED
    rec = pd.read_csv(os.path.join(processed, f"records_{split}.csv"), dtype={"record": str})
    return dict(zip(rec["record"], rec["duration_s"] / 3600))


def load_labels(split, processed=None, _confirmed_access=False):
    """Labels for scoring. The confirmation split is readable only after a logged access (see _confirmation_access)."""
    processed = processed or PROCESSED
    if split in E.CONFIRMATION_SPLITS:
        if not _confirmed_access:
            raise PermissionError(f"{split} labels are readable only through a logged confirmation access")
        path = os.path.join(processed, "confirm", f"labels_{split}.csv")
    else:
        path = os.path.join(processed, f"labels_{split}.csv")
    return pd.read_csv(path, dtype={"record": str, "beat_id": str}), path


def prediction_set(split):
    """Label-free frame of the beats that must be predicted (for validation before any label access)."""
    pos = load_positions(split)
    pos = pos[pos["predict"]].reset_index(drop=True)
    return pos.assign(aami="?", is_unit=False)[["beat_id", "record", "aami", "is_unit"]]


def _read_pred(path):
    return pd.read_csv(path, dtype={"beat_id": str, "pred": str})


def _expand(patterns):
    files = []
    for p in patterns:
        hits = sorted(glob.glob(p))
        if not hits:
            raise SystemExit(f"no prediction file matches {p}")
        files.extend(hits)
    return files


def _confirmation_access(split, reason, ids, preds):
    """Validate against the label-free prediction set, enforce the cap, then log. Returns True if labels may be read."""
    if split not in E.CONFIRMATION_SPLITS:
        return False
    if not reason:
        raise SystemExit(f"split {split} is the confirmation set: pass --confirm-reason and log the access in EVAL.md")
    pset = prediction_set(split)
    for p in preds:
        scorer.validate(p, pset)
    used = sum(1 for _ in open(ACCESS_LOG)) if os.path.exists(ACCESS_LOG) else 0
    if used >= E.CONFIRMATION_CAP:
        raise SystemExit(f"confirmation cap reached ({used}/{E.CONFIRMATION_CAP}); a further access needs a new EV version")
    os.makedirs(os.path.dirname(ACCESS_LOG), exist_ok=True)
    with open(ACCESS_LOG, "a") as f:
        f.write(json.dumps({"time": _now(), "split": split, "ids": ids, "reason": reason, "access": used + 1}) + "\n")
    return True


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _write(out, payload):
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w") as f:
        json.dump(payload, f, indent=1)
    print(f"wrote {out}")


def cmd_score(a):
    pred = _read_pred(a.pred)
    ok = _confirmation_access(a.split, a.confirm_reason, [a.id], [pred])
    labels, lpath = load_labels(a.split, _confirmed_access=ok)
    res = scorer.score(pred, labels, load_hours(a.split))
    meta = {"ev": E.EV, "split": a.split, "candidate_id": a.id, "pred_file": a.pred, "pred_sha256": sha256(a.pred),
            "labels_sha256": sha256(lpath), "time": _now(), "command": " ".join(sys.argv)}
    _write(a.out, {**meta, **res})
    pc = res["per_class"]
    print(f"{a.id} {a.split}: macro-F1 {res['macro_f1']:.4f} | " +
          " | ".join(f"{c} Se {pc[c]['sensitivity'] or 0:.3f} PPV {pc[c]['ppv'] or 0:.3f}" for c in E.CLASSES))


def cmd_compare(a):
    cf, bf = _expand(a.cand), _expand(a.base)
    cp, bp = [_read_pred(f) for f in cf], [_read_pred(f) for f in bf]
    if len(cp) != len(bp):
        raise SystemExit(f"arms need equal seed counts (got {len(cp)} and {len(bp)})")
    if len(cp) != E.N_SEEDS:
        print(f"warning: {len(cp)} seeds per arm; headline comparisons use {E.N_SEEDS}")
    ok = _confirmation_access(a.split, a.confirm_reason, [a.cand_id, a.base_id], cp + bp)
    labels, lpath = load_labels(a.split, _confirmed_access=ok)
    res = scorer.compare(cp, bp, labels, dominant_record=E.DOMINANT_RECORD.get(a.split), n_comparisons=a.n_comparisons)
    payload = {"ev": E.EV, "split": a.split, "candidate_id": a.cand_id, "baseline_id": a.base_id,
               "candidate_files": {f: sha256(f) for f in cf}, "baseline_files": {f: sha256(f) for f in bf},
               "labels_sha256": sha256(lpath), "practical_gain": E.PRACTICAL_GAIN,
               "suspicious_gain_threshold": E.SUSPICIOUS_GAIN, "time": _now(), "command": " ".join(sys.argv), **res}
    if a.split in E.CONFIRMATION_SPLITS:
        payload["confirmed"] = bool(res["delta"] > 0 and res["ci"][0] > 0)
    _write(a.out, payload)
    print(f"{a.cand_id} vs {a.base_id} on {a.split}: delta {res['delta']:+.4f} "
          f"CI{res['ci_level']:.3f} [{res['ci'][0]:+.4f}, {res['ci'][1]:+.4f}] "
          f"(without {res['dominant_record']}: {res['delta_without_dominant_record']}) -> {res['outcome']}"
          + (" | SUSPICIOUS GAIN: queue verification" if res["suspicious_gain"] else ""))


def reference_predictions(rule, positions):
    """Minimal references, using only released beat positions (never labels); one-hot probabilities.
    const_n: every beat is N. rr_rule: S when the pre-RR interval is < 0.85 x the mean of the previous (up to) 10
    pre-RR intervals of the same record, else N; it never predicts V."""
    out = []
    for _, g in positions.sort_values(["record", "sample"]).groupby("record", sort=False):
        s = g["sample"].to_numpy()
        pre = np.diff(s, prepend=np.nan)
        prev_mean = pd.Series(pre).shift(1).rolling(10, min_periods=1).mean().to_numpy()
        if rule == "const_n":
            pred = np.full(len(g), "N")
        elif rule == "rr_rule":
            pred = np.where(pre < 0.85 * prev_mean, "S", "N")
        else:
            raise SystemExit(f"unknown rule {rule}")
        out.append(pd.DataFrame({"beat_id": g["beat_id"].to_numpy(), "pred": pred, "predict": g["predict"].to_numpy()}))
    df = pd.concat(out)
    df = df.loc[df["predict"], ["beat_id", "pred"]]
    for c in E.CLASSES:
        df[f"prob_{c}"] = (df["pred"] == c).astype(float)
    return df


def cmd_reference(a):
    if a.split in E.CONFIRMATION_SPLITS:
        raise SystemExit("references are not run on the confirmation set")
    pred = reference_predictions(a.rule, load_positions(a.split))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pred.to_csv(a.out, index=False)
    print(f"wrote {a.out} ({len(pred)} rows)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="EV1 evaluation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score")
    s.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    s.add_argument("--pred", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--confirm-reason")
    s.set_defaults(fn=cmd_score)
    c = sub.add_parser("compare")
    c.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    c.add_argument("--cand", required=True, nargs="+", help="one prediction file (or glob) per seed")
    c.add_argument("--base", required=True, nargs="+")
    c.add_argument("--cand-id", required=True)
    c.add_argument("--base-id", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--n-comparisons", type=int, default=1,
                   help="m for the Bonferroni-adjusted CI when the headline pair has been replaced (EVAL.md rule 4)")
    c.add_argument("--confirm-reason")
    c.set_defaults(fn=cmd_compare)
    r = sub.add_parser("reference")
    r.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    r.add_argument("--rule", required=True, choices=["const_n", "rr_rule"])
    r.add_argument("--out", required=True)
    r.set_defaults(fn=cmd_reference)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
