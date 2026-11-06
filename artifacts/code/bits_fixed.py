#!/usr/bin/env python3
"""ビットスライス版 AradiBlockCipher（AND ゲート重み）で、与えた状態差分トレイル（平文＋各段 round_output）を全固定し、
重み ≤ k が SAT になる最小 k を k=lo..hi で探す。= その状態トレイルの gate-level 重み。"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import words_to_int, SatXorDifferentialModel, sat_utils, set_fixed_variables, integer_to_bit_list, get_single_key_scenario_format_for_fixed_values, solve
from claasp.ciphers.block_ciphers.aradi_block_cipher import AradiBlockCipher
S = "/tmp/claude-1000/-home-otoi-explore-aradi/696d3d9c-fd8e-4655-94e1-2ae1b7081df8/scratchpad"
tf = sys.argv[1]; lo, hi = int(sys.argv[2]), int(sys.argv[3])
trail = json.load(open(tf))["trail"]; R = len(trail) - 1
states = [words_to_int([int(h, 16) for h in st["in"]]) for st in trail]
for k in range(lo, hi + 1):
    cipher = AradiBlockCipher(number_of_rounds=R)
    model = SatXorDifferentialModel(cipher)
    fixed = [f for f in get_single_key_scenario_format_for_fixed_values(cipher) if f["component_id"] != "plaintext"]
    fixed.append(set_fixed_variables("plaintext", "equal", list(range(128)), integer_to_bit_list(states[0], 128, "big")))
    ro = [c.id for c in cipher.get_all_components() if c.type == "intermediate_output" and c.description[0] == "round_output"]
    assert len(ro) == R, (len(ro), R)
    for r in range(1, R + 1):
        fixed.append(set_fixed_variables(ro[r - 1], "equal", list(range(128)), integer_to_bit_list(states[r], 128, "big")))
    model.build_xor_differential_trail_model(weight=k, fixed_variables=fixed)
    variables, numerical = sat_utils.create_numerical_cnf(model._model_constraints)
    dimacs = sat_utils.numerical_cnf_to_dimacs(variables, numerical)
    status, dt, values = solve(dimacs, f"{S}/bits_fixed_{os.path.basename(tf)}_k{k}.cnf", 300)
    res = {"trail": os.path.basename(tf), "k": k, "status": status, "sec": round(dt, 1)}
    if status == "SATISFIABLE":
        v2v = model._get_solver_solution_parsed(variables, values)
        comp, total = model._parse_solver_output(v2v)
        per = {}
        for cid, v in comp.items():
            if cid.startswith("and_"):
                r = int(cid.split("_")[1]); per[r] = per.get(r, 0) + v["weight"]
        res["gate_level_weight"] = total; res["and_weight_per_round"] = [per.get(r, 0) for r in range(R)]
    print(json.dumps(res), flush=True)
    if status == "SATISFIABLE": break
