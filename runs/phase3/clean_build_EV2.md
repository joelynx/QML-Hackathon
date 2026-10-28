# Full clean build with SVDB, EV2 (approved by the human 2026-10-26 22:14)

Fresh copy of src/, tests/, scripts/, pyproject.toml, requirements-lock.txt and README.md, in a scratch directory outside the project. Fresh venv from the system Python 3.12.10, `pip install -r requirements-lock.txt`, then `pip install -e .`.

Steps: fresh download of MIT-BIH and SVDB, with the sums-file hashes pinned in `scripts/download_data.py`; full `python -I -m qhc.units`; comparison of the manifest hash strings with the project's manifest; all fixtures.

The SVDB labels file the build wrote in the scratch copy (`confirm/labels_svdb.csv`) was never opened by the agent and was deleted at 22:32. The SVDB class totals printed by `qhc.units` are those already recorded in the project manifest and the EVAL.md data card.

Script: the session scratchpad `clean_full.sh`, reproduced in substance by the README steps. Log excerpt:

```
=== venv  22:15:57
=== lock  22:16:11
=== editable  22:22:38
=== revision  22:22:52
8501643023cd2eb6
=== download  22:22:56
mitdb: 48 records, 144 files verified, 0 failed []
svdb: 78 records, 234 files verified, 0 failed []
=== units  22:31:36
ds1 50964 50542 {'N': 45813, 'V': 3786, 'S': 943} nonunit: {'F': 414, 'Q': 8} not predicted: {'N': 53, 'V': 2, 'S': 1, 'F': 1}
ds2s 47523 47129 {'N': 42148, 'V': 3200, 'S': 1781} nonunit: {'F': 387, 'Q': 7} not predicted: {'N': 50, 'V': 2, 'S': 1}
ds2 49657 49262 {'N': 44207, 'V': 3219, 'S': 1836} nonunit: {'F': 388, 'Q': 7} not predicted: {'N': 52, 'V': 2, 'S': 1}
svdb 184389 184286 {'N': 162160, 'S': 12193, 'V': 9933} nonunit: {'Q': 79, 'F': 23, 'other': 1} not predicted: {'N': 179, 'V': 10, 'S': 5}
folds: {'fold0': {'N': 11343, 'S': 113, 'V': 612}, 'fold1': {'N': 10604, 'S': 104, 'V': 126}, 'fold2': {'N': 7615, 'S': 383, 'V': 965}, 'fold3': {'N': 9020, 'S': 107, 'V': 685}, 'fold4': {'N': 7231, 'S': 236, 'V': 1398}}
=== compare_manifest  22:31:42
14 outputs compared (hash strings only), 0 differ []
extra outputs in the clean build: []
inputs equal: True
split statistics equal: {'ds1': True, 'ds2s': True, 'ds2': True, 'svdb': True}
=== pytest  22:31:42
43 passed, 3 warnings in 36.63s
=== done  22:32:19
```
