#!/usr/bin/env python3
"""UNSAT+DRAT cube スケジューラ（メモリ監視付き）: cube_drat_sched.py <base.cnf> <cubedir> <outdir> <maxp>
名前順に流す。summary.tsv に SAT か FAIL が出たら新規起動を止める（SAT = k が SAT と判明）。"""
import os, sys, time, subprocess, signal
base, cubedir, outdir, MAXP = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
ONE = "/home/otoi/explore/aradi/review/cube_drat_one_6R.sh"
LAUNCH_MIN, PAUSE_MIN, RESUME_MIN = 2000, 1200, 3000
os.makedirs(outdir, exist_ok=True)
def mem():
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024
def rows():
    p = f"{outdir}/summary.tsv"
    return [l.rstrip("\n").split("\t") for l in open(p)] if os.path.exists(p) else []
done = {r[0] for r in rows() if r[2] in ("VERIFIED", "SAT")}
inflight = {f[:-4] for f in os.listdir(f"{outdir}/tmp") if f.endswith(".cnf")} if os.path.isdir(f"{outdir}/tmp") else set()
queue = [f[:-6] for f in sorted(os.listdir(cubedir)) if f.endswith(".units") and f[:-6] not in done and f[:-6] not in inflight]
log = open(f"{outdir}/sched.log", "a")
def L(m): log.write(f"{time.strftime('%FT%T')} {m}\n"); log.flush()
L(f"start base={base} cubes={len(queue)} maxp={MAXP} skipped_inflight={len(inflight)} DT_SLOTS={os.environ.get('DT_SLOTS')}")
procs = {}; stopped = []; stop_reason = None; t0 = time.time()
while queue or procs:
    for nm, p in list(procs.items()):
        if p.poll() is not None: del procs[nm]
    bad = [r for r in rows() if r[2] in ("SAT", "FAIL")]
    if bad and queue:
        stop_reason = bad[0][2] + ":" + bad[0][0]; L(f"{stop_reason} -> stop launching"); queue = []
    m = mem()
    if m < PAUSE_MIN:
        running = [p.pid for p in procs.values() if p.pid not in stopped]
        if running: os.killpg(running[-1], signal.SIGSTOP); stopped.append(running[-1]); L(f"mem {m}MB: SIGSTOP pg {running[-1]}")
    elif m > RESUME_MIN and stopped:
        pid = stopped.pop(0)
        try: os.killpg(pid, signal.SIGCONT); L(f"mem {m}MB: SIGCONT pg {pid}")
        except ProcessLookupError: pass
    while queue and len(procs) < MAXP and mem() >= LAUNCH_MIN and not stopped:
        nm = queue.pop(0); procs[nm] = subprocess.Popen([ONE, base, cubedir, outdir, nm], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    time.sleep(1)
rs = rows(); v = sum(1 for r in rs if r[2] == "VERIFIED"); s = sum(1 for r in rs if r[2] == "SAT"); f = sum(1 for r in rs if r[2] == "FAIL")
L(f"end VERIFIED={v} SAT={s} FAIL={f} rows={len(rs)} elapsed={time.time()-t0:.0f}s stop={stop_reason}")
open(f"{outdir}/DONE", "w").write(f"VERIFIED={v} SAT={s} FAIL={f} rows={len(rs)} elapsed={time.time()-t0:.0f} stop={stop_reason}\n")
