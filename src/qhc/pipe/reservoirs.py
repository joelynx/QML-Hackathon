"""Reservoir feature maps with matched input encoding and matched readout dimension K = 220 (matched-baseline rule 2).

Input: the L = 40 point beat window, split into N_STEPS = 4 chunks of N_IN = 10 consecutive samples. Chunk k is
injected at step k; a snapshot of the reservoir is read after every step; each beat starts from a fixed initial state
(no state is carried across beats).

QRC  (simulated quantum reservoir, 10 qubits, statevector on GPU). Per step k:
       RY(in_scale * u_{k,q}) on qubit q;  then `depth` times: ZZ(J_e) on the coupling graph, RX(h) on every qubit.
     Couplings J_e = J * (1 + disorder * U[-1, 1]), drawn from the reservoir seed. Readout per snapshot: <Z_q> (10)
     and <Z_q Z_r> for all pairs (45) = 55; x 4 snapshots = 220. Headline readout is finite-shot: `shots` Z-basis
     samples per circuit per beat (one circuit per snapshot), sampled from the shot seed; shots=None gives exact
     expectations (ablation only). Every gate is native to gate-based QPUs (RY, RX, ZZ on a chain or ring).
     Shot noise is deterministic per beat: the uniforms behind beat b's samples come from a Philox stream keyed by
     (beat_key(b), shot_seed), so a beat's features do not depend on batching or on other beats.
ESN  (leaky-tanh echo state network). h <- (1 - leak) h + leak tanh(rho W h + in_scale W_in u_k + bias b), with W
     sparse (density) and scaled to spectral radius 1 before rho. Readout per snapshot: the first 55 units; x 4 = 220.
"""
import hashlib
import itertools

import numpy as np
import torch

N_IN, N_STEPS = 10, 4
N_QUBITS = N_IN
PAIRS = list(itertools.combinations(range(N_QUBITS), 2))
K_SNAP = N_QUBITS + len(PAIRS)  # 55
K = K_SNAP * N_STEPS  # 220
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def _chunks(win):
    win = np.asarray(win, dtype=np.float32)
    assert win.shape[1] == N_IN * N_STEPS
    return win.reshape(len(win), N_STEPS, N_IN)


def _z_table(n):
    """(2^n, n + n(n-1)/2) eigenvalues of Z_q and Z_q Z_r per basis state; qubit q is bit q of the index."""
    b = np.arange(2 ** n)
    z = 1.0 - 2.0 * ((b[:, None] >> np.arange(n)[None, :]) & 1)
    zz = np.stack([z[:, q] * z[:, r] for q, r in PAIRS], 1)
    return np.concatenate([z, zz], 1).astype(np.float32)


def beat_key(beat_id):
    """Stable 63-bit integer key of a beat id such as 'mitdb:207:12345'."""
    return int.from_bytes(hashlib.blake2b(str(beat_id).encode(), digest_size=8).digest(), "little") >> 1


_UNIF_CACHE = {}


def _uniforms(keys, shot_seed, n, cache=True):
    """Per-beat uniforms; the most recent shot seed's arrays are cached (tuning reuses them across configurations)."""
    tag = (int(shot_seed), n, hashlib.blake2b(np.asarray(keys).tobytes(), digest_size=16).hexdigest())
    if cache and tag in _UNIF_CACHE:
        return _UNIF_CACHE[tag]
    out = np.empty((len(keys), n), dtype=np.float32)
    for i, k in enumerate(keys):
        out[i] = np.random.Generator(np.random.Philox(key=[int(k), int(shot_seed)])).random(n, dtype=np.float32)
    if not cache:
        return out
    if any(t[0] != tag[0] for t in _UNIF_CACHE):
        _UNIF_CACHE.clear()
    _UNIF_CACHE[tag] = out
    return out


def _edges(topology):
    e = [(q, q + 1) for q in range(N_QUBITS - 1)]
    return e + [(N_QUBITS - 1, 0)] if topology == "ring" else e


class QRC:
    def __init__(self, in_scale, J, h, depth, topology, disorder, seed, shots=1024, shot_seed=None, device=DEVICE):
        self.cfg = dict(in_scale=in_scale, J=J, h=h, depth=int(depth), topology=topology, disorder=disorder)
        self.seed, self.shots = int(seed), shots
        self.shot_seed = int(seed if shot_seed is None else shot_seed)
        self.device = device
        g = np.random.default_rng(self.seed)
        edges = _edges(topology)
        self.couplings = J * (1 + disorder * g.uniform(-1, 1, len(edges)))
        ztab = _z_table(N_QUBITS)
        zz_energy = sum(c * ztab[:, q] * ztab[:, r] for c, (q, r) in zip(self.couplings, edges))
        self.zz_phase = torch.tensor(np.exp(-1j * zz_energy), dtype=torch.complex64, device=device)
        self.obs = torch.tensor(ztab, device=device)
        c, s = np.cos(h / 2), np.sin(h / 2)
        rx = np.array([[c, -1j * s], [-1j * s, c]])
        self.rx = torch.tensor(rx, dtype=torch.complex64, device=device)

    def _ry(self, psi, q, theta):
        """RY(theta) on qubit q with per-beat angles theta (n,)."""
        n = psi.shape[0]
        v = psi.view(n, 2 ** (N_QUBITS - 1 - q), 2, 2 ** q)
        c, s = torch.cos(theta / 2).view(n, 1, 1), torch.sin(theta / 2).view(n, 1, 1)
        a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
        return torch.stack([c * a0 - s * a1, s * a0 + c * a1], 2).reshape(n, -1)

    def _rx_all(self, psi):
        """RX(h) on every qubit, elementwise (no batched matmul), so results do not depend on the batch size."""
        n = psi.shape[0]
        c, ms = self.rx[0, 0], self.rx[0, 1]  # cos(h/2), -i sin(h/2)
        for q in range(N_QUBITS):
            v = psi.view(n, 2 ** (N_QUBITS - 1 - q), 2, 2 ** q)
            a0, a1 = v[:, :, 0, :], v[:, :, 1, :]
            psi = torch.stack([c * a0 + ms * a1, ms * a0 + c * a1], 2).reshape(n, -1)
        return psi

    def _readout(self, psi, unif):
        p = psi.real ** 2 + psi.imag ** 2
        if self.shots is None:
            return (p.double() @ self.obs.double()).float()
        cdf = torch.cumsum(p.double(), 1)  # fp64: the fp32 CUDA scan depends on the batch size
        idx = torch.searchsorted(cdf, unif.double() * cdf[:, -1:]).clamp(max=p.shape[1] - 1)
        counts = torch.zeros_like(p).scatter_add_(1, idx, torch.ones_like(idx, dtype=p.dtype))
        return (counts / self.shots) @ self.obs

    @torch.no_grad()
    def features(self, win, keys=None, batch=8192):
        """keys: one beat_key per row (required with finite shots)."""
        u_all = _chunks(win)
        if self.shots is not None and keys is None:
            raise ValueError("finite-shot readout needs one beat key per row")
        out = []
        for b0 in range(0, len(u_all), batch):
            u = torch.tensor(u_all[b0:b0 + batch], device=self.device)
            unif = None
            if self.shots is not None:
                unif = torch.tensor(_uniforms(keys[b0:b0 + batch], self.shot_seed, N_STEPS * self.shots),
                                    device=self.device).view(-1, N_STEPS, self.shots)
            n = u.shape[0]
            psi = torch.zeros(n, 2 ** N_QUBITS, dtype=torch.complex64, device=self.device)
            psi[:, 0] = 1
            feats = []
            for k in range(N_STEPS):
                for q in range(N_QUBITS):
                    psi = self._ry(psi, q, self.cfg["in_scale"] * u[:, k, q])
                for _ in range(self.cfg["depth"]):
                    psi = self._rx_all(psi * self.zz_phase)
                feats.append(self._readout(psi, None if unif is None else unif[:, k]))
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out).astype(np.float32)


class ESN:
    def __init__(self, size, rho, leak, in_scale, density, bias, seed, device=DEVICE):
        self.cfg = dict(size=int(size), rho=rho, leak=leak, in_scale=in_scale, density=density, bias=bias)
        self.seed, self.device = int(seed), device
        g = np.random.default_rng(self.seed)
        size = int(size)
        W = g.uniform(-1, 1, (size, size)) * (g.random((size, size)) < density)
        radius = np.abs(np.linalg.eigvals(W)).max()
        W = W * (rho / radius) if radius > 0 else W
        # float64 so that each beat's features do not depend on the batch it is computed in (float32 GEMM rounding
        # varies with the batch shape, which the lookahead check would flag)
        self.W = torch.tensor(W, dtype=torch.float64, device=device)
        self.W_in = torch.tensor(in_scale * g.uniform(-1, 1, (size, N_IN)), dtype=torch.float64, device=device)
        self.b = torch.tensor(bias * g.uniform(-1, 1, size), dtype=torch.float64, device=device)

    @torch.no_grad()
    def features(self, win, keys=None, batch=65536):
        u_all = _chunks(win)
        a, out = self.cfg["leak"], []
        for b0 in range(0, len(u_all), batch):
            u = torch.tensor(u_all[b0:b0 + batch], dtype=torch.float64, device=self.device)
            h = torch.zeros(u.shape[0], self.cfg["size"], dtype=torch.float64, device=self.device)
            feats = []
            for k in range(N_STEPS):
                h = (1 - a) * h + a * torch.tanh(h @ self.W.T + u[:, k] @ self.W_in.T + self.b)
                feats.append(h[:, :K_SNAP])
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out).astype(np.float32)


class MeanField(QRC):
    """Classical-spin control of a QRC configuration (EVAL.md rule 7; after Kornjača et al. 2024): the same gates
    applied to a product state of Bloch vectors. RY and RX rotate each vector exactly; a ZZ(J) gate on edge (a, b)
    becomes Z rotations by 2 J <Z_b> on a and 2 J <Z_a> on b (simultaneous update). Readout: <Z_q> and the product
    <Z_q><Z_r>, or, with finite shots, independent bits per qubit sampled from the same per-beat Philox streams."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.edges = _edges(self.cfg["topology"])

    @torch.no_grad()
    def features(self, win, keys=None, batch=4096):
        u_all = _chunks(win)
        if self.shots is not None and keys is None:
            raise ValueError("finite-shot readout needs one beat key per row")
        pairs = torch.tensor(PAIRS, device=self.device)
        J = torch.tensor(self.couplings, dtype=torch.float32, device=self.device)
        ea = torch.tensor([e[0] for e in self.edges], device=self.device)
        eb = torch.tensor([e[1] for e in self.edges], device=self.device)
        ch, sh = np.cos(self.cfg["h"]), np.sin(self.cfg["h"])
        out = []
        for b0 in range(0, len(u_all), batch):
            u = torch.tensor(u_all[b0:b0 + batch], device=self.device)
            n = u.shape[0]
            x = torch.zeros(n, N_QUBITS, device=self.device)
            y = torch.zeros_like(x)
            z = torch.ones_like(x)
            unif = None
            if self.shots is not None:
                unif = torch.tensor(_uniforms(keys[b0:b0 + batch], self.shot_seed, N_STEPS * N_QUBITS * self.shots,
                                              cache=False), device=self.device).view(n, N_STEPS, N_QUBITS, self.shots)
            feats = []
            for k in range(N_STEPS):
                th = self.cfg["in_scale"] * u[:, k]
                x, z = x * torch.cos(th) + z * torch.sin(th), -x * torch.sin(th) + z * torch.cos(th)
                for _ in range(self.cfg["depth"]):
                    phi = torch.zeros_like(z)
                    phi.index_add_(1, ea, 2 * J * z[:, eb])
                    phi.index_add_(1, eb, 2 * J * z[:, ea])
                    x, y = x * torch.cos(phi) - y * torch.sin(phi), x * torch.sin(phi) + y * torch.cos(phi)
                    y, z = y * ch - z * sh, y * sh + z * ch
                if self.shots is None:
                    zs = z
                    zz = z[:, pairs[:, 0]] * z[:, pairs[:, 1]]
                else:
                    # bit q of shot s is 0 with probability (1 + <Z_q>) / 2, from its own slice of the beat's stream
                    zb = torch.where(unif[:, k] < ((1 + z) / 2).unsqueeze(-1), 1.0, -1.0)
                    zs = zb.mean(-1)
                    zz = (zb[:, pairs[:, 0]] * zb[:, pairs[:, 1]]).mean(-1)
                feats.append(torch.cat([zs, zz], 1))
            out.append(torch.cat(feats, 1).cpu().numpy())
        return np.concatenate(out).astype(np.float32)


ARMS = {"qrc": QRC, "esn": ESN, "mf": MeanField}


def make(arm, cfg, seed, **kw):
    return ARMS[arm](**cfg, seed=seed, **kw)
