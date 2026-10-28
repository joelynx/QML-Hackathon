#!/usr/bin/env bash
# Full clean build with SVDB (approved by the human 2026-10-26 22:14): fresh copy of the EV2 code, fresh venv from the
# lockfile, fresh download of MIT-BIH and SVDB (pinned sums-file hashes), full `qhc.units` build (it reads the SVDB
# annotations to write confirm/labels_svdb.csv inside this scratch copy; the agent never opens that file), all fixtures,
# then a comparison of every manifest hash with the project's manifest (hash strings only).
set -u
PROJ="/c/Users/admin/Desktop/Water Hackathon/quantum_healthcare"
D="$1"
PY312="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
rm -rf "$D"; mkdir -p "$D"
cd "$PROJ"
tar --exclude='__pycache__' --exclude='*.egg-info' -cf - src tests scripts pyproject.toml requirements-lock.txt README.md | (cd "$D" && tar -xf -)
cd "$D"
step() { echo; echo "=== $1  $(date +%H:%M:%S)"; }
step venv;      "$PY312" -m venv .venv || exit 1
P=.venv/Scripts/python
step lock;      $P -m pip install -q -r requirements-lock.txt 2>&1 | grep -v notice
step editable;  $P -m pip install -q -e . 2>&1 | grep -v notice
step revision;  $P -I -c "from qhc.evaluate import code_revision; print(code_revision())"
step download;  $P scripts/download_data.py || exit 1
step units;     $P -I -m qhc.units || exit 1
step compare_manifest
$P -I - "$PROJ/runs/data/processed/EV1/manifest.json" <<'EOF'
import json, sys
ref = json.load(open(sys.argv[1]))
new = json.load(open("runs/data/processed/EV1/manifest.json"))
keys = sorted(ref["outputs"])
bad = [k for k in keys if ref["outputs"][k] != new["outputs"].get(k)]
print(f"{len(keys)} outputs compared (hash strings only), {len(bad)} differ {bad}")
print("extra outputs in the clean build:", sorted(set(new["outputs"]) - set(ref["outputs"])))
print("inputs equal:", ref["inputs"] == new["inputs"])
print("split statistics equal:", {s: ref["splits"][s] == new["splits"].get(s) for s in ref["splits"]})
EOF
step pytest;    $P -I -m pytest -q -p no:cacheprovider 2>&1 | grep -E "passed|failed|FAILED" | tail -5
step done
