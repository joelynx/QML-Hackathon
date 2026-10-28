# Ideas

## Index
| ID | Idea | Grounding | Probe type | Evidence | Gain | P(success) | Effort | Informative | Status |
|---|---|---|---|---|---|---|---|---|---|
| I001 | Classical-spin (mean-field) reservoir of the selected QRC Hamiltonian, K = 220 | EVAL.md rule 7; Kornjača et al. 2024 | full (secondary) | E004 (A016) | n/a (control) | high (runs) | low | high | passed (control run as E004; its criterion, "report either way", is met: the mean-field model matches the QRC) |
| I002 | Separable QRC (J = 0, no entanglement), K = 220 | EVAL.md rule 7; Bowles et al. 2024 | full (secondary) | E005 (A016) | n/a (control) | high | low | high | passed (control run as E005; reported: V F1 -0.063 without couplings) |
| I003 | RR-only readout as a reported control | A009: RR alone 0.637 DS1 OOF, competitive with every reservoir | full (secondary) | E001, E006 | n/a (control) | high | low | high | passed (control run as E006; ds2s 0.6997) |
| I004 | Exact-expectation QRC (shots = None) and a shot-count sweep | EVAL.md rule 6 (ablation) | proxy then full | none yet | low | high | low | medium | passed (ablation run as E012/E013; reported: no measurable shot-noise effect at 1,024 shots) |
| I005 | Device-noise simulation of the selected QRC (depolarising and readout error at published Rigetti Cepheus / IQM Garnet rates) | EVAL.md hardware and noise tracks | full (secondary) | none yet | n/a | medium | medium | high | failed (E015: mechanism checks passed; the declared prediction, V F1 towards the separable control's, did not hold on DS1; reported) |
| I006 | Braket hardware subset: about 100 ds2s beats, several 10-qubit copies run in parallel on disjoint qubits of one device to cut per-task cost | EVAL.md hardware track; Braket per-task fee USD 0.30 | diagnostic | pricing checked 2026-10-26 | n/a | medium | medium | high | passed (E019: one approved Rigetti task, 48 beats, diagnostic reported) |
| I007 | Ablations over qubit count and readout size (K changes, so these are not headline-search members) | EVAL.md rule 2 | proxy then full | none yet | unknown | medium | medium | medium | passed (ablation run as E014; reported) |
| I008 | Mechanism diagnostic: kernel-target alignment or geometric difference between QRC and ESN feature Gram matrices, per patient | scorecard Depth anchor 3 | diagnostic | none yet | n/a | high | medium | high | passed (diagnostic run as E017; reported) |
| I009 | Strong non-reservoir classical context model (gradient boosting on window + RR), declared DS1 budget | progress review P1; EVAL.md rule 7 ("a strong classical reference for context only") | full (secondary, post-hoc) | none yet | n/a (context) | high (runs) | low | high | passed (context model run as E016; reported) |

Ratings: low / medium / high. Status: backlog / parked / probing / passed / failed / promoted / dropped.
*passed* = the probe met its predeclared criterion. *promoted* = a full-evaluation experiment built on it was verified and adopted as incumbent. If a full experiment built on a passed probe fails and the line is abandoned, set *dropped* and record why on the card; *passed* describes the probe, not the idea's fate.

## I001
- **Grounding:** EVAL.md matched-baseline rule 7; Kornjača et al. 2024 (`doi:10.48550/arxiv.2407.02553`) use a classical-spin model of the same Hamiltonian as a heuristic control for what quantum dynamics add.
- **Hypothesis (mechanism and prediction):** if the QRC's value comes from entanglement and quantum correlations, the mean-field product-state evolution of the same gates (Bloch vectors, ZZ replaced by Z rotations driven by neighbours' <Z>, ZZ readout = product of <Z>) scores lower. If it scores the same, the QRC acts as a classical nonlinear map.
- **Control:** the headline QRC (E003) and the ESN (E002).
- **Smallest informative experiment:** the same selected configuration, 5 seeds, 1,024-shot sampling of independent bits; DS1 OOF first (proxy), then `compare --role secondary` on ds2s after the headline.
- **If pass / If fail:** either result is reported; it is a control, not a candidate.
- **Ratings:** evidence low, plausible gain n/a, P(success) high, total effort low, informative value high
- **Why selected / not selected:** needed for the Ingenuity anchor 3 and the Depth analysis.
- **Linked experiments:** E004 (DS1 OOF proxy, then EV2 secondary on ds2s: E003 vs E004 +0.0039 [-0.0028, +0.0115]); A012, A016
- **Status:** passed (2026-10-26 22:16; the control's criterion is to report the result either way)

## I009
- **Grounding:** the progress review supplied by the author (2026-10-28, P1): no strong non-reservoir classical model was run; the RR-only readout (E006, 0.700) already gives most of the performance. EVAL.md rule 7 lists "a strong classical reference for context only".
- **Hypothesis (mechanism and prediction):** a nonlinear tabular learner on the same inputs (patient-relative window + RR) is a stronger classical reference than the matched ESN; if it matches or beats E003, the quantum arm's position is "comparable to a strong classical model at best".
- **Control:** E003 and E002 as candidates against E016 as the base (positive = the reservoir arm is better).
- **Smallest informative experiment:** E016: HistGradientBoosting, N = 30 DS1 configurations (20-minute cap), 5 seeds, DS1 OOF (proxy), then two ds2s secondary comparisons (full, descriptive). Post-hoc: chosen after the ds2s results; disclosed.
- **If pass / If fail:** context either way; reported in the README whatever the outcome.
- **Ratings:** evidence medium, plausible gain n/a, P(success) high, total effort low, informative value high
- **Why selected / not selected:** the review's P1; closes a soundness gap the judges may raise.
- **Linked experiments:** E016
- **Status:** passed (E016 run and reported, 2026-10-28 19:41)
