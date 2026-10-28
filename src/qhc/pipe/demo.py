"""Demo: run a trained arm on one record and draw the ECG with every beat's predicted class and S/V probabilities.

  python -I -m qhc.pipe.demo --exp E003 --seed 0 --db mitdb --record 100 --start 60 --seconds 20 --out runs/demo/x.png

It shows predictions only (no reference labels), so it can be run on a test record without reading test labels.
Beat positions come from the released label-free positions file, as a QRS detector would provide them.
"""
import argparse
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from .. import evalspec as E  # noqa: E402
from ..evaluate import ROOT, load_positions  # noqa: E402
from .features import load_signal  # noqa: E402
from .run import load_artifact, pipeline_fn  # noqa: E402

COLORS = {"N": "#7a8794", "S": "#d9822b", "V": "#c23030"}


def split_of(db, rec):
    if db == "svdb":
        return "svdb"
    for s in ("ds1", "ds2s", "ds2"):
        if rec in (E.SPLITS[s][1] or []):
            return s
    raise SystemExit(f"record {rec} is not in an EV1 split")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--exp", required=True)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--db", default="mitdb", choices=["mitdb", "svdb"])
    ap.add_argument("--record", required=True)
    ap.add_argument("--start", type=float, default=60.0)
    ap.add_argument("--seconds", type=float, default=20.0)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    meta, model, ro = load_artifact(os.path.join(ROOT, "runs", a.exp, f"model_seed{a.seed}.npz"))
    pos = load_positions(split_of(a.db, a.record))
    g = pos[pos["record"] == a.record].sort_values("sample")
    sig, fs, wfs = load_signal(a.db, a.record)
    samples = g["sample"].to_numpy() * (wfs / fs)
    probs = pipeline_fn(meta, model, ro, a.db, a.record)(sig, samples, wfs)
    pred = np.array(E.CLASSES)[probs.argmax(1)]
    t0, t1 = a.start, a.start + a.seconds
    lo, hi = int(t0 * wfs), int(t1 * wfs)
    t = np.arange(lo, hi) / wfs
    in_win = (samples >= lo) & (samples < hi) & g["predict"].to_numpy()
    fig, (ax, bx) = plt.subplots(2, 1, figsize=(14, 5), sharex=True, gridspec_kw={"height_ratios": [3, 1]})
    ax.plot(t, sig[lo:hi], color="#202b33", lw=0.8)
    top = sig[lo:hi].max()
    for s, c in zip(samples[in_win], pred[in_win]):
        ax.axvline(s / wfs, color=COLORS[c], alpha=0.35 if c == "N" else 0.9, lw=1 if c == "N" else 2)
        ax.text(s / wfs, top, c, color=COLORS[c], ha="center", va="bottom", fontsize=9,
                fontweight="bold" if c != "N" else "normal")
    ax.set_ylabel("ECG (mV)")
    ax.set_title(f"{a.db} record {a.record}: {meta['arm'].upper()} arm {a.exp}, seed {a.seed} "
                 f"(predictions only; {int((pred[in_win] != 'N').sum())} of {int(in_win.sum())} beats flagged)")
    st = samples[in_win] / wfs
    bx.bar(st, probs[in_win, 1], width=0.08, color=COLORS["S"], label="P(S)")
    bx.bar(st + 0.09, probs[in_win, 2], width=0.08, color=COLORS["V"], label="P(V)")
    bx.set_ylim(0, 1)
    bx.set_ylabel("probability")
    bx.set_xlabel("time (s)")
    bx.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fig.savefig(a.out, dpi=120)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
