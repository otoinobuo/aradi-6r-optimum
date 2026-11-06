#!/usr/bin/env python3
"""トレイル JSON を CLAASP の無制約モデル（重み≤k）に全固定して解く（既存 cnf/ を上書きしないよう scratch に書く）。
使い方: claasp_fixed_check.py <trail.json> <k>"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import build, solve
S = "/tmp/claude-1000/-home-otoi-explore-aradi/696d3d9c-fd8e-4655-94e1-2ae1b7081df8/scratchpad"
trail = json.load(open(sys.argv[1]))["trail"]; k = int(sys.argv[2])
cipher, model, variables, dimacs = build(6, k, trail)
status, dt, values = solve(dimacs, f"{S}/fixed_{os.path.basename(sys.argv[1])}_k{k}.cnf", 600)
res = {"trail_file": sys.argv[1], "k": k, "status": status, "sec": round(dt, 1)}
if status == "SATISFIABLE":
    v2v = model._get_solver_solution_parsed(variables, values)
    comp, total = model._parse_solver_output(v2v)
    res["claasp_total_weight"] = total
print(json.dumps(res))
