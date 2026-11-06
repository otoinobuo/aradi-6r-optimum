#!/usr/bin/env python3
"""hybrid_bits.py の meta から cube を作る（make_cubes.py と同じ分割、start を考慮）。"""
import json, os, argparse
ap = argparse.ArgumentParser(); ap.add_argument("--meta", required=True); ap.add_argument("--outdir", required=True); ap.add_argument("--split2", action="store_true")
a = ap.parse_args(); m = json.load(open(a.meta))
R, k, B, s = m["rounds"], m["k"], m["bounds"], m.get("start", 0)
reg = {int(i): {int(t): v for t, v in d.items()} for i, d in m["prefix_reg"].items()}
def eq(n, t):
    cl = []
    if t >= 1: cl.append([reg[n][t]])
    if t + 1 in reg[n]: cl.append([-reg[n][t + 1]])
    return cl
os.makedirs(a.outdir, exist_ok=True); cubes = []
j_lo, j_hi = B[str(s % 4)][1], k - B[str((s + 1) % 4)][R - 1]
for j in range(j_lo, j_hi + 1):
    base = eq(128, j); name = f"w0_{j:02d}"; subs = [(name, base)]
    if a.split2 and R >= 3:
        subs = [(f"{name}_w01_{t:02d}", base + eq(256, t)) for t in range(j + B[str((s + 1) % 4)][1], k - B[str((s + 2) % 4)][R - 2] + 1)]
    cubes += subs
for nm, cl in cubes:
    open(os.path.join(a.outdir, nm + ".units"), "w").write("".join(" ".join(map(str, c)) + " 0\n" for c in cl))
print(json.dumps({"cubes": len(cubes), "w0_range": [j_lo, j_hi], "outdir": a.outdir}))
