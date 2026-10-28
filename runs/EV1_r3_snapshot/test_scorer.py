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
from qhc.units import predict_flags

ROOT = os.path.dirname(os.path.dirname(__file__))
PROCESSED = os.path.join(ROOT, "runs", "data", "processed", E.EV)


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
    # false flags per hour: S FP = 1, V FP = 1, over 1.0 h
    assert r["per_class"]["S"]["false_flags_per_hour"] == pytest.approx(1.0)
    assert r["per_class"]["V"]["false_flags_per_hour"] == pytest.approx(1.0)
    # record-averaged: S sensitivity A 1/1, B 0/1 -> 0.5; V PPV A 1/1, B 1/2 -> 0.75
    assert r["per_class"]["S"]["record_avg_sensitivity"] == pytest.approx(0.5)
    assert r["per_class"]["V"]["record_avg_ppv"] == pytest.approx(0.75)


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
    c = scorer.compare([p], [p], lab, n_boot=300)
    assert c["delta"] == 0 and c["ci"] == [0.0, 0.0] and c["outcome"] == "no detectable change"


def test_compare_directions_and_suspicious_flag():
    lab = _synthetic()
    good, bad = make_pred(lab, lab["aami"]), make_pred(lab, "N" * len(lab))
    up = scorer.compare([good], [bad], lab, n_boot=300)
    down = scorer.compare([bad], [good], lab, n_boot=300)
    assert up["outcome"] == "favorable" and up["suspicious_gain"] and up["ci"][0] > 0
    assert down["outcome"] == "unfavorable" and down["delta"] == pytest.approx(-up["delta"])
    assert up["per_class"]["S"]["delta"] == pytest.approx(1.0) and up["per_class"]["S"]["ci"][0] > 0
    assert up["auprc"]["S"]["delta"] > 0 and up["auprc"]["S"]["ci"][0] > 0


def test_small_detectable_regression_is_unfavorable():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    worse = truth.copy()
    worse[np.flatnonzero(truth == "S")[::12]] = "N"  # lose ~8% of S beats in every record
    c = scorer.compare([make_pred(lab, worse)], [make_pred(lab, truth)], lab, n_boot=500)
    assert -E.PRACTICAL_GAIN < c["delta"] < 0 and c["ci"][1] < 0 and c["outcome"] == "unfavorable"


def test_gain_carried_by_one_record_is_not_favorable():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    base = np.where(truth == "S", "N", truth)  # baseline misses every S beat
    cand = base.copy()
    in_r0 = (lab["record"] == "r0").to_numpy()
    cand[in_r0] = truth[in_r0]  # candidate fixes S only in r0 ...
    cand[(~in_r0) & (truth == "V")] = "N"  # ... and loses V elsewhere
    c = scorer.compare([make_pred(lab, cand)], [make_pred(lab, base)], lab, dominant_record="r0", n_boot=300)
    assert c["delta_without_dominant_record"] < 0
    assert c["outcome"] != "favorable"
    assert c["leave_one_record_out_delta"]["r0"] == pytest.approx(c["delta_without_dominant_record"])


def test_seed_resampling_widens_ci_and_counts_are_enforced():
    lab = _synthetic()
    truth = lab["aami"].to_numpy()
    rng = np.random.default_rng(1)
    noisy = [make_pred(lab, np.where(rng.random(len(lab)) < q, "N", truth)) for q in (0.05, 0.1, 0.2, 0.3, 0.4)]
    a = scorer.compare(noisy, noisy[::-1], lab, n_boot=400)
    assert a["delta"] == pytest.approx(0) and a["ci"][1] - a["ci"][0] > 0.01  # seed spread enters the CI
    assert a["ci"] == scorer.compare(noisy, noisy[::-1], lab, n_boot=400)["ci"]  # reproducible
    assert a["candidate_macro_f1"] == pytest.approx(np.mean(a["candidate_per_seed"]))
    with pytest.raises(scorer.PredictionError, match="equal"):
        scorer.compare(noisy[:1], noisy, lab, n_boot=50)


def test_compare_rejects_extra_rows_and_adjusts_level():
    lab = _synthetic()
    p = make_pred(lab, lab["aami"])
    extra = pd.concat([p, make_pred(make_labels({"zz": "N"}), "N")])
    with pytest.raises(scorer.PredictionError, match="not in the prediction set"):
        scorer.compare([extra], [p], lab, n_boot=50)
    assert scorer.compare([p], [p], lab, n_comparisons=3, n_boot=50)["ci_level"] == pytest.approx(1 - 0.05 / 3)


def test_rr_rule_reference_uses_positions_only():
    s = [0, 100, 200, 300, 400, 470, 600, 700]  # beat at 470 is premature (70 < 0.85 * 100)
    pos = pd.DataFrame({"beat_id": [f"x:A:{v}" for v in s], "record": "A", "sample": s, "predict": True})
    pred = ev.reference_predictions("rr_rule", pos).set_index("beat_id")
    assert pred.loc["x:A:470", "pred"] == "S" and (pred.drop("x:A:470")["pred"] == "N").all()
    assert (pred[[f"prob_{c}" for c in E.CLASSES]].sum(1) == 1).all()


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


# ---- confirmation guard (synthetic files; never touches the real confirmation set or log) ----
def _fake_processed(tmp_path):
    lab = make_labels({"A": "NNSV", "B": "NVNN"})
    proc = tmp_path / "processed"
    (proc / "confirm").mkdir(parents=True)
    pos = lab.assign(sample=range(len(lab)), fs=128, predict=True)[["beat_id", "record", "sample", "fs", "predict"]]
    pos.to_csv(proc / "positions_svdb.csv", index=False)
    pd.DataFrame({"record": ["A", "B"], "fs": 128, "sig_len": 230400, "duration_s": 1800.0}).to_csv(
        proc / "records_svdb.csv", index=False)
    lab.to_csv(proc / "confirm" / "labels_svdb.csv", index=False)
    return lab, proc


def test_confirmation_guard(tmp_path, monkeypatch):
    real = os.path.join(PROCESSED, "confirm", "labels_svdb.csv")
    opened = []
    orig_read_csv = pd.read_csv
    monkeypatch.setattr(pd, "read_csv", lambda path, *a, **k: (opened.append(str(path)), orig_read_csv(path, *a, **k))[1])
    lab, proc = _fake_processed(tmp_path)
    log = tmp_path / "access.jsonl"
    monkeypatch.setattr(ev, "PROCESSED", str(proc))
    monkeypatch.setattr(ev, "ACCESS_LOG", str(log))
    good = tmp_path / "good.csv"
    make_pred(lab, lab["aami"]).to_csv(good, index=False)
    bad = tmp_path / "bad.csv"
    make_pred(lab, lab["aami"]).iloc[1:].to_csv(bad, index=False)
    out = str(tmp_path / "s.json")
    with pytest.raises(PermissionError):
        ev.load_labels("svdb", processed=str(proc))
    with pytest.raises(SystemExit):  # no reason given
        ev.main(["score", "--split", "svdb", "--pred", str(good), "--id", "x", "--out", out])
    with pytest.raises(scorer.PredictionError):  # malformed file is rejected before any access is logged
        ev.main(["score", "--split", "svdb", "--pred", str(bad), "--id", "x", "--out", out, "--confirm-reason", "t"])
    assert not log.exists()
    for _ in range(E.CONFIRMATION_CAP):
        ev.main(["score", "--split", "svdb", "--pred", str(good), "--id", "x", "--out", out, "--confirm-reason", "t"])
    assert sum(1 for _ in open(log)) == E.CONFIRMATION_CAP
    with pytest.raises(SystemExit, match="cap"):
        ev.main(["score", "--split", "svdb", "--pred", str(good), "--id", "x", "--out", out, "--confirm-reason", "t"])
    assert not any(os.path.abspath(p) == os.path.abspath(real) for p in opened)  # the real confirmation labels stay closed


# ---- real-data checks ----
manifest_path = os.path.join(PROCESSED, "manifest.json")
needs_data = pytest.mark.skipif(not os.path.exists(manifest_path), reason="run python -m qhc.units first")


@needs_data
def test_units_reproduce_de_chazal_counts():
    m = json.load(open(manifest_path))["splits"]
    for split, ref in {"ds1": {"N": 45866, "S": 944, "V": 3788, "F": 415, "Q": 8},
                       "ds2": {"N": 44259, "S": 1837, "V": 3221, "F": 388, "Q": 7}}.items():
        parts = ("class_counts", "predicted_nonunit_by_aami", "not_predicted_by_aami")
        total = {c: sum(m[split][p].get(c, 0) for p in parts) for c in ref}
        assert total == ref


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
