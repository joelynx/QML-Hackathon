"""Headline tables (Markdown) from an EV1 comparison output; no label access.

  python -I -m qhc.pipe.tables --cmp runs/E003/compare_ds2s_headline.json --out runs/tables/headline_ds2s.md
"""
import argparse
import json
import os


def _f(x, d=4, sign=False):
    return "n/a" if x is None else (f"{x:+.{d}f}" if sign else f"{x:.{d}f}")


def _ci(ci, d=4):
    return f"[{ci[0]:+.{d}f}, {ci[1]:+.{d}f}]"


def render(r):
    p, c, b = r["primary"], r["candidate_id"], r["baseline_id"]
    out = [f"# {r['role'].capitalize()} comparison on {r['split']}: {c} vs {b}", "",
           f"Evaluation {r['scorer']['ev']}, code `{r['scorer']['code_revision']}`; {r['n_records']} records, "
           f"{r['n_units']} N/S/V units, {r['n_seeds']} seeds per arm; two-level bootstrap B = {r['n_boot']}, seed "
           f"{r['boot_seed']}; labels sha256 `{r['labels_sha256'][:16]}`; run {r['time']}.", "",
           "## Primary: macro-F1 over N/S/V (mean of per-seed values)", "",
           f"| {c} | {b} | Delta | {p['ci_level']:.0%} CI | Without {p['dominant_record']} | Outcome |",
           "|---|---|---|---|---|---|",
           f"| {_f(p['candidate_macro_f1'])} | {_f(p['baseline_macro_f1'])} | {_f(p['delta'], sign=True)} | {_ci(p['ci'])} | "
           f"{_f(p['delta_without_dominant_record'], sign=True)} | {p['outcome']} ({p['outcome_reason']}) |", ""]
    if r.get("slices"):
        sl = r["slices"]
        out += [f"## Slice family (m = {sl.get('m', len(sl['members']))}, {sl['ci_level']:.2%} intervals)", "",
                "| Member | Delta | CI | Decision |", "|---|---|---|---|"]
        out += [f"| {k} | {_f(v['delta'], sign=True)} | {_ci(v['ci'])} | {v['decision']} |" for k, v in sl["members"].items()]
        out.append("")
    out += ["## Per class (95%, descriptive)", "", f"| Class | F1 {c} | F1 {b} | Delta | CI |", "|---|---|---|---|---|"]
    out += [f"| {k} | {_f(v['candidate_f1'], 3)} | {_f(v['baseline_f1'], 3)} | {_f(v['delta'], sign=True)} | {_ci(v['ci'])} |"
            for k, v in r["per_class_f1"].items()]
    out += ["", f"| AUPRC | {c} | {b} | Delta | CI |", "|---|---|---|---|---|"]
    out += [f"| {k} | {_f(v['candidate'], 3)} | {_f(v['baseline'], 3)} | {_f(v['delta'], sign=True)} | {_ci(v['ci'])} |"
            for k, v in r["auprc"].items()]
    out += ["", "## Per arm (seed-averaged)", "",
            "| Arm | Macro-F1 per seed | N Se / PPV | S Se / PPV | V Se / PPV | VEB Se / +P / FPR | SVEB Se / +P / FPR | "
            "S-or-V flags / h | Normal beats flagged / h | Missed ectopic / h |", "|---|---|---|---|---|---|---|---|---|---|"]
    for name, key in ((c, "candidate"), (b, "baseline")):
        a = r["arms"][key]
        sa, pc = a["seed_average"], a["seed_average"]["per_class"]
        pp, rb = sa["paper_compatible"], sa["review_burden"]
        out.append(f"| {name} | {', '.join(_f(x) for x in a['per_seed_macro_f1'])} | "
                   + " | ".join(f"{_f(pc[k]['sensitivity'], 3)} / {_f(pc[k]['ppv'], 3)}" for k in "NSV") + " | "
                   + " | ".join(f"{_f(pp[k]['sensitivity'], 3)} / {_f(pp[k]['ppv'], 3)} / {_f(pp[k]['fpr'], 3)}"
                                for k in ("VEB", "SVEB"))
                   + f" | {rb['ectopic_flags_per_hour']:.0f} | {rb['normal_beats_flagged_per_hour']:.0f} | "
                     f"{rb['missed_ectopic_per_hour']:.0f} |")
    lo = sorted(r["leave_one_record_out_delta"].items(), key=lambda t: t[1])
    out += ["", "## Leave-one-record-out delta", "", "| Record left out | Delta |", "|---|---|"]
    out += [f"| {k} | {_f(v, sign=True)} |" for k, v in lo]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cmp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    with open(a.cmp) as f:
        md = render(json.load(f))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    print(f"wrote {a.out}")


if __name__ == "__main__":
    main()
