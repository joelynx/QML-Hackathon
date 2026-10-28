"""Download MIT-BIH Arrhythmia (mitdb) and MIT-BIH Supraventricular Arrhythmia (svdb) v1.0.0 from the PhysioNet
open-data mirror and verify every file against PhysioNet's SHA256SUMS.txt. Standard library only.

    python scripts/download_data.py [--out runs/data/raw] [--db mitdb svdb]

The sums file itself must match the hash pinned in PINNED_SUMS (the EV1 data card). Already-present files that verify
are skipped. Licence: ODC-By 1.0 (cite the databases and PhysioNet).
"""
import argparse
import hashlib
import os
import sys
import urllib.request

MIRROR = "https://physionet-open.s3.amazonaws.com/{db}/1.0.0/{name}"
EXTS = ("hea", "dat", "atr")
# sha256 of PhysioNet's SHA256SUMS.txt for each database v1.0.0, as recorded in the EV1 data card (EVAL.md) and in
# runs/data/processed/EV1/manifest.json. The per-file sums are trusted only after this file matches.
PINNED_SUMS = {"mitdb": "b61158a96d5f2ca80edfb354a9a66a6324836c390a84e1966dcee2b907d6be43",
               "svdb": "59791a754f68ac6889424a22aced4bffc90b6d03389f9f49ae95b6e345be3552"}


def fetch(url, path):
    tmp = path + ".part"
    with urllib.request.urlopen(url, timeout=300) as r, open(tmp, "wb") as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    os.replace(tmp, path)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def get_db(db, out):
    d = os.path.join(out, db)
    os.makedirs(d, exist_ok=True)
    for name in ("RECORDS", "SHA256SUMS.txt"):
        fetch(MIRROR.format(db=db, name=name), os.path.join(d, name))
    got = sha256(os.path.join(d, "SHA256SUMS.txt"))
    if got != PINNED_SUMS[db]:
        print(f"{db}: SHA256SUMS.txt has sha256 {got}, not the pinned {PINNED_SUMS[db]}; stopping")
        return False
    sums = {}
    for line in open(os.path.join(d, "SHA256SUMS.txt")):
        parts = line.split()
        if len(parts) == 2:
            sums[parts[1]] = parts[0]
    bad = []
    for rec in open(os.path.join(d, "RECORDS")).read().split():
        for ext in EXTS:
            name = f"{rec}.{ext}"
            path = os.path.join(d, name)
            if not (os.path.exists(path) and sha256(path) == sums.get(name)):
                fetch(MIRROR.format(db=db, name=name), path)
            if sha256(path) != sums.get(name):
                bad.append(name)
    n = len(open(os.path.join(d, "RECORDS")).read().split())
    print(f"{db}: {n} records, {n * len(EXTS) - len(bad)} files verified, {len(bad)} failed {bad[:5]}")
    return not bad


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=os.path.join("runs", "data", "raw"))
    ap.add_argument("--db", nargs="+", default=["mitdb", "svdb"], choices=["mitdb", "svdb"])
    a = ap.parse_args()
    ok = all([get_db(db, a.out) for db in a.db])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
