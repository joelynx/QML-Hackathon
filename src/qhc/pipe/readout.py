"""Readout shared by every arm: standardised features -> class-balanced multinomial logistic regression (L2), full
batch L-BFGS on the GPU; decision = argmax of the probabilities. The regularisation grid LAMBDAS is nested inside every
configuration (EVAL.md matched-baseline rule 3) and is the only readout search.
"""
import numpy as np
import torch

from .. import evalspec as E
from ..scorer import f1_from_confusion
from .reservoirs import DEVICE

CLASS_IDX = {c: i for i, c in enumerate(E.CLASSES)}
LAMBDAS = (1e-3, 1e-2, 1e-1, 1.0)


class Readout:
    def __init__(self, lam, device=DEVICE):
        self.lam, self.device = float(lam), device

    def fit(self, X, y):
        X = np.asarray(X, dtype=np.float32)
        self.mu, self.sd = X.mean(0), X.std(0) + 1e-6
        Xt = torch.tensor((X - self.mu) / self.sd, device=self.device)
        yt = torch.tensor(np.asarray(y), device=self.device, dtype=torch.long)
        counts = torch.bincount(yt, minlength=len(E.CLASSES)).float()
        cw = torch.where(counts > 0, len(yt) / (len(E.CLASSES) * counts.clamp(min=1)), torch.zeros_like(counts))
        w = cw[yt]
        W = torch.zeros(X.shape[1], len(E.CLASSES), device=self.device, requires_grad=True)
        b = torch.zeros(len(E.CLASSES), device=self.device, requires_grad=True)
        opt = torch.optim.LBFGS([W, b], lr=1, max_iter=500, history_size=20, tolerance_grad=1e-6,
                                tolerance_change=1e-9, line_search_fn="strong_wolfe")

        def closure():
            opt.zero_grad()
            ce = torch.nn.functional.cross_entropy(Xt @ W + b, yt, reduction="none")
            loss = (w * ce).sum() / w.sum() + self.lam * (W ** 2).sum()
            loss.backward()
            return loss

        opt.step(closure)
        self.W, self.b = W.detach().cpu().numpy(), b.detach().cpu().numpy()
        return self

    def predict_proba(self, X):
        """In float64, so that a beat's probabilities do not depend on the other rows of X."""
        z = ((np.asarray(X, dtype=np.float64) - self.mu) / self.sd) @ self.W.astype(np.float64) + self.b
        z = z - z.max(1, keepdims=True)
        p = np.exp(z)
        return p / p.sum(1, keepdims=True)

    def state(self):
        return {"lam": self.lam, "mu": self.mu, "sd": self.sd, "W": self.W, "b": self.b}


def macro_f1(y_true, y_pred):
    cm = np.zeros((len(E.CLASSES),) * 2, dtype=np.int64)
    np.add.at(cm, (y_true, y_pred), 1)
    return float(f1_from_confusion(cm).mean())


def cv_oof(F, y, records, folds, lams=LAMBDAS):
    """Grouped-CV out-of-fold probabilities for every beat (units and F/Q beats), one array per lambda.
    F (n, d) features of all prediction-set beats; y (n,) class index for N/S/V units, -1 otherwise."""
    out = {lam: np.zeros((len(F), len(E.CLASSES)), dtype=np.float32) for lam in lams}
    for recs in folds.values():
        test = np.isin(records, recs)
        train = ~test & (y >= 0)
        for lam in lams:
            out[lam][test] = Readout(lam).fit(F[train], y[train]).predict_proba(F[test])
    return out


def oof_scores(oof, y):
    units = y >= 0
    return {lam: macro_f1(y[units], p[units].argmax(1)) for lam, p in oof.items()}
