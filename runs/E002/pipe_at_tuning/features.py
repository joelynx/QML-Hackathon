"""Label-free beat features, causal up to the EV1 decision boundary b_i = max(t_{i+1}, t_i + 1.0 s).

For beat i at R-peak t_i (sample index at the record's native rate fs):
  window  the MLII signal (MIT-BIH, chosen by lead name) or ECG1 (SVDB) on [t_i - PRE_S, t_i + POST_S], linearly
          interpolated onto a fine grid and bin-averaged to L points (anti-aliasing that does not depend on fs), minus
          its median, divided by its standard deviation. It ends at t_i + 0.45 s, inside the boundary.
  rel     the window minus the patient's causal template: the element-wise median of the previous TEMPLATE_N beats'
          windows of the same record (the first beat's template is itself). This is the reservoir input of every arm;
          it removes the patient's own normal morphology, which does not transfer across patients (ANOMALIES A009).
  rr      pre-RR and post-RR (the next beat is allowed by the one-beat lookahead), the means of the last 10 and 50
          pre-RR intervals (causal, including the current one), log-ratios of these, and the log of the window's
          peak-to-peak amplitude relative to the median of the previous 32 beats (causal).
Both reservoir arms consume the same windows; the rr block is shared by every arm (matched-baseline rule 1).

  python -I -m qhc.pipe.features --splits ds1 ds2s   -> runs/features/EV1/<split>.npz
"""
import argparse
import os

import numpy as np
import pandas as pd
import wfdb

from .. import evalspec as E
from ..evaluate import ROOT, load_positions
from . import pipe_revision

PRE_S, POST_S, L, FINE = 0.25, 0.45, 40, 8
TEMPLATE_N = 32
RR_NAMES = ["pre_rr", "post_rr", "avg10_rr", "log_pre_avg10", "log_post_avg10", "log_pre_post", "log_avg10_avg50",
            "log_amp_rel32"]
FEATURE_DIR = os.path.join(ROOT, "runs", "features", E.EV)
RAW = os.path.join(ROOT, "runs", "data", "raw")


def load_signal(db, rec, raw_root=RAW):
    sig, fields = wfdb.rdsamp(os.path.join(raw_root, db, rec))
    ch = fields["sig_name"].index("MLII" if db == "mitdb" else "ECG1")
    return np.nan_to_num(sig[:, ch].astype(np.float64)), float(fields["fs"])


def beat_windows(signal, samples, fs):
    """(n, L) normalised windows and (n,) raw peak-to-peak amplitudes of the bin-averaged windows."""
    width = PRE_S + POST_S
    grid = -PRE_S + (np.arange(L * FINE) + 0.5) * width / (L * FINE)
    t = np.asarray(samples, dtype=float)[:, None] + grid[None, :] * fs
    x = np.interp(t.ravel(), np.arange(len(signal)), signal).reshape(len(samples), L, FINE).mean(2)
    p2p = x.max(1) - x.min(1)
    x = x - np.median(x, 1, keepdims=True)
    return x / (x.std(1, keepdims=True) + 1e-6), p2p


def rr_features(samples, fs, p2p):
    s = np.asarray(samples, dtype=float) / fs
    n = len(s)
    if n < 2:
        return np.zeros((n, len(RR_NAMES)))
    pre = np.diff(s, prepend=np.nan)
    post = np.diff(s, append=np.nan)
    pre[0] = post[0]  # the first beat's next beat is within its boundary
    post[-1] = pre[-1]  # the last beat has no next beat: fall back to the past
    avg10 = pd.Series(pre).rolling(10, min_periods=1).mean().to_numpy(copy=True)
    avg50 = pd.Series(pre).rolling(50, min_periods=1).mean().to_numpy(copy=True)
    ref = pd.Series(p2p).shift(1).rolling(32, min_periods=1).median().to_numpy(copy=True)
    ref[0] = p2p[0]
    eps = 1e-6
    return np.c_[pre, post, avg10, np.log((pre + eps) / (avg10 + eps)), np.log((post + eps) / (avg10 + eps)),
                 np.log((pre + eps) / (post + eps)), np.log((avg10 + eps) / (avg50 + eps)),
                 np.log((p2p + eps) / (ref + eps))]


def relative_windows(win):
    tmpl = pd.DataFrame(win).shift(1).rolling(TEMPLATE_N, min_periods=1).median().to_numpy(copy=True)
    tmpl[0] = win[0]
    return win - tmpl


def record_features(signal, samples, fs):
    """Per-record feature function in the form qhc.leakcheck expects: (n, 2 L + len(RR_NAMES)) = [win | rel | rr]."""
    win, p2p = beat_windows(signal, samples, fs)
    return np.c_[win, relative_windows(win), rr_features(samples, fs, p2p)]


def build_split(split):
    pos = load_positions(split).sort_values(["record", "sample"])
    parts = []
    for rec, g in pos.groupby("record", sort=True):
        sig, fs = load_signal(g["db"].iloc[0], rec)
        assert fs == g["fs"].iloc[0]
        f = record_features(sig, g["sample"].to_numpy(), fs)
        keep = g["predict"].to_numpy()
        parts.append((g["beat_id"].to_numpy()[keep], g["record"].to_numpy()[keep], f[keep]))
    ids = np.concatenate([p[0] for p in parts])
    recs = np.concatenate([p[1] for p in parts])
    feats = np.concatenate([p[2] for p in parts]).astype(np.float32)
    os.makedirs(FEATURE_DIR, exist_ok=True)
    out = os.path.join(FEATURE_DIR, f"{split}.npz")
    np.savez_compressed(out, beat_id=ids.astype(str), record=recs.astype(str), win=feats[:, :L], rel=feats[:, L:2 * L],
                        rr=feats[:, 2 * L:], pipe_revision=pipe_revision())
    return out, len(ids)


def load_split(split):
    z = np.load(os.path.join(FEATURE_DIR, f"{split}.npz"))
    return {k: z[k] for k in ("beat_id", "record", "win", "rel", "rr")}


def main():
    ap = argparse.ArgumentParser(description="build beat features")
    ap.add_argument("--splits", nargs="+", default=["ds1"], choices=sorted(E.SPLITS))
    a = ap.parse_args()
    for s in a.splits:
        print(*build_split(s))


if __name__ == "__main__":
    main()
