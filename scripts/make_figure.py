"""Build docs/figures/ds2s_per_class_f1.png from the logged ds2s comparison and score outputs.

Reads only the JSON files written by `qhc.evaluate` (no label file is opened, nothing is rescored):
  runs/E003/compare_ds2s_headline_EV2.json              E003 (QRC, candidate) and E002 (ESN, baseline)
  runs/E004/compare_ds2s_secondary_E003_vs_E004.json    E004 (mean-field, baseline arm)
  runs/E005/compare_ds2s_secondary_E005_vs_E003.json    E005 (separable J = 0, candidate arm)
  runs/E006/score_ds2s.json                             E006 (RR only, one deterministic run)

    .venv/Scripts/python -I scripts/make_figure.py      (from the project root)
"""
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "figures", "ds2s_per_class_f1.png")

# Colour roles (dataviz reference palette, light mode; slots 1-3 validate all-pairs for colour-vision deficiency).
SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
QRC, ESN, MF, CONTEXT = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984"


def load(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)


def arm_scores(seed_average):
    pc = seed_average["per_class"]
    return {"Macro-F1": seed_average["macro_f1"], "N F1": pc["N"]["f1"], "S F1": pc["S"]["f1"], "V F1": pc["V"]["f1"]}


def main():
    head = load("runs/E003/compare_ds2s_headline_EV2.json")
    mf = load("runs/E004/compare_ds2s_secondary_E003_vs_E004.json")
    sep = load("runs/E005/compare_ds2s_secondary_E005_vs_E003.json")
    rr = load("runs/E006/score_ds2s.json")
    assert head["candidate_id"] == "E003" and head["baseline_id"] == "E002"
    assert mf["candidate_id"] == "E003" and mf["baseline_id"] == "E004"
    assert sep["candidate_id"] == "E005" and sep["baseline_id"] == "E003"
    assert rr["candidate_id"] == "E006"

    # Rows top to bottom: (label, scores, colour)
    arms = [
        ("E003  quantum reservoir (QRC)", arm_scores(head["arms"]["candidate"]["seed_average"]), QRC),
        ("E002  echo state network (R0)", arm_scores(head["arms"]["baseline"]["seed_average"]), ESN),
        ("E004  mean-field model of E003", arm_scores(mf["arms"]["baseline"]["seed_average"]), MF),
        ("E005  E003 with J = 0 (separable)", arm_scores(sep["arms"]["candidate"]["seed_average"]), CONTEXT),
        ("E006  RR features only (1 run)", arm_scores(rr), CONTEXT),
    ]
    p, s = head["primary"], head["slices"]["members"]
    v_mf = mf["per_class_f1"]["V"]
    notes = {
        "Macro-F1": "E003 − E002: {:+.3f}\n95% CI [{:+.3f}, {:+.3f}]\nno detectable change".format(
            p["delta"], p["ci"][0], p["ci"][1]),
        "V F1": "E003 − E002: {:+.3f}\n98.75% CI [{:+.3f}, {:+.3f}]\nfavorable (slice)\nE003 − E004: {:+.4f}\n95% CI [{:+.4f}, {:+.4f}] (secondary)".format(
            s["V_f1"]["delta"], s["V_f1"]["ci"][0], s["V_f1"]["ci"][1], v_mf["delta"], v_mf["ci"][0], v_mf["ci"][1]),
        "S F1": "E003 − E002: {:+.3f}\n98.75% CI [{:+.3f}, {:+.3f}]\nno detectable change".format(
            s["S_f1"]["delta"], s["S_f1"]["ci"][0], s["S_f1"]["ci"][1]),
        "N F1": "",
    }
    metrics = ["Macro-F1", "N F1", "S F1", "V F1"]

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID,
                         "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2})
    fig, axes = plt.subplots(1, 4, figsize=(13.2, 3.9), sharey=True, facecolor=SURFACE)
    n = len(arms)
    ys = list(range(n))[::-1]
    for ax, m in zip(axes, metrics):
        ax.set_facecolor(SURFACE)
        vals = [a[1][m] for a in arms]
        lo, hi = min(vals), max(vals)
        pad = max(0.15 * (hi - lo), 0.004)
        ax.set_xlim(lo - pad, hi + 2.2 * pad)
        for y in ys:
            ax.axhline(y, color=GRID, lw=0.8, zorder=0)
        for y, (label, sc, col) in zip(ys, arms):
            ax.scatter(sc[m], y, s=70, color=col, edgecolor=SURFACE, linewidth=2, zorder=3)
            ax.annotate("{:.3f}".format(sc[m]), (sc[m], y), xytext=(7, 0), textcoords="offset points",
                        va="center", ha="left", fontsize=8.5, color=INK)
        ax.set_title(m, color=INK, fontsize=10.5, loc="left", fontweight="bold")
        ax.tick_params(axis="x", labelsize=8, length=0)
        ax.tick_params(axis="y", length=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        if notes[m]:
            ax.text(0.02, -0.16, notes[m], transform=ax.transAxes, va="top", ha="left", fontsize=8, color=INK2)
    axes[0].set_yticks(ys)
    axes[0].set_yticklabels([a[0] for a in arms], color=INK, fontsize=9)
    fig.suptitle("Test split ds2s (21 unseen patients, 47,129 N/S/V beats): F1 per arm, mean of 5 seeds "
                 "(E006: one deterministic run). Each panel has its own x-axis range.",
                 x=0.01, ha="left", fontsize=10, color=INK)
    fig.text(0.01, 0.005, "Sources: runs/E003/compare_ds2s_headline_EV2.json, runs/E004/compare_ds2s_secondary_E003_vs_E004.json, "
             "runs/E005/compare_ds2s_secondary_E005_vs_E003.json, runs/E006/score_ds2s.json\n(evaluation EV2 "
             + head["scorer"]["code_revision"] + "). Intervals: paired record-and-seed bootstrap, B = 8,000. "
             "The headline and slices are pre-registered; E004-E006 are secondary, descriptive comparisons.", fontsize=7, color=INK2, ha="left", va="bottom")
    fig.subplots_adjust(left=0.19, right=0.99, top=0.86, bottom=0.33, wspace=0.12)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=160, facecolor=SURFACE)
    print(OUT)


if __name__ == "__main__":
    main()
