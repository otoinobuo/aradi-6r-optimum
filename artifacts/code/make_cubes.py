#!/usr/bin/env python3
"""混成 CNF（hybrid_cnf.py の出力）を cube に分ける。cube は単位節だけの小ファイル（base.cnf に連結して解く）。
分割 1: 第 1 段（round 0）の重み w0 = j（j = B_0[1] .. k − B_1[R−1]）。
分割 2（--split2）: さらに round 0..1 の重み = a（a = j + B_1[1] .. k − B_2[R−2]）で細分。
分割 mode=pos: 第 1 段で活性な最小の S-box 列 c（列 < c は入力差分 0、列 c は非 0）。重み分割と直交して併用可。
全 cube が UNSAT なら元の CNF（重み ≤ k）も UNSAT（cube が取りうる値を尽くすため）。
"""
import json, os, argparse, itertools
ap = argparse.ArgumentParser()
ap.add_argument("--meta", required=True)
ap.add_argument("--outdir", required=True)
ap.add_argument("--split2", action="store_true", help="round 0..1 の重みでも細分する")
ap.add_argument("--pos", action="store_true", help="第 1 段の最小活性 S-box 列でも分ける（×32）")
a = ap.parse_args()
m = json.load(open(a.meta))
R, k, B = m["rounds"], m["k"], m["bounds"]
reg = {int(i): {int(t): v for t, v in d.items()} for i, d in m["prefix_reg"].items()}
def eq(nvars_prefix, t):  # 先頭 nvars_prefix 個の hw 変数の和 = t（レジスタは双方向なので厳密）
    cl = []
    if t >= 1: cl.append([reg[nvars_prefix][t]])
    if t + 1 in reg[nvars_prefix]: cl.append([-reg[nvars_prefix][t + 1]])
    return cl
os.makedirs(a.outdir, exist_ok=True)
cubes = []
j_lo, j_hi = B["0"][1], k - B["1"][R - 1]
for j in range(j_lo, j_hi + 1):
    base = eq(128, j); name = f"w0_{j:02d}"
    subs = [(name, base)]
    if a.split2:
        subs = [(f"{name}_w01_{t:02d}", base + eq(256, t)) for t in range(j + B["1"][1], k - B["2"][R - 2] + 1)]
    if a.pos:
        subs2 = []
        for nm, cl in subs:
            for c in range(32):
                pc = [[-v] for cc in range(c) for v in m["sbox_in_round0"][str(cc)]] + [m["sbox_in_round0"][str(c)]]
                subs2.append((f"{nm}_c{c:02d}", cl + pc))
        subs = subs2
    cubes += subs
for nm, cl in cubes:
    with open(os.path.join(a.outdir, nm + ".units"), "w") as f:
        f.write("".join(" ".join(map(str, c)) + " 0\n" for c in cl))
print(json.dumps({"cubes": len(cubes), "w0_range": [j_lo, j_hi], "outdir": a.outdir}))
