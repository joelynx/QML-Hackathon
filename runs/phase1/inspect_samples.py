"""Phase 1 data-sample inspection. Usage: python -I inspect_samples.py <samples_dir>"""
import collections
import gzip
import os
import sys

import numpy as np
import pandas as pd

B = sys.argv[1]


def hdr(t):
    print("\n" + "=" * 8, t)


# ---------- MIT-BIH ----------
hdr("MIT-BIH Arrhythmia")
import wfdb

mdir = os.path.join(B, "mitdb")
recs = open(os.path.join(mdir, "RECORDS")).read().split()
print("records:", len(recs))
# AAMI mapping (de Chazal 2004)
AAMI = {**{s: "N" for s in "NLRej"}, **{s: "S" for s in "AaJS"}, **{s: "V" for s in "VE"}, "F": "F", **{s: "Q" for s in "/fQ"}}
DS1 = [101, 106, 108, 109, 112, 114, 115, 116, 118, 119, 122, 124, 201, 203, 205, 207, 208, 209, 215, 220, 223, 230]
DS2 = [100, 103, 105, 111, 113, 117, 121, 123, 200, 202, 210, 212, 213, 214, 219, 221, 222, 228, 231, 232, 233, 234]
PACED = [102, 104, 107, 217]
tot = collections.Counter()
per = {}
leads = collections.Counter()
for r in recs:
    h = wfdb.rdheader(os.path.join(mdir, r))
    a = wfdb.rdann(os.path.join(mdir, r), "atr")
    c = collections.Counter(AAMI.get(s) for s in a.symbol if s in AAMI)
    per[int(r)] = c
    tot += c
    leads[tuple(h.sig_name)] += 1
    if r == "100":
        print("100 header: fs", h.fs, "n_sig", h.n_sig, "sig_len", h.sig_len, "dur_min", round(h.sig_len / h.fs / 60, 1), "names", h.sig_name, "comments", h.comments)
        sig, _ = wfdb.rdsamp(os.path.join(mdir, r), sampto=720)
        print("100 first 2 s: shape", sig.shape, "range mV", sig.min(0).round(2), sig.max(0).round(2), "finite", np.isfinite(sig).all())
print("lead configs:", dict(leads))
print("AAMI totals (all 48):", dict(tot))
for name, ds in [("DS1", DS1), ("DS2", DS2)]:
    c = sum((per[r] for r in ds), collections.Counter())
    print(name, len(ds), "records:", dict(c), "| S-beat records:", sum(per[r]["S"] > 0 for r in ds))
print("paced:", {r: dict(per[r]) for r in PACED})
s_conc = sorted(((per[r]["S"], r) for r in DS2), reverse=True)[:3]
print("DS2 S-beat concentration (top 3 records):", s_conc, "of", sum(per[r]["S"] for r in DS2))

# ---------- SPECT ----------
hdr("UCI SPECT Heart")
sd = os.path.join(B, "spect")
tr = pd.read_csv(os.path.join(sd, "SPECT.train"), header=None)
te = pd.read_csv(os.path.join(sd, "SPECT.test"), header=None)
print("train", tr.shape, "test", te.shape, "label balance train", tr[0].value_counts().to_dict(), "test", te[0].value_counts().to_dict())
allx = pd.concat([tr, te])
print("values", sorted(pd.unique(allx.values.ravel())), "feature means", allx.iloc[:, 1:].mean().round(2).tolist())
print("duplicate rows (all 23 cols):", allx.duplicated().sum(), "| distinct feature patterns:", allx.iloc[:, 1:].drop_duplicates().shape[0])

# ---------- MedMNIST ----------
hdr("MedMNIST PneumoniaMNIST")
z = np.load(os.path.join(B, "medmnist", "pneumoniamnist.npz"))
for k in z.files:
    v = z[k]
    print(k, v.shape, v.dtype, (np.unique(v, return_counts=True) if "label" in k else (v.min(), v.max())))

# ---------- BBBP ----------
hdr("MoleculeNet BBBP")
d = pd.read_csv(os.path.join(B, "bbbp", "BBBP.csv"))
print(d.shape, list(d.columns), d["p_np"].value_counts().to_dict(), "dup smiles", d["smiles"].duplicated().sum())
print(d.head(3).to_string())

# ---------- PTB-XL ----------
hdr("PTB-XL metadata")
p = pd.read_csv(os.path.join(B, "ptbxl", "ptbxl_database.csv"))
print(p.shape, "patients", p["patient_id"].nunique(), "folds", p["strat_fold"].value_counts().sort_index().to_dict())
print("date range", p["recording_date"].min(), p["recording_date"].max(), "cols", list(p.columns)[:12], "...")

# ---------- CinC 2012 ----------
hdr("PhysioNet/CinC 2012 outcomes (set-a)")
o = pd.read_csv(os.path.join(B, "cinc2012", "Outcomes-a.txt"))
print(o.shape, list(o.columns), "mortality", o["In-hospital_death"].value_counts().to_dict())

# ---------- CHB-MIT ----------
hdr("CHB-MIT chb01 summary")
t = open(os.path.join(B, "chbmit", "chb01-summary.txt")).read()
print(t[:600])
print("files listed:", t.count("File Name:"), "seizure entries:", t.count("Seizure Start") + t.count("Seizure 1 Start"))

# ---------- TCGA BRCA ----------
hdr("TCGA BRCA (UCSC Xena)")
cl = pd.read_csv(os.path.join(B, "tcga_brca", "BRCA_clinicalMatrix"), sep="\t", low_memory=False)
print("clinical", cl.shape)
for col in ["PAM50Call_RNAseq", "breast_carcinoma_estrogen_receptor_status", "vital_status", "sample_type"]:
    if col in cl:
        print(col, cl[col].value_counts(dropna=False).head(8).to_dict())
with gzip.open(os.path.join(B, "tcga_brca", "HiSeqV2.gz"), "rt") as f:
    head = f.readline().rstrip("\n").split("\t")
    n_genes = sum(1 for _ in f)
print("expression: samples", len(head) - 1, "genes", n_genes, "first ids", head[1:3])
