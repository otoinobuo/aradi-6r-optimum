#!/usr/bin/env python3
"""Drive CLAASP's own SatXorDifferentialModel for AradiBlockCipherSBox (sage replaced by a stub),
export the DIMACS CLAASP builds, solve with kissat under a timeout, and parse with CLAASP's parser."""
import sys, os, json, time, subprocess, argparse
BASE = os.path.expanduser("~/explore/aradi/claasp_src")
sys.path[:0] = [f"{BASE}/sagestub", f"{BASE}/claasp"]
os.environ["PATH"] = f"{BASE}/espresso-logic/bin:" + os.environ["PATH"]
from claasp.ciphers.block_ciphers.aradi_block_cipher_sbox import AradiBlockCipherSBox
from claasp.cipher_modules.models.sat.sat_models.sat_xor_differential_model import SatXorDifferentialModel
from claasp.cipher_modules.models.sat.utils import utils as sat_utils
from claasp.cipher_modules.models.utils import set_fixed_variables, integer_to_bit_list, get_single_key_scenario_format_for_fixed_values
from claasp.cipher_modules.models.utils import convert_solver_solution_to_dictionary
KISSAT = os.path.expanduser("~/kissat/build/kissat")

def words_to_int(ws):  # [w,x,y,z] (ints) -> 128-bit int, CLAASP bit 0 = MSB
    return (ws[0] << 96) | (ws[1] << 64) | (ws[2] << 32) | ws[3]

def build(rounds, k, trail=None):
    cipher = AradiBlockCipherSBox(number_of_rounds=rounds)
    model = SatXorDifferentialModel(cipher)
    fixed = get_single_key_scenario_format_for_fixed_values(cipher)  # key = 0, plaintext != 0
    if trail is not None:
        # fix plaintext difference and every round_output difference to the given trail
        states = [words_to_int([int(h, 16) for h in st["in"]]) for st in trail]
        fixed = [f for f in fixed if f["component_id"] != "plaintext"]
        fixed.append(set_fixed_variables("plaintext", "equal", list(range(128)), integer_to_bit_list(states[0], 128, "big")))
        ro = [c.id for c in cipher.get_all_components() if c.type == "intermediate_output" and c.description[0] == "round_output"]
        assert len(ro) == rounds, (len(ro), rounds)
        for r in range(1, min(len(states), rounds + 1)):
            fixed.append(set_fixed_variables(ro[r - 1], "equal", list(range(128)), integer_to_bit_list(states[r], 128, "big")))
    model.build_xor_differential_trail_model(weight=k, fixed_variables=fixed)
    variables, numerical_cnf = sat_utils.create_numerical_cnf(model._model_constraints)
    dimacs = sat_utils.numerical_cnf_to_dimacs(variables, numerical_cnf)
    return cipher, model, variables, dimacs

def solve(dimacs, path, timeout):
    with open(path, "w") as f: f.write(dimacs + "\n")
    t0 = time.time()
    p = subprocess.run(["timeout", str(timeout), "nice", "-n", "19", KISSAT, "-q", path], capture_output=True, text=True)
    dt = time.time() - t0
    out = p.stdout.splitlines()
    s = [l for l in out if l.startswith("s ")]
    status = s[0].split()[1] if s else "UNKNOWN"
    values = []
    if status == "SATISFIABLE":
        for l in out:
            if l.startswith("v "): values.extend(l.split()[1:])
        values = values[:-1]
    return status, dt, values

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, required=True)
    ap.add_argument("--k", type=int, required=True, help="weight <= k (CLAASP sequential counter)")
    ap.add_argument("--trail", help="json file with trail [{'in':[w,x,y,z hex]},...] to fix all state differences")
    ap.add_argument("--timeout", type=int, default=600)
    ap.add_argument("--out")
    a = ap.parse_args()
    trail = None
    if a.trail:
        trail = json.load(open(a.trail))["trail"]
    t0 = time.time()
    cipher, model, variables, dimacs = build(a.rounds, a.k, trail)
    tb = time.time() - t0
    nv, nc = dimacs.split("\n")[0].split()[2:4]
    path = os.path.expanduser(f"~/explore/aradi/cnf/claasp_{a.rounds}R_k{a.k}{'_fixed' if trail else ''}.cnf")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    status, dt, values = solve(dimacs, path, a.timeout)
    res = {"rounds": a.rounds, "k": a.k, "fixed_trail": bool(trail), "status": status, "build_s": round(tb, 1),
           "solve_s": round(dt, 1), "vars": int(nv), "clauses": int(nc)}
    if status == "SATISFIABLE":
        v2v = model._get_solver_solution_parsed(variables, values)
        comp, total = model._parse_solver_output(v2v)
        sol = convert_solver_solution_to_dictionary(cipher, "xor_differential", "KISSAT_EXT", dt, 0, comp, float(total))
        comps = sol["components_values"]
        res["total_weight"] = sol["total_weight"]
        res["plaintext"] = comps["plaintext"]["value"]
        res["round_outputs"] = {k: v["value"] for k, v in comps.items() if k.startswith("intermediate_output") and v.get("weight", 0) == 0}
        per_round = {}
        for cid, v in comps.items():
            if cid.startswith("sbox_"):
                r = int(cid.split("_")[1]); per_round[r] = per_round.get(r, 0) + v["weight"]
        res["sbox_weight_per_round"] = [per_round.get(r, 0) for r in range(a.rounds)]
        res["nonzero_weight_components"] = {k: v["weight"] for k, v in comps.items() if v.get("weight", 0) and not k.startswith("sbox_")}
    print(json.dumps(res))
    if a.out:
        json.dump(res, open(a.out, "w"), indent=1)

if __name__ == "__main__":
    main()
