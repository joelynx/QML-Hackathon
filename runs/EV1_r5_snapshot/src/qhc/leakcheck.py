"""Decision-time boundary check (EV1).

A pipeline exposes a per-record function f(signal, samples, fs) -> array (n_beats, d) of features or class
probabilities, one row per beat position in `samples` (sorted). For beat i the allowed inputs end at
    b_i = max(samples[i+1], samples[i] + LOOKAHEAD_SEC * fs).
check_lookahead replaces the signal after b_i with noise and drops beat positions after b_i, recomputes f, and
requires row i to be unchanged. Every pipeline must pass it before its first full evaluation.
"""
import numpy as np

from . import evalspec as E


def boundary(samples, fs, i):
    nxt = samples[i + 1] if i + 1 < len(samples) else samples[i]
    return int(max(nxt, samples[i] + round(E.LOOKAHEAD_SEC * fs)))


def check_lookahead(fn, signal, samples, fs, beat_indices, seed=0, rtol=1e-6, atol=1e-9):
    """Return the beat indices whose output changes when the data after their boundary is altered."""
    samples = np.asarray(samples)
    full = np.asarray(fn(signal, samples, fs))
    rng = np.random.default_rng(seed)
    bad = []
    for i in beat_indices:
        b = boundary(samples, fs, i)
        sig = np.array(signal, dtype=float, copy=True)
        tail = sig[b + 1:]
        sig[b + 1:] = rng.normal(np.mean(signal), np.std(signal) + 1e-9, size=tail.shape)
        keep = samples <= b
        out = np.asarray(fn(sig, samples[keep], fs))
        if not np.allclose(out[i], full[i], rtol=rtol, atol=atol, equal_nan=True):
            bad.append(int(i))
    return bad
