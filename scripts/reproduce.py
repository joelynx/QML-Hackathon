"""One command from raw data to the EV1 headline tables (run from the project root of a fresh checkout):

    python scripts/reproduce.py                 # download, units, fixtures, features, tune, final, lookahead, headline, tables
    python scripts/reproduce.py --check         # same, but instead of scoring ds2s again, compare the regenerated
                                                # prediction hashes with the ones logged for the headline in
                                                # runs/full_eval_log.jsonl (no new test-split access), then rebuild the
                                                # tables from the logged comparison output
    python scripts/reproduce.py --tables-only   # tables from runs/E003/compare_ds2s_headline.json

It refuses to overwrite existing runs/E002 or runs/E003 outputs, unless --tables-only is given. With --skip-data, the raw data
and processed units already present are used. Standard library only; every step runs `python -I -m ...` with this interpreter.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CMP = os.path.join("runs", "E003", "compare_ds2s_headline_EV2.json")
TABLES = os.path.join("runs", "tables", "headline_ds2s.md")
SEEDS = ["0", "1", "2", "3", "4"]


def run(*args):
    cmd = [sys.executable, "-I", *args]
    print("\n$", " ".join(args), flush=True)
    subprocess.run(cmd, cwd=ROOT, check=True)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def preds(exp):
    return [os.path.join("runs", exp, f"pred_ds2s_seed{s}.csv") for s in SEEDS]


def check_against_log():
    log_path = os.path.join(ROOT, "runs", "full_eval_log.jsonl")
    with open(log_path) as f:
        heads = [e for e in map(json.loads, filter(str.strip, f)) if e.get("role") == "headline" and e.get("split") == "ds2s"]
    if not heads:
        raise SystemExit("no logged headline to check against")
    logged = {os.path.normpath(k): v for k, v in heads[0]["files"].items()}
    ok = True
    for f in preds("E003") + preds("E002"):
        same = logged.get(os.path.normpath(f)) == sha256(os.path.join(ROOT, f))
        ok &= same
        print(f"{f}: {'identical to the logged headline input' if same else 'DIFFERS from the logged headline input'}")
    if not ok:
        raise SystemExit("regenerated predictions differ from the scored ones")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tables-only", action="store_true")
    ap.add_argument("--skip-data", action="store_true")
    a = ap.parse_args()
    if not a.tables_only:
        for exp in ("E002", "E003"):
            if os.path.exists(os.path.join(ROOT, "runs", exp, "tuning.jsonl")):
                raise SystemExit(f"runs/{exp} already has outputs; run this in a fresh checkout (or use --tables-only)")
        if not a.skip_data:
            subprocess.run([sys.executable, "scripts/download_data.py"], cwd=ROOT, check=True)
            run("-m", "qhc.units")
        run("-m", "pytest", "-q", "-p", "no:cacheprovider")
        run("-m", "qhc.pipe.features", "--splits", "ds1", "ds2s")
        for arm, exp in (("esn", "E002"), ("qrc", "E003")):
            run("-m", "qhc.pipe.run", "tune", "--arm", arm, "--exp", exp)
            run("-m", "qhc.pipe.run", "final", "--exp", exp, "--seeds", *SEEDS, "--oof", "--splits", "ds2s")
            run("-m", "qhc.pipe.run", "leakcheck", "--exp", exp, "--seed", "0")
        if a.check:
            check_against_log()
        else:
            run("-m", "qhc.evaluate", "compare", "--split", "ds2s", "--role", "headline", "--cand", *preds("E003"),
                "--base", *preds("E002"), "--cand-id", "E003", "--base-id", "E002", "--out", CMP)
    run("-m", "qhc.pipe.tables", "--cmp", CMP, "--out", TABLES)


if __name__ == "__main__":
    main()
