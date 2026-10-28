#!/bin/bash
# V005 critic: clean environment + fresh download + reproduce.py --check (no test-split scoring)
set -u
P="/c/Users/admin/Desktop/Water Hackathon/quantum_healthcare"
C="/c/Users/admin/AppData/Local/Temp/v005_clean"
ts(){ echo "=== $1  $(date +%H:%M:%S)"; }
ts start
rm -rf "$C"; mkdir -p "$C/runs/E003"
cp -r "$P/src" "$P/tests" "$P/scripts" "$P/pyproject.toml" "$P/requirements-lock.txt" "$C/"
# remove copied caches / egg-info so the build is fresh
find "$C" -name "__pycache__" -type d -prune -exec rm -rf {} + ; rm -rf "$C/src/qhc.egg-info"
cp "$P/runs/full_eval_log.jsonl" "$C/runs/"
cp "$P/runs/E003/compare_ds2s_headline_EV2.json" "$C/runs/E003/"
sha256sum "$C/runs/full_eval_log.jsonl" "$C/runs/E003/compare_ds2s_headline_EV2.json"
ls -la "$C" "$C/runs"
cd "$C"
ts venv
/c/Users/admin/AppData/Local/Programs/Python/Python312/python -m venv .venv || exit 1
ts lock
.venv/Scripts/python -m pip install -q -r requirements-lock.txt || { echo LOCK_FAIL; exit 1; }
ts editable
.venv/Scripts/python -m pip install -q -e . || { echo EDITABLE_FAIL; exit 1; }
.venv/Scripts/python -c "import sys,torch;print(sys.version);print('torch',torch.__version__,'cuda',torch.cuda.is_available())"
ts reproduce_check
CUDA_VISIBLE_DEVICES=0 .venv/Scripts/python scripts/reproduce.py --check
echo "EXIT reproduce.py --check: $?"
ts post
ls runs/data/processed/EV1/ 2>/dev/null | grep -v '^confirm$'
if [ -d runs/data/processed/EV1/confirm ]; then rm -rf runs/data/processed/EV1/confirm && echo "confirm/ existed; deleted unopened"; fi
sha256sum runs/tables/headline_ds2s.md "$P/runs/tables/headline_ds2s.md"
ts done
