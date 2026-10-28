"""EV1 scorer: macro-F1 over N/S/V on fixed beat units, secondary metrics, and the paired two-level bootstrap.

`labels` frames have one row per prediction-set beat: beat_id, record, aami, is_unit. Pipelines predict every row;
only rows with is_unit (class N, S or V) enter the primary metric. `hours` maps record -> recording duration in hours.
"""
import numpy as np
import pandas as pd

from . import evalspec as E

K = len(E.CLASSES)
IDX = {c: i for i, c in enumerate(E.CLASSES)}
PROB_COLS = [f"prob_{c}" for c in E.CLASSES]
# Truth classes of de Chazal et al. 2004, Table V. A beat of any other class (e.g. one SVDB `B` beat) counts as Q.
TRUTH5 = ("N", "S", "V", "F", "Q")


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
    """Primary metric and N/S/V-restricted per-class metrics: every count here is over N/S/V-truth units only."""
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
            "nsv_record_avg_sensitivity":
                float((rec_tp[has_true, i] / rec_true[has_true, i]).mean()) if has_true.any() else None,
            "nsv_record_avg_ppv": float((rec_tp[has_pred, i] / rec_pred[has_pred, i]).mean()) if has_pred.any() else None,
            "nsv_class_false_flags_per_hour":
                float((pred_n[i] - tp[i]) / total_hours) if total_hours and c != "N" else None,
        }
    out["confusion_true_by_pred"] = total.tolist()
    return out


def paper_metrics(truth, pred):
    """Gross (beat-pooled) VEB and SVEB measures of de Chazal et al. 2004, Table V(a)-(b), over the full prediction
    set. V: FP = Nv + Sv, and Fv, Qv are neither rewarded nor penalised. S: FP = Ns + Vs + Fs, and Qs is neither
    rewarded nor penalised. Pipelines predict N/S/V only, so the f and q prediction columns are empty."""
    truth, pred = np.asarray(truth), np.asarray(pred)
    t = np.where(np.isin(truth, TRUTH5), truth, "Q")
    cm = {(a, b): int(((t == a) & (pred == b)).sum()) for a in TRUTH5 for b in E.CLASSES}

    def block(c, fp_from, ignored):
        tp = cm[(c, c)]
        fn = sum(cm[(c, b)] for b in E.CLASSES if b != c)
        fp = sum(cm[(a, c)] for a in fp_from)
        ign = sum(cm[(a, c)] for a in ignored)
        tn = len(t) - tp - fn - fp - ign
        return {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "not_scored": ign,
                "sensitivity": tp / (tp + fn) if tp + fn else None,
                "ppv": tp / (tp + fp) if tp + fp else None,
                "fpr": fp / (tn + fp) if tn + fp else None}

    return {"VEB": block("V", ("N", "S"), ("F", "Q")), "SVEB": block("S", ("N", "V", "F"), ("Q",)),
            "confusion_truth5_by_pred": [[cm[(a, b)] for b in E.CLASSES] for a in TRUTH5]}


def review_burden(truth, pred, total_hours):
    """Flags per hour over the full prediction set, for a general ectopic-beat review workflow."""
    truth, pred = np.asarray(truth), np.asarray(pred)
    flag = np.isin(pred, ("S", "V"))
    ectopic = np.isin(truth, ("S", "V"))
    per_h = lambda m: float(m.sum() / total_hours)
    return {
        "hours": total_hours,
        "ectopic_flags_per_hour": per_h(flag),  # every S or V prediction
        "normal_beats_flagged_per_hour": per_h(flag & (truth == "N")),
        "f_q_beats_flagged_per_hour": per_h(flag & ~np.isin(truth, E.CLASSES)),
        "s_v_class_swaps_per_hour": per_h(flag & ectopic & (truth != pred)),  # ectopic beat flagged, wrong class
        "missed_ectopic_per_hour": per_h(ectopic & (pred == "N")),
    }


def arm_summary(labels, aligned, hours=None):
    """Every reported metric of one prediction set (one seed of one arm), from validated, aligned predictions."""
    units, au = _units(labels, aligned)
    records = sorted(labels["record"].astype(str).unique())
    cm = per_record_confusion(units, au, records)
    result = summarize(cm, records, hours)
    for c in ("S", "V"):
        result["per_class"][c]["auprc"] = average_precision(units["aami"].eq(c), au[f"prob_{c}"])
    result["n_predict"] = int(len(labels))
    result["n_units"] = int(len(units))
    truth, pred = labels["aami"].to_numpy(), aligned["pred"].to_numpy()
    nonunit = ~labels["is_unit"].to_numpy(dtype=bool)
    result["nonunit_predictions"] = {
        a: {c: int(((truth[nonunit] == a) & (pred[nonunit] == c)).sum()) for c in E.CLASSES}
        for a in sorted(set(truth[nonunit]))
    }
    result["paper_compatible"] = paper_metrics(truth, pred)
    rec_all = labels["record"].astype(str).to_numpy()
    result["paper_compatible_per_record"] = {
        r: paper_metrics(truth[rec_all == r], pred[rec_all == r])["confusion_truth5_by_pred"] for r in records}
    if hours:
        result["review_burden"] = review_burden(truth, pred, float(sum(hours[r] for r in records)))
    result["per_record"] = {r: {"confusion_true_by_pred": cm[i].tolist(), "n": int(cm[i].sum())}
                            for i, r in enumerate(records)}
    return result


def score(pred, labels, hours=None):
    return arm_summary(labels, validate(pred, labels), hours)


def seed_average(summaries):
    """Arithmetic mean over seeds of every scalar metric of arm_summary (None when any seed has None). Count matrices
    and per-record tables are not averaged; they are kept per seed. This is not the score of a seed ensemble."""
    out = {}
    for k, v in summaries[0].items():
        vals = [s[k] for s in summaries]
        if k == "per_record" or isinstance(v, (list, bool, str)):
            continue
        if isinstance(v, dict):
            out[k] = seed_average(vals)
        else:
            out[k] = None if any(x is None for x in vals) else float(np.mean(vals))
    return out


def _arm(preds, labels, records, hours):
    """Per-seed per-record confusions (n_seeds, n_records, K, K), per-seed unit probabilities, per-seed summaries."""
    cms, probs, summaries, units = [], [], [], None
    for p in preds:
        aligned = validate(p, labels)
        units, au = _units(labels, aligned)
        cms.append(per_record_confusion(units, au, records))
        probs.append(au[PROB_COLS].to_numpy(dtype=float))
        summaries.append(arm_summary(labels, aligned, hours))
    return np.stack(cms), np.stack(probs), units, summaries


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
    """Three-way outcome of the decision rule, with the reason it was reached."""
    if hi < 0:
        return "unfavorable", "CI upper bound < 0"
    if lo > 0:
        if delta < E.PRACTICAL_GAIN:
            return "no detectable change", "detectable gain below the practical threshold"
        if delta_without_dominant is not None and delta_without_dominant <= 0:
            return "no detectable change", "gain disappears without the dominant record"
        return "favorable", "meets the decision rule"
    return "no detectable change", "CI includes 0"


def slice_decision(lo, hi):
    """Slice rule: favorable only if the slice-level CI lower bound is > 0 (no practical or dominant-record test)."""
    return "favorable" if lo > 0 else "unfavorable" if hi < 0 else "no detectable change"


def compare(cand_preds, base_preds, labels, hours=None, role="diagnostic", dominant_record=None, n_boot=None,
            seed=E.BOOT_SEED):
    """Paired comparison of two arms on the same units. Each arm is a list of prediction frames, one per seed; the arm
    score is the mean of the per-seed macro-F1 values (not the macro-F1 of a seed ensemble). Uncertainty: two-level
    bootstrap, records resampled jointly for both arms and seeds resampled independently within each arm; one set of
    replicates serves every interval. The primary interval is at CI_LEVEL, except for a low-data slice comparison,
    whose primary delta is itself a member of the slice family and uses SLICE_CI_LEVEL. The headline comparison also
    reports its two slice-family members (S and V F1) at SLICE_CI_LEVEL with the slice rule."""
    if role not in E.ROLES:
        raise PredictionError(f"unknown role {role!r}; one of {sorted(E.ROLES)}")
    n_boot = n_boot or E.N_BOOT
    if not cand_preds or len(cand_preds) != len(base_preds):
        raise PredictionError(f"arms need equal, non-zero seed counts (got {len(cand_preds)} and {len(base_preds)})")
    records = sorted(labels["record"].astype(str).unique())
    cc, cprob, units, c_sum = _arm(cand_preds, labels, records, hours)
    bc, bprob, _, b_sum = _arm(base_preds, labels, records, hours)
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

    def ci(draws, level):
        return [float(x) for x in np.quantile(draws, [(1 - level) / 2, 1 - (1 - level) / 2])]

    lowdata = role in ("lowdata_k5", "lowdata_k11")
    level = E.SLICE_CI_LEVEL if lowdata else E.CI_LEVEL
    lo, hi = ci(d_macro, level)

    loo = {}
    for i, r in enumerate(records):
        w = one_r.copy()
        w[0, i] = 0
        loo[r] = float(_boot_f1(cc, w, one_s)[0].mean() - _boot_f1(bc, w, one_s)[0].mean())
    d_wo = loo.get(str(dominant_record)) if dominant_record is not None else None
    outcome, reason = decide(delta, lo, hi, d_wo)

    inference = {"headline": "confirmatory (pre-registered headline pair)",
                 "lowdata_k5": "slice-family member", "lowdata_k11": "slice-family member",
                 "secondary": "descriptive (not confirmatory; may follow adaptive development on ds2s)",
                 "confirmation": "external confirmation (SVDB pass criterion)",
                 "diagnostic": "diagnostic (no claim)"}[role]
    slice_info = {"family": list(E.SLICE_FAMILY), "m": len(E.SLICE_FAMILY), "ci_level": E.SLICE_CI_LEVEL,
                  "rule": "favorable iff the slice CI lower bound > 0", "members": {}}
    if role == "headline":
        for name, c in (("S_f1", "S"), ("V_f1", "V")):
            s_lo, s_hi = ci(d_cls[:, IDX[c]], E.SLICE_CI_LEVEL)
            slice_info["members"][name] = {"delta": float(c_cls[IDX[c]] - b_cls[IDX[c]]), "ci": [s_lo, s_hi],
                                           "decision": slice_decision(s_lo, s_hi)}
    elif lowdata:
        slice_info["members"][role] = {"delta": delta, "ci": [lo, hi], "decision": slice_decision(lo, hi)}

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
                    "ci": ci(d, E.CI_LEVEL), "ci_level": E.CI_LEVEL}
    return {
        "role": role,
        "n_records": n_rec,
        "n_units": int(len(units)),
        "n_seeds": n_seed,
        "n_boot": n_boot,
        "boot_seed": seed,
        "estimand": "mean over seeds of per-seed macro-F1 (candidate) minus the same for the baseline, on matched units;"
                    " conditional on the DS1 training cohort and the selected configurations",
        "primary": {
            "inference": inference,
            "candidate_macro_f1": float(c_cls.mean()),
            "baseline_macro_f1": float(b_cls.mean()),
            "delta": delta,
            "ci": [lo, hi],
            "ci_level": level,
            "dominant_record": dominant_record,
            "delta_without_dominant_record": d_wo,
            "outcome": outcome,
            "outcome_reason": reason,
            "outcome_without_dominant_record_condition": decide(delta, lo, hi)[0],
            "suspicious_gain": bool(delta >= E.SUSPICIOUS_GAIN),
        },
        "slices": slice_info if slice_info["members"] else None,
        "per_class_f1": {
            c: {"candidate_f1": float(c_cls[i]), "baseline_f1": float(b_cls[i]), "delta": float(c_cls[i] - b_cls[i]),
                "ci": ci(d_cls[:, i], E.CI_LEVEL), "ci_level": E.CI_LEVEL}
            for c, i in IDX.items()
        },
        "auprc": auprc,
        "leave_one_record_out_delta": loo,
        "arms": {
            "candidate": {"per_seed_macro_f1": [s["macro_f1"] for s in c_sum], "seed_average": seed_average(c_sum),
                          "per_seed": c_sum},
            "baseline": {"per_seed_macro_f1": [s["macro_f1"] for s in b_sum], "seed_average": seed_average(b_sum),
                         "per_seed": b_sum},
        },
    }
