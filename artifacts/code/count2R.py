#!/usr/bin/env python3
"""2R・重み≤8 のトレイル集合（平文差分, 1段目出力, 2段目出力）を、我々のモデル(aradi_diff.py)と CLAASP モデルで全列挙し、集合として一致するかを見る。"""
import sys, os, json, time
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from pysat.solvers import Solver
CAP = 200000
def enum(clauses, proj, name):
    # proj: list of lists of var ids (each a 128-bit state in CLAASP bit order MSB-first)
    sols = set(); t0 = time.time()
    with Solver(name="cadical195", bootstrap_with=clauses) as s:
        while s.solve():
            m = set(l for l in s.get_model() if l > 0)
            key = tuple(tuple(int(v in m) for v in st) for st in proj)
            sols.add(key)
            s.add_clause([(-v if v in m else v) for st in proj for v in st])
            if len(sols) >= CAP: break
    print(json.dumps({"model": name, "count": len(sols), "sec": round(time.time() - t0, 1)}), flush=True)
    return sols
# CLAASP
from claasp_run import build
cipher, model, variables, dimacs = build(2, 8, None)
vid = {v: i + 1 for i, v in enumerate(variables)}
clauses = [[int(t) for t in l.split()[:-1]] for l in dimacs.split("\n")[1:] if l.strip()]
ro = [c.id for c in cipher.get_all_components() if c.type == "intermediate_output" and c.description[0] == "round_output"]
proj = [[vid[f"plaintext_{i}"] for i in range(128)]] + [[vid[f"{r}_{i}"] for i in range(128)] for r in ro]
A = enum(clauses, proj, "CLAASP SatXorDifferentialModel 2R k<=8")
# ours: bit i (MSB-first) of state r = word wd = i//32, bit j = 31 - i%32  -> x[r][32*wd + j]
import aradi_diff
m = aradi_diff.Model(2, 0); m.constrain(8, [0])
proj2 = [[m.x[r][32 * (i // 32) + (31 - i % 32)] for i in range(128)] for r in range(3)]
B = enum(m.cnf.clauses, proj2, "aradi_diff.py Model 2R k<=8")
print(json.dumps({"equal_sets": A == B, "only_claasp": len(A - B), "only_ours": len(B - A)}))
