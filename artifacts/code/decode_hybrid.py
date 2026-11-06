#!/usr/bin/env python3
"""kissat の v 行（混成 CNF の解）を状態差分トレイルに復号し、JSON（verify_trail.py 形式）で出す。
使い方: decode_hybrid.py <meta.json> <kissat_output> <out.json>"""
import sys, os, json
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import AradiBlockCipherSBox, SatXorDifferentialModel, sat_utils, get_single_key_scenario_format_for_fixed_values
meta = json.load(open(sys.argv[1]))
R = meta["rounds"]
cipher = AradiBlockCipherSBox(number_of_rounds=R)
model = SatXorDifferentialModel(cipher)
model.build_xor_differential_trail_model(weight=-1, fixed_variables=get_single_key_scenario_format_for_fixed_values(cipher))
variables, _ = sat_utils.create_numerical_cnf(model._model_constraints)
assert len(variables) == meta["claasp_vars"]
vid = {v: i + 1 for i, v in enumerate(variables)}
vals = []
for l in open(sys.argv[2]):
    if l.startswith("v "): vals += [int(t) for t in l.split()[1:]]
pos = {v for v in vals if v > 0}
def state(prefix):
    x = 0
    for i in range(128):
        x = (x << 1) | (vid[f"{prefix}_{i}"] in pos)
    return [f"{(x >> (96 - 32 * j)) & 0xffffffff:08x}" for j in range(4)]
ro = [c.id for c in cipher.get_all_components() if c.type == "intermediate_output" and c.description[0] == "round_output"]
trail = [{"in": state("plaintext")}] + [{"in": state(r)} for r in ro]
hw = sum(1 for v in variables if v.startswith("hw_sbox_") and vid[v] in pos)
per_round = [sum(1 for v in meta["hw_per_round"][r] if v in pos) for r in range(R)]
out = {"R": R, "k": meta["k"], "hw_weight": hw, "hw_per_round": per_round, "trail": trail}
json.dump(out, open(sys.argv[3], "w"))
print(json.dumps(out))
