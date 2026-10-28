"""Print the worked-example and product-state numbers quoted in the PDF write-up (docs/report/report.html).

Reads only runs/E019/analysis_features.npz: features of the 48 label-free hardware beats (E019), as
"exact" (statevector), "shot" (our 1,024-shot simulation) and "hw" (Rigetti Cepheus-1-108Q). No label file is
opened and nothing is scored. Feature layout per snapshot: <Z_q> for q = 0..9, then <Z_q Z_r> for the 45 pairs
in itertools.combinations order; 4 snapshots x 55 = 220.

    .venv/Scripts/python -I scripts/report_numbers.py      (from the project root)
"""
import itertools
import os

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAIRS = list(itertools.combinations(range(10), 2))


def main():
    d = np.load(os.path.join(ROOT, "runs", "E019", "analysis_features.npz"), allow_pickle=True)
    beats, ex, sh, hw = d["beat_id"], d["exact"], d["shot"], d["hw"]

    i = 0
    print(f"worked example: beat {beats[i]} (record:sample at 360 Hz)")
    for name, f in (("exact", ex), ("1,024-shot", sh), ("hardware", hw)):
        z0, z1, z0z1 = f[i, 0], f[i, 1], f[i, 10]
        print(f"  {name:10s} step 1: <Z0> {z0:+.3f}  <Z1> {z1:+.3f}  <Z0 Z1> {z0z1:+.3f}  "
              f"<Z0><Z1> {z0 * z1:+.3f} | step 4: <Z0> {f[i, 165]:+.3f}")
    print(f"  mean |hardware - exact| over this beat's 220 features: {np.abs(hw[i] - ex[i]).mean():.3f}")

    conn, raw = [], []
    for k in range(4):
        z = ex[:, 55 * k:55 * k + 10]
        zz = ex[:, 55 * k + 10:55 * (k + 1)]
        prod = np.stack([z[:, q] * z[:, r] for q, r in PAIRS], 1)
        conn.append(np.abs(zz - prod))
        raw.append(np.abs(zz))
    conn, raw = np.concatenate(conn, 1), np.concatenate(raw, 1)
    print("exact simulation, 48 beats x 4 snapshots x 45 pairs:")
    print(f"  mean |<Zq Zr>| = {raw.mean():.3f}; mean |<Zq Zr> - <Zq><Zr>| = {conn.mean():.4f}; "
          f"max = {conn.max():.4f}")


if __name__ == "__main__":
    main()
