"""Build the write-up figures docs/figures/fig_*.png from logged outputs only.

Reads only JSON / CSV / NPZ files already written under runs/ (no label file is opened, nothing is rescored):
  runs/E003/compare_ds2s_headline_EV2.json                 E003 vs E002: headline, V/S slices, per-class F1, review burden
  runs/E004/compare_ds2s_secondary_E003_vs_E004.json       E003 vs E004 (mean-field)
  runs/E005/compare_ds2s_secondary_E005_vs_E003.json       E005 (separable, J = 0) vs E003
  runs/E007/compare_ds2s_lowdata_k5.json                   slice: readouts refitted on 5 training patients
  runs/E008/compare_ds2s_lowdata_k11.json                  slice: readouts refitted on 11 training patients
  runs/E012/compare_ds2s_secondary_E012_vs_E003.json       exact expectations vs 1,024 shots
  runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json     6-qubit variant vs E003
  runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json  Rigetti-calibrated noise simulation vs E003
  runs/E016/compare_ds2s_secondary_E003_vs_E016.json       E003 vs boosted trees
  runs/E016/compare_ds2s_secondary_E002_vs_E016.json       E002 vs boosted trees
  runs/E018/confirm_svdb.json                              external confirmation on SVDB
  runs/E013/summary.json, runs/E013/table.csv              shot sweep (DS1 out-of-fold proxy) and feature error
  runs/E012/summary.json                                   exact-expectation DS1 out-of-fold proxy (cross-check)
  runs/E019/analysis_localsim_test.json, runs/E019/analysis_features_localsim_test.npz   Braket LocalSimulator, 24 beats
  runs/E019/analysis.json, runs/E019/analysis_features.npz                               Rigetti Cepheus-1-108Q, 48 beats
  (in the E019 npz files: "hw" = Braket-executed features, "shot" = our 1,024-shot simulation, "exact" = statevector)

fig_pipeline.png and fig_circuit.png are schematics and read no data.

    .venv/Scripts/python -I scripts/make_report_figures.py      (from the project root)
"""
import csv
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
from matplotlib.transforms import blended_transform_factory  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG_DIR = os.path.join(ROOT, "docs", "figures")

# Colour roles (same as scripts/make_figure.py; pure white surface for print, purple added for hardware / Braket).
SURFACE, INK, INK2, GRID = "#ffffff", "#0b0b0b", "#52514e", "#e4e3df"
QRC, ESN, MF, CONTEXT, HW = "#2a78d6", "#eb6834", "#1baf7a", "#8a8984", "#7b4fc9"
HW_LIGHT = "#b9a3e3"
DPI = 200

plt.rcParams.update({
    "font.family": "DejaVu Sans", "mathtext.fontset": "dejavusans", "font.size": 9,
    "axes.edgecolor": INK2, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 10,
    "axes.titleweight": "bold", "axes.titlelocation": "left", "xtick.color": INK2, "ytick.color": INK2,
    "xtick.labelsize": 8.5, "ytick.labelsize": 8.5, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
    "legend.fontsize": 8.5, "legend.frameon": False,
})


def load(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)


def save(fig, name):
    out = os.path.join(FIG_DIR, name)
    fig.savefig(out, dpi=DPI, facecolor=SURFACE)
    plt.close(fig)
    print(out)


def sgn(v, nd=4):
    return "{:+.{}f}".format(v, nd).replace("-", "−")


def num(v, nd=4):
    return "{:.{}f}".format(v, nd).replace("-", "−")


def close(a, b, tol):
    assert abs(a - b) <= tol, (a, b)


# ---------------------------------------------------------------- 1. forest plot
def fig_forest(log):
    head = load("runs/E003/compare_ds2s_headline_EV2.json")
    k5 = load("runs/E007/compare_ds2s_lowdata_k5.json")
    k11 = load("runs/E008/compare_ds2s_lowdata_k11.json")
    mf = load("runs/E004/compare_ds2s_secondary_E003_vs_E004.json")
    sep = load("runs/E005/compare_ds2s_secondary_E005_vs_E003.json")
    e12 = load("runs/E012/compare_ds2s_secondary_E012_vs_E003.json")
    e14 = load("runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json")
    e15 = load("runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json")
    q16 = load("runs/E016/compare_ds2s_secondary_E003_vs_E016.json")
    e16 = load("runs/E016/compare_ds2s_secondary_E002_vs_E016.json")
    svdb = load("runs/E018/confirm_svdb.json")
    ids = [(head, "E003", "E002"), (k5, "E007-E003-k5", "E007-E002-k5"), (k11, "E008-E003-k11", "E008-E002-k11"),
           (mf, "E003", "E004"), (sep, "E005", "E003"), (e12, "E012", "E003"), (e14, "E014-n6", "E003"),
           (e15, "E015-rigetti", "E003"), (q16, "E003", "E016"), (e16, "E002", "E016"), (svdb, "E003", "E002")]
    for d, c, b in ids:
        assert d["candidate_id"] == c and d["baseline_id"] == b, (d["candidate_id"], d["baseline_id"])
    assert svdb["split"] == "svdb" and all(d["split"] == "ds2s" for d, _, _ in ids[:-1])

    def prim(d, src):
        p = d["primary"]
        return p["delta"], p["ci"][0], p["ci"][1], p["ci_level"], src + " primary"

    def pcv(d, src):
        v = d["per_class_f1"]["V"]
        return v["delta"], v["ci"][0], v["ci"][1], v["ci_level"], src + " per_class_f1.V"

    def sl(d, key, src):
        m = d["slices"]["members"][key]
        return m["delta"], m["ci"][0], m["ci"][1], d["slices"]["ci_level"], src + " slices.members." + key

    H = "runs/E003/compare_ds2s_headline_EV2.json"
    groups = [
        ("(a) Pre-registered (ds2s, 21 patients)", [
            ("QRC − ESN, macro-F1 (headline)", prim(head, H), "headline"),
            ("QRC − ESN, V F1 (slice)", sl(head, "V_f1", H), "fav"),
            ("QRC − ESN, S F1 (slice)", sl(head, "S_f1", H), ""),
            ("QRC − ESN, refit on 5 patients (E007)", sl(k5, "lowdata_k5", "runs/E007/compare_ds2s_lowdata_k5.json"), ""),
            ("QRC − ESN, refit on 11 patients (E008)", sl(k11, "lowdata_k11", "runs/E008/compare_ds2s_lowdata_k11.json"), ""),
        ]),
        ("(b) Controls (ds2s, secondary)", [
            ("QRC − mean-field (E004), macro-F1", prim(mf, "runs/E004/compare_ds2s_secondary_E003_vs_E004.json"), ""),
            ("separable (E005) − QRC, macro-F1", prim(sep, "runs/E005/compare_ds2s_secondary_E005_vs_E003.json"), ""),
            ("separable (E005) − QRC, V F1", pcv(sep, "runs/E005/compare_ds2s_secondary_E005_vs_E003.json"), ""),
        ]),
        ("(c) Depth experiments (ds2s, secondary)", [
            ("exact expectations (E012) − QRC, macro-F1", prim(e12, "runs/E012/compare_ds2s_secondary_E012_vs_E003.json"), ""),
            ("6 qubits (E014) − QRC, macro-F1", prim(e14, "runs/E014/compare_ds2s_secondary_E014n6_vs_E003.json"), ""),
            ("Rigetti noise (E015) − QRC, macro-F1", prim(e15, "runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json"), ""),
            ("Rigetti noise (E015) − QRC, V F1", pcv(e15, "runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json"), ""),
            ("QRC − boosted trees (E016), macro-F1", prim(q16, "runs/E016/compare_ds2s_secondary_E003_vs_E016.json"), ""),
            ("ESN − boosted trees (E016), macro-F1", prim(e16, "runs/E016/compare_ds2s_secondary_E002_vs_E016.json"), ""),
        ]),
        ("(d) External confirmation (SVDB, 78 records)", [
            ("QRC − ESN, macro-F1", prim(svdb, "runs/E018/confirm_svdb.json"), "headline"),
        ]),
    ]

    n_rows = sum(1 + len(r) for _, r in groups)
    fh = 0.3 * n_rows + 1.6
    fig, ax = plt.subplots(figsize=(7.4, fh))
    fig.subplots_adjust(left=0.375, right=0.685, top=1 - 0.55 / fh, bottom=1.12 / fh)
    y = 0
    yt, ylab = [], []
    heads = []
    for gname, rows in groups:
        heads.append((y, gname))
        y -= 1
        for label, (d, lo, hi, lev, src), style in rows:
            col = QRC if style == "fav" else INK
            ms = 6.5 if style in ("fav", "headline") else 5
            excl = lo > 0 or hi < 0
            ax.plot([lo, hi], [y, y], color=col, lw=1.6 if style == "fav" else 1.2, solid_capstyle="butt", zorder=2)
            ax.plot([lo, lo], [y - 0.16, y + 0.16], color=col, lw=1.0, zorder=2)
            ax.plot([hi, hi], [y - 0.16, y + 0.16], color=col, lw=1.0, zorder=2)
            marker = "D" if style == "headline" else "o"
            ax.plot(d, y, marker=marker, ms=ms, color=col, mec=SURFACE, mew=1.0, zorder=3)
            lev_txt = "" if abs(lev - 0.95) < 1e-9 else "*"
            assert lev_txt == "" or abs(lev - 0.9875) < 1e-9
            ax.text(1.03, y, "{} [{}, {}]{}".format(sgn(d), sgn(lo), sgn(hi), lev_txt), transform=ax.get_yaxis_transform(),
                    va="center", ha="left", fontsize=8.5, color=QRC if style == "fav" else INK,
                    fontweight="bold" if excl else "normal")
            yt.append(y)
            ylab.append(label)
            log.append(("fig_forest", label, "delta {:+.4f} CI [{:+.4f}, {:+.4f}] level {:g}".format(d, lo, hi, lev), src))
            y -= 1
    for yy, g in heads:
        ax.text(0.015, yy, g, transform=blended_transform_factory(fig.transFigure, ax.transData),
                va="center", ha="left", fontsize=9, fontweight="bold", color=INK)
        if yy != 0:
            ax.axhline(yy + 0.5, color=GRID, lw=0.8, zorder=0, xmin=-1.5, xmax=1.75, clip_on=False)
    ax.axvline(0, color=INK2, lw=0.9, zorder=1)
    ax.set_yticks(yt)
    ax.set_yticklabels(ylab, fontsize=8.5, color=INK)
    ax.tick_params(axis="y", length=0)
    ax.set_ylim(y + 0.4, 0.6)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(-0.21, 0.175)
    ax.set_xticks([-0.2, -0.1, 0, 0.1])
    ax.grid(axis="x", color=GRID, lw=0.6, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("Difference in F1 (first arm minus second; positive = first arm better)", fontsize=8.5)
    ax.text(1.03, 0.6, "delta [CI]", transform=ax.get_yaxis_transform(), va="bottom", ha="left", fontsize=8.5,
            color=INK2, fontweight="bold")
    fig.suptitle("Every logged comparison: paired difference with confidence interval", x=0.015, ha="left",
                 fontsize=10, fontweight="bold", color=INK)
    fig.text(0.015, 0.012, "Paired record-and-seed bootstrap, B = 8,000, 5 seeds per arm. 95% CI; * 98.75% CI (slice "
             "family, m = 4).\nBold: CI excludes 0. Blue: the one favorable pre-registered result. Diamonds: headline "
             "pair (ds2s)\nand its external confirmation (SVDB). Secondary rows are descriptive and were chosen after "
             "the\nds2s results had been seen.", fontsize=8.5, color=INK2, ha="left", va="bottom")
    save(fig, "fig_forest.png")


# ---------------------------------------------------------------- 2. Braket
def fig_braket(log):
    ls_j = load("runs/E019/analysis_localsim_test.json")
    hw_j = load("runs/E019/analysis.json")
    ls = np.load(os.path.join(ROOT, "runs/E019/analysis_features_localsim_test.npz"), allow_pickle=False)
    hw = np.load(os.path.join(ROOT, "runs/E019/analysis_features.npz"), allow_pickle=False)
    assert ls_j["devices"] == ["local:braket_sv"] and "rigetti/Cepheus-1-108Q" in hw_j["devices"][0]
    assert ls["hw"].shape == (ls_j["n_beats_complete"], 220) and hw["hw"].shape == (hw_j["n_beats_complete"], 220)
    zz_idx = np.array([55 * k + j for k in range(4) for j in range(10, 55)])
    z_idx = np.array([55 * k + j for k in range(4) for j in range(10)])

    fig = plt.figure(figsize=(7.4, 6.0))
    gs = fig.add_gridspec(1, 2, wspace=0.32, left=0.09, right=0.98, top=0.86, bottom=0.40)
    gs2 = fig.add_gridspec(1, 1, left=0.36, right=0.95, top=0.235, bottom=0.085)
    panels = [
        (fig.add_subplot(gs[0, 0]), ls, ls_j, "(a) Braket LocalSimulator, {} beats".format(ls_j["n_beats_complete"]),
         "LocalSimulator feature (1,024 shots)", "runs/E019/analysis_localsim_test.json",
         "{} beats, end-to-end dry run".format(ls_j["n_beats_complete"])),
        (fig.add_subplot(gs[0, 1]), hw, hw_j, "(b) Rigetti Cepheus-1-108Q, {} beats".format(hw_j["n_beats_complete"]),
         "Hardware feature (1,024 shots)", "runs/E019/analysis.json",
         "{} beats, one QPU task".format(hw_j["n_beats_complete"])),
    ]
    for ax, z, j, title, ylabel, src, sub in panels:
        H, R = z["hw"].astype(np.float64), z["exact"].astype(np.float64)
        # cross-check the logged numbers against the logged arrays (no labels involved)
        close(np.abs(H - R).mean(), j["vs_exact"]["mean_abs_diff"], 1e-6)
        close(np.corrcoef(H.ravel(), R.ravel())[0, 1], j["vs_exact"]["pooled_corr"], 1e-6)
        slope, icpt = np.polyfit(R[:, zz_idx].ravel(), H[:, zz_idx].ravel(), 1)
        close(slope, j["vs_exact"]["zz_shrink_slope"], 1e-6)
        ax.scatter(R[:, z_idx].ravel(), H[:, z_idx].ravel(), s=3, color=CONTEXT, alpha=0.45, lw=0,
                   label=r"$\langle Z_q\rangle$ (10 per snapshot)", rasterized=True)
        ax.scatter(R[:, zz_idx].ravel(), H[:, zz_idx].ravel(), s=3, color=HW, alpha=0.30, lw=0,
                   label=r"$\langle Z_qZ_r\rangle$ (45 per snapshot)", rasterized=True)
        xs = np.array([-1.05, 1.05])
        ax.plot(xs, xs, color=INK2, lw=0.9, ls="--", label="identity")
        ax.plot(xs, slope * xs + icpt, color=INK, lw=1.3, label=r"fit to $\langle Z_qZ_r\rangle$")
        ax.set_xlim(-1.05, 1.05)
        ax.set_ylim(-1.05, 1.05)
        ax.set_aspect("equal")
        ax.set_xticks([-1, -0.5, 0, 0.5, 1])
        ax.set_yticks([-1, -0.5, 0, 0.5, 1])
        ax.grid(color=GRID, lw=0.6)
        ax.set_axisbelow(True)
        ax.set_title(title, fontsize=9.5)
        ax.set_xlabel("Exact simulation feature")
        ax.set_ylabel(ylabel)
        v = j["vs_exact"]
        ax.text(0.04, 0.96, "mean abs. difference {}\npooled correlation {}\nZZ fit slope {}".format(
            num(v["mean_abs_diff"], 4 if v["mean_abs_diff"] < 0.1 else 3), num(v["pooled_corr"], 3 if v["pooled_corr"] > 0.9 else 2),
            num(v["zz_shrink_slope"], 2)), transform=ax.transAxes, va="top", ha="left", fontsize=8.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.3", fc=SURFACE, ec=GRID, lw=0.6))
        for k in ("mean_abs_diff", "pooled_corr", "zz_shrink_slope"):
            log.append(("fig_braket", title + " " + k, "{:.6f}".format(v[k]), src + " vs_exact." + k))
    h, l = panels[1][0].get_legend_handles_labels()
    fig.legend(h, l, loc="center", ncol=4, bbox_to_anchor=(0.53, 0.305), markerscale=3.5, handlelength=1.6,
               columnspacing=1.0)

    # (c) mean absolute difference from exact simulation
    ax = fig.add_subplot(gs2[0, 0])
    shot = hw_j["shot_vs_exact_mean_abs_diff"]
    close(np.abs(hw["shot"].astype(np.float64) - hw["exact"].astype(np.float64)).mean(), shot, 1e-6)
    bars = [("1,024-shot simulation (shot noise only)", shot, QRC,
             "runs/E019/analysis.json shot_vs_exact_mean_abs_diff (48 beats)"),
            ("Braket LocalSimulator", ls_j["vs_exact"]["mean_abs_diff"], HW_LIGHT,
             "runs/E019/analysis_localsim_test.json vs_exact.mean_abs_diff (24 beats)"),
            ("Rigetti Cepheus-1-108Q (hardware)", hw_j["vs_exact"]["mean_abs_diff"], HW,
             "runs/E019/analysis.json vs_exact.mean_abs_diff (48 beats)")]
    ys = np.arange(len(bars))[::-1]
    for yy, (lab, val, col, src) in zip(ys, bars):
        ax.barh(yy, val, color=col, height=0.62)
        ax.text(val + 0.004, yy, num(val, 4 if val < 0.1 else 3), va="center", ha="left", fontsize=8.5, color=INK)
        log.append(("fig_braket", "(c) " + lab, "{:.6f}".format(val), src))
    ax.set_yticks(ys)
    ax.set_yticklabels([b[0] for b in bars], color=INK)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 0.40)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Mean absolute difference (features range from −1 to 1)")
    ax.set_title("(c) Mean absolute difference from exact simulation", fontsize=9.5, x=-0.46, ha="left")
    fig.suptitle("From simulator to QPU: E003's circuits, feature by feature", x=0.015,
                 y=0.985, ha="left", fontsize=10, fontweight="bold", color=INK, va="top")
    fig.text(0.015, 0.948, "Each point is one feature of one beat. (a) 24-beat end-to-end dry run; (b) one real QPU "
             "task.", fontsize=8.5, color=INK2, ha="left", va="top")
    save(fig, "fig_braket.png")


# ---------------------------------------------------------------- 3. shots and noise
def fig_shots_noise(log):
    s13 = load("runs/E013/summary.json")
    s12 = load("runs/E012/summary.json")
    with open(os.path.join(ROOT, "runs/E013/table.csv")) as f:
        table = {r["shots"]: r for r in csv.DictReader(f)}
    keys = ["64", "256", "1024", "4096", "exact (E012)"]
    f1 = [s13["rows"][k]["lam0.1"]["mean"]["macro_f1"] for k in keys]
    seeds = [[s13["rows"][k]["lam0.1"]["per_seed"][str(i)]["macro_f1"] for i in range(5)] for k in keys]
    err = [s13["rows"][k]["feature_error_vs_exact_seed0"]["mae_all"] for k in keys]
    close(f1[-1], s12["ds1_oof_lam0.1"]["mean"]["macro_f1"], 1e-9)  # exact row = E012's own summary
    for k, a, e in zip(keys, f1, err):
        close(a, float(table[k]["mean_macro_f1_lam0.1"]), 6e-5)
        close(e, float(table[k]["feature_mae_vs_exact_seed0"]), 6e-6)
        log.append(("fig_shots_noise", "(a) shots {}: DS1 OOF macro-F1 (5-seed mean)".format(k), "{:.4f}".format(a),
                    "runs/E013/summary.json rows[{}].lam0.1.mean.macro_f1".format(k)))
        log.append(("fig_shots_noise", "(a) shots {}: feature error (seed 0)".format(k), "{:.5f}".format(e),
                    "runs/E013/summary.json rows[{}].feature_error_vs_exact_seed0.mae_all".format(k)))
    xs = [64, 256, 1024, 4096, 16384]

    fig = plt.figure(figsize=(7.4, 3.9))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.7, 1.0], hspace=0.12, wspace=0.62,
                          left=0.125, right=0.965, top=0.85, bottom=0.25)
    a1 = fig.add_subplot(gs[0, 0])
    a2 = fig.add_subplot(gs[1, 0], sharex=a1)
    for x, ss in zip(xs, seeds):
        a1.scatter([x] * 5, ss, s=8, color=QRC, alpha=0.35, lw=0, zorder=2)
    a1.plot(xs[:4], f1[:4], color=QRC, lw=1.5, marker="o", ms=5, zorder=3)
    a1.plot(xs[3:], f1[3:], color=QRC, lw=1.0, ls=":", zorder=3)
    a1.plot(xs[4], f1[4], marker="D", ms=5.5, color=QRC, mec=SURFACE, zorder=4)
    for x, v in zip(xs, f1):
        a1.annotate(num(v, 4), (x, v), xytext=(0, -13), textcoords="offset points", ha="center", fontsize=8.5,
                    color=INK)
    a1.set_ylim(0.632, 0.682)
    a1.set_ylabel("DS1 out-of-fold\nmacro-F1")
    a1.set_title("(a) Shots per circuit (E013, DS1 proxy)", fontsize=9.5)
    a1.grid(axis="y", color=GRID, lw=0.6)
    a1.tick_params(axis="x", labelbottom=False)
    a2.plot(xs[:4], err[:4], color=INK2, lw=1.3, marker="o", ms=4)
    a2.plot(xs[3:], err[3:], color=INK2, lw=1.0, ls=":")
    a2.plot(xs[4], err[4], marker="D", ms=4.5, color=INK2)
    a2.set_ylim(0, 0.08)
    a2.set_yticks([0, 0.04, 0.08])
    a2.set_ylabel("feature\nerror")
    a2.grid(axis="y", color=GRID, lw=0.6)
    a2.set_xscale("log", base=2)
    a2.set_xticks(xs)
    a2.set_xticklabels(["64", "256", "1,024", "4,096", "exact"])
    a2.minorticks_off()
    a2.set_xlim(45, 23000)
    a2.set_xlabel("Shots per circuit (log scale)")
    for x, v in zip(xs[:4], err[:4]):
        a2.annotate(num(v, 4), (x, v), xytext=(5, 3), textcoords="offset points", ha="left", fontsize=8.5, color=INK2)

    # (b) V F1 per arm
    head = load("runs/E003/compare_ds2s_headline_EV2.json")
    mf = load("runs/E004/compare_ds2s_secondary_E003_vs_E004.json")
    sep = load("runs/E005/compare_ds2s_secondary_E005_vs_E003.json")
    e15 = load("runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json")
    q16 = load("runs/E016/compare_ds2s_secondary_E003_vs_E016.json")
    vf = lambda d, arm: d["arms"][arm]["seed_average"]["per_class"]["V"]["f1"]  # noqa: E731
    arms = [
        ("ESN (E002)", vf(head, "baseline"), ESN, "runs/E003/compare_ds2s_headline_EV2.json arms.baseline"),
        ("QRC (E003)", vf(head, "candidate"), QRC, "runs/E003/compare_ds2s_headline_EV2.json arms.candidate"),
        ("mean-field (E004)", vf(mf, "baseline"), MF, "runs/E004/compare_ds2s_secondary_E003_vs_E004.json arms.baseline"),
        ("separable, J = 0 (E005)", vf(sep, "candidate"), CONTEXT, "runs/E005/compare_ds2s_secondary_E005_vs_E003.json arms.candidate"),
        ("QRC + Rigetti noise (E015)", vf(e15, "candidate"), HW, "runs/E015/compare_ds2s_secondary_E015rigetti_vs_E003.json arms.candidate"),
        ("boosted trees (E016)", vf(q16, "baseline"), CONTEXT, "runs/E016/compare_ds2s_secondary_E003_vs_E016.json arms.baseline"),
    ]
    b = fig.add_subplot(gs[:, 1])
    ys = np.arange(len(arms))[::-1]
    for yy, (lab, v, col, src) in zip(ys, arms):
        b.barh(yy, v, color=col, height=0.64)
        b.text(v + 0.012, yy, num(v, 3), va="center", ha="left", fontsize=8.5, color=INK)
        log.append(("fig_shots_noise", "(b) V F1 " + lab, "{:.4f}".format(v), src + ".seed_average.per_class.V.f1"))
    b.set_yticks(ys)
    b.set_yticklabels([a[0] for a in arms], color=INK)
    b.tick_params(axis="y", length=0)
    b.spines["left"].set_visible(False)
    b.set_xlim(0, 1.12)
    b.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    b.grid(axis="x", color=GRID, lw=0.6)
    b.set_axisbelow(True)
    b.set_xlabel("V-class F1 on ds2s (mean of 5 seeds)")
    b.set_title("(b) V-class F1 by arm (ds2s)", fontsize=9.5)
    fig.suptitle("Shot noise, device noise and V-class F1",
                 x=0.015, ha="left", fontsize=10, fontweight="bold", color=INK)
    fig.text(0.015, 0.01, "(a) Proxy: DS1 out-of-fold, λ = 0.1; line = 5-seed mean, dots = seeds; feature error = mean "
             "absolute difference\nfrom exact features (seed 0). (b) Full evaluation on ds2s, seed means; descriptive "
             "(E015, E016 are secondary).", fontsize=8.5, color=INK2, ha="left", va="bottom")
    save(fig, "fig_shots_noise.png")


# ---------------------------------------------------------------- 4. review burden
def fig_review_burden(log):
    head = load("runs/E003/compare_ds2s_headline_EV2.json")
    q = head["arms"]["candidate"]["seed_average"]["review_burden"]
    e = head["arms"]["baseline"]["seed_average"]["review_burden"]
    rows = [("S-or-V flags", "ectopic_flags_per_hour"), ("Normal beats flagged", "normal_beats_flagged_per_hour"),
            ("Missed ectopic beats", "missed_ectopic_per_hour")]
    fig, ax = plt.subplots(figsize=(7.2, 2.7))
    fig.subplots_adjust(left=0.22, right=0.97, top=0.80, bottom=0.2)
    ys = np.arange(len(rows))[::-1] * 1.0
    hgt = 0.36
    src = "runs/E003/compare_ds2s_headline_EV2.json arms.{}.seed_average.review_burden."
    for yy, (lab, key) in zip(ys, rows):
        for off, val, col, name, arm in ((hgt / 2, e[key], ESN, "ESN (E002)", "baseline"),
                                         (-hgt / 2, q[key], QRC, "QRC (E003)", "candidate")):
            ax.barh(yy + off, val, height=hgt, color=col, label=name if yy == ys[0] else None)
            ax.text(val + 8, yy + off, "{:.0f}".format(val), va="center", ha="left", fontsize=8.5, color=INK)
            log.append(("fig_review_burden", "{} {}".format(lab, name), "{:.3f}".format(val), src.format(arm) + key))
    ax.set_yticks(ys)
    ax.set_yticklabels([r[0] for r in rows], color=INK)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 900)
    ax.grid(axis="x", color=GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.set_xlabel("Beats per hour of recording (ds2s, {:.2f} h, mean of 5 seeds)".format(q["hours"]))
    ax.legend(loc="lower right", ncol=1)
    fig.suptitle("Review burden: fewer flags, but more missed ectopic beats", x=0.015, ha="left", fontsize=10,
                 fontweight="bold", color=INK)
    fig.text(0.015, 0.865, "Lower is better in every row. Descriptive, at each arm's selected operating point.",
             fontsize=8.5, color=INK2, ha="left")
    log.append(("fig_review_burden", "hours", "{:.4f}".format(q["hours"]), src.format("candidate") + "hours"))
    save(fig, "fig_review_burden.png")


# ---------------------------------------------------------------- 5. pipeline schematic
def box(ax, x, y, w, h, text, fc, ec, fs=8.5, bold_first=False, lw=1.0):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.08", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=INK, linespacing=1.25)


def arrow(ax, p0, p1, col=INK2):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=10, color=col, lw=1.1,
                                 shrinkA=0, shrinkB=0))


def fig_pipeline():
    W, Hh = 7.5, 3.2
    fig = plt.figure(figsize=(W, Hh))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, Hh)
    ax.axis("off")
    NEU, NEU_E = "#f1f0ec", "#a9a7a1"
    yc, h = 2.18, 0.95
    b1 = (0.08, 1.30)
    b2 = (1.56, 1.38)
    b3 = (3.12, 1.55)
    box(ax, b1[0], yc - h / 2, b1[1], h, "ECG record\n(lead MLII,\n360 Hz)", NEU, NEU_E)
    box(ax, b2[0], yc - h / 2, b2[1], h, "Beat window\n−0.25 s … +0.45 s,\n40 bins", NEU, NEU_E)
    box(ax, b3[0], yc - h / 2, b3[1], h, "Patient-relative\nwindow (minus median\nof the patient's\nprevious 32 beats)",
        NEU, NEU_E)
    arrow(ax, (b1[0] + b1[1], yc), (b2[0], yc))
    arrow(ax, (b2[0] + b2[1], yc), (b3[0], yc))
    # interchangeable reservoir pair
    rx, rw, rh = 5.12, 2.26, 0.58
    qy, ey = 2.30, 1.48
    ax.add_patch(FancyBboxPatch((rx - 0.08, ey - 0.10), rw + 0.16, qy + rh - ey + 0.20, boxstyle="round,pad=0,rounding_size=0.1",
                                fc="none", ec=INK2, lw=0.9, ls=(0, (3, 2))))
    box(ax, rx, qy, rw, rh, "Quantum reservoir: 10 qubits,\n4 input steps, 1,024 shots\n→ 220 features",
        "#dbe8f8", QRC, lw=1.3)
    box(ax, rx, ey, rw, rh, "Classical reservoir (ESN):\n55 units, 4 steps\n→ 220 features", "#fbe1d6", ESN, lw=1.3)
    ax.text(rx + rw / 2, (qy + ey + rh) / 2, "or", ha="center", va="center", fontsize=8.5, color=INK2, style="italic")
    ax.text(rx - 0.18, ey - 0.06, "swap one box, keep everything else identical", ha="right", va="center",
            fontsize=8.5, color=INK2, style="italic")
    arrow(ax, (b3[0] + b3[1], yc + 0.08), (rx, qy + rh / 2))
    arrow(ax, (b3[0] + b3[1], yc - 0.08), (rx, ey + rh / 2))
    # bottom row
    by, bh = 0.10, 0.74
    c1, c2, c3 = (0.55, 2.05), (3.10, 2.35), (5.95, 1.35)
    box(ax, c1[0], by, c1[1], bh, "220 reservoir features\n+ 8 RR-interval features", NEU, NEU_E)
    box(ax, c2[0], by, c2[1], bh, "Class-balanced logistic readout\n(the only trained part)", "#f3eedf", INK2, lw=1.2)
    box(ax, c3[0], by, c3[1], bh, "N / S / V\nper beat", NEU, NEU_E)
    arrow(ax, (c1[0] + c1[1], by + bh / 2), (c2[0], by + bh / 2))
    arrow(ax, (c2[0] + c2[1], by + bh / 2), (c3[0], by + bh / 2))
    # elbow from the reservoir pair down to the first box of the bottom row
    xm, ytop, yel = rx + rw / 2, ey - 0.10, 1.10
    xa = c1[0] + c1[1] / 2
    ax.plot([xm, xm, xa], [ytop, yel, yel], color=INK2, lw=1.1, solid_capstyle="butt")
    arrow(ax, (xa, yel), (xa, by + bh))
    save(fig, "fig_pipeline.png")


# ---------------------------------------------------------------- 6. circuit schematic
def fig_circuit():
    W, Hh = 7.5, 3.4
    fig = plt.figure(figsize=(W, Hh))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, Hh)
    ax.axis("off")
    n = 10
    top, dy = 2.50, 0.212
    ys = [top - i * dy for i in range(n)]
    x0, x1 = 0.48, 5.30
    for i, y in enumerate(ys):
        ax.text(0.12, y, r"$q_{%d}$" % i, ha="left", va="center", fontsize=8.5, color=INK)
        ax.plot([x0, x1], [y, y], color=INK2, lw=0.8, zorder=0)
    bh = 0.17
    # encoding column
    ex, ew = 0.88, 0.95
    for i, y in enumerate(ys):
        ax.add_patch(Rectangle((ex, y - bh / 2), ew, bh, fc="#dbe8f8", ec=QRC, lw=0.9, zorder=2))
        ax.text(ex + ew / 2, y, r"RY$(s\cdot x_{%d})$" % i, ha="center", va="center", fontsize=8.5, color=INK, zorder=3)
    # ZZ block
    zx, zw = 2.20, 1.62
    yb, yt = ys[-1] - bh / 2 - 0.02, ys[0] + bh / 2 + 0.02
    ax.add_patch(FancyBboxPatch((zx, yb), zw, yt - yb, boxstyle="round,pad=0,rounding_size=0.06", fc="#ece6f8", ec=HW,
                                lw=1.1, zorder=2))
    ax.text(zx + zw / 2, (yb + yt) / 2, "ZZ couplings\non a ring\n\n" + r"$\exp(-i\,\Sigma\,J_{qr}Z_qZ_r)$",
            ha="center", va="center", fontsize=8.5, color=INK, zorder=3, linespacing=1.3)
    # RX column
    rx, rw = 4.02, 0.62
    for y in ys:
        ax.add_patch(Rectangle((rx, y - bh / 2), rw, bh, fc="#f1f0ec", ec=INK2, lw=0.9, zorder=2))
        ax.text(rx + rw / 2, y, r"RX$(h)$", ha="center", va="center", fontsize=8.5, color=INK, zorder=3)
    # depth bracket under ZZ + RX
    bx0, bx1, by = zx - 0.06, rx + rw + 0.06, yb - 0.10
    ax.plot([bx0, bx0, bx1, bx1], [by + 0.06, by, by, by + 0.06], color=INK, lw=1.0)
    ax.text((bx0 + bx1) / 2, by - 0.13, "× depth (2)", ha="center", va="center", fontsize=9, color=INK,
            fontweight="bold")
    # encoding label under RY
    ax.plot([ex, ex, ex + ew, ex + ew], [by + 0.06, by, by, by + 0.06], color=INK2, lw=0.9)
    ax.text(ex + ew / 2, by - 0.13, "encode 10 samples", ha="center", va="center", fontsize=8.5, color=INK2)
    # measurement
    mx, mw = 4.88, 0.34
    for y in ys:
        ax.add_patch(Rectangle((mx, y - bh / 2), mw, bh, fc=SURFACE, ec=INK, lw=0.9, zorder=2))
        th = np.linspace(np.pi * 0.15, np.pi * 0.85, 20)
        cx, cy, r = mx + mw / 2, y - bh / 2 + 0.03, 0.11
        ax.plot(cx + r * np.cos(th), cy + 0.9 * r * np.sin(th) * 0.9, color=INK, lw=0.7, zorder=3)
        ax.plot([cx, cx + 0.08], [cy, cy + 0.11], color=INK, lw=0.7, zorder=3)
    ax.text(5.42, (yb + yt) / 2 + 0.38, r"Measure $\langle Z_q\rangle$ and $\langle Z_qZ_r\rangle$", ha="left",
            va="center", fontsize=9, color=INK)
    ax.text(5.42, (yb + yt) / 2 + 0.02, "from 1,024 shots:\n10 + 45 = 55 values per\nsnapshot (end of circuit k)", ha="left", va="center",
            fontsize=8.5, color=INK2, linespacing=1.3)
    # top note
    ax.text(0.12, 3.24, "One input step of the quantum reservoir (10 qubits)", ha="left", va="center", fontsize=10,
            fontweight="bold", color=INK)
    ax.text(0.12, 2.96, "Repeated for 4 input steps (data re-uploading); snapshot after step k = separate circuit k; "
            "4 × 55 = 220 features.", ha="left", va="center", fontsize=8.5, color=INK2)
    ax.text(0.12, 2.76, r"Each circuit starts in $|0\cdots0\rangle$; one step is drawn.", ha="left", va="center",
            fontsize=8.5, color=INK2)
    save(fig, "fig_circuit.png")


def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    log = []
    fig_forest(log)
    fig_braket(log)
    fig_shots_noise(log)
    fig_review_burden(log)
    fig_pipeline()
    fig_circuit()
    print("\nNumbers plotted (figure | item | value | source):")
    for row in log:
        print(" | ".join(row).replace("−", "-"))


if __name__ == "__main__":
    main()
