"""Frozen evaluation constants (EV1). Changing anything here after approval creates a new evaluation version."""

EV = "EV1"

# Prediction classes for the primary metric (AAMI EC57 superclasses).
CLASSES = ("N", "S", "V")

# AAMI mapping of MIT-BIH beat symbols (de Chazal et al. 2004, doi:10.1109/tbme.2004.827359).
AAMI = {
    **{s: "N" for s in "NLRej"},
    **{s: "S" for s in "AaJS"},
    **{s: "V" for s in "VE"},
    "F": "F",
    **{s: "Q" for s in "/fQ"},
}

# Every WFDB beat annotation code. Positions of all of these are released to pipelines (for RR intervals);
# only beats mapped to CLASSES are evaluation units.
BEAT_SYMBOLS = set("NLRBAaJSVrFejnE/fQ?!")

# Prediction set (label-free): every beat annotation except the first and last of a record and any beat within
# EDGE_SEC of the record start or end. Evaluation units are the prediction-set beats whose class is in CLASSES.
EDGE_SEC = 1.0

# Decision-time boundary for beat i at R-peak t_i: inputs may use signal and beat positions up to
# b_i = max(t_{i+1}, t_i + LOOKAHEAD_SEC) (one-beat lookahead, at least LOOKAHEAD_SEC), nothing later.
LOOKAHEAD_SEC = 1.0

# Record lists. Paced records 102, 104, 107, 217 are excluded everywhere (AAMI practice).
PACED = ["102", "104", "107", "217"]
DS1 = ["101", "106", "108", "109", "112", "114", "115", "116", "118", "119", "122",
       "124", "201", "203", "205", "207", "208", "209", "215", "220", "223", "230"]
DS2 = ["100", "103", "105", "111", "113", "117", "121", "123", "200", "202", "210",
       "212", "213", "214", "219", "221", "222", "228", "231", "232", "233", "234"]
# Record 202 comes from the same subject as DS1 record 201 (ANOMALIES A004), so the strict test split drops it.
DS2_STRICT = [r for r in DS2 if r != "202"]

# split id -> (database, records, labels released to pipelines?)
SPLITS = {
    "ds1": ("mitdb", DS1, True),          # training and all tuning (grouped CV inside)
    "ds2s": ("mitdb", DS2_STRICT, False),  # primary full-evaluation test split
    "ds2": ("mitdb", DS2, False),          # secondary: the published de Chazal split, for literature comparability
    "svdb": ("svdb", None, False),         # confirmation set: access-capped, logged (None = all records in RECORDS)
}
CONFIRMATION_SPLITS = {"svdb"}

# Comparison procedure (metric units: macro-F1 over N, S, V; positive delta = candidate better).
PRACTICAL_GAIN = 0.02
SUSPICIOUS_GAIN = 0.05
N_BOOT = 2000
BOOT_SEED = 20261026
CI_LEVEL = 0.95

# Record whose exclusion must not erase a favorable result (ANOMALIES A001: 232 holds 77.5% of ds2s S units).
# "favorable" additionally requires the point delta without this record to be > 0.
DOMINANT_RECORD = {"ds2s": "232", "ds2": "232"}

# Arms must have exactly this many seeds for a headline comparison (enforced: equal counts; warned if not this).
N_SEEDS = 5

# Confirmation-set accesses allowed project-wide (enforced from runs/confirmation_access.jsonl).
CONFIRMATION_CAP = 2

# DS1 grouped cross-validation folds for tuning (fixed so that every arm tunes on the same folds).
N_CV_FOLDS = 5
