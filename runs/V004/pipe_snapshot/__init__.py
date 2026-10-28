"""EV1 pipelines: beat features, reservoirs (classical and simulated quantum), readout, tuning and prediction.

Not part of the evaluation revision (that covers the top-level src/qhc/*.py only); see pipe_revision().
"""
import glob
import hashlib
import os


def pipe_revision():
    """First 16 hex of sha256 over src/qhc/pipe/*.py (sorted), line endings normalised to LF: the pipeline code
    identity for run manifests."""
    h = hashlib.sha256()
    for p in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "*.py"))):
        with open(p, "rb") as f:
            h.update(f.read().replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]
