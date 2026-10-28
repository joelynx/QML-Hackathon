#!/bin/bash
# V005 critic: regenerate E018 predictions (label-free) from the saved artifacts into runs/V005/E018
set -u
cd "/c/Users/admin/Desktop/Water Hackathon/quantum_healthcare"
export CUDA_VISIBLE_DEVICES=1 OMP_NUM_THREADS=8 MKL_NUM_THREADS=8
O=runs/V005/E018
ts(){ echo "=== $1  $(date +%H:%M:%S)"; }
ts build_svdb; .venv/Scripts/python -I -m qhc.p4.predict build-features --split svdb --features-dir $O/features
ts ds2s_E003; .venv/Scripts/python -I -m qhc.p4.predict predict --exp E003 --split ds2s --out $O/selfcheck_ds2s/E003
ts ds2s_E002; .venv/Scripts/python -I -m qhc.p4.predict predict --exp E002 --split ds2s --out $O/selfcheck_ds2s/E002
ts svdb_E003; .venv/Scripts/python -I -m qhc.p4.predict predict --exp E003 --split svdb --out $O/E003 --features-dir $O/features
ts svdb_E002; .venv/Scripts/python -I -m qhc.p4.predict predict --exp E002 --split svdb --out $O/E002 --features-dir $O/features
ts done
