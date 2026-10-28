"""EV1 evaluation command.

  python -m qhc.evaluate score     --split ds2s --pred P.csv --id NAME --out runs/E###/score_ds2s.json
  python -m qhc.evaluate compare   --split ds2s --role headline --cand C_seed*.csv --base B_seed*.csv
                                   --cand-id X --base-id Y --out runs/E###/compare_ds2s.json
  python -m qhc.evaluate reference --split ds2s --rule const_n --out runs/EV1_reference_r4/pred_const_n_ds2s.csv

Prediction files are CSV with columns beat_id, pred (N/S/V), prob_N, prob_S, prob_V, with one row per beat whose
`predict` flag is set in positions_<split>.csv. Only N/S/V beats enter the primary metric.

Comparison roles (evalspec.ROLES): strict roles (headline, lowdata_k5, lowdata_k11, secondary, confirmation) need
exactly 5 distinct seeded runs per arm, each with a run manifest <file without .csv>.run.json bound to the prediction
file by hash, one configuration per arm, distinct model artifacts, and the same seed indices in both arms. All of
this, the role and split, the order rules below, and the predictions themselves are checked before any label is read.
Every scoring of ds2s, ds2 or svdb is appended to runs/full_eval_log.jsonl.

Order on the test splits ds2s and ds2: until the headline is logged, only the minimal-reference predictions may be
scored there; diagnostics there are limited to them; score, secondary and low-data runs wait for the headline; the
headline compares models (never the references alone) and must be the first non-reference scoring; the headline and
the two low-data comparisons each run once (an identical rerun, by file content, is accepted at any later time). The
confirmation split waits for a logged headline. Strict arms are scored in seed order, other arms in content-hash order,
so the same files in any order or location give identical numbers (D3). The low-data roles also need, in every run
manifest, the parent headline configuration of that arm, the DS1 training records (the frozen subset for k) and the
refit scope (D4). --out may not overwrite an input file, run manifest, referenced model artifact, ledger or dataset
file (D5).

The confirmation split (svdb) is scored only by `compare --role confirmation --confirm-reason ...`, which emits the
complete report (every per-seed and seed-averaged secondary metric and per-record confusions) in that one access.
Order: validate; check that --out is a new file that can be written, and preflight the scorer on placeholder labels
(this catches output and code errors, not failures that depend on the real labels or on resources); enforce the
project-wide cap (a second access also needs --repair-reason and, in the same roles and seeds, the same model artifacts
as the first, unless --approved-model-change records the human's approval, D1); append the access with artifact and
prediction hashes to runs/confirmation_access.jsonl; only then read the labels. Each access's complete report is
archived immutably as runs/confirmation_reports/access_<n>.json, with its hash and status (completed or failed) in
runs/confirmation_reports/index.jsonl, before the --out copy is written (D2). A summary is printed.
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd

from . import evalspec as E
from . import scorer
from .units import sha256

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # project root (src/qhc/..)
PROCESSED = os.path.join(ROOT, "runs", "data", "processed", E.EV)
ACCESS_LOG = os.path.join(ROOT, "runs", "confirmation_access.jsonl")
FULL_EVAL_LOG = os.path.join(ROOT, "runs", "full_eval_log.jsonl")
CONFIRM_REPORTS = os.path.join(ROOT, "runs", "confirmation_reports")
LOGGED_SPLITS = {"ds2s", "ds2", "svdb"}


def code_revision():
    """First 16 hex of sha256 over the concatenated src/qhc/*.py files (sorted), the evaluation revision id. Line endings
    are normalised to LF first, so a checkout that converts them reproduces the same id."""
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(ROOT, "src", "qhc", "*.py"))):
        with open(p, "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def scorer_identity():
    return {"ev": E.EV, "code_revision": code_revision(), "practical_gain": E.PRACTICAL_GAIN,
            "suspicious_gain": E.SUSPICIOUS_GAIN, "ci_level": E.CI_LEVEL, "slice_ci_level": E.SLICE_CI_LEVEL,
            "slice_family": list(E.SLICE_FAMILY), "n_boot": E.N_BOOT, "boot_seed": E.BOOT_SEED,
            "n_seeds": E.N_SEEDS, "lookahead_sec": E.LOOKAHEAD_SEC, "edge_sec": E.EDGE_SEC}


def load_positions(split, processed=None):
    processed = processed or PROCESSED
    return pd.read_csv(os.path.join(processed, f"positions_{split}.csv"), dtype={"record": str})


def load_hours(split, processed=None):
    processed = processed or PROCESSED
    rec = pd.read_csv(os.path.join(processed, f"records_{split}.csv"), dtype={"record": str})
    return dict(zip(rec["record"], rec["duration_s"] / 3600))


def load_labels(split, processed=None, _confirmed_access=False):
    """Labels for scoring. The confirmation split is readable only after a logged access (see _confirmation_access)."""
    processed = processed or PROCESSED
    if split in E.CONFIRMATION_SPLITS:
        if not _confirmed_access:
            raise PermissionError(f"{split} labels are readable only through a logged confirmation access")
        path = os.path.join(processed, "confirm", f"labels_{split}.csv")
    else:
        path = os.path.join(processed, f"labels_{split}.csv")
    return pd.read_csv(path, dtype={"record": str, "beat_id": str}), path


def prediction_set(split):
    """Label-free frame of the beats that must be predicted (for validation before any label access)."""
    pos = load_positions(split)
    pos = pos[pos["predict"]].reset_index(drop=True)
    return pos.assign(aami="?", is_unit=False)[["beat_id", "record", "aami", "is_unit"]]


def _read_pred(path):
    return pd.read_csv(path, dtype={"beat_id": str, "pred": str})


def _resolved(path):
    return os.path.normcase(os.path.realpath(path))


def _expand(patterns, seen=None):
    """Expand the file patterns of one arm. A file that resolves to one already given (in either arm) is refused:
    repeating a file is not a seed."""
    seen = {} if seen is None else seen
    files = []
    for p in patterns:
        hits = sorted(glob.glob(p))
        if not hits:
            raise SystemExit(f"no prediction file matches {p}")
        for f in hits:
            r = _resolved(f)
            if r in seen:
                raise SystemExit(f"prediction file {f} is given twice (same file as {seen[r]}); each seed needs its own run")
            seen[r] = f
            files.append(f)
    return files


def run_manifest_path(pred_path):
    return os.path.splitext(pred_path)[0] + ".run.json"


def check_runs(files, split, arm):
    """Strict roles: exactly N_SEEDS distinct seeded runs, each with a run manifest bound to its prediction file and
    model artifact by hash. Distinct predictions are not required (valid runs can agree); distinct provenance is."""
    if len(files) != E.N_SEEDS:
        raise SystemExit(f"{arm}: {len(files)} runs given; this role needs exactly {E.N_SEEDS} distinct seeded runs")
    runs = []
    for f in files:
        mp = run_manifest_path(f)
        if not os.path.exists(mp):
            raise SystemExit(f"{arm}: run manifest {mp} is missing")
        with open(mp) as fh:
            m = json.load(fh)
        missing = [k for k in E.RUN_KEYS if k not in m]
        if missing:
            raise SystemExit(f"{arm}: run manifest {mp} lacks {missing}")
        if m["prediction_sha256"] != sha256(f):
            raise SystemExit(f"{arm}: {f} does not match the prediction_sha256 in its run manifest")
        if m["split"] != split:
            raise SystemExit(f"{arm}: run manifest {mp} is for split {m['split']}, not {split}")
        art = m["model_artifact"] if os.path.isabs(m["model_artifact"]) else os.path.join(ROOT, m["model_artifact"])
        if not os.path.exists(art) or sha256(art) != m["model_artifact_sha256"]:
            raise SystemExit(f"{arm}: model artifact {m['model_artifact']} is missing or does not match its hash")
        runs.append({**m, "_artifact": _resolved(art), "_file": f})
    if len({r["arm_id"] for r in runs}) != 1:
        raise SystemExit(f"{arm}: runs come from different arms {sorted({r['arm_id'] for r in runs})}")
    if len({json.dumps(r["config_id"]) for r in runs}) != 1:
        raise SystemExit(f"{arm}: runs come from different configurations {sorted({str(r['config_id']) for r in runs})}")
    seeds = [r["seed"] for r in runs]
    if len(set(seeds)) != len(seeds):
        raise SystemExit(f"{arm}: duplicate seed ids {seeds}")
    if len({r["_artifact"] for r in runs}) != len(runs):
        raise SystemExit(f"{arm}: two runs point to the same model artifact")
    if len({r["model_artifact_sha256"] for r in runs}) != len(runs):
        raise SystemExit(f"{arm}: two runs have byte-identical model artifacts (the same model is not two seeds)")
    rand = [json.dumps([r["reservoir_seed"], r["shot_seed"]]) for r in runs]
    if len(set(rand)) != len(rand):
        raise SystemExit(f"{arm}: two runs share both reservoir and shot randomness")
    numeric = all(isinstance(r["seed"], (int, float)) for r in runs)
    return sorted(runs, key=lambda r: r["seed"] if numeric else str(r["seed"]))  # canonical seed order (D3)


def check_lowdata(role, c_runs, b_runs):
    """Reduced-data roles (D4): every run names the headline configuration of its own arm as parent, was fitted on
    exactly the frozen DS1 subset for k, and declares this role as its refit scope. Checked before any label access."""
    k = role.split("_k")[1]
    with open(os.path.join(PROCESSED, "lowdata_subsets.json")) as f:
        subset = sorted(json.load(f)["subsets"][f"k{k}"]["records"])
    parents = _headline_config_ids()
    if parents is None:
        raise SystemExit(f"{role}: the configurations of the logged headline cannot be established from its run manifests")
    for arm, runs, parent in (("candidate", c_runs, parents[0]), ("baseline", b_runs, parents[1])):
        for r in runs:
            missing = [x for x in E.LOWDATA_RUN_KEYS if x not in r]
            if missing:
                raise SystemExit(f"{arm}: run manifest of {r['_file']} lacks {missing} (needed for {role})")
            if r["refit_scope"] != role:
                raise SystemExit(f"{arm}: {r['_file']} declares refit scope {r['refit_scope']!r}, not {role!r}")
            if sorted(str(x) for x in r["train_records"]) != subset:
                raise SystemExit(f"{arm}: {r['_file']} was fitted on {sorted(r['train_records'])}, not the frozen k{k} "
                                 f"subset {subset}")
            if r["parent_config_id"] != parent:
                raise SystemExit(f"{arm}: {r['_file']} derives from {r['parent_config_id']!r}, but the headline {arm} "
                                 f"configuration is {parent!r}")


def _log_lines(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


def _append(path, entry):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")


def _file_hashes(files):
    return {f: sha256(f) for f in files}


def _arm_identity(arm_hashes):
    """Content identity of a request: per arm, the sorted file hashes (independent of paths)."""
    return [sorted(h) for h in arm_hashes]


def _entry_arms(e):
    return e.get("arms") or [sorted(e["files"].values())]


def _headline_entries(log):
    """Logged headline comparisons on ds2s whose arms are not the minimal references alone."""
    return [e for e in log if e.get("role") == "headline" and e.get("split") == "ds2s"
            and not all(h in E.REFERENCE_PRED_SHA256 for a in _entry_arms(e) for h in a)]


def _headline_config_ids():
    """[candidate config_id, baseline config_id] of the logged headline: from the log entry, or, for an entry written
    before config ids were logged, from the run manifests of its logged files (each checked against the logged hash)."""
    entries = _headline_entries(_log_lines(FULL_EVAL_LOG))
    if not entries:
        return None
    e = entries[0]
    if e.get("config_ids"):
        return e["config_ids"]
    out = []
    for hashes in _entry_arms(e):
        ids = set()
        for f, h in e["files"].items():
            if h not in hashes:
                continue
            path = f if os.path.isabs(f) else os.path.join(ROOT, f)
            mp = run_manifest_path(path)
            if not (os.path.exists(path) and os.path.exists(mp) and sha256(path) == h):
                return None
            with open(mp) as fh:
                m = json.load(fh)
            if m.get("prediction_sha256") != h:
                return None
            ids.add(json.dumps(m["config_id"]))
        if len(ids) != 1:
            return None
        out.append(json.loads(ids.pop()))
    return out


def _check_out(out, inputs, runs=(), new_file=False):
    """--out (and its temporary file's directory) may not resolve to an input prediction file, run manifest,
    referenced model artifact, evaluation ledger or confirmation report, or lie inside the processed dataset (D5).
    new_file: the output must not exist yet (confirmation, D2)."""
    protected = {_resolved(f) for f in inputs} | {_resolved(run_manifest_path(f)) for f in inputs}
    protected |= {r["_artifact"] for r in runs} | {_resolved(FULL_EVAL_LOG), _resolved(ACCESS_LOG)}
    r = _resolved(out)
    if r in protected:
        raise SystemExit(f"--out {out} would overwrite an input file, model artifact or ledger")
    for d in (PROCESSED, CONFIRM_REPORTS):
        if r == _resolved(d) or r.startswith(_resolved(d) + os.sep):
            raise SystemExit(f"--out {out} lies inside {d}")
    if os.path.isdir(out):
        raise SystemExit(f"--out {out} is a directory")
    if new_file and os.path.exists(out):
        raise SystemExit(f"--out {out} exists; a confirmation report is never overwritten (choose a new file)")


def _check_order(role, split, arm_hashes):
    """Order rules on the test splits (V003 B1); role None is a single-arm `score`."""
    if split not in E.TEST_SPLITS:
        return
    log = [e for e in _log_lines(FULL_EVAL_LOG) if e.get("split") in E.TEST_SPLITS]
    only_refs = lambda arms: all(h in E.REFERENCE_PRED_SHA256 for a in arms for h in a)
    ident = _arm_identity(arm_hashes)
    if role == "headline" and only_refs(ident):
        raise SystemExit("the headline compares models; the minimal references alone cannot be the headline")
    if only_refs(ident):
        return  # minimal references may always be scored
    if role == "diagnostic":
        raise SystemExit("on ds2s and ds2, diagnostic scoring is limited to the minimal-reference predictions")
    headline = _headline_entries(log)
    if role == "headline":
        if any(_entry_arms(e) != ident for e in headline):
            raise SystemExit(f"a different headline was already evaluated ({headline[0]['ids']}, {headline[0]['time']}); "
                             "later pairs use --role secondary")
        if not headline:
            for e in log:
                if not only_refs(_entry_arms(e)):
                    raise SystemExit(f"the headline must be the first non-reference scoring on the test splits; the "
                                     f"log already holds {e.get('cmd')} {e.get('role')} {e.get('ids')} ({e['time']})")
    elif not headline:
        raise SystemExit(f"{role or 'score'} on {split} waits until the pre-registered headline pair is logged")
    if role in E.RUN_ONCE_ROLES:
        for e in log:
            if e.get("role") == role and e["split"] == split and _entry_arms(e) != ident:
                raise SystemExit(f"{role} was already evaluated on {split} ({e['ids']}, {e['time']}) with other runs; "
                                 "it runs once (later variants use --role secondary)")


def _check_writable(out):
    """Fail before any access if the output file cannot be written."""
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    existed = os.path.exists(out)
    with open(out, "a"):
        pass
    if not existed:
        os.remove(out)


def _smoke_test(split, cp, bp):
    """Preflight: run the whole comparison once on placeholder labels (cycling N/S/V, few replicates). It catches
    output and code errors before a confirmation access is logged; it cannot rule out failures that depend on the real
    labels or on resources (those are recorded as a failed access, see _archive_report)."""
    pset = prediction_set(split)
    fake = pset.assign(aami=np.array(E.CLASSES)[np.arange(len(pset)) % len(E.CLASSES)], is_unit=True)
    json.dumps(scorer.compare(cp, bp, fake, hours=load_hours(split), role="confirmation", n_boot=20))


def _role_identity(runs, n_cand):
    """Model identity per role (D1): for candidate and baseline, the arm id, the configuration id and the artifact hash
    of each seed."""
    out = {}
    for role, rr in (("candidate", runs[:n_cand]), ("baseline", runs[n_cand:])):
        out[role] = {"arm_id": rr[0]["arm_id"], "config_id": rr[0]["config_id"],
                     "artifacts_by_seed": {json.dumps(r["seed"]): r["model_artifact_sha256"] for r in rr}}
    return out


def _report_paths(access):
    return os.path.join(CONFIRM_REPORTS, f"access_{access}.json"), os.path.join(CONFIRM_REPORTS, "index.jsonl")


def _archive_report(access, status, payload=None, error=None):
    """Immutable record of one confirmation access (D2): the complete report as access_<n>.json, never overwritten, and
    an index line with its sha256 and status (completed / failed)."""
    path, index = _report_paths(access)
    entry = {"time": _now(), "access": access, "status": status}
    if payload is not None:
        os.makedirs(CONFIRM_REPORTS, exist_ok=True)
        with open(path, "x") as f:  # exclusive: an existing report is never replaced
            json.dump(payload, f, indent=1, default=str)
        entry.update(report=os.path.relpath(path, ROOT).replace(os.sep, "/"), sha256=sha256(path))
    if error is not None:
        entry["error"] = error
    _append(index, entry)
    return entry


def _confirmation_access(split, a, ids, preds, file_hashes, runs, cp, bp):
    """Validate against the label-free prediction set, check the output and the scorer, enforce the cap and the repair
    rules, then log. Returns True if labels may be read."""
    if split not in E.CONFIRMATION_SPLITS:
        return False
    if not a.confirm_reason:
        raise SystemExit(f"split {split} is the confirmation set: pass --confirm-reason and log the access in EVAL.md")
    if not _headline_entries(_log_lines(FULL_EVAL_LOG)):
        raise SystemExit("the confirmation set is scored only after the headline pair has been evaluated on ds2s")
    pset = prediction_set(split)
    for p in preds:
        scorer.validate(p, pset)
    _check_writable(a.out)
    _smoke_test(split, cp, bp)
    previous = _log_lines(ACCESS_LOG)
    used = len(previous)
    if used >= E.CONFIRMATION_CAP:
        raise SystemExit(f"confirmation cap reached ({used}/{E.CONFIRMATION_CAP}); a further access needs a new EV version")
    if os.path.exists(_report_paths(used + 1)[0]):
        raise SystemExit(f"{_report_paths(used + 1)[0]} already exists; the confirmation archive and log disagree")
    artifacts = {r["_file"]: r["model_artifact_sha256"] for r in runs}
    roles = _role_identity(runs, len(runs) // 2)
    changed = False
    if used >= 1:
        if not a.repair_reason:
            raise SystemExit("a second confirmation access is a documented repair only: pass --repair-reason "
                             "(the implementation defect corrected), and keep the first result")
        first = previous[0].get("roles")
        changed = first is None or any(first[k]["artifacts_by_seed"] != roles[k]["artifacts_by_seed"]
                                       for k in ("candidate", "baseline"))
        if changed and not a.approved_model_change:
            raise SystemExit("a repair access must score the same model artifacts as the first access, in the same roles "
                             "and seeds (candidate stays candidate); a model or role change needs --approved-model-change "
                             "recording the human's approval")
    _append(ACCESS_LOG, {"time": _now(), "split": split, "ids": ids, "reason": a.confirm_reason,
                         "repair_reason": a.repair_reason, "approved_model_change": a.approved_model_change,
                         "models_changed_from_first": changed, "access": used + 1, "code_revision": code_revision(),
                         "prediction_sha256": file_hashes, "model_artifact_sha256": artifacts, "roles": roles})
    return {"access": used + 1, "models_changed_from_first": changed}


def _log_full_eval(cmd, split, role, ids, file_hashes, arm_hashes, config_ids=None):
    if split in LOGGED_SPLITS:
        entry = {"time": _now(), "cmd": cmd, "split": split, "role": role, "ids": ids, "files": file_hashes,
                 "arms": _arm_identity(arm_hashes), "code_revision": code_revision(), "argv": sys.argv[1:]}
        if config_ids:
            entry["config_ids"] = config_ids
        _append(FULL_EVAL_LOG, entry)


def _now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _write(out, payload):
    """Atomic write; if --out fails, the result goes to a fallback file under runs/ so that it is never lost."""
    try:
        d = os.path.dirname(os.path.abspath(out))
        os.makedirs(d, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=d, prefix=os.path.basename(out) + ".", suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(payload, f, indent=1)
            os.replace(tmp, out)
        finally:
            if os.path.exists(tmp):
                os.remove(tmp)
    except (OSError, TypeError, ValueError) as err:
        fallback = os.path.join(ROOT, "runs", f"eval_output_fallback_{datetime.datetime.now():%Y%m%d_%H%M%S}.json")
        with open(fallback, "w") as f:
            json.dump(payload, f, indent=1, default=str)
        print(f"could not write {out} ({err}); wrote {fallback}")
        return
    print(f"wrote {out}")


def cmd_score(a):
    if a.split in E.CONFIRMATION_SPLITS:
        raise SystemExit(f"{a.split} is scored only by `compare --role confirmation`, which reports everything in one access")
    _check_out(a.out, [a.pred])
    pred = _read_pred(a.pred)
    scorer.validate(pred, prediction_set(a.split))  # before any label is read
    hashes = _file_hashes([a.pred])
    _check_order(None, a.split, [list(hashes.values())])
    _log_full_eval("score", a.split, None, [a.id], hashes, [list(hashes.values())])
    labels, lpath = load_labels(a.split)
    res = scorer.score(pred, labels, load_hours(a.split))
    meta = {"split": a.split, "candidate_id": a.id, "pred_file": a.pred, "pred_sha256": hashes[a.pred],
            "labels_sha256": sha256(lpath), "scorer": scorer_identity(), "time": _now(), "command": " ".join(sys.argv)}
    _write(a.out, {**meta, **res})
    pc = res["per_class"]
    print(f"{a.id} {a.split}: macro-F1 {res['macro_f1']:.4f} | " +
          " | ".join(f"{c} Se {pc[c]['sensitivity'] or 0:.3f} PPV {pc[c]['ppv'] or 0:.3f}" for c in E.CLASSES))


def cmd_compare(a):
    role = E.ROLES.get(a.role)
    if role is None:
        raise SystemExit(f"unknown role {a.role}")
    if a.split not in role["splits"]:
        raise SystemExit(f"role {a.role} is for split(s) {role['splits']}, not {a.split}")
    seen = {}
    cf, bf = _expand(a.cand, seen), _expand(a.base, seen)
    if len(cf) != len(bf):
        raise SystemExit(f"arms need equal seed counts (got {len(cf)} and {len(bf)})")
    runs, config_ids = [], None
    if role["strict"]:
        c_runs, b_runs = check_runs(cf, a.split, "candidate"), check_runs(bf, a.split, "baseline")
        if c_runs[0]["arm_id"] == b_runs[0]["arm_id"]:
            raise SystemExit(f"candidate and baseline carry the same arm_id {c_runs[0]['arm_id']!r}")
        if sorted(r["seed"] for r in c_runs) != sorted(r["seed"] for r in b_runs):
            raise SystemExit("matched rule 1: both arms must use the same seed indices")
        runs = c_runs + b_runs
        cf, bf = [r["_file"] for r in c_runs], [r["_file"] for r in b_runs]  # seed order (D3)
        config_ids = [c_runs[0]["config_id"], b_runs[0]["config_id"]]
    else:
        if len(cf) != E.N_SEEDS:
            print(f"note: diagnostic comparison with {len(cf)} run(s) per arm")
        cf, bf = sorted(cf, key=sha256), sorted(bf, key=sha256)  # content order (D3)
    confirm = a.split in E.CONFIRMATION_SPLITS
    _check_out(a.out, cf + bf, runs, new_file=confirm)
    cp, bp = [_read_pred(f) for f in cf], [_read_pred(f) for f in bf]
    hashes = _file_hashes(cf + bf)
    arm_hashes = [[hashes[f] for f in cf], [hashes[f] for f in bf]]
    _check_order(a.role, a.split, arm_hashes)
    if a.role in ("lowdata_k5", "lowdata_k11"):
        check_lowdata(a.role, c_runs, b_runs)
    if not confirm:
        pset = prediction_set(a.split)
        for p in cp + bp:
            scorer.validate(p, pset)
    access = _confirmation_access(a.split, a, [a.cand_id, a.base_id], cp + bp, hashes, runs, cp, bp)
    _log_full_eval("compare", a.split, a.role, [a.cand_id, a.base_id], hashes, arm_hashes, config_ids)
    keys = E.RUN_KEYS + (E.LOWDATA_RUN_KEYS if a.role in ("lowdata_k5", "lowdata_k11") else ())
    try:
        labels, lpath = load_labels(a.split, _confirmed_access=bool(access))
        res = scorer.compare(cp, bp, labels, hours=load_hours(a.split), role=a.role,
                             dominant_record=E.DOMINANT_RECORD.get(a.split))
        payload = {"split": a.split, "candidate_id": a.cand_id, "baseline_id": a.base_id,
                   "candidate_files": {f: hashes[f] for f in cf}, "baseline_files": {f: hashes[f] for f in bf},
                   "run_manifests": {r["_file"]: {k: r[k] for k in keys} for r in runs},
                   "labels_sha256": sha256(lpath), "scorer": scorer_identity(), "time": _now(),
                   "command": " ".join(sys.argv), **res}
        if confirm:
            payload["confirmed"] = bool(res["primary"]["delta"] > 0 and res["primary"]["ci"][0] > 0)
            payload["confirmation_access"] = access["access"]
            if access["models_changed_from_first"]:
                payload["note"] = ("approved model or role change: this is not a repair of the first confirmation, whose "
                                   "result stands and is reported alongside")
            arch = _archive_report(access["access"], "completed", payload)
            print(f"archived {arch['report']} (sha256 {arch['sha256'][:16]})")
    except BaseException as err:
        if confirm:
            _archive_report(access["access"], "failed", error=repr(err))
        raise
    pr = res["primary"]
    print(f"[{a.role}] {a.cand_id} vs {a.base_id} on {a.split}: delta {pr['delta']:+.4f} "
          f"CI{pr['ci_level']:.4f} [{pr['ci'][0]:+.4f}, {pr['ci'][1]:+.4f}] "
          f"(without {pr['dominant_record']}: {pr['delta_without_dominant_record']}) -> {pr['outcome']} "
          f"({pr['outcome_reason']})" + (" | SUSPICIOUS GAIN: queue verification" if pr["suspicious_gain"] else ""))
    if res["slices"]:
        for name, s in res["slices"]["members"].items():
            print(f"  slice {name}: delta {s['delta']:+.4f} CI{res['slices']['ci_level']:.4f} "
                  f"[{s['ci'][0]:+.4f}, {s['ci'][1]:+.4f}] -> {s['decision']}")
    if "confirmed" in payload:
        print(f"  confirmed: {payload['confirmed']}")
    _write(a.out, payload)


def reference_predictions(rule, positions):
    """Minimal references, using only released beat positions (never labels); one-hot probabilities.
    const_n: every beat is N. rr_rule: S when the pre-RR interval is < 0.85 x the mean of the previous (up to) 10
    pre-RR intervals of the same record, else N; it never predicts V."""
    out = []
    for _, g in positions.sort_values(["record", "sample"]).groupby("record", sort=False):
        s = g["sample"].to_numpy()
        pre = np.diff(s, prepend=np.nan)
        prev_mean = pd.Series(pre).shift(1).rolling(10, min_periods=1).mean().to_numpy()
        if rule == "const_n":
            pred = np.full(len(g), "N")
        elif rule == "rr_rule":
            pred = np.where(pre < 0.85 * prev_mean, "S", "N")
        else:
            raise SystemExit(f"unknown rule {rule}")
        out.append(pd.DataFrame({"beat_id": g["beat_id"].to_numpy(), "pred": pred, "predict": g["predict"].to_numpy()}))
    df = pd.concat(out)
    df = df.loc[df["predict"], ["beat_id", "pred"]]
    for c in E.CLASSES:
        df[f"prob_{c}"] = (df["pred"] == c).astype(float)
    return df


def cmd_reference(a):
    if a.split in E.CONFIRMATION_SPLITS:
        raise SystemExit("references are not run on the confirmation set")
    pred = reference_predictions(a.rule, load_positions(a.split))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pred.to_csv(a.out, index=False)
    print(f"wrote {a.out} ({len(pred)} rows)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="EV1 evaluation")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score", help="score one prediction file (not available for the confirmation split)")
    s.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    s.add_argument("--pred", required=True)
    s.add_argument("--id", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_score)
    c = sub.add_parser("compare")
    c.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    c.add_argument("--role", required=True, choices=sorted(E.ROLES),
                   help="headline (the single pre-registered pair), lowdata_k5 / lowdata_k11 (slice family), "
                        "secondary (descriptive), confirmation (svdb), diagnostic (references, null check)")
    c.add_argument("--cand", required=True, nargs="+", help="one prediction file (or glob) per seed")
    c.add_argument("--base", required=True, nargs="+")
    c.add_argument("--cand-id", required=True)
    c.add_argument("--base-id", required=True)
    c.add_argument("--out", required=True)
    c.add_argument("--confirm-reason")
    c.add_argument("--repair-reason", help="required for the second (repair) confirmation access")
    c.add_argument("--approved-model-change",
                   help="only with --repair-reason: records the human's approval to score different model artifacts")
    c.set_defaults(fn=cmd_compare)
    r = sub.add_parser("reference")
    r.add_argument("--split", required=True, choices=sorted(E.SPLITS))
    r.add_argument("--rule", required=True, choices=["const_n", "rr_rule"])
    r.add_argument("--out", required=True)
    r.set_defaults(fn=cmd_reference)
    a = ap.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    main()
