#!/usr/bin/env python3
"""SAT 方向の cube 探索スケジューラ（メモリ監視付き）。
使い方: sat_sched.py <base.cnf> <cubedir> <outdir> <maxp> <per-cube timeout s> <global budget s>
cube は名前順（w0 昇順→w01 昇順）。SAT が 1 本出たら残りを止めて終了（model は <outdir>/<cube>.model）。
記録: <outdir>/results.tsv（cube status sec）、<outdir>/sched.log。MemAvailable < 2000MB で起動抑制、< 1200MB で SIGSTOP。"""
import os, sys, time, subprocess, signal
base, cubedir, outdir, MAXP, TO, BUDGET = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), int(sys.argv[6])
KISSAT = os.path.expanduser("~/kissat/build/kissat")
os.makedirs(f"{outdir}/tmp", exist_ok=True)
LAUNCH_MIN, PAUSE_MIN, RESUME_MIN = 2000, 1200, 3000
def mem(): 
    for l in open("/proc/meminfo"):
        if l.startswith("MemAvailable:"): return int(l.split()[1]) // 1024
log = open(f"{outdir}/sched.log", "a")
def L(m): log.write(f"{time.strftime('%FT%T')} {m}\n"); log.flush()
done = set()
if os.path.exists(f"{outdir}/results.tsv"):
    done = {l.split("\t")[0] for l in open(f"{outdir}/results.tsv")}
hdr = open(base).readline().split(); nv, nc0 = hdr[2], int(hdr[3])
queue = [f[:-6] for f in sorted(os.listdir(cubedir)) if f.endswith(".units") and f[:-6] not in done]
L(f"start base={base} cubes={len(queue)} maxp={MAXP} timeout={TO} budget={BUDGET}")
t_start = time.time(); procs = {}; stopped = []; found = None
def launch(nm):
    cnf = f"{outdir}/tmp/{nm}.cnf"
    with open(cnf, "w") as f:
        units = open(f"{cubedir}/{nm}.units").read()
        f.write(f"p cnf {nv} {nc0 + units.count(chr(10))}\n")
        with open(base) as b: b.readline(); f.write(b.read())
        f.write(units)
    out = open(f"{outdir}/tmp/{nm}.out", "w")
    p = subprocess.Popen(["timeout", str(TO), "nice", "-n", "10", KISSAT, "-q", cnf], stdout=out, stderr=subprocess.DEVNULL)
    procs[nm] = (p, time.time(), out)
def finish(nm):
    p, t0, out = procs.pop(nm); out.close()
    txt = open(f"{outdir}/tmp/{nm}.out").read()
    st = [l.split()[1] for l in txt.splitlines() if l.startswith("s ")]
    st = st[0] if st else "UNKNOWN"
    with open(f"{outdir}/results.tsv", "a") as r: r.write(f"{nm}\t{st}\t{time.time()-t0:.1f}\n")
    if st == "SATISFIABLE":
        os.rename(f"{outdir}/tmp/{nm}.out", f"{outdir}/{nm}.model"); return nm
    os.remove(f"{outdir}/tmp/{nm}.out"); os.remove(f"{outdir}/tmp/{nm}.cnf"); return None
while queue or procs:
    for nm in list(procs):
        if procs[nm][0].poll() is not None:
            if finish(nm):
                found = nm; L(f"SAT found: {nm}"); queue = []
                for o in list(procs): procs[o][0].kill()
    over = time.time() - t_start > BUDGET
    if over and queue: L("budget exhausted: stop launching"); queue = []
    if over and procs:
        for o in list(procs): procs[o][0].kill()
    m = mem()
    if m < PAUSE_MIN:
        running = [nm for nm in procs if procs[nm][0].pid not in stopped]
        if running:
            pid = procs[running[-1]][0].pid; os.kill(pid, signal.SIGSTOP); stopped.append(pid); L(f"mem {m}MB: SIGSTOP {pid}")
    elif m > RESUME_MIN and stopped:
        pid = stopped.pop(0)
        try: os.kill(pid, signal.SIGCONT); L(f"mem {m}MB: SIGCONT {pid}")
        except ProcessLookupError: pass
    while queue and len(procs) < MAXP and mem() >= LAUNCH_MIN and not stopped:
        launch(queue.pop(0))
    time.sleep(1)
n = sum(1 for _ in open(f"{outdir}/results.tsv")) if os.path.exists(f"{outdir}/results.tsv") else 0
L(f"end found={found} results={n} elapsed={time.time()-t_start:.0f}s")
with open(f"{outdir}/DONE", "w") as f: f.write(f"found={found} results={n} elapsed={time.time()-t_start:.0f}\n")
