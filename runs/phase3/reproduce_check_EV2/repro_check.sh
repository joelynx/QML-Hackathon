#!/usr/bin/env bash
# One-command reproduction check: fresh copy of the code, fresh venv from the lockfile, then
# `scripts/reproduce.py --skip-data --check`. Data: the SHA256-verified MIT-BIH raw files and the EV1 processed units,
# copied WITHOUT confirm/ (no SVDB labels in the copy). --check compares regenerated ds2s predictions with the hashes
# logged for the headline; it does not score the test split. The copied full_eval_log.jsonl is read only.
set -u
PROJ="/c/Users/admin/Desktop/Water Hackathon/quantum_healthcare"
D="$1"
PY312="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
rm -rf "$D"; mkdir -p "$D"
cd "$PROJ"
tar --exclude='__pycache__' --exclude='*.egg-info' --exclude='runs/data/processed/EV1/confirm' -cf - \
    src tests scripts pyproject.toml requirements-lock.txt README.md runs/data/raw/mitdb runs/data/processed/EV1 \
    runs/full_eval_log.jsonl runs/E003/compare_ds2s_headline_EV2.json | (cd "$D" && tar -xf -)
cd "$D"
step() { echo; echo "=== $1  $(date +%H:%M:%S)"; }
step venv;      "$PY312" -m venv .venv || exit 1
P=.venv/Scripts/python
step lock;      $P -m pip install -q -r requirements-lock.txt 2>&1 | grep -v notice
step editable;  $P -m pip install -q -e . 2>&1 | grep -v notice
step revision;  $P -I -c "from qhc.evaluate import code_revision; print(code_revision())"
step confirm_absent; ls runs/data/processed/EV1/confirm 2>&1 | head -1
step reproduce; $P scripts/reproduce.py --skip-data --check; echo "reproduce exit $?"
step tables_diff; diff -q runs/tables/headline_ds2s.md "$PROJ/runs/tables/headline_ds2s.md" && echo "headline table identical"
step done
