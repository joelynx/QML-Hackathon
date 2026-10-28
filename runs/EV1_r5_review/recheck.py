"""Independent r5 review: training-data checks and isolated synthetic commands.
Never reads real held-out labels or writes the real scoring ledgers.
Run: .venv/Scripts/python.exe -I -B runs/EV1_r5_review/recheck.py
"""
import contextlib
import difflib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

import numpy as np
import pandas as pd
import wfdb

from qhc import evaluate as ev, evalspec as E, scorer, units

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PROC = ROOT / "runs/data/processed/EV1"
SNAP = ROOT / "runs/EV1_r3_snapshot"
RESULT = {}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def guard(event, args):
    if event != "open" or not isinstance(args[0], (str, bytes)):
        return
    p = Path(args[0]).resolve()
    # Reject *all* opens of held-out label files, including hashing.
    if p in {PROC / "labels_ds2s.csv", PROC / "labels_ds2.csv", PROC / "confirm/labels_svdb.csv"}:
        raise RuntimeError(f"Review must not open real held-out labels: {p.name}")
    if p.parent == ROOT / "runs/data/raw/svdb" and p.suffix == ".atr":
        raise RuntimeError("Review must not open raw SVDB annotations")


def pred_frame(lab, pred):
    out = pd.DataFrame({"beat_id": lab.beat_id, "pred": pred})
    for c in E.CLASSES:
        out[f"prob_{c}"] = out.pred.eq(c).astype(float)
    return out


def synthetic(tmp, split, nrec=8, size=45):
    rng = np.random.default_rng(612)
    rows = [(f"fake:r{r}:{j}", f"r{r}", c, c in E.CLASSES)
            for r in range(nrec)
            for j, c in enumerate(rng.choice(list("NNNNSSVVFQ"), size=size))]
    lab = pd.DataFrame(rows, columns=["beat_id", "record", "aami", "is_unit"])
    proc = tmp / "processed"
    (proc / "confirm").mkdir(parents=True)
    lab.assign(sample=np.arange(len(lab)), fs=128, predict=True).to_csv(proc / f"positions_{split}.csv", index=False)
    pd.DataFrame({"record": lab.record.unique(), "duration_s": 1800.0}).to_csv(proc / f"records_{split}.csv", index=False)
    lab.to_csv(proc / ("confirm" if split == "svdb" else "") / f"labels_{split}.csv", index=False)
    return lab, proc


def runs(tmp, lab, arm, split, rates):
    folder = tmp / arm
    folder.mkdir()
    truth = np.where(lab.is_unit, lab.aami, "N")
    files = []
    for seed, rate in enumerate(rates):
        rng = np.random.default_rng(913 + seed)
        yhat = np.where(rng.random(len(lab)) < rate, "N", truth)
        p = folder / f"seed{seed}.csv"
        artifact = folder / f"model{seed}.bin"
        artifact.write_text(f"synthetic {arm} seed {seed}", encoding="utf-8")
        pred_frame(lab, yhat).to_csv(p, index=False)
        manifest = dict(arm_id=arm, seed=seed, split=split, config_id=f"{arm}_cfg", code_revision="synthetic",
                        model_artifact=str(artifact), model_artifact_sha256=digest(artifact), reservoir_seed=seed,
                        shot_seed=1000+seed, prediction_sha256=digest(p))
        p.with_suffix(".run.json").write_text(json.dumps(manifest), encoding="utf-8")
        files.append(str(p))
    return files


def args(split, role, cand, base, out, extra=()):
    return ["compare", "--split", split, "--role", role, "--cand", *cand, "--base", *base,
            "--cand-id", "candidate", "--base-id", "baseline", "--out", str(out), *extra]


def execute(argv):
    capture = io.StringIO()
    try:
        with contextlib.redirect_stdout(capture):
            ev.main(argv)
        return {"status": "accepted", "stdout": capture.getvalue()}
    except BaseException as exc:
        if isinstance(exc, KeyboardInterrupt):
            raise
        return {"status": "rejected", "error": f"{type(exc).__name__}: {exc}"}


def seed_headline():
    ev._append(ev.FULL_EVAL_LOG, {"split": "ds2s", "role": "headline", "time": "synthetic-only",
                                "cmd": "compare", "ids": ["candidate", "baseline"], "files": {},
                                "arms": [["a" * 64], ["b" * 64]]})


def main():
    sys.addaudithook(guard)
    initial_log = (ROOT / "runs/full_eval_log.jsonl").read_bytes()
    assert not (ROOT / "runs/confirmation_access.jsonl").exists()
    RESULT["code_revision"] = ev.code_revision()
    RESULT["fixture_sha256"] = digest(ROOT / "tests/test_scorer.py")
    RESULT["eval_sha256"] = digest(ROOT / "EVAL.md")
    RESULT["source_hashes"] = {p.name: digest(p) for p in sorted((ROOT / "src/qhc").glob("*.py"))}
    changes = {}
    diff_text = []
    for old in sorted(SNAP.glob("*.py")):
        new = ROOT / ("tests" if old.name == "test_scorer.py" else "src/qhc") / old.name
        a, b = old.read_text(encoding="utf-8"), new.read_text(encoding="utf-8")
        d = list(difflib.unified_diff(a.splitlines(True), b.splitlines(True), fromfile=f"r3/{old.name}", tofile=f"r5/{old.name}"))
        changes[old.name] = {"changed": a != b, "diff_lines": len(d)}
        diff_text.extend(d)
    (OUT / "source_changes.diff").write_text("".join(diff_text), encoding="utf-8")
    RESULT["source_changes"] = changes

    manifest = json.loads((PROC / "manifest.json").read_text())
    old_manifest = json.loads((SNAP / "processed_r3/manifest.json").read_text())
    safe_outputs = {p: h for p, h in manifest["outputs"].items() if not (p.startswith("confirm/") or p.startswith("labels_ds2"))}
    RESULT["accessible_output_hashes"] = {p: digest(PROC / p) == h for p, h in safe_outputs.items()}
    assert all(RESULT["accessible_output_hashes"].values())
    RESULT["manifest_changes"] = {p: {"r3": old_manifest["outputs"].get(p), "r5": h}
                                  for p, h in manifest["outputs"].items() if old_manifest["outputs"].get(p) != h}
    lab = pd.read_csv(PROC / "labels_ds1.csv", dtype={"record": str})
    pos = pd.read_csv(PROC / "positions_ds1.csv", dtype={"record": str})
    old_lab = pd.read_csv(SNAP / "processed_r3/labels_ds1.csv", dtype={"record": str})
    expected = old_lab[old_lab.symbol != "!"]
    pd.testing.assert_frame_equal(lab.reset_index(drop=True), expected.reset_index(drop=True))
    # Independent beat-symbol rule applied to raw DS1 annotations, not the production selector.
    expected_positions = []
    for record in E.DS1:
        ann = wfdb.rdann(str(ROOT / "runs/data/raw/mitdb" / record), "atr")
        expected_positions.extend(f"mitdb:{record}:{int(s)}" for s, sym in zip(ann.sample, ann.symbol)
                                  if sym in set("NLRBAaJSVrFejnE/fQ?"))
    assert pos.beat_id.tolist() == expected_positions
    RESULT["R1"] = {"n_predict": len(lab), "n_units": int(lab.is_unit.sum()),
                     "exactly_removed_472_flutter_labels": len(old_lab) - len(lab) == 472,
                     "raw_DS1_positions_match_independent_whitelist": True,
                     "folds_unchanged": digest(PROC / "ds1_folds.json") == old_manifest["outputs"]["ds1_folds.json"]}
    refs = {}
    for rule in ("const_n", "rr_rule"):
        predicted = ev.reference_predictions(rule, pos)
        recorded = pd.read_csv(ROOT / f"runs/EV1_reference_r4/pred_{rule}_ds1.csv")
        pd.testing.assert_frame_equal(predicted.reset_index(drop=True), recorded.reset_index(drop=True))
        refs[rule] = scorer.score(predicted, lab)["macro_f1"]
    RESULT["DS1_reference_scores"] = refs
    RESULT["frozen_subsets_reproduced"] = units.draw_lowdata_subsets(lab[lab.is_unit]) == json.loads((PROC / "lowdata_subsets.json").read_text())

    # Every truth/prediction cell independently checked against Table V's explicit term lists.
    metric_errors = []
    for truth in "NSVFQ":
        for pred in "NSV":
            r = scorer.paper_metrics([truth], [pred])
            expectations = {
                "VEB": {"tp": truth == pred == "V", "fn": truth == "V" and pred != "V",
                        "fp": truth in "NS" and pred == "V", "not_scored": truth in "FQ" and pred == "V"},
                "SVEB": {"tp": truth == pred == "S", "fn": truth == "S" and pred != "S",
                         "fp": truth in "NVF" and pred == "S", "not_scored": truth == "Q" and pred == "S"}}
            for name, counts in expectations.items():
                counts["tn"] = 1 - sum(counts.values())
                metric_errors.extend([f"{truth}->{pred}:{name}:{k}" for k, v in counts.items() if r[name][k] != int(v)])
    assert not metric_errors
    RESULT["R2_table_V_cell_checks"] = {"cells": 15, "endpoints": 2, "errors": metric_errors}

    with tempfile.TemporaryDirectory(prefix="synthetic_", dir=OUT) as temp:
        tmp = Path(temp)
        # Run the normal command twice with one arm's same seed files permuted.
        first = tmp / "ordering"
        lab, proc = synthetic(first, "ds2s")
        cand = runs(first, lab, "q", "ds2s", (.02, .10, .20, .25, .36))
        base = runs(first, lab, "c", "ds2s", (.10, .20, .24, .35, .42))
        with patch.object(ev, "PROCESSED", str(proc)), patch.object(ev, "FULL_EVAL_LOG", str(first / "full.jsonl")), patch.object(ev, "ACCESS_LOG", str(first / "access.jsonl")):
            r1 = execute(args("ds2s", "headline", cand, base, first / "first.json"))
            r2 = execute(args("ds2s", "headline", cand[::-1], base, first / "permuted.json"))
            a = json.loads((first / "first.json").read_text())
            b = json.loads((first / "permuted.json").read_text())
            RESULT["seed_order"] = {"first": r1["status"], "permuted": r2["status"],
                "same_log_identity": ev._log_lines(ev.FULL_EVAL_LOG)[0]["arms"] == ev._log_lines(ev.FULL_EVAL_LOG)[1]["arms"],
                "delta_first": a["primary"]["delta"], "delta_permuted": b["primary"]["delta"],
                "primary_CI_first": a["primary"]["ci"], "primary_CI_permuted": b["primary"]["ci"],
                "S_slice_CI_first": a["slices"]["members"]["S_f1"]["ci"],
                "S_slice_CI_permuted": b["slices"]["members"]["S_f1"]["ci"]}
            # Unrelated full-data model manifests are accepted as a predeclared low-data family member.
            other = runs(first, lab, "unrelated_full_data", "ds2s", (.01,) * 5)
            low = execute(args("ds2s", "lowdata_k5", other, base, first / "low.json"))
            RESULT["lowdata_not_bound_to_headline"] = {"status": low["status"],
                "candidate_config": "unrelated_full_data_cfg", "headline_candidate_config": "q_cfg",
                "training_subset_provenance_supplied": False}
            # The output collision check protects neither model files nor the evaluation ledger.
            artifact = json.loads(Path(ev.run_manifest_path(other[0])).read_text())["model_artifact"]
            before_art = digest(artifact)
            overwrite = execute(args("ds2s", "secondary", other, base, artifact))
            RESULT["model_output_collision"] = {"status": overwrite["status"], "artifact_changed": digest(artifact) != before_art}

        second = tmp / "repair"
        lab, proc = synthetic(second, "svdb", nrec=4, size=30)
        cand = runs(second, lab, "q", "svdb", (.85,) * 5)
        base = runs(second, lab, "c", "svdb", (0.,) * 5)
        with patch.object(ev, "PROCESSED", str(proc)), patch.object(ev, "FULL_EVAL_LOG", str(second / "full.jsonl")), patch.object(ev, "ACCESS_LOG", str(second / "access.jsonl")):
            seed_headline()
            out = second / "confirmation.json"
            r1 = execute(args("svdb", "confirmation", cand, base, out, ["--confirm-reason", "synthetic final pair"]))
            original = out.read_bytes()
            a = json.loads(original)
            r2 = execute(args("svdb", "confirmation", base, cand, out,
                              ["--confirm-reason", "synthetic repair", "--repair-reason", "synthetic file assembly correction"]))
            b = json.loads(out.read_bytes())
            ledger = ev._log_lines(ev.ACCESS_LOG)
            RESULT["confirmation_swapped_arms"] = {"first": r1["status"], "swapped_repair": r2["status"],
                "first_delta": a["primary"]["delta"], "swapped_delta": b["primary"]["delta"],
                "first_confirmed": a["confirmed"], "swapped_confirmed": b["confirmed"],
                "same_union_of_artifact_hashes": set(ledger[0]["model_artifact_sha256"].values()) == set(ledger[1]["model_artifact_sha256"].values()),
                "approved_model_change": ledger[1]["approved_model_change"]}
            RESULT["confirmation_overwrite"] = {"output_changed": original != out.read_bytes(),
                "first_result_still_available_in_output": b["primary"]["delta"] == a["primary"]["delta"],
                "other_result_JSON_files": [p.name for p in second.glob("*.json") if p != out],
                "ledger_has_first_metrics": any("primary" in e or "delta" in e for e in ledger)}
    # Verify pending real run provenance only; do not read or score any test labels.
    provenance = {}
    for exp, n in (("E002", 5), ("E003", 5)):
        files = [str(ROOT / "runs" / exp / f"pred_ds2s_seed{s}.csv") for s in range(n)]
        rr = ev.check_runs(files, "ds2s", exp)
        provenance[exp] = {"checked_runs": len(rr), "config_ids": sorted({r["config_id"] for r in rr}),
                           "seed_ids": sorted(r["seed"] for r in rr)}
    RESULT["pending_headline_provenance_only"] = provenance
    RESULT["real_logs_unchanged"] = initial_log == (ROOT / "runs/full_eval_log.jsonl").read_bytes() and not (ROOT / "runs/confirmation_access.jsonl").exists()
    assert RESULT["real_logs_unchanged"]
    (OUT / "results.json").write_text(json.dumps(RESULT, indent=2), encoding="utf-8")
    print(json.dumps(RESULT, indent=2))


if __name__ == "__main__":
    main()
