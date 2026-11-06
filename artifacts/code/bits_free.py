#!/usr/bin/env python3
"""ビットスライス版（gate-level）無制約モデル: bits_free.py <R> <k> <timeout>"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import SatXorDifferentialModel, sat_utils, get_single_key_scenario_format_for_fixed_values, solve, convert_solver_solution_to_dictionary
from claasp.ciphers.block_ciphers.aradi_block_cipher import AradiBlockCipher
S = "/tmp/claude-1000/-home-otoi-explore-aradi/696d3d9c-fd8e-4655-94e1-2ae1b7081df8/scratchpad"
R, k, to = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
cipher = AradiBlockCipher(number_of_rounds=R); model = SatXorDifferentialModel(cipher)
model.build_xor_differential_trail_model(weight=k, fixed_variables=get_single_key_scenario_format_for_fixed_values(cipher))
variables, numerical = sat_utils.create_numerical_cnf(model._model_constraints)
status, dt, values = solve(sat_utils.numerical_cnf_to_dimacs(variables, numerical), f"{S}/bits_free_{R}R_k{k}.cnf", to)
res = {"model": "bitsliced gate-level", "rounds": R, "k": k, "status": status, "solve_s": round(dt, 1), "timeout": to}
if status == "SATISFIABLE":
    v2v = model._get_solver_solution_parsed(variables, values); comp, total = model._parse_solver_output(v2v)
    sol = convert_solver_solution_to_dictionary(cipher, "xor_differential", "KISSAT_EXT", dt, 0, comp, float(total))
    comps = sol["components_values"]; per = {}
    for cid, v in comps.items():
        if cid.startswith("and_"): r = int(cid.split("_")[1]); per[r] = per.get(r, 0) + v["weight"]
    res["gate_level_weight"] = sol["total_weight"]; res["and_weight_per_round"] = [per.get(r, 0) for r in range(R)]
    res["plaintext"] = comps["plaintext"]["value"]
    ro = [c.id for c in cipher.get_all_components() if c.type == "intermediate_output" and c.description[0] == "round_output"]
    res["round_outputs"] = [comps[r]["value"] for r in ro]
print(json.dumps(res))
