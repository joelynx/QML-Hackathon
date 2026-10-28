"""EV1 scorer fixtures (recorded in EVAL.md)."""
import json
import os

import numpy as np
import pandas as pd
import pytest

from qhc import evalspec as E
from qhc import evaluate as ev
from qhc import scorer
from qhc.leakcheck import check_lookahead
from qhc.units import draw_lowdata_subsets, predict_flags, select_beats, sha256

ROOT = os.path.dirname(os.path.dirname(__file__))
PROCESSED = os.path.join(ROOT, "runs", "data", "processed", E.EV)
REAL_SVDB_LABELS = os.path.join(PROCESSED, "confirm", "labels_svdb.csv")


def make_labels(spec):
    """spec: {record: 'NNNSV'} -> labels frame (prediction set) with ids x:rec:i. F and Q rows are non-units."""
    rows = [(f"x:{r}:{i}", r, c, c in E.CLASSES) for r, s in spec.items() for i, c in enumerate(s)]
    return pd.DataFrame(rows, columns=["beat_id", "record", "aami", "is_unit"])


def make_pred(labels, preds, probs=None):
    df = pd.DataFrame({"beat_id": labels["beat_id"].to_numpy(), "pred": list(preds)})
    for c in E.CLASSES:
        df[f"prob_{c}"] = (df["pred"] == c).astype(float) if probs is None else probs[c]
    return df


# Worked example (hand-computed in EVAL.md): N F1 0.6, S F1 0.5, V F1 2/3, macro 0.588889, accuracy 0.6.
# Record B also holds one F beat, which must be predicted but does not enter the metric.
WORKED_LABELS = make_labels({"A": "NNNSV", "B": "NNSVVF"})
WORKED_PRED = "NNSSV" + "NVNVN" + "V"


def test_worked_example():
    r = scorer.score(make_pred(WORKED_LABELS, WORKED_PRED), WORKED_LABELS, hours={"A": 0.5, "B": 0.5})
    assert r["per_class"]["N"]["f1"] == pytest.approx(0.6)
    assert r["per_class"]["S"]["f1"] == pytest.approx(0.5)
    assert r["per_class"]["V"]["f1"] == pytest.approx(2 / 3)
    assert r["macro_f1"] == pytest.approx((0.6 + 0.5 + 2 / 3) / 3)
    assert r["accuracy"] == pytest.approx(0.6)
    assert r["confusion_true_by_pred"] == [[3, 1, 1], [1, 1, 0], [1, 0, 2]]
    assert r["n_predict"] == 11 and r["n_units"] == 10
    assert r["nonunit_predictions"] == {"F": {"N": 0, "S": 0, "V": 1}}
    # N/S/V-restricted class-specific false flags per hour: S FP = 1, V FP = 1, over 1.0 h
    assert r["per_class"]["S"]["nsv_class_false_flags_per_hour"] == pytest.approx(1.0)
    assert r["per_class"]["V"]["nsv_class_false_flags_per_hour"] == pytest.approx(1.0)
    # N/S/V-restricted record-averaged: S sensitivity A 1/1, B 0/1 -> 0.5; V PPV A 1/1, B 1/2 -> 0.75
    assert r["per_class"]["S"]["nsv_record_avg_sensitivity"] == pytest.approx(0.5)
    assert r["per_class"]["V"]["nsv_record_avg_ppv"] == pytest.approx(0.75)
    # review burden over the full prediction set (1.0 h): S/V predictions A 3, B 3 (incl. the F beat) = 6;
    # N flagged: A beat 2 (S), B beat 1 (V) = 2; F flagged 1; no S<->V swaps; missed ectopic: B beat 2 (S->N) and
    # B beat 4 (V->N) = 2
    rb = r["review_burden"]
    assert rb["ectopic_flags_per_hour"] == pytest.approx(6.0)
    assert rb["normal_beats_flagged_per_hour"] == pytest.approx(2.0)
    assert rb["f_q_beats_flagged_per_hour"] == pytest.approx(1.0)
    assert rb["s_v_class_swaps_per_hour"] == pytest.approx(0.0)
    assert rb["missed_ectopic_per_hour"] == pytest.approx(2.0)


def test_paper_compatible_metrics_count_f_as_s_false_positive():
    """Review item R2: de Chazal Table V counts F->S as an S false positive (and leaves F->V, Q->V, Q->S unscored)."""
    lab = make_labels({"A": "NSVF"})
    r = scorer.score(make_pred(lab, "NSVS"), lab)
    assert r["macro_f1"] == pytest.approx(1.0)  # the primary metric is N/S/V-restricted by declaration
    assert r["per_class"]["S"]["ppv"] == pytest.approx(1.0)
    pc = r["paper_compatible"]
    assert pc["SVEB"]["ppv"] == pytest.approx(0.5) and pc["SVEB"]["fp"] == 1 and pc["SVEB"]["tn"] == 2
    assert pc["SVEB"]["fpr"] == pytest.approx(1 / 3)
    # F predicted V and Q predicted V/S are neither rewarded nor penalised
    lab2 = make_labels({"A": "NSVFQQ"})
    r2 = scorer.score(make_pred(lab2, "NSVVVS"), lab2)["paper_compatible"]
    assert r2["VEB"]["ppv"] == pytest.approx(1.0) and r2["VEB"]["not_scored"] == 2
    assert r2["SVEB"]["ppv"] == pytest.approx(1.0) and r2["SVEB"]["not_scored"] == 1
    assert r2["VEB"]["tp"] + r2["VEB"]["fn"] + r2["VEB"]["fp"] + r2["VEB"]["tn"] + r2["VEB"]["not_scored"] == 6


def test_known_good_is_one():
    truth = "".join(WORKED_LABELS["aami"].replace({"F": "N"}))
    assert scorer.score(make_pred(WORKED_LABELS, truth), WORKED_LABELS)["macro_f1"] == pytest.approx(1.0)


def test_all_normal_is_poor():
    r = scorer.score(make_pred(WORKED_LABELS, "N" * 11), WORKED_LABELS)
    assert r["macro_f1"] == pytest.approx((2 * 5 / (5 + 10)) / 3)  # F1_N = 2 nN / (nN + n); S and V score 0
    assert r["per_class"]["S"]["ppv"] is None and r["per_class"]["S"]["f1"] == 0


def test_shuffled_rows_score_the_same():
    p = make_pred(WORKED_LABELS, WORKED_PRED).sample(frac=1, random_state=0)
    assert scorer.score(p, WORKED_LABELS)["macro_f1"] == pytest.approx(0.588889, abs=1e-6)


def test_absent_class_is_vacuous_one():
    lab = make_labels({"A": "NNVV"})
    assert scorer.score(make_pred(lab, "NNVV"), lab)["per_class"]["S"]["f1"] == 1.0
    assert scorer.score(make_pred(lab, "NSVV"), lab)["per_class"]["S"]["f1"] == 0.0


def test_average_precision_hand_example():
    # scores 0.9 (pos), 0.8 (neg), 0.7 (pos), 0.6 (neg): AP = 0.5 * 1 + 0.5 * 2/3
    assert scorer.average_precision([1, 0, 1, 0], [0.9, 0.8, 0.7, 0.6]) == pytest.approx(0.5 + 1 / 3)
    # a tie between a positive and a negative at the top counts as one threshold: precision 1/2 at recall 1
    assert scorer.average_precision([1, 0], [0.5, 0.5]) == pytest.approx(0.5)


@pytest.mark.parametrize(
    "mutate, msg",
    [
        (lambda p: p.iloc[1:], "no prediction"),
        (lambda p: p[p["beat_id"] != "x:B:5"], "no prediction"),  # the F beat must be predicted too
        (lambda p: pd.concat([p, p.iloc[:1]]), "duplicate"),
        (lambda p: pd.concat([p, make_pred(make_labels({"Z": "N"}), "N")]), "not in the prediction set"),
        (lambda p: p.assign(pred=["n"] + list(p["pred"][1:])), "outside"),
        (lambda p: p.assign(pred=["F"] + list(p["pred"][1:])), "outside"),
        (lambda p: p.rename(columns={"pred": "label"}), "columns"),
        (lambda p: p.drop(columns=["prob_V"]), "required"),
        (lambda p: p.assign(beat_id=[None] + list(p["beat_id"][1:])), "missing beat_id"),
        (lambda p: p.assign(prob_N=np.nan), "non-finite"),
        (lambda p: p.assign(prob_N=0.5, prob_S=0.5, prob_V=0.5), "sum to 1"),
    ],
)
def test_malformed_predictions_are_rejected(mutate, msg):
    with pytest.raises(scorer.PredictionError, match=msg):
        scorer.score(mutate(make_pred(WORKED_LABELS, WORKED_PRED)), WORKED_LABELS)


def _synthetic(n_rec=20, seed=0):
    rng = np.random.default_rng(seed)
    spec = {f"r{i}": "".join(rng.choice(list("NNNNNNNNSV"), size=200)) for i in range(n_rec)}
    return make_labels(spec)


def test_compare_identical_is_null():
    lab = _synthetic()
    p = make_pred(lab, lab["aami"])
    c = scorer.compare([p], [p], lab, n_boot=300)["primary"]
    assert c["delta"] == 0 and c["ci"] == [0.0, 0.0] and c["outcome"] == "no detectable change"


def test_compare_directions_and_suspicious_flag():
    lab = _synthetic()
    good, bad = make_pred(lab, lab["aami"]), make_pred(lab, "N" * len(lab))
    up = scorer.compare([good], [bad], lab, n_boot=300)
    down = scorer.compare([bad], [good], lab, n_boot=300)
    assert up["primary"]["outcome"] == "favorable" and up["primary"]["suspicious_gain"] and up["primary"]["ci"][0] > 0
    assert down["primary"]["outcome"] == "unfavorable"
    assert down["primary"]["delta"] == pytest.approx(-up["primary"]["delta"])
    assert up["per_class_f1"]["S"]["delta"] == pytest.approx(1.0) and up["per_class_f1"]["S"]["ci"][0] > 0
    assert up["auprc"]["S"]["delta"] > 0 and up["auprc"]["S"]["ci"][0] > 0


def test_small_detectable_regression_is_unfavorable():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    worse = truth.copy()
    worse[np.flatnonzero(truth == "S")[::12]] = "N"  # lose ~8% of S beats in every record
    c = scorer.compare([make_pred(lab, worse)], [make_pred(lab, truth)], lab, n_boot=500)["primary"]
    assert -E.PRACTICAL_GAIN < c["delta"] < 0 and c["ci"][1] < 0 and c["outcome"] == "unfavorable"


def test_decision_reasons():
    assert scorer.decide(0.01, 0.005, 0.015) == ("no detectable change", "detectable gain below the practical threshold")
    assert scorer.decide(0.03, 0.01, 0.05, -0.001) == ("no detectable change", "gain disappears without the dominant record")
    assert scorer.decide(0.03, 0.01, 0.05, 0.01) == ("favorable", "meets the decision rule")
    assert scorer.decide(-0.01, -0.02, -0.001) == ("unfavorable", "CI upper bound < 0")
    assert scorer.decide(0.05, -0.01, 0.1) == ("no detectable change", "CI includes 0")


def test_gain_carried_by_one_record_is_not_favorable():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    base = np.where(truth == "S", "N", truth)  # baseline misses every S beat
    cand = base.copy()
    in_r0 = (lab["record"] == "r0").to_numpy()
    cand[in_r0] = truth[in_r0]  # candidate fixes S only in r0 ...
    cand[(~in_r0) & (truth == "V")] = "N"  # ... and loses V elsewhere
    c = scorer.compare([make_pred(lab, cand)], [make_pred(lab, base)], lab, dominant_record="r0", n_boot=300)
    assert c["primary"]["delta_without_dominant_record"] < 0
    assert c["primary"]["outcome"] != "favorable"
    assert c["leave_one_record_out_delta"]["r0"] == pytest.approx(c["primary"]["delta_without_dominant_record"])


def test_seed_resampling_widens_ci_and_counts_are_enforced():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    rng = np.random.default_rng(1)
    noisy = [make_pred(lab, np.where(rng.random(len(lab)) < q, "N", truth)) for q in (0.05, 0.1, 0.2, 0.3, 0.4)]
    a = scorer.compare(noisy, noisy[::-1], lab, n_boot=400)
    assert a["primary"]["delta"] == pytest.approx(0) and a["primary"]["ci"][1] - a["primary"]["ci"][0] > 0.01
    assert a["primary"]["ci"] == scorer.compare(noisy, noisy[::-1], lab, n_boot=400)["primary"]["ci"]  # reproducible
    cand = a["arms"]["candidate"]
    assert a["primary"]["candidate_macro_f1"] == pytest.approx(np.mean(cand["per_seed_macro_f1"]))
    assert cand["seed_average"]["macro_f1"] == pytest.approx(a["primary"]["candidate_macro_f1"])
    with pytest.raises(scorer.PredictionError, match="equal"):
        scorer.compare(noisy[:1], noisy, lab, n_boot=50)


def test_compare_rejects_extra_rows():
    lab = _synthetic()
    p = make_pred(lab, lab["aami"])
    extra = pd.concat([p, make_pred(make_labels({"zz": "N"}), "N")])
    with pytest.raises(scorer.PredictionError, match="not in the prediction set"):
        scorer.compare([extra], [p], lab, n_boot=50)


def test_primary_and_slice_levels_and_decisions():
    """Review item R4: the headline's primary CI is at 95%; its S and V slice members at 98.75% with the slice rule
    (CI lower bound > 0, no practical threshold); a low-data comparison's primary delta is a slice member at 98.75%."""
    lab = _synthetic(n_rec=30)
    truth = lab["aami"].to_numpy()
    base = truth.copy()
    base[np.flatnonzero(truth == "S")[::4]] = "N"  # baseline misses 25% of S beats everywhere
    cand = truth.copy()
    cand[np.flatnonzero(truth == "S")[::5]] = "N"  # candidate misses 20%: a small, consistent S gain
    c = scorer.compare([make_pred(lab, cand)], [make_pred(lab, base)], lab, role="headline", n_boot=2000)
    assert c["primary"]["ci_level"] == pytest.approx(0.95)
    assert c["slices"]["ci_level"] == pytest.approx(1 - 0.05 / 4) and c["slices"]["m"] == 4
    assert set(c["slices"]["members"]) == {"S_f1", "V_f1"}
    s = c["slices"]["members"]["S_f1"]
    assert s["ci"][0] > 0 and s["decision"] == "favorable"
    assert c["primary"]["delta"] < E.PRACTICAL_GAIN and c["primary"]["outcome"] == "no detectable change"
    assert c["primary"]["outcome_reason"] == "detectable gain below the practical threshold"
    assert c["slices"]["members"]["V_f1"]["decision"] == "no detectable change"  # V identical in both arms
    # the slice interval is wider than the 95% per-class interval of the same quantity
    assert s["ci"][0] < c["per_class_f1"]["S"]["ci"][0] and s["ci"][1] > c["per_class_f1"]["S"]["ci"][1]
    low = scorer.compare([make_pred(lab, cand)], [make_pred(lab, base)], lab, role="lowdata_k5", n_boot=2000)
    assert low["primary"]["ci_level"] == pytest.approx(0.9875)
    assert low["slices"]["members"]["lowdata_k5"]["ci"] == low["primary"]["ci"]
    assert scorer.compare([make_pred(lab, cand)], [make_pred(lab, base)], lab, role="secondary", n_boot=200)["slices"] is None


def test_rr_rule_reference_uses_positions_only():
    s = [0, 100, 200, 300, 400, 470, 600, 700]  # beat at 470 is premature (70 < 0.85 * 100)
    pos = pd.DataFrame({"beat_id": [f"x:A:{v}" for v in s], "record": "A", "sample": s, "predict": True})
    pred = ev.reference_predictions("rr_rule", pos).set_index("beat_id")
    assert pred.loc["x:A:470", "pred"] == "S" and (pred.drop("x:A:470")["pred"] == "N").all()
    assert (pred[[f"prob_{c}" for c in E.CLASSES]].sum(1) == 1).all()


def test_non_beat_annotations_are_not_beat_positions():
    """Review item R1: flutter waves (!) and other non-beat codes never become beat positions or RR endpoints."""
    samples = [100, 200, 230, 260, 300, 330, 400, 500, 520]
    symbols = ["N", "!", "!", "+", "N", "~", "V", "|", "N"]
    b = select_beats(samples, symbols)
    assert b["sample"].tolist() == [100, 300, 400, 520] and b["symbol"].tolist() == ["N", "N", "V", "N"]
    assert np.diff(b["sample"]).tolist() == [200, 100, 120]
    assert "!" not in E.BEAT_SYMBOLS


# ---- decision-time boundary (lookahead) check ----
FS = 100
SIG = np.sin(np.arange(3000) / 7.0)
BEATS = np.array([100, 180, 260, 420, 500, 900, 980, 1060, 1500, 2900])


def _causal(sig, samples, fs):
    pre = np.diff(samples, prepend=samples[0])
    post = np.diff(samples, append=samples[-1])
    win = np.array([sig[max(0, s - 20):s + 50].sum() for s in samples])
    return np.c_[pre, post, win]


def _leaky_mean_rr(sig, samples, fs):
    return np.full((len(samples), 1), np.diff(samples).mean())  # whole-record statistic


def _leaky_window(sig, samples, fs):
    return np.array([[sig[s:s + 300].sum()] for s in samples])  # 3 s window, beyond the boundary


def test_lookahead_check():
    idx = range(1, len(BEATS) - 1)
    assert check_lookahead(_causal, SIG, BEATS, FS, idx) == []
    assert check_lookahead(_leaky_mean_rr, SIG, BEATS, FS, idx) != []
    assert check_lookahead(_leaky_window, SIG, BEATS, FS, idx) != []


# ---- command-level checks on synthetic files (never touch the real test labels, confirmation set or logs) ----
def _fake_split(tmp_path, split, spec):
    lab = make_labels(spec)
    proc = tmp_path / "processed"
    (proc / "confirm").mkdir(parents=True, exist_ok=True)
    pos = lab.assign(sample=range(len(lab)), fs=128, predict=True)[["beat_id", "record", "sample", "fs", "predict"]]
    pos.to_csv(proc / f"positions_{split}.csv", index=False)
    pd.DataFrame({"record": sorted(spec), "fs": 128, "sig_len": 230400, "duration_s": 1800.0}).to_csv(
        proc / f"records_{split}.csv", index=False)
    lab.to_csv(proc / ("confirm" if split in E.CONFIRMATION_SPLITS else ".") / f"labels_{split}.csv", index=False)
    return lab, proc


def _runs(tmp_path, lab, arm, preds, split, seeds=(0, 1, 2, 3, 4), shot=True):
    """Write one prediction file, model artifact and run manifest per seed; return the prediction paths."""
    d = tmp_path / arm
    d.mkdir(exist_ok=True)
    files = []
    for s, p in zip(seeds, preds):
        f, art = d / f"pred_seed{s}_{split}_{len(files)}.csv", d / f"model_seed{s}_{len(files)}.npz"
        make_pred(lab, p).to_csv(f, index=False)
        art.write_bytes(f"{arm}-{s}-{len(files)}".encode())
        man = {"arm_id": arm, "seed": s, "split": split, "config_id": "cfg", "code_revision": "test",
               "model_artifact": str(art), "model_artifact_sha256": sha256(str(art)), "reservoir_seed": 100 + s,
               "shot_seed": (200 + s) if shot else None, "prediction_sha256": sha256(str(f))}
        (d / (f.stem + ".run.json")).write_text(json.dumps(man))
        files.append(str(f))
    return files


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    opened = []
    orig_read_csv = pd.read_csv
    monkeypatch.setattr(pd, "read_csv", lambda path, *a, **k: (opened.append(str(path)), orig_read_csv(path, *a, **k))[1])
    monkeypatch.setattr(ev, "ACCESS_LOG", str(tmp_path / "access.jsonl"))
    monkeypatch.setattr(ev, "FULL_EVAL_LOG", str(tmp_path / "full_eval.jsonl"))
    yield tmp_path, opened
    assert not any(os.path.abspath(p) == os.path.abspath(REAL_SVDB_LABELS) for p in opened)


def _labels_read(opened, proc, split):
    return any(os.path.basename(p) == f"labels_{split}.csv" and str(proc) in p for p in opened)


def test_command_rejects_repeated_files_and_bad_runs_before_labels(sandbox, monkeypatch):
    """Review item R5: duplicate files, too few runs, duplicate seed ids, a stale manifest or mismatched seed sets are
    refused before any label access; a valid 5 x 5 headline runs; a different headline is then refused."""
    tmp_path, opened = sandbox
    rng = np.random.default_rng(0)
    spec = {f"r{i}": "".join(rng.choice(list("NNNNNNSV"), size=60)) for i in range(8)}
    lab, proc = _fake_split(tmp_path, "ds2s", spec)
    monkeypatch.setattr(ev, "PROCESSED", str(proc))
    truth = lab["aami"].to_numpy()
    noisy = lambda q, s: np.where(np.random.default_rng(s).random(len(lab)) < q, "N", truth)
    cand = _runs(tmp_path, lab, "qrc", [noisy(0.1, s) for s in range(5)], "ds2s")
    base = _runs(tmp_path, lab, "esn", [noisy(0.2, s) for s in range(5)], "ds2s", shot=False)
    out = str(tmp_path / "c.json")
    args = lambda c, b, role="headline": ["compare", "--split", "ds2s", "--role", role, "--cand", *c, "--base", *b,
                                          "--cand-id", "Q", "--base-id", "C", "--out", out]
    refusals = [
        (args([cand[0]] * 5, base), "given twice"),
        (args(cand, cand), "given twice"),
        (args(cand[:1], base[:1]), "exactly 5"),
    ]
    dup_seed = _runs(tmp_path, lab, "qrc_dup", [noisy(0.1, s) for s in range(5)], "ds2s", seeds=(0, 1, 2, 3, 3))
    refusals.append((args(dup_seed, base), "duplicate seed"))
    other_seeds = _runs(tmp_path, lab, "qrc_other", [noisy(0.1, 50 + s) for s in range(5)], "ds2s", seeds=(5, 6, 7, 8, 9))
    refusals.append((args(other_seeds, base), "same seed indices"))
    stale = _runs(tmp_path, lab, "qrc_stale", [noisy(0.1, s) for s in range(5)], "ds2s")
    make_pred(lab, truth).to_csv(stale[2], index=False)  # file changed after its manifest was written
    refusals.append((args(stale, base), "prediction_sha256"))
    refusals.append((args(cand, base, role="confirmation"), "role confirmation is for split"))
    for argv, msg in refusals:
        with pytest.raises(SystemExit, match=msg):
            ev.main(argv)
    assert not _labels_read(opened, proc, "ds2s") and not os.path.exists(ev.FULL_EVAL_LOG)
    ev.main(args(cand, base))
    res = json.load(open(out))
    assert res["role"] == "headline" and res["primary"]["ci_level"] == pytest.approx(0.95)
    assert res["slices"]["ci_level"] == pytest.approx(0.9875) and set(res["slices"]["members"]) == {"S_f1", "V_f1"}
    assert res["n_boot"] == E.N_BOOT and res["scorer"]["code_revision"] == ev.code_revision()
    assert len(res["arms"]["candidate"]["per_seed"]) == 5 and len(res["run_manifests"]) == 10
    assert len(ev._log_lines(ev.FULL_EVAL_LOG)) == 1
    ev.main(args(cand, base))  # rerunning the identical headline is allowed
    other_base = _runs(tmp_path, lab, "esn_other", [noisy(0.2, 60 + s) for s in range(5)], "ds2s", seeds=(5, 6, 7, 8, 9),
                       shot=False)
    with pytest.raises(SystemExit, match="different headline was already evaluated"):
        ev.main(args(other_seeds, other_base))
    with pytest.raises(SystemExit, match="limited to the minimal-reference"):  # no peeking through diagnostics
        ev.main(args(cand[:1], base[:1], role="diagnostic"))


def _ds2s_sandbox(tmp_path, monkeypatch, n_rec=8, size=60, seed=0):
    rng = np.random.default_rng(seed)
    spec = {f"r{i}": "".join(rng.choice(list("NNNNNNSV"), size=size)) for i in range(n_rec)}
    lab, proc = _fake_split(tmp_path, "ds2s", spec)
    monkeypatch.setattr(ev, "PROCESSED", str(proc))
    truth = lab["aami"].to_numpy()
    noisy = lambda q, s: np.where(np.random.default_rng(s).random(len(lab)) < q, "N", truth)
    return lab, proc, noisy


def test_order_rules_on_test_splits(sandbox, monkeypatch):
    """Review V003 B1 and M4: before the headline only the minimal references may be scored on ds2s (score, secondary,
    low-data and non-reference diagnostics are refused, and a prior non-reference scoring blocks the headline); the
    low-data comparisons run once, at the 98.75% slice level, with the slice decision in the command output."""
    tmp_path, opened = sandbox
    lab, proc, noisy = _ds2s_sandbox(tmp_path, monkeypatch)
    ref, ref2 = str(tmp_path / "ref.csv"), str(tmp_path / "ref2.csv")
    make_pred(lab, "N" * len(lab)).to_csv(ref, index=False)
    make_pred(lab, noisy(0.5, 99)).to_csv(ref2, index=False)
    monkeypatch.setattr(E, "REFERENCE_PRED_SHA256", {sha256(ref), sha256(ref2)})
    out = str(tmp_path / "o.json")
    cmp_ = lambda c, b, role: ["compare", "--split", "ds2s", "--role", role, "--cand", *c, "--base", *b,
                               "--cand-id", "Q", "--base-id", "C", "--out", out]
    cand = _runs(tmp_path, lab, "qrc", [noisy(0.1, s) for s in range(5)], "ds2s")
    base = _runs(tmp_path, lab, "esn", [noisy(0.3, s) for s in range(5)], "ds2s", shot=False)
    low = _runs(tmp_path, lab, "qrc_k5", [noisy(0.15, 10 + s) for s in range(5)], "ds2s")
    low_b = _runs(tmp_path, lab, "esn_k5", [noisy(0.3, 20 + s) for s in range(5)], "ds2s", shot=False)
    for argv, msg in [(["score", "--split", "ds2s", "--pred", cand[0], "--id", "x", "--out", out], "waits"),
                      (cmp_(cand, base, "secondary"), "waits"), (cmp_(low, low_b, "lowdata_k5"), "waits"),
                      (cmp_(cand[:1], base[:1], "diagnostic"), "limited to the minimal-reference")]:
        with pytest.raises(SystemExit, match=msg):
            ev.main(argv)
    assert not _labels_read(opened, proc, "ds2s")
    ev.main(["score", "--split", "ds2s", "--pred", ref, "--id", "const_n", "--out", out])  # references are fine
    ev.main(cmp_([ref2], [ref], "diagnostic"))
    ev.main(cmp_(cand, base, "headline"))
    ev.main(cmp_(low, low_b, "lowdata_k5"))
    res = json.load(open(out))
    assert res["primary"]["ci_level"] == pytest.approx(0.9875)
    assert res["slices"]["members"]["lowdata_k5"]["ci"] == res["primary"]["ci"]
    assert res["slices"]["members"]["lowdata_k5"]["decision"] in ("favorable", "no detectable change", "unfavorable")
    ev.main(cmp_(low[::-1], low_b, "lowdata_k5"))  # the same files in another order and spelling: identical rerun
    low2 = _runs(tmp_path, lab, "qrc_k5b", [noisy(0.05, 30 + s) for s in range(5)], "ds2s")
    with pytest.raises(SystemExit, match="runs once"):
        ev.main(cmp_(low2, low_b, "lowdata_k5"))
    ev.main(cmp_(low2, low_b, "secondary"))  # later variants are descriptive
    ev.main(["score", "--split", "ds2s", "--pred", cand[0], "--id", "x", "--out", out])
    ev.main(cmp_(cand[::-1], base, "headline"))  # V003 N3: an identical headline rerun is accepted after later entries
    with pytest.raises(SystemExit, match="overwrite an input"):  # V003 N4
        ev.main(cmp_(low2, low_b, "secondary")[:-1] + [low2[0]])
    with pytest.raises(SystemExit, match="cannot be the headline"):  # V003 N1: references alone are not a headline
        ev._check_order("headline", "ds2s", [[sha256(ref)], [sha256(ref2)]])


def _fake_headline_log():
    ev._append(ev.FULL_EVAL_LOG, {"time": "t", "cmd": "compare", "split": "ds2s", "role": "headline", "ids": ["Q", "C"],
                                  "files": {}, "arms": [["1" * 64], ["2" * 64]]})


def test_headline_refused_after_an_earlier_non_reference_scoring(sandbox, monkeypatch):
    tmp_path, _ = sandbox
    lab, proc, noisy = _ds2s_sandbox(tmp_path, monkeypatch)
    cand = _runs(tmp_path, lab, "qrc", [noisy(0.1, s) for s in range(5)], "ds2s")
    base = _runs(tmp_path, lab, "esn", [noisy(0.3, s) for s in range(5)], "ds2s", shot=False)
    ev._append(ev.FULL_EVAL_LOG, {"time": "t", "cmd": "score", "split": "ds2s", "role": None, "ids": ["peek"],
                                  "files": {"x.csv": "0" * 64}})
    with pytest.raises(SystemExit, match="headline must be the first"):
        ev.main(["compare", "--split", "ds2s", "--role", "headline", "--cand", *cand, "--base", *base,
                 "--cand-id", "Q", "--base-id", "C", "--out", str(tmp_path / "o.json")])


def test_copies_and_mixed_configurations_are_not_seeds(sandbox, monkeypatch):
    """Review V003 S1: byte-identical model artifacts, mixed config_ids within an arm, or one arm_id for both arms are
    refused, before any label is read."""
    tmp_path, opened = sandbox
    lab, proc, noisy = _ds2s_sandbox(tmp_path, monkeypatch)
    base = _runs(tmp_path, lab, "esn", [noisy(0.3, s) for s in range(5)], "ds2s", shot=False)
    out = str(tmp_path / "o.json")
    args = lambda c, b: ["compare", "--split", "ds2s", "--role", "headline", "--cand", *c, "--base", *b,
                         "--cand-id", "Q", "--base-id", "C", "--out", out]
    copies = _runs(tmp_path, lab, "qrc_copy", [noisy(0.1, 0)] * 5, "ds2s")
    for f in copies:  # make every model artifact byte-identical, with manifests updated to match
        m = json.load(open(f[:-4] + ".run.json"))
        open(m["model_artifact"], "wb").write(b"same model")
        m["model_artifact_sha256"] = sha256(m["model_artifact"])
        json.dump(m, open(f[:-4] + ".run.json", "w"))
    mixed = _runs(tmp_path, lab, "qrc_mixed", [noisy(0.1, s) for s in range(5)], "ds2s")
    m = json.load(open(mixed[3][:-4] + ".run.json"))
    m["config_id"] = "other"
    json.dump(m, open(mixed[3][:-4] + ".run.json", "w"))
    same_arm = _runs(tmp_path, lab, "esn_twin", [noisy(0.1, s) for s in range(5)], "ds2s")
    for f in same_arm:
        m = json.load(open(f[:-4] + ".run.json"))
        m["arm_id"] = "esn"
        json.dump(m, open(f[:-4] + ".run.json", "w"))
    for c, msg in [(copies, "byte-identical model artifacts"), (mixed, "different configurations"),
                   (same_arm, "same arm_id")]:
        with pytest.raises(SystemExit, match=msg):
            ev.main(args(c, base))
    assert not _labels_read(opened, proc, "ds2s") and not os.path.exists(ev.FULL_EVAL_LOG)


def test_confirmation_command_reports_everything_in_one_logged_access(sandbox, monkeypatch):
    """Review item R6: one confirmation command emits every per-seed and seed-averaged secondary metric and the
    per-record confusions, and logs exactly one access bound to prediction and artifact hashes. A second access
    needs a repair reason; a third is refused. The real confirmation labels are never opened."""
    tmp_path, opened = sandbox
    rng = np.random.default_rng(3)
    spec = {f"s{i}": "".join(rng.choice(list("NNNNNSSVFQ"), size=50)) for i in range(10)}
    lab, proc = _fake_split(tmp_path, "svdb", spec)
    monkeypatch.setattr(ev, "PROCESSED", str(proc))
    with pytest.raises(PermissionError):
        ev.load_labels("svdb", processed=str(proc))
    truth = np.where(lab["is_unit"], lab["aami"], "N")
    noisy = lambda q, s: np.where(np.random.default_rng(s).random(len(lab)) < q, "N", truth)
    cand = _runs(tmp_path, lab, "qrc", [noisy(0.05, s) for s in range(5)], "svdb")
    base = _runs(tmp_path, lab, "esn", [noisy(0.3, 10 + s) for s in range(5)], "svdb", shot=False)
    out = str(tmp_path / "confirm.json")
    argv = ["compare", "--split", "svdb", "--role", "confirmation", "--cand", *cand, "--base", *base,
            "--cand-id", "Q", "--base-id", "C", "--out", out]
    with pytest.raises(SystemExit, match="confirm-reason"):
        ev.main(argv)
    with pytest.raises(SystemExit, match="only after the headline"):  # V003 N2
        ev.main(argv + ["--confirm-reason", "too early"])
    _fake_headline_log()
    with pytest.raises(SystemExit, match="only by `compare --role confirmation`"):
        ev.main(["score", "--split", "svdb", "--pred", cand[0], "--id", "x", "--out", out])
    bad = str(tmp_path / "bad.csv")
    make_pred(lab, truth).iloc[1:].to_csv(bad, index=False)
    with pytest.raises(SystemExit):  # one run instead of five, and no manifest: refused before any access
        ev.main(argv[:5] + ["--cand", bad, "--base", base[0]] + argv[-6:] + ["--confirm-reason", "t"])
    assert not os.path.exists(ev.ACCESS_LOG) and not _labels_read(opened, proc, "svdb")
    ev.main(argv + ["--confirm-reason", "final pair"])
    log = ev._log_lines(ev.ACCESS_LOG)
    assert len(log) == 1 and log[0]["access"] == 1 and len(log[0]["prediction_sha256"]) == 10
    assert len(log[0]["model_artifact_sha256"]) == 10 and log[0]["code_revision"] == ev.code_revision()
    res = json.load(open(out))
    assert res["confirmed"] is True and res["primary"]["ci_level"] == pytest.approx(0.95)
    for arm in ("candidate", "baseline"):
        per_seed = res["arms"][arm]["per_seed"]
        assert len(per_seed) == 5
        for s in per_seed:
            for c in E.CLASSES:
                assert {"sensitivity", "ppv", "f1", "nsv_record_avg_sensitivity", "nsv_record_avg_ppv",
                        "nsv_class_false_flags_per_hour"} <= set(s["per_class"][c])
            assert set(s["nonunit_predictions"]) == {"F", "Q"} and len(s["per_record"]) == 10
            assert {"VEB", "SVEB"} <= set(s["paper_compatible"]) and "ectopic_flags_per_hour" in s["review_burden"]
        avg = res["arms"][arm]["seed_average"]
        assert avg["per_class"]["S"]["sensitivity"] == pytest.approx(np.mean([s["per_class"]["S"]["sensitivity"]
                                                                              for s in per_seed]))
    assert set(res["arms"]["candidate"]["per_seed"][0]["paper_compatible_per_record"]) == set(spec)
    with pytest.raises(SystemExit, match="repair-reason"):
        ev.main(argv + ["--confirm-reason", "again"])
    other = _runs(tmp_path, lab, "qrc_other", [noisy(0.05, 40 + s) for s in range(5)], "svdb")
    argv_other = argv[:5] + ["--cand", *other] + argv[11:]
    with pytest.raises(SystemExit, match="same model artifacts"):  # V003 S3: a repair is not a model change
        ev.main(argv_other + ["--confirm-reason", "repair", "--repair-reason", "x"])
    ev.main(argv + ["--confirm-reason", "repair", "--repair-reason", "fixed resampling bug"])
    with pytest.raises(SystemExit, match="cap"):
        ev.main(argv + ["--confirm-reason", "third", "--repair-reason", "x"])
    assert len(ev._log_lines(ev.ACCESS_LOG)) == E.CONFIRMATION_CAP


def test_confirmation_checks_output_and_scorer_before_logging(sandbox, monkeypatch):
    """Review V003 S2: an unwritable output or a scorer crash fails before the access is logged."""
    tmp_path, opened = sandbox
    rng = np.random.default_rng(4)
    spec = {f"s{i}": "".join(rng.choice(list("NNNNNSSV"), size=40)) for i in range(6)}
    lab, proc = _fake_split(tmp_path, "svdb", spec)
    monkeypatch.setattr(ev, "PROCESSED", str(proc))
    truth = lab["aami"].to_numpy()
    cand = _runs(tmp_path, lab, "qrc", [np.where(np.random.default_rng(s).random(len(lab)) < 0.1, "N", truth)
                                         for s in range(5)], "svdb")
    base = _runs(tmp_path, lab, "esn", [np.where(np.random.default_rng(9 + s).random(len(lab)) < 0.3, "N", truth)
                                         for s in range(5)], "svdb", shot=False)
    _fake_headline_log()
    blocker = tmp_path / "a_file"
    blocker.write_text("x")
    argv = lambda out: ["compare", "--split", "svdb", "--role", "confirmation", "--cand", *cand, "--base", *base,
                        "--cand-id", "Q", "--base-id", "C", "--out", out, "--confirm-reason", "final"]
    with pytest.raises(OSError):
        ev.main(argv(str(blocker / "sub" / "out.json")))  # parent is a file
    monkeypatch.setattr(scorer, "compare", lambda *a, **k: (_ for _ in ()).throw(MemoryError("boom")))
    with pytest.raises(MemoryError):
        ev.main(argv(str(tmp_path / "ok.json")))
    assert not os.path.exists(ev.ACCESS_LOG) and not _labels_read(opened, proc, "svdb")


# ---- real-data checks ----
manifest_path = os.path.join(PROCESSED, "manifest.json")
needs_data = pytest.mark.skipif(not os.path.exists(manifest_path), reason="run python -m qhc.units first")

# Current-dataset class totals (all beat annotations of the split, before the edge and first/last exclusions), from the
# checksum-verified PhysioNet annotations. de Chazal 2004, Table II, gives DS1 N 45,868, S 942, V 3,787 and DS2
# N 44,258; the other totals agree. EV1 uses de Chazal's record split and class mapping with these documented
# current-annotation differences (EVAL.md, review item R3); labels are not altered to force agreement.
CURRENT_COUNTS = {"ds1": {"N": 45866, "S": 944, "V": 3788, "F": 415, "Q": 8},
                  "ds2": {"N": 44259, "S": 1837, "V": 3221, "F": 388, "Q": 7}}
DE_CHAZAL_TABLE_II = {"ds1": {"N": 45868, "S": 942, "V": 3787, "F": 415, "Q": 8},
                      "ds2": {"N": 44258, "S": 1837, "V": 3221, "F": 388, "Q": 7}}


@needs_data
def test_units_match_current_dataset_counts():
    m = json.load(open(manifest_path))["splits"]
    for split, ref in CURRENT_COUNTS.items():
        parts = ("class_counts", "predicted_nonunit_by_aami", "not_predicted_by_aami")
        total = {c: sum(m[split][p].get(c, 0) for p in parts) for c in ref}
        assert total == ref
        assert "other" not in m[split]["predicted_nonunit_by_aami"]  # no non-beat codes in the prediction set
    diff = {s: {c: CURRENT_COUNTS[s][c] - DE_CHAZAL_TABLE_II[s][c] for c in CURRENT_COUNTS[s]} for s in CURRENT_COUNTS}
    assert diff == {"ds1": {"N": -2, "S": 2, "V": 1, "F": 0, "Q": 0}, "ds2": {"N": 1, "S": 0, "V": 0, "F": 0, "Q": 0}}
    assert m["ds1"]["n_predict"] == 50964 and m["ds1"]["n_units"] == 50542


@needs_data
def test_splits_disjoint_and_released_files_are_label_free():
    m = json.load(open(manifest_path))["splits"]
    ds1, ds2s = set(m["ds1"]["records"]), set(m["ds2s"]["records"])
    assert not ds1 & ds2s and "202" not in ds2s and not (ds1 | ds2s) & set(E.PACED)
    assert not os.path.exists(os.path.join(PROCESSED, "labels_svdb.csv"))
    for split in E.SPLITS:
        pos = pd.read_csv(os.path.join(PROCESSED, f"positions_{split}.csv"), dtype={"record": str})
        rec = pd.read_csv(os.path.join(PROCESSED, f"records_{split}.csv"), dtype={"record": str}).set_index("record")
        assert set(pos.columns) == {"beat_id", "db", "record", "sample", "fs", "predict"}
        # the released flag is a function of positions and record length only
        for r, g in pos.groupby("record"):
            g = g.sort_values("sample")
            want = predict_flags(g["sample"].to_numpy(), rec.loc[r, "fs"], rec.loc[r, "sig_len"])
            assert (g["predict"].to_numpy() == want).all()


@needs_data
def test_lowdata_subsets_are_reproducible():
    """Review V003 M3: the frozen subsets equal units.draw_lowdata_subsets on the DS1 units."""
    lab = pd.read_csv(os.path.join(PROCESSED, "labels_ds1.csv"), dtype={"record": str})
    frozen = json.load(open(os.path.join(PROCESSED, "lowdata_subsets.json")))
    assert draw_lowdata_subsets(lab[lab["is_unit"]]) == frozen
    assert frozen["subsets"]["k5"]["records"] == ["101", "122", "209", "215", "223"]
