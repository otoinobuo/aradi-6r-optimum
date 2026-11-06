#!/usr/bin/env python3
"""メモリ監視付きスケジューラ: 残り cube を元解時間の降順に最大 MAXP 並列で drat_full_one.sh に流す。
MemAvailable < LAUNCH_MIN なら起動を止め、< PAUSE_MIN なら実行中の drat-trim を SIGSTOP、> RESUME_MIN で SIGCONT。
summary.tsv に FAIL が出たら新規起動を止めて終了。"""
import os, sys, time, subprocess, signal, json
A = "/home/otoi/explore/aradi"; D = f"{A}/review/drat_full"
MAXP = int(sys.argv[1]) if len(sys.argv) > 1 else 18
LAUNCH_MIN, PAUSE_MIN, RESUME_MIN = 2000, 1200, 3000  # MB
def mem_avail_mb():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024
def verified():
    s = set()
    if os.path.exists(f"{D}/summary.tsv"):
        for l in open(f"{D}/summary.tsv"):
            p = l.rstrip("\n").split("\t")
            if len(p) >= 3 and p[2] == "VERIFIED": s.add(p[0])
    return s
def failed():
    if not os.path.exists(f"{D}/summary.tsv"): return []
    return [l.split("\t")[0] for l in open(f"{D}/summary.tsv") if "\tFAIL\t" in l]
def drat_trim_pids():
    out = subprocess.run(["pgrep", "-f", f"^{os.path.expanduser('~')}.*drat-trim {D}/tmp"], capture_output=True, text=True).stdout.split()
    out += subprocess.run(["pgrep", "-f", f"drat-trim {D}/tmp"], capture_output=True, text=True).stdout.split()
    return sorted(set(int(p) for p in out))
order = [l.split("\t")[0] for l in sorted(open(f"{A}/results_6R_k81.tsv"), key=lambda l: -float(l.split("\t")[2]))]
done = verified()
inflight_at_start = {f[:-4] for f in os.listdir(f"{D}/tmp") if f.endswith(".cnf")}
queue = [n for n in order if n not in done and n not in inflight_at_start]
log = open(f"{D}/sched.log", "a")
def L(msg):
    log.write(f"{time.strftime('%FT%T')} {msg}\n"); log.flush()
L(f"start MAXP={MAXP} queue={len(queue)} verified={len(done)} inflight_at_start={sorted(inflight_at_start)}")
procs = {}; stopped = []
while queue or procs:
    for nm, p in list(procs.items()):
        if p.poll() is not None: del procs[nm]
    f = failed()
    if f:
        L(f"FAIL detected {f}; stop launching, waiting for {len(procs)} running"); queue = []
    m = mem_avail_mb()
    if m < PAUSE_MIN:
        running = [p for p in drat_trim_pids() if p not in stopped]
        if running:
            pid = running[-1]; os.kill(pid, signal.SIGSTOP); stopped.append(pid); L(f"mem {m}MB < {PAUSE_MIN}: SIGSTOP drat-trim {pid}")
    elif m > RESUME_MIN and stopped:
        pid = stopped.pop(0)
        try: os.kill(pid, signal.SIGCONT); L(f"mem {m}MB > {RESUME_MIN}: SIGCONT drat-trim {pid}")
        except ProcessLookupError: pass
    while queue and len(procs) < MAXP and mem_avail_mb() >= LAUNCH_MIN and not stopped:
        nm = queue.pop(0)
        procs[nm] = subprocess.Popen([f"{A}/review/drat_full_one.sh", nm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
v = len(verified()); f = failed()
L(f"end verified={v} fail={len(f)} {f}")
with open(f"{D}/run.log", "a") as r: r.write(f"end {time.strftime('%FT%T')}  VERIFIED={v} FAIL={len(f)} lines={sum(1 for _ in open(f'{D}/summary.tsv'))}\n")
