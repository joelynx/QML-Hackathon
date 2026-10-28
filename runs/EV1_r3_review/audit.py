"""Read-only EV1 r3 review probes. Real SVDB annotations/labels must remain unopened.

Run from the project root:
  .venv/Scripts/python.exe -I -B runs/EV1_r3_review/audit.py
"""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

import numpy as np
import pandas as pd

from qhc import evaluate as ev, evalspec as E, scorer

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PROC = ROOT / "runs/data/processed/EV1"
REPORT = {}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def labels(spec):
    return pd.DataFrame(
        [(f"x:{r}:{i}", r, c, c in E.CLASSES)
         for r, seq in spec.items() for i, c in enumerate(seq)],
        columns=["beat_id", "record", "aami", "is_unit"],
    )


def predictions(lab, chars):
    p = pd.DataFrame({"beat_id": lab.beat_id, "pred": list(chars)})
    for c in E.CLASSES:
        p[f"prob_{c}"] = p.pred.eq(c).astype(float)
    return p


# Fail closed on any read of the real SVDB labels or raw annotations, including hashing.
def audit_hook(event, args):
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    path = Path(args[0]).resolve()
    if path == (PROC / "confirm/labels_svdb.csv").resolve() or (
        path.parent == (ROOT / "runs/data/raw/svdb").resolve() and path.suffix == ".atr"
    ):
        raise RuntimeError("Review must not open real SVDB labels/annotations")


def main():
    import sys
    sys.addaudithook(audit_hook)
    started = time.perf_counter()
    paths = sorted((ROOT / "src/qhc").glob("*.py"))
    REPORT["source_revision"] = hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()[:16]
    REPORT["source_files"] = {p.name: sha(p) for p in paths}
    REPORT["fixture_revision"] = sha(ROOT / "tests/test_scorer.py")[:16]
    REPORT["eval_sha256"] = sha(ROOT / "EVAL.md")
    manifest = json.loads((PROC / "manifest.json").read_text())
    checks = {name: sha(PROC / name) == value for name, value in manifest["outputs"].items()
              if not name.startswith("confirm/")}
    REPORT["processed_hashes"] = checks
    assert all(checks.values())

    # Verify MIT-BIH raw files against the downloaded checksum list; SVDB labels stay closed.
    raw = ROOT / "runs/data/raw/mitdb"
    checked, failed = 0, []
    for line in (raw / "SHA256SUMS.txt").read_text().splitlines():
        digest, filename = line.split(maxsplit=1)
        path = raw / filename.lstrip("*")
        if path.exists() and path.suffix in (".hea", ".atr", ".dat"):
            checked += 1
            if sha(path) != digest:
                failed.append(path.name)
    REPORT["mitdb_raw_hashes"] = {"checked": checked, "failed": failed}
    assert not failed

    lab1 = pd.read_csv(PROC / "labels_ds1.csv", dtype={"record": str})
    other = lab1[lab1.aami.eq("other")]
    REPORT["ds1_other"] = {"count": len(other), "symbols": other.symbol.value_counts().to_dict(),
                           "records": other.record.value_counts().to_dict()}
    pos = pd.read_csv(PROC / "positions_ds1.csv", dtype={"record": str})
    affected = {}
    for rec in other.record.unique():
        g = pos[pos.record.eq(rec)].sort_values("sample")
        unusual = set(other.loc[other.record.eq(rec), "beat_id"])
        cleaned = g[~g.beat_id.isin(unusual)]
        original_pre = dict(zip(g.beat_id, g["sample"].diff()))
        cleaned_pre = dict(zip(cleaned.beat_id, cleaned["sample"].diff()))
        original_post = dict(zip(g.beat_id, g["sample"].shift(-1) - g["sample"]))
        cleaned_post = dict(zip(cleaned.beat_id, cleaned["sample"].shift(-1) - cleaned["sample"]))
        ids = lab1.loc[lab1.record.eq(rec) & lab1.is_unit, "beat_id"]
        pre = [i for i in ids if original_pre[i] != cleaned_pre[i]]
        post = [i for i in ids if original_post[i] != cleaned_post[i]]
        affected[rec] = {"scored_beats_with_changed_pre_rr": len(pre),
                         "scored_beats_with_changed_post_rr": len(post),
                         "example_ids": sorted(set(pre + post))[:8]}
    REPORT["removing_flutter_positions_effect"] = affected

    # Independently reconstruct the reference metric from the label/prediction pairs.
    lab2 = pd.read_csv(PROC / "labels_ds2s.csv", dtype={"record": str})
    refs = {}
    for rule in ("const_n", "rr_rule"):
        pred = pd.read_csv(ROOT / f"runs/EV1_reference/pred_{rule}_ds2s.csv")
        merged = lab2[lab2.is_unit].merge(pred, on="beat_id", validate="one_to_one")
        fs = []
        for c in E.CLASSES:
            tp = ((merged.aami == c) & (merged.pred == c)).sum()
            den = (merged.aami == c).sum() + (merged.pred == c).sum()
            fs.append(float(2 * tp / den) if den else 1.0)
        refs[rule] = float(np.mean(fs))
    REPORT["independent_reference_scores"] = refs
    REPORT["reference_delta"] = refs["rr_rule"] - refs["const_n"]
    REPORT["ds2s_S_share_232"] = float(((lab2.record == "232") & (lab2.aami == "S")).sum() / lab2.aami.eq("S").sum())

    # Show the default slice level, explicit correction, and missing report fields on synthetic data.
    lab = labels({f"r{i}": "NNNSVVFQ" for i in range(6)})
    good = predictions(lab, lab.aami.where(lab.is_unit, "V"))
    bad = predictions(lab, "N" * len(lab))
    default = scorer.compare([good] * 5, [bad] * 5, lab)
    adjusted = scorer.compare([good] * 5, [bad] * 5, lab, n_comparisons=4)
    REPORT["slice_levels"] = {"default": default["ci_level"], "default_draws": default["n_boot"],
                              "explicit_m4": adjusted["ci_level"], "m4_draws": adjusted["n_boot"]}
    REPORT["compare_output_fields"] = sorted(default)
    REPORT["compare_per_class_fields"] = sorted(default["per_class"]["S"])
    REPORT["compare_missing_required_diagnostics"] = [
        "per-class sensitivity and PPV", "record-averaged sensitivity and PPV",
        "false flags per hour", "F/Q prediction distribution", "per-record confusion matrices",
    ]

    # A real command, directed entirely at temporary synthetic confirmation files.
    real_log = Path(ev.ACCESS_LOG)
    before = real_log.read_bytes() if real_log.exists() else None
    with tempfile.TemporaryDirectory(prefix="synthetic_", dir=OUT) as tmp:
        tmp = Path(tmp)
        proc = tmp / "processed"
        (proc / "confirm").mkdir(parents=True)
        lab.to_csv(proc / "confirm/labels_svdb.csv", index=False)
        lab.assign(sample=np.arange(len(lab)), fs=128, predict=True).to_csv(proc / "positions_svdb.csv", index=False)
        pd.DataFrame({"record": lab.record.unique(), "duration_s": 1800}).to_csv(proc / "records_svdb.csv", index=False)
        good.to_csv(tmp / "good.csv", index=False)
        bad.to_csv(tmp / "bad.csv", index=False)
        capture = io.StringIO()
        args = ["compare", "--split", "svdb", "--cand", *([str(tmp / "good.csv")] * 5),
                "--base", *([str(tmp / "bad.csv")] * 5), "--cand-id", "synthetic_candidate",
                "--base-id", "synthetic_baseline", "--confirm-reason", "synthetic review only",
                "--out", str(tmp / "comparison.json")]
        with patch.object(ev, "PROCESSED", str(proc)), patch.object(ev, "ACCESS_LOG", str(tmp / "access.jsonl")), contextlib.redirect_stdout(capture):
            ev.main(args)
        result = json.loads((tmp / "comparison.json").read_text())
        REPORT["synthetic_confirmation"] = {
            "confirmed": result["confirmed"], "reported_n_seeds": result["n_seeds"],
            "distinct_candidate_files": len(result["candidate_files"]),
            "distinct_baseline_files": len(result["baseline_files"]),
            "warning_emitted": "warning" in capture.getvalue(),
            "accesses": len((tmp / "access.jsonl").read_text().splitlines()),
            "has_nonunit_predictions": "nonunit_predictions" in result,
            "has_per_record_confusions": "per_record" in result,
            "has_sensitivity": "sensitivity" in result["per_class"]["S"],
        }
        with patch.object(ev, "PROCESSED", str(proc)), patch.object(ev, "ACCESS_LOG", str(tmp / "one_seed_access.jsonl")), contextlib.redirect_stdout(capture):
            ev.main(["compare", "--split", "svdb", "--cand", str(tmp / "good.csv"), "--base", str(tmp / "bad.csv"),
                     "--cand-id", "one_seed_candidate", "--base-id", "one_seed_baseline", "--confirm-reason", "synthetic review only",
                     "--out", str(tmp / "one_seed.json")])
        one_seed = json.loads((tmp / "one_seed.json").read_text())
        REPORT["one_seed_confirmation"] = {"confirmed": one_seed["confirmed"], "n_seeds": one_seed["n_seeds"]}
    after = real_log.read_bytes() if real_log.exists() else None
    assert before == after
    REPORT["real_confirmation_log_unchanged"] = True
    REPORT["real_svdb_labels_or_annotations_read"] = False
    REPORT["small_positive_gain_label"] = scorer.decide(0.01, 0.005, 0.015)
    paper = ROOT / "papers/Automatic Classification of Heartbeats Using ECG.pdf"
    REPORT["supplied_paper_sha256"] = sha(paper)
    # Independently transcribed from the visually inspected Table II (PDF page 2).
    paper_counts = {
        "ds1": {"N": 38104 + 3949 + 3783 + 16 + 16, "S": 808 + 100 + 32 + 2,
                "V": 3682 + 105, "F": 415, "Q": 8},
        "ds2": {"N": 36444 + 4125 + 3476 + 213, "S": 1736 + 50 + 51,
                "V": 3220 + 1, "F": 388, "Q": 7},
    }
    count_checks = {}
    for split, published in paper_counts.items():
        actual = {c: sum(manifest["splits"][split][part].get(c, 0)
                         for part in ("class_counts", "predicted_nonunit_by_aami", "not_predicted_by_aami"))
                  for c in published}
        count_checks[split] = {"paper": published, "current_annotations_before_edge_exclusions": actual,
                               "current_minus_paper": {c: actual[c] - published[c] for c in published}}
    REPORT["paper_table_II_reconciliation"] = count_checks
    ec57_lab = labels({"A": "NSVF"})
    ec57_score = scorer.score(predictions(ec57_lab, "NSVS"), ec57_lab, {"A": 0.5})
    REPORT["fusion_to_S_example"] = {
        "truth": "NSVF", "predictions": "NSVS",
        "current_S_ppv": ec57_score["per_class"]["S"]["ppv"],
        "paper_table_V_S_ppv": 0.5,
        "primary_macro_f1": ec57_score["macro_f1"],
        "note": "Primary excludes F by design; the mismatch concerns secondary EC57-style naming/definitions.",
    }
    REPORT["sequential_bonferroni_counterexample"] = {
        "description": "Independent null tests at step-dependent levels; illustration, not an estimated EV1 error rate",
        "m": 15,
        "any_two_sided_rejection_probability": float(1 - np.prod(1 - 0.05 / np.arange(1, 16))),
        "any_positive_CI_probability": float(1 - np.prod(1 - 0.025 / np.arange(1, 16))),
    }
    REPORT["elapsed_seconds"] = time.perf_counter() - started
    (OUT / "audit_results.json").write_text(json.dumps(REPORT, indent=2), encoding="utf-8")
    print(json.dumps(REPORT, indent=2))


if __name__ == "__main__":
    main()
