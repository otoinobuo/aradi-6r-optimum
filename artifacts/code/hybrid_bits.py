#!/usr/bin/env python3
"""ビットスライス版 AradiBlockCipher（AND ゲート重み）用の混成 CNF（hybrid_cnf.py と同じ構成: CLAASP 部品節＋双方向順序カウンタ＋Matsui 窓）。
--start s で線形層の開始添字をずらした派生暗号（L_{(i+s) mod 4}）を使える（下界 B_s の計算用）。
bounds.json は {"0":[0,B1,...], "1":[...], ...}（ビットスライス版で証明済み or 自明に正しい下界のみを入れること）。
出力: <out>.cnf, <out>.meta.json（make_cubes.py 互換）。--fixpt <trail.json> で平文差分を固定（動作確認用）。"""
import sys, os, json, argparse
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import SatXorDifferentialModel, sat_utils, get_single_key_scenario_format_for_fixed_values, set_fixed_variables, integer_to_bit_list, words_to_int
from claasp.ciphers.block_ciphers.aradi_block_cipher import AradiBlockCipher

def make_cipher(R, start):
    if start == 0:
        return AradiBlockCipher(number_of_rounds=R)
    class Shifted(AradiBlockCipher):
        def l_function(self, *args):
            args = list(args); args[-1] = args[-1] + start     # 最後の引数が round_index
            return AradiBlockCipher.l_function(self, *args)
    return Shifted(number_of_rounds=R)

def build(R, k, bounds, windows="all", start=0, fixpt=None):
    cipher = make_cipher(R, start)
    model = SatXorDifferentialModel(cipher)
    fixed = get_single_key_scenario_format_for_fixed_values(cipher)
    if fixpt is not None:
        fixed = [f for f in fixed if f["component_id"] != "plaintext"]
        fixed.append(set_fixed_variables("plaintext", "equal", list(range(128)), integer_to_bit_list(fixpt, 128, "big")))
    model.build_xor_differential_trail_model(weight=-1, fixed_variables=fixed)
    variables, numerical = sat_utils.create_numerical_cnf(model._model_constraints)
    assert all("x" not in cl for cl in numerical)
    vid = {v: i + 1 for i, v in enumerate(variables)}
    clauses = [[int(t) for t in cl.split()] for cl in numerical]
    hw = sorted((v for v in variables if v.startswith("hw_and_")), key=lambda v: tuple(int(t) for t in v.split("_")[2:]))
    per_round = [[vid[v] for v in hw if int(v.split("_")[2]) == r] for r in range(R)]
    assert all(len(p) == 128 for p in per_round), [len(p) for p in per_round]
    assert len(hw) == 128 * R
    xs = [v for p in per_round for v in p]
    N, K = len(xs), k + 1
    nv = len(variables)
    def new():
        nonlocal nv; nv += 1; return nv
    T = new(); clauses.append([T])
    c = [[None] * (K + 1) for _ in range(N + 1)]
    lit = lambda i, j: T if j <= 0 else (-T if i == 0 or j > i else c[i][j])
    for i in range(1, N + 1):
        xi = xs[i - 1]
        for j in range(1, min(i, K) + 1):
            c[i][j] = new()
            pp, qq, z = lit(i - 1, j), lit(i - 1, j - 1), c[i][j]
            clauses.extend([[-pp, z], [-xi, -qq, z], [-z, pp, xi], [-z, pp, qq]])
    b = [128 * r for r in range(R + 1)]
    if N >= K:
        clauses.append([-c[N][K]])
    nwin = 0
    for s in range(R):
        for e in range(s, R):
            if s == 0 and e == R - 1: continue
            if windows == "ends" and not (s == 0 or e == R - 1): continue
            if windows == "none": continue
            pre, post = s, R - 1 - e
            Bpre = bounds[str(start % 4)][pre]                 # 接頭 0..s-1 は L_start 始まり
            Bpost = bounds[str((start + e + 1) % 4)][post]     # 接尾 e+1..R-1 は L_{start+e+1} 始まり
            m = k - Bpre - Bpost
            if m < 0:
                return None
            lo, hi = b[s], b[e + 1]
            added = False
            for j in range(0, K):
                t = j + m + 1
                if t > K or t > hi: break
                clauses.append([-lit(hi, t), lit(lo, j + 1)]); added = True
            nwin += added
    ro = [x.id for x in cipher.get_all_components() if x.type == "intermediate_output" and x.description[0] == "round_output"]
    assert len(ro) == R
    meta = {"model": "AradiBlockCipher(bitsliced)", "start": start, "rounds": R, "k": k, "bounds": bounds, "windows": windows, "nvars": nv, "nclauses": len(clauses),
            "n_windows": nwin, "claasp_vars": len(variables),
            "prefix_reg": {str(b[r]): {str(t): c[b[r]][t] for t in range(1, min(b[r], K) + 1)} for r in range(1, R + 1)},
            "hw_per_round": per_round, "plaintext": [vid[f"plaintext_{i}"] for i in range(128)],
            "round_outputs": {r: [vid[f"{r}_{i}"] for i in range(128)] for r in ro},
            "sbox_in_round0": {str(col): [vid[f"plaintext_{32 * w + col}"] for w in range(4)] for col in range(32)}}
    return clauses, nv, meta

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, required=True); ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--bounds", required=True); ap.add_argument("--windows", default="all", choices=["all", "ends", "none"])
    ap.add_argument("--start", type=int, default=0); ap.add_argument("--fixpt", help="trail json whose plaintext difference is fixed")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    bounds = json.load(open(a.bounds))
    fixpt = None
    if a.fixpt:
        fixpt = words_to_int([int(h, 16) for h in json.load(open(a.fixpt))["trail"][0]["in"]])
    res = build(a.rounds, a.k, bounds, a.windows, a.start, fixpt)
    if res is None:
        print(json.dumps({"status": "trivially UNSAT (bounds exceed k)"})); sys.exit(0)
    clauses, nv, meta = res
    with open(a.out + ".cnf", "w") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for cl in clauses: f.write(" ".join(map(str, cl)) + " 0\n")
    json.dump(meta, open(a.out + ".meta.json", "w"))
    print(json.dumps({x: meta[x] for x in ("model", "start", "rounds", "k", "windows", "nvars", "nclauses", "n_windows", "claasp_vars")}))
