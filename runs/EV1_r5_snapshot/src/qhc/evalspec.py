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
# only beats mapped to CLASSES are evaluation units. Non-beat annotations are never beat positions: in particular
# `!` (ventricular flutter wave) is a non-beat code in the PhysioNet annotation definitions (EV1 r4, review item R1).
BEAT_SYMBOLS = set("NLRBAaJSVrFejnE/fQ?")

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
N_BOOT = 8000  # one replicate set for every interval, enough draws for the 98.75% slice tails
BOOT_SEED = 20261026
CI_LEVEL = 0.95

# Pre-declared slice family of the headline pair (EV1 r4, review item R4): fixed now, never extended after results.
# S_f1 and V_f1 come from the headline comparison; lowdata_k5 and lowdata_k11 from the two low-data comparisons.
SLICE_FAMILY = ("S_f1", "V_f1", "lowdata_k5", "lowdata_k11")
SLICE_CI_LEVEL = 1 - (1 - CI_LEVEL) / len(SLICE_FAMILY)  # Bonferroni over the fixed family: 0.9875

# Comparison roles. Strict roles need exactly N_SEEDS distinct seeded runs per arm, each with a run manifest bound to
# its prediction file, checked before any label access (review item R5). `headline` is the single pre-registered
# confirmatory pair and is immutable once evaluated; `secondary` comparisons are descriptive.
ROLES = {
    "headline": {"splits": ("ds2s",), "strict": True},
    "lowdata_k5": {"splits": ("ds2s",), "strict": True},
    "lowdata_k11": {"splits": ("ds2s",), "strict": True},
    "secondary": {"splits": ("ds2s", "ds2"), "strict": True},
    "confirmation": {"splits": ("svdb",), "strict": True},
    "diagnostic": {"splits": ("ds1", "ds2s", "ds2"), "strict": False},  # minimal references, null self-comparison
}
# Roles that run once per split with one fixed set of runs per arm (identity = per-arm sets of file content hashes).
RUN_ONCE_ROLES = ("headline", "lowdata_k5", "lowdata_k11")
# Order on the test splits ds2s and ds2 (review V003 B1): until the headline is logged, the only predictions that may be
# scored there are the minimal references below (runs/EV1_reference_r4/); diagnostics there are limited to them at all
# times; score, secondary and low-data runs wait for the headline.
TEST_SPLITS = ("ds2s", "ds2")
REFERENCE_PRED_SHA256 = {
    "d16215992953f4fb3f23a4f5bfc64b658c13e40c04d594fc6a9e879a7184a3b5",  # const_n ds2s
    "b1744586bda91aa39cad9322c8639c5c8ba9d88cc41dbd9abdaceb049fbae759",  # rr_rule ds2s
    "418cb8b5da2624d29ffa92f91919a112cab53f6df80f24a4e90f2ed27b583b78",  # const_n ds2
    "459139c96058f1f24ec49045559a46212ae6de0d84e1035cd317b579b0fa820a",  # rr_rule ds2
}

# Reduced-data refitting slice (EVAL.md slice c): DS1 record-subset sizes, drawn by units.draw_lowdata_subsets.
LOWDATA_K = (5, 11)
LOWDATA_MIN_UNITS = 10  # each subset must hold at least this many S and V units

# Record whose exclusion must not erase a favorable result (ANOMALIES A001: 232 holds 77.5% of ds2s S units).
# "favorable" additionally requires the point delta without this record to be > 0.
DOMINANT_RECORD = {"ds2s": "232", "ds2": "232"}

# Arms in strict roles must have exactly this many distinct seeded runs (diagnostic comparisons may use fewer).
N_SEEDS = 5
# Keys every run manifest (<prediction file without .csv>.run.json) must carry in strict roles. shot_seed is null for
# arms without measurement sampling (classical reservoirs).
RUN_KEYS = ("arm_id", "seed", "split", "config_id", "code_revision", "model_artifact", "model_artifact_sha256",
            "reservoir_seed", "shot_seed", "prediction_sha256")

# Confirmation-set accesses allowed project-wide (enforced from runs/confirmation_access.jsonl).
CONFIRMATION_CAP = 2

# DS1 grouped cross-validation folds for tuning (fixed so that every arm tunes on the same folds).
N_CV_FOLDS = 5
