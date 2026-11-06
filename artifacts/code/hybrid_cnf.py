#!/usr/bin/env python3
"""混成 CNF: CLAASP の AradiBlockCipherSBox 差分モデル（部品制約のみ、重みカウンタなし）に、
我々の双方向順序カウンタ（aradi_diff.py と同じ）と Matsui 窓境界を足して DIMACS を出す。
境界は段の開始添字 s (mod 4) ごとに与える: bounds.json = {"0":[0,2,8,14,32,50], "1":[...], "2":[...], "3":[...]}
（B_s[r] = L_{s}, L_{s+1}, ... で始まる r 段の最適重みの下界。未確定なら確定している下界でよい）
出力: <out>.cnf と <out>.meta.json（段境界ごとの接頭和レジスタ id、hw/plaintext の id）。
"""
import sys, os, json, argparse
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from claasp_run import AradiBlockCipherSBox, SatXorDifferentialModel, sat_utils, get_single_key_scenario_format_for_fixed_values

def build_hybrid(R, k, bounds, windows="all"):
    cipher = AradiBlockCipherSBox(number_of_rounds=R)
    model = SatXorDifferentialModel(cipher)
    fixed = get_single_key_scenario_format_for_fixed_values(cipher)
    model.build_xor_differential_trail_model(weight=-1, fixed_variables=fixed)   # 部品制約のみ
    variables, numerical = sat_utils.create_numerical_cnf(model._model_constraints)
    vid = {v: i + 1 for i, v in enumerate(variables)}
    clauses = [[int(t) for t in cl.split()] for cl in numerical]
    assert all("x" not in cl for cl in numerical)
    hw = sorted((v for v in variables if v.startswith("hw_sbox_")), key=lambda v: tuple(int(t) for t in v.split("_")[2:]))
    per_round = [[vid[v] for v in hw if int(v.split("_")[2]) == r] for r in range(R)]
    assert all(len(p) == 128 for p in per_round), [len(p) for p in per_round]
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
            if s == 0 and e == R - 1:
                continue
            if windows == "ends" and not (s == 0 or e == R - 1):
                continue
            pre, post = s, R - 1 - e
            Bpre = bounds["0"][pre]                      # 接頭 0..s-1 は L_0 始まり
            Bpost = bounds[str((e + 1) % 4)][post]       # 接尾 e+1..R-1 は L_{e+1} 始まり
            m = k - Bpre - Bpost
            if m < 0:
                clauses.append([]); return None
            lo, hi = b[s], b[e + 1]
            added = False
            for j in range(0, K):
                t = j + m + 1
                if t > K or t > hi:
                    break
                clauses.append([-lit(hi, t), lit(lo, j + 1)]); added = True
            nwin += added
    meta = {"rounds": R, "k": k, "bounds": bounds, "windows": windows, "nvars": nv, "nclauses": len(clauses),
            "n_windows": nwin, "claasp_vars": len(variables),
            "prefix_reg": {str(b[r]): {str(t): c[b[r]][t] for t in range(1, min(b[r], K) + 1)} for r in range(1, R + 1)},
            "hw_per_round": per_round, "plaintext": [vid[f"plaintext_{i}"] for i in range(128)],
            "sbox_in_round0": {str(col): [vid[f"plaintext_{32 * w + col}"] for w in range(4)] for col in range(32)}}
    return clauses, nv, meta

def write_dimacs(path, clauses, nv):
    with open(path, "w") as f:
        f.write(f"p cnf {nv} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--bounds", default=os.path.expanduser("~/explore/aradi/bounds.json"))
    ap.add_argument("--windows", default="all", choices=["all", "ends", "none"])
    ap.add_argument("--out", required=True, help="出力の接頭（.cnf / .meta.json を付ける）")
    a = ap.parse_args()
    bounds = json.load(open(a.bounds))
    res = build_hybrid(a.rounds, a.k, bounds, a.windows)
    if res is None:
        print(json.dumps({"status": "trivially UNSAT (bounds exceed k)"})); sys.exit(0)
    clauses, nv, meta = res
    write_dimacs(a.out + ".cnf", clauses, nv)
    json.dump(meta, open(a.out + ".meta.json", "w"))
    print(json.dumps({k: meta[k] for k in ("rounds", "k", "windows", "nvars", "nclauses", "n_windows", "claasp_vars")}))
