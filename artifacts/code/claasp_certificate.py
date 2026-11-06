#!/usr/bin/env python3
"""Certificate: the satisfying assignment of CLAASP's 6R model with our trail fixed (k=82)
satisfies every clause of CLAASP's *unconstrained* 6R model with weight <= k (same variable names)."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import build, solve, KISSAT
R, K = int(sys.argv[1]), int(sys.argv[2])
trail = json.load(open(sys.argv[3]))["trail"]
_, mf, vars_f, dimacs_f = build(R, K, trail)
status, dt, values = solve(dimacs_f, os.path.expanduser(f"~/explore/aradi/cnf/cert_fixed_{R}R_k{K}.cnf"), 600)
assert status == "SATISFIABLE", status
assign = {v: (values[i][0] != "-") for i, v in enumerate(vars_f)}
_, mfree, vars_free, _ = build(R, K, None)
missing = [v for v in vars_free if v not in assign]
bad = 0; n = 0
for clause in mfree._model_constraints:
    n += 1
    lits = clause.split()
    assert lits[0] != "x", clause
    ok = any(((lit[0] != "-") == assign[lit.lstrip("-")]) for lit in lits)
    if not ok: bad += 1
print(json.dumps({"rounds": R, "k": K, "fixed_status": status, "free_clauses": n, "violated": bad,
                  "vars_free": len(vars_free), "vars_missing_in_assignment": len(missing)}))
