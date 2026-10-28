# Problem Brief (open mode)

- **Brief version / date:** `hackathon_details.md` (local copy of the organisers' brief, file dated 2026-10-25), read 2026-10-26. Phase 1 written 2026-10-26 by the agent.
- **Conflict rule:** official text wins: the organisers' brief, then the official Submissions panel and form once published, with later organiser announcements superseding earlier ones. Pages about other quantum hackathons are context only and never rules. Where the official text is silent, the assumption is written here and flagged.

## Sources
| Source | Link | Accessed / rule version | Kind (official / forum / assumption) |
|---|---|---|---|
| Hackathon brief: overview, steps, assessment, deliverables, timeline | `hackathon_details.md` (supplied by the human; no public URL found) | 2026-10-26 | official |
| Web search for the event by name ("Quantum Healthcare Hackathon" UAE 2026): no public page found; closest hits are NYUAD's quantum hackathons for social good | https://hackathon.nyuad.nyu.edu/ | 2026-10-26 | external, context only |
| Past winners, NYUAD Hackathon 2023 (health entries) | https://hackathon.nyuad.nyu.edu/year/2023/ | 2026-10-26 | external, context only |
| Past winners, Pakistan national quantum hackathon (LUMS news) | https://sbasse.lums.edu.pk/winners-of-national-quantum-hackathon | 2026-10-26 | external, context only |
| MIT-BIH Arrhythmia Database v1.0.0 (ODC-By 1.0, open access) | https://physionet.org/content/mitdb/1.0.0/ (files via https://physionet-open.s3.amazonaws.com/mitdb/1.0.0/) | 2026-10-26 | data source |
| UCI SPECT Heart (CC BY 4.0) | https://archive.ics.uci.edu/dataset/95/spect+heart | 2026-10-26 | data source |
| MedMNIST v2, PneumoniaMNIST (CC BY 4.0; DermaMNIST is CC BY-NC) | https://medmnist.com/ ; https://zenodo.org/records/10519652 | 2026-10-26 | data source |
| TCGA-BRCA RNA-seq and clinical matrix, UCSC Xena TCGA hub | https://tcga-xena-hub.s3.us-east-1.amazonaws.com/download/TCGA.BRCA.sampleMap%2FHiSeqV2.gz | 2026-10-26 | data source (terms page not readable; TCGA open-access tier assumed) |
| PTB-XL v1.0.3 metadata (CC BY 4.0) | https://physionet.org/content/ptb-xl/1.0.3/ | 2026-10-26 | data source |
| PhysioNet/CinC Challenge 2012, outcomes for set A | https://physionet.org/content/challenge-2012/1.0.0/ | 2026-10-26 | data source (licence not checked) |
| CHB-MIT Scalp EEG, chb01 summary | https://physionet.org/content/chbmit/1.0.0/ | 2026-10-26 | data source (licence not checked) |
| MoleculeNet BBBP | https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/BBBP.csv | 2026-10-26 | data source (licence not checked) |
| IBM Quantum Open Plan: free, up to 10 QPU minutes per 28-day window | https://quantum.cloud.ibm.com/docs/guides/plans-overview (seen through search results, page not opened) | 2026-10-26 | external, provider terms |
| Literature (paper keys inline below; about 31 papers annotated in paperfetch with tag `qhack-phase1`) | paperfetch local store | 2026-10-26 | literature |

## The competition
- **Theme and tracks:** use quantum techniques to improve a classical ML approach, or build a quantum model that outperforms a baseline, on a healthcare problem the team chooses. National / Hybrid track. *official*
- **Judges: who, how long per team, what they see:** who: not stated *(open question)*. How long: not stated. What they see: the submitted codebase, comparative evaluation, write-up of approach and reproduction instructions; shortlisted teams give a final presentation on 2026-10-31 (format to be announced). *official*, except where marked unknown.
- **Rubric:** no weights published. The assessment sentence names one performance criterion and three quality criteria:

| Criterion | Weight | What the rubric text says | What past winners did |
|---|---|---|---|
| Performance relative to the classical baseline | not stated (assumption: listed first, so likely heavy) | "the quantum approach's performance relative to its classical baseline"; the baseline should be "comparably similar ... through similar data preprocessing, feature engineering, or model architectures"; the quantum part must address "a limitation of the classical approach and support measurable performance gains" | Pakistan national quantum hackathon, 1st place (6-8 Feb; year not on the page, consistent with 2025): a hybrid QCNN for TB chest X-rays, claimed to beat "a fair classical baseline under severe data limitations"; no metrics published |
| Ingenuity | not stated | "ingenuity ... of the chosen problem-solving approach" | NYUAD 2023: QML tumour detection placed 3rd (feeQra); QML for early Alzheimer's won Audience Choice (FuQdan); methods and data not published |
| Depth | not stated | "depth ... of the chosen problem-solving approach" | not visible |
| Soundness | not stated | "soundness"; plus step 4: "consistent evaluation conditions", "appropriate metrics and consistent data", "results, improvements, and limitations clearly" | not visible |

The four challenge steps are what the judges will look for in the write-up: (1) problem definition, relevance, data and intended outcome; (2) a strong classical baseline, credited and documented with configuration and performance; (3) the quantum contribution, why it is appropriate and which limitation it addresses; (4) shared evaluation of both approaches. *official*

- **Deliverables and formats:** functional codebase implementing the classical and the quantum approach; comparative evaluation showing both models' results; explanation of the healthcare problem, methods and purpose of the quantum part; reproduction material (settings, dependencies, instructions). File formats and size limits are not yet published; the Submissions panel will hold them. *official*
- **Constraints:**
  - Team size: not stated *(open question)*.
  - Allowed tools and data: not restricted by the brief. *Assumption:* public datasets and open-source libraries are allowed, provided existing work is credited ("Credit existing work" is in step 2).
  - Licensing: every dataset used must permit research use with attribution. All three shortlisted datasets do (ODC-By 1.0, TCGA open tier, CC BY 4.0).
  - Must be built during the event: not stated (n/a as far as known). All code will be written during the event anyway.
  - QPU use: not required by the brief. *Assumption:* simulator results are acceptable, and a small real-hardware run is optional extra evidence.
  - Deadline: 2026-10-28 23:59 UAE (UTC+4), which is 19:59 UTC, through the official form. Final presentations 2026-10-31. *official*

## Problem selection
What the crowd will build: the past winners above, and the 2025 review of quantum ML in healthcare (Gupta et al., `doi:10.1038/s41746-025-01597-z`; 169 eligible studies, 81.7% simulation only, datasets cluster on a few open databases, quantum kernels and annealing dominate, error bars almost never reported), point to hybrid QCNNs on chest X-ray or MedMNIST images and QSVMs on small UCI tables (breast cancer, heart disease, diabetes). Most report no matched baseline or uncertainty.

What the evidence says about gains: there is no published result of a quantum model beating a carefully matched classical model on real clinical data. In the largest careful benchmark, out-of-the-box classical models won and circuits without entanglement did as well as entangled ones (Bowles, Ahmed & Schuld 2024, `doi:10.48550/arxiv.2403.07059`). With bandwidth tuned on both sides, quantum kernels become competitive but not better (Shaydulin & Wild, `doi:10.1103/physreva.106.042407`). With matched size and tuning effort, quantum reservoirs lose their edge (Pandey 2026, `doi:10.48550/arxiv.2607.09905`, abstract only). Every candidate below therefore has low-to-medium odds of a detectable gain against a fair baseline. The choice is about where a gain is most plausible, which result is most credible either way, and where we differ from the crowd.

| # | Candidate | User and pain | Data sources (named) | Sample inspected? | Rubric fit (perf / ingenuity / depth / soundness) | Tractable in time | Distinct from the crowd | Main risk |
|---|---|---|---|---|---|---|---|---|
| C1 | **Patient-independent heartbeat classification (arrhythmia) with quantum reservoir features, compared with matched classical reservoirs** | Holter and wearable ECG review: models trained on other patients degrade on a new patient (S-beat PPV is typically 35-50% inter-patient), and many published QML ECG results come from beat-level splits that leak the patient | MIT-BIH Arrhythmia DB (48 records, 47 subjects, ~110k beat labels, ODC-By 1.0) | **yes, full database in hand**; 144 files SHA256-verified; AAMI class counts are within 2 beats per class of de Chazal's Table II (EV1 r4 reconciliation) | low-med / high / high / high | medium: the signal pipeline is standard; simulating 8-12 qubits for about 100k beats on GPU is minutes; reservoirs need no gradient training | **high**: no quantum reservoir study on MIT-BIH with an inter-patient split and a matched classical reservoir was found; the quantum ECG papers found use beat- or image-level splits | no detectable gain against a matched reservoir (the likeliest outcome); DS2 S-class metrics dominated by one record (A001); one subject sits on both sides of DS1/DS2 (A004) |
| C2 | **Small gene-panel breast-cancer classification with bandwidth-matched quantum kernels, screened by geometric difference** | Labs in low-resource settings that can afford only a cheap 8-16 gene qPCR panel rather than full PAM50 or RNA-seq; small cohorts | TCGA-BRCA RNA-seq (UCSC Xena HiSeqV2: 1,218 samples x 20,530 genes) + clinical matrix (1,247 rows: PAM50 call 956, ER IHC status 1,178, vital status 1,242) | **yes**, expression and clinical files in hand | low-med / medium / medium-high / high | **high**: tabular, one qubit per gene, kernels on 8-16 qubits are cheap | medium-low: QSVMs on gene expression are common in the literature (e.g. Krunic et al. 2022, `doi:10.1109/tqe.2022.3176806`, on EHR) | PAM50 target is computed from the same RNA-seq (A003); ER status is nearly trivial from ESR1; survival signal is weak; most likely no detectable change |
| C3 | Hybrid quantum CNN for paediatric pneumonia chest X-ray | Radiograph triage where labelled images are scarce | MedMNIST v2 PneumoniaMNIST (5,856 images, 28x28; train 4,708 / val 524 / test 624; CC BY 4.0) | yes | low / low / medium / medium | high | **low**: the crowd default, and the past winner's approach | indistinct; no patient IDs, so patient overlap across splits cannot be checked; quantum layers usually only match a small CNN |
| C4 | Quantum circuit Born machine as a generative classifier and synthetic-patient generator for cardiac SPECT diagnosis | Cardiac SPECT on small cohorts; sharing data without exposing patients | UCI SPECT Heart (267 patients, 22 binary features; CC BY 4.0) | yes | low-med / high / medium / low-med | medium: 23 qubits as a statevector is easy, but generative evaluation takes design work | high: binary features map natively onto qubits; Born vs Boltzmann at matched parameters is a classic pairing (Cheng, Chen & Wang 2018, `doi:10.3390/e20080583`) | tiny data (55 normal patients), 39 duplicate rows and a 172:15 test file (A002) give very wide intervals; likely judged a toy problem |
| C5 | Seizure detection from scalp EEG with quantum kernels on Riemannian covariance features | Epilepsy monitoring units | CHB-MIT Scalp EEG (256 Hz, 23 channels; chb01: 42 files, 7 seizures) | partial: summary file only, no EDF signals | low / medium / medium / medium | low-medium: heavy EEG preprocessing; full set is about 40 GB | medium: pyRiemann-qiskit already does this | on P300 data quantum classifiers did not generalise (Cattan & Quemy 2023, `doi:10.3390/brainsci13020303`) |
| C6 | Blood-brain-barrier permeability for CNS drug design with quantum kernels on molecular descriptors | Medicinal chemists screening CNS drug candidates | MoleculeNet BBBP (2,050 SMILES, 1,567 positive / 483 negative) | yes | low / medium / medium / medium | medium (needs RDKit, scaffold split) | medium | healthcare link is indirect; licence unclear; QSVMs on fingerprints are common |
| C7 | ICU in-hospital mortality from the first 48 h with quantum kernels or quantum LSTM | ICU early-warning | PhysioNet/CinC 2012 set A (4,000 stays, 13.9% mortality) | partial: outcomes only, time series not downloaded | low / low-medium / medium / medium | medium | low-medium | tuned gradient boosting is a strong baseline; a quantum LSTM is slow to simulate per time step |
| C8 | Sparse clinical risk score selected by QUBO and solved with QAOA | Bedside scoring rules with few items | e.g. CinC 2012 or UCI Heart Disease | not inspected | very low / medium / low / **low** | high | medium | at sizes we can simulate, classical solvers match or beat QAOA, so any gain would come from the QUBO formulation, not from the quantum part |

- **Recommended: C1, quantum reservoir features for patient-independent heartbeat classification on MIT-BIH.**
  - It is the most distinctive option with data fully in hand.
  - Its comparable baseline is natural and strict: an echo-state network and a classical-spin (mean-field) version of the same Hamiltonian, at equal readout size and equal tuning effort, following the matching rule of Kornjača et al. 2024 (`doi:10.48550/arxiv.2407.02553`).
  - It puts our effort where judges can check it: patient-level evaluation instead of the leaky beat-level splits common in quantum ECG work.
  - It fills a gap: no quantum reservoir study on MIT-BIH with an inter-patient split was found.
  - A quantum reservoir needs no gradient training on the quantum side, so a few beats can be run on real hardware cheaply.
- **Runner-up (pivot target): C2, small gene-panel classification on TCGA-BRCA with bandwidth-matched quantum kernels.** Its data is in hand and its pipeline is the fastest to build, which is what a pivot needs. It is less distinctive than C1. If chosen as the pivot, prefer ER status by IHC or a survival target over PAM50 (A003).
- **Shortlist (top 3, each with an inspected sample):** C1 > C2 > C4.
  - C4 is more distinctive than C2 but less sound at n = 267, so it ranks third. The human may prefer it to C2 as the runner-up; its data is also in hand.
- **Ranked list with reasons:**
  1. C1: distinct, matched controls available, data verified, strong soundness story.
  2. C2: fastest to build, credible small-cohort framing, less distinct.
  3. C4: quantum-native binary data and a classic Born-vs-Boltzmann comparison, but tiny data.
  4. C3: tractable but the crowd default.
  5. C7: strong classical baseline, little quantum rationale.
  6. C6: indirect healthcare link, licence unclear.
  7. C5: prior evidence negative, data heavy.
  8. C8: rejected on soundness.
- **Watchlist (blocked on a request; not eligible as runner-up; choosing one needs a stated contingency):** none. No candidate needs gated data. MIMIC-III/IV and eICU were not considered, because credentialed access cannot be obtained before the deadline.
- **Rejected and why:**
  - C8: no plausible quantum mechanism for a gain at simulable sizes; a claim would mislead.
  - C5: no signal data sampled; prior work negative; preprocessing cost.
  - C6: indirect healthcare relevance; licence unverified.
  - C7: low distinctiveness; strong classical baseline.
  - C3: kept off the shortlist for indistinctness, though its data is in hand.
- **Human decision and date:** 2026-10-26, between 02:15 and 15:50 UAE (exact time not recorded). The human chose **C1**, with **C2 as the runner-up** ("move on with C1, and C2 as the runner up"). The human also asked how to use the USD 15 for an edge; the agent's recommendation and the pending choices are in STATE.md.

## Chosen problem (exact)
C1, chosen by the human on 2026-10-26.

- **User:** a cardiology technician or physician reviewing long ambulatory ECGs (Holter or wearable patch). Interpreting algorithms trained on other patients must work on a new patient without per-patient labels.
- **Decision the system supports:** for each detected heartbeat, flag it as normal (N), supraventricular ectopic (S) or ventricular ectopic (V), so that abnormal beats and episodes are prioritised for human review. F (fusion) and Q (unclassifiable) are reported but not part of the primary metric.
- **Input:**
  - Single-lead ECG (MLII, chosen by lead name; A005), 360 Hz, band-pass filtered.
  - A window around each reference R-peak from the MIT-BIH annotations; using reference beat locations is standard practice for this benchmark (assumption, see the open questions).
  - Causal RR-interval features of the same patient.
- **Output and deliverable:**
  - Per-beat class probabilities for N/S/V.
  - A reproducible pipeline with interchangeable feature blocks: (a) classical handcrafted features (RR intervals and morphology); (b) an echo-state network reservoir; (c) a classical-spin (mean-field) reservoir from the same Hamiltonian as (d); (d) a simulated quantum reservoir of 8-12 qubits (transverse-field Ising or Rydberg-type dynamics, inputs injected as rotations, readout of one- and two-qubit Pauli expectations).
  - All blocks feed the same classically trained linear readout. Ablations: separable (non-interacting) quantum reservoir, and readout size swept.
  - Optional: a small real-QPU run of the quantum reservoir on a few hundred test beats.
  - Write-up, comparative evaluation, reproduction instructions.
- **Technical success criterion (declared before modelling, 2026-10-26; Phase 2 justifies it and sets the thresholds):**
  - Primary metric: macro-F1 over N, S and V on patient-held-out beats. Training on DS1, testing on DS2 (de Chazal 2004, `doi:10.1109/tbme.2004.827359`), with the four paced records excluded.
  - Primary comparison: pipeline + quantum reservoir features against pipeline + matched classical reservoir features, with equal readout dimension, equal input encoding and equal hyperparameter-search budget.
  - The quantum contribution succeeds if the paired delta is positive, its patient-level (record-cluster) bootstrap 95% CI excludes 0, and it meets the practical gain threshold Phase 2 sets.
  - Secondary, all reported:
    - S and V sensitivity and PPV: N/S/V-restricted, plus the gross VEB/SVEB measures of de Chazal 2004 Table V on the full prediction set (EV1 r4; the complete EC57 standard was not audited);
    - the same comparison under patient-grouped cross-validation over all 44 non-paced records in 43 subject groups (201 and 202 as one group, A004), for statistical power;
    - results with record 232 excluded (A001);
    - the delta against the classical-spin reservoir and against the separable ablation;
    - context only (EV1 removes edge beats, predicts three classes, uses MLII by name and a stricter temporal boundary than de Chazal's whole-record RR features) against published classical inter-patient results (de Chazal 2004 DS2: S sensitivity 75.9% / PPV 38.5%, V 77.7% / 81.9%; Dias et al. 2021, `doi:10.1016/j.cmpb.2021.105948`: S 89.7 / 36.8, V 87.9 / 93.9).
- **Rubric mapping:**
  - *Performance against the comparable baseline:* the paired delta against a classical reservoir at equal readout size is exactly the comparison the brief asks for ("similar preprocessing, features, or architecture"). If the gain is not detectable, we report it as such, together with where the quantum features help (per class, per patient) and where they do not.
  - *Ingenuity:* a quantum reservoir is a physical, training-free feature map suited to low-power wearable sensing, and it is untested on the inter-patient ECG benchmark. The classical-spin control isolates what quantum dynamics add beyond the same classical physics.
  - *Depth:* ablations (entanglement off, readout size, qubit count, mean-field limit); per-class and per-patient analysis.
  - *Soundness:* patient-held-out evaluation; the subject overlap in the standard split (A004) is disclosed and handled; patient-level uncertainty; equal tuning budgets (Bowles et al. pitfalls); leaky beat-level splits in prior quantum ECG work called out with citations.
- **Information available at decision time:**
  - The ECG up to the current beat, plus a short lookahead to the next R-peak (about 1 s) for the post-RR interval, a declared latency.
  - The same patient's past RR history (causal running averages).
  - No labels from the test patient.
  - Not available: whole-record RR statistics (we use causal windows instead) and any test-patient labels. A patient-adaptive variant that uses the first 5 minutes of labelled beats (allowed under AAMI EC57) would be a separately declared track, not the primary result.

## Data (summary; the data card is in EVAL.md)
- **Sources and access status:**
  - C1: MIT-BIH, all 48 records in `runs/data/samples/mitdb/`, checksums verified against PhysioNet's SHA256SUMS.txt; open access, ODC-By 1.0. Citation: Moody & Mark 2001, IEEE EMB 20(3):45-50, and Goldberger et al. 2000 (PhysioNet).
  - C2: TCGA-BRCA (Xena) in `runs/data/samples/tcga_brca/`.
  - C4: SPECT in `runs/data/samples/spect/`.
  - Other samples (MedMNIST, BBBP, PTB-XL metadata, CinC 2012 outcomes, CHB-MIT summary) are in `runs/data/samples/`.
  - PhysioNet's main site served about 5 KB/s from here; the AWS open-data mirror (`physionet-open.s3.amazonaws.com`) served about 850 KB/s.
- **Requests filed for the human:** QPU access, optional (STATE.md, updated with the IBM Open Plan finding). No data requests.

## Observed structure
- **MIT-BIH:**
  - 48 records, 30.1 min each, 360 Hz, 2 leads, 47 subjects.
  - AAMI totals: N 90,631, S 2,781, V 7,236, F 803, Q 8,043; Q is mostly the paced records.
  - DS1: N 45,866, S 944, V 3,788, F 415, Q 8. DS2: N 44,259, S 1,837, V 3,221, F 388, Q 7. These differ slightly from de Chazal 2004 Table II (DS1 N 45,868, S 942, V 3,787; DS2 N 44,258; the rest equal). Corrected 2026-10-26 after the EV1 r3 review (R3); the earlier claim of an exact match was wrong. Cause unverified (annotation revisions are possible).
  - S beats are rare (about 2-4%) and concentrated by patient (A001). Lead order varies (A005). One subject is on both sides of the standard split (A004).
- **TCGA-BRCA:** 1,218 expression samples (1,101 primary tumours, 139 normal tissue, 7 metastatic in the clinical matrix); 20,530 genes. PAM50: LumA 434, LumB 194, Basal 142, Normal 119, Her2 67. ER Positive 912 / Negative 266. 203 deceased.
- **SPECT:** 267 rows, 22 binary features, 212 abnormal and 55 normal; train 40/40, test 172/15; 39 duplicates (A002).
- **PneumoniaMNIST:** train 4,708 (1,214 normal / 3,494 pneumonia), val 524, test 624 (234 / 390).
- **PTB-XL** (possible external ECG set): 21,799 records, 18,869 patients, 10 patient-respecting stratified folds, recorded 1984-2001.

## Notes for later phases (not Phase 1 decisions)
- **Phase 2 (C1):**
  - Uncertainty must be patient-level (cluster bootstrap over records); beat-level intervals would be far too narrow (A001).
  - Decide how to treat A004: report DS2 as published and also with 202 excluded, or use grouped CV.
  - Fix the equal-tuning-budget rule before any quantum run, after Bowles et al.'s pitfalls (unequal tuning, positivity bias from publishing the best of many quantum variants).
  - Pre-register the number of quantum variants tried.
- **Phase 4 ideas (C1):**
  - Geometric difference g_CQ (Huang et al. 2021, `doi:10.1038/s41467-021-22539-9`) between reservoir Gram matrices as a cheap pre-check before full runs.
  - A patient-adaptive small-data track, where any quantum regularity benefit is most plausible (Beaulieu et al., `doi:10.1021/acs.jcim.5c00958`: quantum reservoir parity at 100-200 records, gone by 800).
  - Classical features + quantum reservoir features as an "improve the classical model" variant.
- **External test data (SVDB approved by the human 2026-10-26; raw files in `runs/data/raw/svdb/`):**
  - MIT-BIH Supraventricular Arrhythmia DB (SVDB), https://physionet.org/content/svdb/1.0.0/, ODC-By 1.0, open access.
  - 78 half-hour two-lead recordings "chosen to supplement the examples of supraventricular arrhythmias in the MIT-BIH Arrhythmia Database". Headers checked: 128 Hz, leads named only ECG1 and ECG2, 230,400 samples per record. The subject count is not stated on the page.
  - It would give S-class results that do not rest on one test patient (A001). Needs resampling from 128 to 360 Hz and lead matching.
  - St Petersburg INCART DB (75 records, 12 leads, 257 Hz) is a further option.
  - Both are reachable on the PhysioNet S3 mirror.
- **QPU (prices checked 2026-10-26):**
  - IBM Quantum Open Plan: free, up to 10 QPU minutes per 28-day rolling window, us-east instances only (https://quantum.cloud.ibm.com/docs/guides/plans-overview).
  - Amazon Braket (https://aws.amazon.com/braket/pricing/): every QPU charges USD 0.30 per task plus a per-shot fee:

    | QPU | Per shot | USD 15 buys about |
    |---|---|---|
    | Rigetti Cepheus | USD 0.000425 | 20 circuits at 1,000 shots |
    | IQM Garnet | USD 0.00145 | 8 circuits |
    | QuEra Aquila (analog Rydberg) | USD 0.01 | 11 programs at 100 shots |
    | IonQ Forte | USD 0.08 | under 1 circuit at 1,000 shots |

  - No free QPU tier on Braket. The pricing page does not mention program sets.
  - Agent's estimate, to be measured on a first small job: the IBM free 10 minutes covers several hundred to about 1,000 circuits at 1,000 shots, far more than USD 15 buys on Braket.
  - Update 2026-10-26 ~15:50: the human cannot reach IBM's Open Plan today and may retry tomorrow. Alternatives checked:
    - IQM Resonance Starter is free, "up to 30 credits per month, based on availability", with Qiskit support and IQM Crystal 54, Crystal 20 and Star 24 listed. The page does not say what one credit buys. Pay-as-you-go is listed as "starting at $0.30/sec" of QPU time (https://iqm.tech/products/iqm-resonance/).
    - AWS promotional credits apply "only to the specific Services designated by your AWS contracting entity"; Braket is neither listed as eligible nor excluded (https://aws.amazon.com/awscredits/).
    - The new AWS Free Tier's free plan is "limited to select services only", and Braket is not mentioned (https://aws.amazon.com/free/).
    - Braket cost estimates exclude credits.
    - Pasqal's free Orion hours are for the EU only. qBraid QUEST is applied for through a professor, and its window has likely closed.
  - Hardware circuits must be shallow. A deep reservoir (one Trotter step per input sample) will be dominated by noise, so plan a short-sequence variant for hardware and report the degradation as a result.

## Ambiguities and open questions
| Question | Interpretations | What changes | Blocking / provisional (assumption) | Owner |
|---|---|---|---|---|
| Which problem do we pursue? | C1 (recommended), C2 (runner-up), C4, or another | Everything from Phase 2 on | resolved 2026-10-26: C1, runner-up C2 | human |
| Add an external test database (SVDB, optionally INCART)? | yes / no | S-class evidence beyond one patient (A001); preprocessing work (resampling, lead matching) | resolved 2026-10-26: SVDB approved ("Regarding the dataset, go ahead"); INCART not requested | human |
| How to use the USD 15 and which QPU account | IBM Open Plan (free) for the hardware run with USD 15 as a Braket fallback / USD 15 for a QuEra Aquila analog showcase / unspent | Whether and where a hardware run happens | provisional: recommend the IBM free tier plus the USD 15 held as fallback | human |
| Who organises and judges, and is there a public page, FAQ or forum? | unknown; no public page found | How to pitch (clinical vs quantum audience), rubric weights | provisional: assume a mixed quantum + ML panel, rubric weights equal except performance likely heavier | human |
| Team size and roles | solo plus agent, or a team | Time plan, presentation | provisional: one human plus the agent | human |
| What "comparably similar" baseline means | (a) same architecture with the quantum block swapped for a classical one; (b) strongest classical model on the same features | Which baseline the headline delta uses | provisional: headline = (a), a matched classical reservoir; (b) a strong classical reference is reported as context, so judges see both | agent (Phase 2), human to confirm with EV1 |
| Must results come from real hardware? | simulator OK / QPU expected | QPU spend, credibility | provisional: simulators OK, small QPU demo optional | human (check the Submissions panel) |
| Submission format and limits (repo link vs upload, write-up length, video?) | unknown until the form is published | Packaging in Phase 6 | provisional | human (check the Submissions panel) |
| Beat locations: reference annotations or an automatic QRS detector? | reference (standard in the benchmark) / detector (closer to deployment) | Realism vs comparability | provisional: reference positions, stated as a limitation | agent (Phase 2) |
| Is the 1-beat lookahead for the post-RR interval acceptable? | yes, as a ~1 s latency / no, causal only | Feature set, especially for S beats | provisional: allowed and declared; the causal-only variant is a sensitivity check | agent (Phase 2) |
| Class set for the primary metric | N/S/V / N/S/V/F | Metric noise (F is tiny and concentrated) | provisional: N/S/V primary, F reported | agent (Phase 2), human approves EV1 |
| Presentation on 2026-10-31: format and length | unknown | Phase 6 deliverables | provisional | human |
