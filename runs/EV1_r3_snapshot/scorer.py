"""EV1 scorer: macro-F1 over N/S/V on fixed beat units, and the paired two-level bootstrap comparison.

`labels` frames have one row per prediction-set beat: beat_id, record, aami, is_unit. Pipelines predict every row;
only rows with is_unit (class N, S or V) enter the metric. `hours` maps record -> recording duration in hours.
"""
import numpy as np
import pandas as pd

from . import evalspec as E

K = len(E.CLASSES)
IDX = {c: i for i, c in enumerate(E.CLASSES)}
PROB_COLS = [f"prob_{c}" for c in E.CLASSES]


class PredictionError(ValueError):
    """Malformed prediction file; the scorer refuses to score it."""


def validate(pred, labels):
    """Check a prediction frame against the full prediction set and return it aligned to the label rows."""
    if not isinstance(pred, pd.DataFrame) or not {"beat_id", "pred"} <= set(pred.columns):
        raise PredictionError("predictions need columns 'beat_id' and 'pred'")
    if not set(PROB_COLS) <= set(pred.columns):
        raise PredictionError(f"probability columns {PROB_COLS} are required")
    if pred["beat_id"].isna().any():
        raise PredictionError("missing beat_id values")
    dup = pred["beat_id"].duplicated()
    if dup.any():
        raise PredictionError(f"{int(dup.sum())} duplicate beat_id rows, e.g. {pred.loc[dup, 'beat_id'].iloc[0]}")
    bad = ~pred["pred"].isin(E.CLASSES)
    if bad.any():
        raise PredictionError(f"{int(bad.sum())} predictions outside {E.CLASSES}, e.g. {pred.loc[bad, 'pred'].iloc[0]!r}")
    p = pred[PROB_COLS].to_numpy(dtype=float)
    if not np.isfinite(p).all():
        raise PredictionError("non-finite probabilities")
    if (p < 0).any() or (p > 1).any() or not np.allclose(p.sum(1), 1.0, atol=1e-4):
        raise PredictionError("probabilities must lie in [0, 1] and sum to 1 per beat")
    want, got = set(labels["beat_id"]), set(pred["beat_id"])
    missing, extra = want - got, got - want
    if missing:
        raise PredictionError(f"{len(missing)} prediction-set beats have no prediction, e.g. {sorted(missing)[0]}")
    if extra:
        raise PredictionError(f"{len(extra)} predictions are not in the prediction set, e.g. {sorted(extra)[0]}")
    return pred.set_index("beat_id").loc[labels["beat_id"]].reset_index()


def _units(labels, aligned):
    m = labels["is_unit"].to_numpy(dtype=bool)
    return labels[m].reset_index(drop=True), aligned[m].reset_index(drop=True)


def per_record_confusion(units, aligned_units, records):
    """Array (n_records, K, K) of confusion counts [true, pred] in the given record order."""
    t = units["aami"].map(IDX).to_numpy()
    p = aligned_units["pred"].map(IDX).to_numpy()
    ridx = {r: i for i, r in enumerate(records)}
    r = units["record"].astype(str).map(ridx).to_numpy()
    cm = np.zeros((len(records), K, K), dtype=np.int64)
    np.add.at(cm, (r, t, p), 1)
    return cm


def f1_from_confusion(cm):
    """Per-class F1 from a (..., K, K) confusion array. A class absent from both truth and predictions scores 1
    (vacuous agreement); a class with TP = 0 but some FP or FN scores 0."""
    tp = np.diagonal(cm, axis1=-2, axis2=-1).astype(float)
    fp = cm.sum(-2) - tp
    fn = cm.sum(-1) - tp
    denom = 2 * tp + fp + fn
    return np.where(denom == 0, 1.0, 2 * tp / np.where(denom == 0, 1, denom))


def average_precision(y, score):
    """One-vs-rest average precision (area under the step precision-recall curve), ties grouped."""
    y = np.asarray(y, dtype=bool)
    if not y.any():
        return None
    order = np.argsort(-np.asarray(score), kind="mergesort")
    s, yy = np.asarray(score)[order], y[order]
    last = np.r_[np.flatnonzero(np.diff(s)), len(s) - 1]  # last index of each distinct score
    tp = np.cumsum(yy)[last]
    fp = (last + 1) - tp
    precision = tp / (tp + fp)
    recall = tp / y.sum()
    return float(np.sum(np.diff(np.r_[0.0, recall]) * precision))


def _boot_ap(y, prob, rec_of_unit, rec_w, seed_w, chunk=100):
    """Seed-weighted average precision per bootstrap replicate. y (n,), prob (S, n), rec_of_unit (n,) record index,
    rec_w (B, R) record multiplicities, seed_w (B, S) -> (B,). Units carry their record's multiplicity as weight."""
    out = np.zeros(rec_w.shape[0])
    for s in range(prob.shape[0]):
        order = np.argsort(-prob[s], kind="mergesort")
        ps, ys, rs = prob[s][order], y[order].astype(float), rec_of_unit[order]
        last = np.r_[np.flatnonzero(np.diff(ps)), len(ps) - 1]
        for b0 in range(0, rec_w.shape[0], chunk):
            w = rec_w[b0:b0 + chunk][:, rs]  # (b, n)
            tp = np.cumsum(w * ys, axis=1)[:, last]
            fp = np.cumsum(w * (1 - ys), axis=1)[:, last]
            prec = np.where(tp + fp > 0, tp / np.maximum(tp + fp, 1e-12), 0.0)
            rec = tp / np.maximum(tp[:, -1:], 1e-12)
            ap = np.sum(np.diff(np.concatenate([np.zeros((len(w), 1)), rec], axis=1), axis=1) * prec, axis=1)
            out[b0:b0 + chunk] += ap * seed_w[b0:b0 + chunk, s]
    return out / seed_w.sum(1)


def summarize(cm_records, records, hours=None):
    total = cm_records.sum(0)
    tp = np.diag(total).astype(float)
    pred_n, true_n = total.sum(0), total.sum(1)
    f1 = f1_from_confusion(total)
    out = {"macro_f1": float(f1.mean()), "accuracy": float(tp.sum() / total.sum()), "per_class": {}}
    rec_tp = np.diagonal(cm_records, axis1=1, axis2=2).astype(float)
    rec_true, rec_pred = cm_records.sum(2), cm_records.sum(1)
    total_hours = float(sum(hours[r] for r in records)) if hours else None
    for c, i in IDX.items():
        has_true, has_pred = rec_true[:, i] > 0, rec_pred[:, i] > 0
        out["per_class"][c] = {
            "support": int(true_n[i]),
            "predicted": int(pred_n[i]),
            "sensitivity": float(tp[i] / true_n[i]) if true_n[i] else None,
            "ppv": float(tp[i] / pred_n[i]) if pred_n[i] else None,
            "f1": float(f1[i]),
            "record_avg_sensitivity": float((rec_tp[has_true, i] / rec_true[has_true, i]).mean()) if has_true.any() else None,
            "record_avg_ppv": float((rec_tp[has_pred, i] / rec_pred[has_pred, i]).mean()) if has_pred.any() else None,
            "false_flags_per_hour": float((pred_n[i] - tp[i]) / total_hours) if total_hours and c != "N" else None,
        }
    out["confusion_true_by_pred"] = total.tolist()
    return out


def score(pred, labels, hours=None):
    aligned = validate(pred, labels)
    units, au = _units(labels, aligned)
    records = sorted(labels["record"].astype(str).unique())
    cm = per_record_confusion(units, au, records)
    result = summarize(cm, records, hours)
    for c in ("S", "V"):
        result["per_class"][c]["auprc"] = average_precision(units["aami"].eq(c), au[f"prob_{c}"])
    result["n_predict"] = int(len(labels))
    result["n_units"] = int(len(units))
    nonunit = labels.loc[~labels["is_unit"].to_numpy(dtype=bool), "aami"].to_numpy()
    nonunit_pred = aligned.loc[~labels["is_unit"].to_numpy(dtype=bool), "pred"].to_numpy()
    result["nonunit_predictions"] = {
        a: {c: int(((nonunit == a) & (nonunit_pred == c)).sum()) for c in E.CLASSES} for a in sorted(set(nonunit))
    }
    result["per_record"] = {r: {"confusion_true_by_pred": cm[i].tolist(), "n": int(cm[i].sum())} for i, r in enumerate(records)}
    return result


def _arm(preds, labels, records):
    """Per-seed per-record confusions (n_seeds, n_records, K, K) and per-seed unit probabilities."""
    cms, probs, units = [], [], None
    for p in preds:
        aligned = validate(p, labels)
        units, au = _units(labels, aligned)
        cms.append(per_record_confusion(units, au, records))
        probs.append(au[PROB_COLS].to_numpy(dtype=float))
    return np.stack(cms), np.stack(probs), units


def _boot_f1(cm_arm, rec_w, seed_w):
    """Seed- and record-weighted per-class F1: rec_w (B, R), seed_w (B, S) -> (B, K)."""
    tot = np.einsum("br,srij->bsij", rec_w, cm_arm)
    f1 = f1_from_confusion(tot)  # (B, S, K)
    return np.einsum("bsk,bs->bk", f1, seed_w) / seed_w.sum(1, keepdims=True)


def _record_weights(rng, n_boot, n_rec):
    w = np.zeros((n_boot, n_rec))
    np.add.at(w, (np.repeat(np.arange(n_boot), n_rec), rng.integers(0, n_rec, size=n_boot * n_rec)), 1)
    return w


def decide(delta, lo, hi, delta_without_dominant=None):
    if delta >= E.PRACTICAL_GAIN and lo > 0 and (delta_without_dominant is None or delta_without_dominant > 0):
        return "favorable"
    if hi < 0:
        return "unfavorable"
    return "no detectable change"


def compare(cand_preds, base_preds, labels, dominant_record=None, n_comparisons=1, n_boot=None, seed=E.BOOT_SEED):
    """Paired comparison of two arms on the same units. Each arm is a list of prediction frames, one per seed; the arm
    score is the seed-averaged macro-F1. Uncertainty: two-level bootstrap, records resampled jointly for both arms and
    seeds resampled independently within each arm. The CI level is Bonferroni-adjusted for n_comparisons, and the
    default number of replicates scales with it (N_BOOT x n_comparisons) so the tails keep enough draws."""
    n_boot = n_boot or E.N_BOOT * n_comparisons
    if not cand_preds or len(cand_preds) != len(base_preds):
        raise PredictionError(f"arms need equal, non-zero seed counts (got {len(cand_preds)} and {len(base_preds)})")
    records = sorted(labels["record"].astype(str).unique())
    cc, cprob, units = _arm(cand_preds, labels, records)
    bc, bprob, _ = _arm(base_preds, labels, records)
    n_rec, n_seed = len(records), cc.shape[0]
    one_r, one_s = np.ones((1, n_rec)), np.ones((1, n_seed))
    c_cls, b_cls = _boot_f1(cc, one_r, one_s)[0], _boot_f1(bc, one_r, one_s)[0]
    delta = float(c_cls.mean() - b_cls.mean())

    rng = np.random.default_rng(seed)
    rw = _record_weights(rng, n_boot, n_rec)
    sw_c = np.zeros((n_boot, n_seed))
    sw_b = np.zeros((n_boot, n_seed))
    np.add.at(sw_c, (np.repeat(np.arange(n_boot), n_seed), rng.integers(0, n_seed, size=n_boot * n_seed)), 1)
    np.add.at(sw_b, (np.repeat(np.arange(n_boot), n_seed), rng.integers(0, n_seed, size=n_boot * n_seed)), 1)
    d_cls = _boot_f1(cc, rw, sw_c) - _boot_f1(bc, rw, sw_b)  # (B, K)
    d_macro = d_cls.mean(1)
    level = 1 - (1 - E.CI_LEVEL) / n_comparisons
    q = [(1 - level) / 2, 1 - (1 - level) / 2]
    lo, hi = (float(x) for x in np.quantile(d_macro, q))

    loo = {}
    for i, r in enumerate(records):
        w = one_r.copy()
        w[0, i] = 0
        loo[r] = float(_boot_f1(cc, w, one_s)[0].mean() - _boot_f1(bc, w, one_s)[0].mean())
    d_wo = loo.get(str(dominant_record)) if dominant_record is not None else None

    per_seed = lambda arm: [float(f1_from_confusion(arm[s].sum(0)).mean()) for s in range(arm.shape[0])]
    ridx = {r: i for i, r in enumerate(records)}
    rec_of_unit = units["record"].astype(str).map(ridx).to_numpy()
    auprc = {}
    for c in ("S", "V"):
        y = units["aami"].eq(c).to_numpy()
        pc, pb = cprob[:, :, IDX[c]], bprob[:, :, IDX[c]]
        point_c = float(np.mean([average_precision(y, pc[s]) for s in range(n_seed)]))
        point_b = float(np.mean([average_precision(y, pb[s]) for s in range(n_seed)]))
        d = _boot_ap(y, pc, rec_of_unit, rw, sw_c) - _boot_ap(y, pb, rec_of_unit, rw, sw_b)
        auprc[c] = {"candidate": point_c, "baseline": point_b, "delta": point_c - point_b,
                    "ci": [float(x) for x in np.quantile(d, q)]}
    return {
        "n_records": n_rec,
        "n_units": int(len(units)),
        "n_seeds": n_seed,
        "candidate_macro_f1": float(c_cls.mean()),
        "baseline_macro_f1": float(b_cls.mean()),
        "delta": delta,
        "ci": [lo, hi],
        "ci_level": level,
        "n_comparisons": n_comparisons,
        "n_boot": n_boot,
        "boot_seed": seed,
        "dominant_record": dominant_record,
        "delta_without_dominant_record": d_wo,
        "outcome": decide(delta, lo, hi, d_wo),
        "outcome_without_dominant_record_condition": decide(delta, lo, hi),
        "suspicious_gain": bool(delta >= E.SUSPICIOUS_GAIN),
        "per_class": {
            c: {"candidate_f1": float(c_cls[i]), "baseline_f1": float(b_cls[i]), "delta": float(c_cls[i] - b_cls[i]),
                "ci": [float(x) for x in np.quantile(d_cls[:, i], q)]}
            for c, i in IDX.items()
        },
        "auprc": auprc,
        "leave_one_record_out_delta": loo,
        "candidate_per_seed": per_seed(cc),
        "baseline_per_seed": per_seed(bc),
    }
