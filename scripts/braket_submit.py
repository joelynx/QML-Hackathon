"""E019 Braket lane, SDK side (run with .venv-braket, which has amazon-braket-sdk; the main venv builds the plan).

  localsim                      free: validate the native programs on Braket's LocalSimulator against our statevector
  submit --plan P [--dry-run]   guarded submission of an approved plan (prints plan and cost with --dry-run)
  fetch --plan P                re-fetch results of tasks already submitted (never resubmits)

Guards (all enforced in code before any paid call):
  * device allowlist: Rigetti Cepheus-1-108Q and IQM Garnet ARNs only (IonQ, AQT, QuEra, others refused);
  * shots <= 1,024 per executable; at most HARD_MAX_TASKS quantum tasks;
  * runs/E019/approval.json must exist (written by the coordinator after the human approves): device_arn, max_tasks,
    max_usd; the plan's device must match and the number of tasks must not exceed max_tasks;
  * cost ledger runs/E019/cost_ledger.jsonl: the estimated cost is appended BEFORE each submission; refusal if the
    cumulative estimate (all ledger entries) would exceed approval max_usd or, in any case, USD 35;
  * a task already submitted (results/<sub>.task.json) is never resubmitted.
"""
import argparse
import datetime
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "runs", "E019")
RES = os.path.join(OUT, "results")
LEDGER = os.path.join(OUT, "cost_ledger.jsonl")
APPROVAL = os.path.join(OUT, "approval.json")
PROFILE = "qhack"
# pricing verified on https://aws.amazon.com/braket/pricing/ at 2026-10-28T14:45Z
ALLOWED = {
    "arn:aws:braket:us-west-1::device/qpu/rigetti/Cepheus-1-108Q": dict(region="us-west-1", task_usd=0.30,
                                                                        shot_usd=0.000425),
    "arn:aws:braket:eu-north-1::device/qpu/iqm/Garnet": dict(region="eu-north-1", task_usd=0.30, shot_usd=0.00145),
}
MAX_SHOTS = 1024
HARD_USD_CAP = 35.0
HARD_MAX_TASKS = 100
PS_MAX_EXEC, PS_MAX_SHOTS = 100, 200_000  # program-set limits reported by GetDevice (2026-10-28)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def n_qubits_feats(bits_by_pos, pos):
    """bits_by_pos: (m, n) 0/1 array with weights handled by caller; returns Z (10) and ZZ pairs (45)."""
    v = 1.0 - 2.0 * bits_by_pos[:, pos]
    z = v
    zz = np.stack([v[:, a] * v[:, b] for a in range(10) for b in range(a + 1, 10)], 1)
    return np.concatenate([z, zz], 1)


def feats_from_probs(p, n, pos):
    idx = np.arange(2 ** n)
    bits = ((idx[:, None] >> (n - 1 - np.arange(n))[None, :]) & 1).astype(float)  # Braket: first qubit = MSB
    return np.asarray(p) @ n_qubits_feats(bits, pos)


def feats_from_counts(counts, measured, phys):
    pos = [list(measured).index(p) for p in phys]
    keys = list(counts)
    bits = np.array([[int(c) for c in s] for s in keys], dtype=float)
    w = np.array([counts[s] for s in keys], dtype=float)
    return (w / w.sum()) @ n_qubits_feats(bits, pos)


# --------------------------------------------------------------------------------------------------- local check
def strip_measure(src, n):
    lines = [ln for ln in src.splitlines() if not ln.startswith("bit[") and " = measure " not in ln]
    lines.append("#pragma braket result probability " + ", ".join(f"${i}" for i in range(n)))
    return "\n".join(lines) + "\n"


def localsim(a):
    from braket.devices import LocalSimulator
    from braket.ir.openqasm import Program
    from braket.program_sets import ProgramSet
    v = json.load(open(os.path.join(OUT, "validation", "validation_input.json")))
    dev = LocalSimulator("braket_sv")
    rep = dict(time_utc=now(), items=[])
    worst_exact, worst_shot = 0.0, 0.0
    for it in v["items"]:
        r = dev.run(Program(source=strip_measure(it["qasm"], it["n"])), shots=0).result()
        p = np.asarray(r.values[0])
        errs = []
        for s, ref in zip(it["slots"], it["ref"]):
            f = feats_from_probs(p, it["n"], s["pos"])
            errs.append(float(np.abs(f - np.asarray(ref)).max()))
        worst_exact = max(worst_exact, max(errs))
        row = dict(name=it["name"], n_cz=it.get("n_cz"), n_1q=it.get("n_1q"), max_abs_err_exact=max(errs))
        if it["name"].endswith("k4") or "packed" in it["name"]:  # sampled run: checks counts and bit order
            rs = dev.run(Program(source=it["qasm"]), shots=MAX_SHOTS).result()
            mq = [int(q) for q in rs.measured_qubits]
            e = [float(np.abs(feats_from_counts(rs.measurement_counts, mq, s["pos"]) - np.asarray(ref)).max())
                 for s, ref in zip(it["slots"], it["ref"])]
            row["max_abs_err_1024shots"] = max(e)
            # bit-order control: the same counts read with the ring reversed must be clearly worse
            m = [float(np.abs(feats_from_counts(rs.measurement_counts, mq, s["pos"]) - np.asarray(ref)).mean())
                 for s, ref in zip(it["slots"], it["ref"])]
            mr = [float(np.abs(feats_from_counts(rs.measurement_counts, mq, s["pos"][::-1]) - np.asarray(ref)).mean())
                  for s, ref in zip(it["slots"], it["ref"])]
            row["mean_abs_err_1024shots"], row["mean_abs_err_reversed_control"] = max(m), min(mr)
            worst_shot = max(worst_shot, max(e))
        rep["items"].append(row)
        print(row, flush=True)
    # program set: two executables in one task, results per executable
    two = [it for it in v["items"] if it["name"] in ("rigetti_single_0_k1", "rigetti_single_1_k2")]
    ps = ProgramSet([it["qasm"] for it in two], shots_per_executable=MAX_SHOTS)
    rr = dev.run(ps, shots=MAX_SHOTS * len(two)).result()
    pe = []
    for it, ent in zip(two, rr.entries):
        e0 = ent.entries[0] if hasattr(ent, "entries") else ent
        counts, mq = dict(e0.counts), [int(q) for q in e0.measured_qubits]
        pe.append(float(np.abs(feats_from_counts(counts, mq, it["slots"][0]["pos"]) - np.asarray(it["ref"][0])).max()))
    rep.update(worst_exact=worst_exact, worst_1024shots=worst_shot, programset_max_abs_err_1024shots=pe,
               programset_result_type=type(rr).__name__)
    json.dump(rep, open(os.path.join(OUT, "validation", "localsim_report.json"), "w"), indent=1)
    print("worst exact", worst_exact, "worst 1024-shot", worst_shot, "program set", pe)


# ----------------------------------------------------------------------------------------------------- submission
def ledger_total():
    if not os.path.exists(LEDGER):
        return 0.0
    tot = 0.0
    for ln in open(LEDGER):
        e = json.loads(ln)
        if e.get("event") == "pre-submit":
            tot += float(e["est_usd"])
        elif e.get("event") == "create-failed" and e.get("task_created") is False:
            # CreateQuantumTask was refused, no task exists (checked with search_quantum_tasks): release its estimate
            tot -= float(e["released_usd"])
    return tot


def ledger_append(**e):
    with open(LEDGER, "a") as f:
        f.write(json.dumps(dict(time_utc=now(), **e)) + "\n")


def submissions(plan, mode):
    """Group the plan's circuits into quantum tasks: one per circuit, or program sets of <= 100 executables."""
    circ = plan["circuits"]
    if mode == "tasks":
        return [[c] for c in circ]
    per = min(PS_MAX_EXEC, PS_MAX_SHOTS // plan["shots"])
    n = -(-len(circ) // per)
    size = -(-len(circ) // n)  # balanced chunks
    return [circ[i:i + size] for i in range(0, len(circ), size)]


def est_cost(price, n_exec, shots):
    return price["task_usd"] + n_exec * shots * price["shot_usd"]


def check_plan(plan, mode, dry):
    arn = plan["arn"]
    if arn not in ALLOWED:
        sys.exit(f"REFUSED: device {arn} is not on the allowlist")
    price = ALLOWED[arn]
    if plan["region"] != price["region"]:
        sys.exit("REFUSED: region mismatch")
    if plan["shots"] > MAX_SHOTS or plan["shots"] < 1:
        sys.exit(f"REFUSED: shots {plan['shots']} above the cap {MAX_SHOTS}")
    subs = submissions(plan, mode)
    costs = [est_cost(price, len(s), plan["shots"]) for s in subs]
    total = sum(costs)
    print(f"device {arn} mode {mode} beats {plan['n_beats']} P {plan['P']} circuits {len(plan['circuits'])} "
          f"tasks {len(subs)} shots/executable {plan['shots']} est USD {total:.2f} "
          f"(ledger so far USD {ledger_total():.2f})")
    for i, (s, c) in enumerate(zip(subs, costs)):
        print(f"  task {i}: {len(s)} executables {s[0]['circuit_id']}..{s[-1]['circuit_id']} est USD {c:.4f}")
    if dry:
        return subs, costs, None
    if not os.path.exists(APPROVAL):
        sys.exit("REFUSED: runs/E019/approval.json missing (the human must approve first)")
    ap = json.load(open(APPROVAL))
    if ap.get("device_arn") != arn:
        sys.exit(f"REFUSED: approval is for {ap.get('device_arn')}, plan is for {arn}")
    cap = min(float(ap["max_usd"]), HARD_USD_CAP)
    if len(subs) > min(int(ap["max_tasks"]), HARD_MAX_TASKS):
        sys.exit(f"REFUSED: {len(subs)} tasks > approved max_tasks {ap['max_tasks']}")
    if ap.get("mode", mode) != mode:
        sys.exit(f"REFUSED: approval is for mode {ap.get('mode')}")
    return subs, costs, cap


def task_file(sub):
    return os.path.join(RES, f"{sub[0]['circuit_id']}__{len(sub)}.task.json")


def save_results(plan, sub, task_arn, res, mode):
    entries = res.entries if mode == "programset" else [res]
    for c, ent in zip(sub, entries):
        e0 = ent.entries[0] if (mode == "programset" and hasattr(ent, "entries")) else ent
        counts = dict(e0.counts) if mode == "programset" else dict(e0.measurement_counts)
        rec = dict(device=plan["arn"], task_arn=task_arn, circuit_id=c["circuit_id"], snapshot=c["snapshot"],
                   slots=c["slots"], qasm_sha16=c["sha16"], shots=plan["shots"],
                   measured_qubits=[int(q) for q in e0.measured_qubits], counts=counts, saved_utc=now())
        json.dump(rec, open(os.path.join(RES, f"{c['circuit_id']}.json"), "w"))


def device_and_session(arn):
    import boto3
    from braket.aws import AwsDevice, AwsSession
    sess = AwsSession(boto_session=boto3.Session(profile_name=PROFILE, region_name=ALLOWED[arn]["region"]))
    return AwsDevice(arn, aws_session=sess), sess


def submit(a):
    plan = json.load(open(a.plan))
    subs, costs, cap = check_plan(plan, a.mode, a.dry_run)
    if a.dry_run:
        print("DRY RUN: nothing submitted")
        return
    from braket.aws import AwsQuantumTask
    from braket.ir.openqasm import Program
    from braket.program_sets import ProgramSet
    os.makedirs(RES, exist_ok=True)
    device, sess = device_and_session(plan["arn"])
    print("device status", device.status)
    if device.status != "ONLINE":
        sys.exit(f"REFUSED: device status {device.status}")
    tasks = []
    for sub, c in zip(subs, costs):
        tf = task_file(sub)
        if os.path.exists(tf):  # never resubmit
            tasks.append((sub, AwsQuantumTask(json.load(open(tf))["task_arn"], aws_session=sess)))
            continue
        cum = ledger_total()
        if cum + c > cap + 1e-9:
            sys.exit(f"REFUSED: cumulative estimate {cum:.2f} + {c:.2f} > approved cap {cap:.2f}")
        ledger_append(event="pre-submit", device=plan["arn"], plan=os.path.basename(a.plan), mode=a.mode,
                      first=sub[0]["circuit_id"], n_exec=len(sub), shots_per_exec=plan["shots"], est_usd=round(c, 4),
                      cum_after_usd=round(cum + c, 4))
        if a.mode == "programset":
            prog = ProgramSet([s["qasm"] for s in sub], shots_per_executable=plan["shots"])
            t = device.run(prog, shots=plan["shots"] * len(sub))
        else:
            t = device.run(Program(source=sub[0]["qasm"]), shots=plan["shots"])
        json.dump(dict(task_arn=t.id, circuits=[s["circuit_id"] for s in sub], mode=a.mode, submitted_utc=now(),
                       est_usd=c), open(tf, "w"), indent=1)
        ledger_append(event="submitted", task_arn=t.id, first=sub[0]["circuit_id"], est_usd=round(c, 4))
        print("submitted", t.id, flush=True)
        tasks.append((sub, t))
    collect(plan, tasks, a.mode, a.deadline_utc)


def collect(plan, tasks, mode, deadline_utc):
    deadline = datetime.datetime.fromisoformat(deadline_utc) if deadline_utc else None
    pending = list(tasks)
    while pending:
        nxt = []
        for sub, t in pending:
            st = t.state()
            if st == "COMPLETED":
                save_results(plan, sub, t.id, t.result(), mode)
                print("completed", t.id, flush=True)
            elif st in ("FAILED", "CANCELLED"):
                print("ended", st, t.id, t.metadata().get("failureReason"), flush=True)
            else:
                nxt.append((sub, t))
        pending = nxt
        if pending:
            if deadline and datetime.datetime.now(datetime.timezone.utc) > deadline:
                print("deadline reached; still pending:", [t.id for _, t in pending])
                return
            time.sleep(20)


def fetch(a):
    from braket.aws import AwsQuantumTask
    plan = json.load(open(a.plan))
    _, sess = device_and_session(plan["arn"])
    tasks = []
    for sub in submissions(plan, a.mode):
        tf = task_file(sub)
        if os.path.exists(tf):
            tasks.append((sub, AwsQuantumTask(json.load(open(tf))["task_arn"], aws_session=sess)))
    collect(plan, tasks, a.mode, a.deadline_utc)


def simplan(a):
    """Free end-to-end test of the analysis: each ring of each planned circuit, cut out of the packed program, run on
    the local simulator with the same shots; records written in the hardware result format to --out."""
    import re
    from braket.devices import LocalSimulator
    from braket.ir.openqasm import Program
    plan = json.load(open(a.plan))
    os.makedirs(a.out, exist_ok=True)
    dev = LocalSimulator("braket_sv")
    for c in plan["circuits"]:
        body = c["qasm"].split("box{")[1].split("}")[0].strip().splitlines()
        for j, sl in enumerate(c["slots"]):
            ph = sl["phys"]
            m = {p: i for i, p in enumerate(ph)}
            keep = [ln for ln in body if set(int(x) for x in re.findall(r"\$(\d+)", ln)) <= set(ph)]
            src = ["OPENQASM 3.0;", "bit[10] b;", "#pragma braket verbatim", "box{"] + keep + ["}"]
            src += [f"b[{i}] = measure ${p};" for i, p in enumerate(ph)]
            src = re.sub(r"\$(\d+)", lambda x: f"${m[int(x.group(1))]}", "\n".join(src) + "\n")
            r = dev.run(Program(source=src), shots=plan["shots"]).result()
            mq = [ph[int(q)] for q in r.measured_qubits]
            rec = dict(device="local:braket_sv", task_arn=None, circuit_id=c["circuit_id"], snapshot=c["snapshot"],
                       slots=[sl], shots=plan["shots"], measured_qubits=mq, counts=dict(r.measurement_counts))
            json.dump(rec, open(os.path.join(a.out, f"{c['circuit_id']}_s{j}.json"), "w"))
    print("wrote", a.out)


def cancel(a):
    """Cancel every submitted task of the plan that has not completed (queued tasks are not run, hence not billed)."""
    from braket.aws import AwsQuantumTask
    plan = json.load(open(a.plan))
    _, sess = device_and_session(plan["arn"])
    for sub in submissions(plan, a.mode):
        tf = task_file(sub)
        if os.path.exists(tf):
            t = AwsQuantumTask(json.load(open(tf))["task_arn"], aws_session=sess)
            st = t.state()
            if st not in ("COMPLETED", "FAILED", "CANCELLED"):
                t.cancel()
                ledger_append(event="cancel-requested", task_arn=t.id, state_before=st)
            print(t.id, st)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["localsim", "submit", "fetch", "simplan", "cancel"])
    ap.add_argument("--plan")
    ap.add_argument("--out")
    ap.add_argument("--mode", choices=["programset", "tasks"], default="programset")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--deadline-utc", default="2026-10-28T17:30:00+00:00", help="stop waiting (21:30 UAE)")
    a = ap.parse_args()
    {"localsim": localsim, "submit": submit, "fetch": fetch, "simplan": simplan, "cancel": cancel}[a.cmd](a)


if __name__ == "__main__":
    main()
