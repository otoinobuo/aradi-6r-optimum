#!/usr/bin/env python3
"""T モデル: ビットスライス版（CLAASP AradiBlockCipher の AND 差分モデル）と同じ最適値を持つ S-box レベルの圧縮モデル。
補題: 状態差分を固定すると各 S-box の内部 AND 出力の選択は独立なので、bitsliced トレイルの最小重み = Σ_i T(din_i, dout_i)、
T(din,dout) = その S-box の 4 つの Toffoli AND ゲート（CLAASP の順: x^=w&y, z^=x&y, y^=w&z, w^=x&z、活性 AND は重み 1 で出力差分自由）
で (din→dout) を実現する最小の活性 AND 数（不可能なら ∞）。T は 16×16 の全列挙で得る（gate-feasible 161 組、重み {0,2,3,4}）。
符号化: aradi_diff.py と同じ線形層・双方向順序カウンタ・Matsui 窓。S-box ごとに unary の u1..u4（u_{j+1}→u_j）、重み = Σu。
使い方: tmodel.py --rounds R --k K --start s --bounds bounds.json --out base  （.cnf と .meta.json を出す、make_cubes_bits.py 互換）
        --fixtrail trail.json で状態差分を全固定（T 重みの検算用）。--table で T を表示。"""
import sys, os, json, argparse, itertools
sys.path.insert(0, os.path.expanduser("~/explore/aradi"))
from aradi_diff import SHIFTS, lin_word

def gate_table():
    T = {}
    for din in range(16):
        w, x, y, z = (din >> 3) & 1, (din >> 2) & 1, (din >> 1) & 1, din & 1
        for ch in itertools.product([0, 1], repeat=4):
            wt = 0; ci = 0; W, X, Y, Z = w, x, y, z
            def AND(a, b):
                nonlocal wt, ci
                if a or b:
                    wt += 1; o = ch[ci]; ci += 1; return o
                return 0
            X ^= AND(W, Y); Z ^= AND(X, Y); Y ^= AND(W, Z); W ^= AND(X, Z)
            dout = W << 3 | X << 2 | Y << 1 | Z
            T[(din, dout)] = min(T.get((din, dout), 99), wt)
    return T
T = gate_table()

class Model:
    def __init__(self, R, start=0):
        self.R, self.start, self.nv, self.cnf = R, start, 0, []
        self.x = [[self.new() for _ in range(128)] for _ in range(R + 1)]
        self.hw = []  # per round: list of 128 unary vars (32 sboxes × 4)
        for r in range(R): self.round(r)
        self.cnf.append(self.x[0][:])   # plaintext != 0
    def new(self):
        self.nv += 1; return self.nv
    def xor4(self, p, q, r, s):
        for bits in range(16):
            if bin(bits).count("1") % 2 == 1:
                self.cnf.append([(-v if (bits >> j) & 1 else v) for j, v in enumerate((p, q, r, s))])
    def round(self, r):
        X = self.x[r]; Y = [self.new() for _ in range(128)]; hws = []
        lit = lambda var, bit: var if bit else -var
        for c in range(32):
            din = [X[c], X[32 + c], X[64 + c], X[96 + c]]; dout = [Y[c], Y[32 + c], Y[64 + c], Y[96 + c]]
            u = [self.new() for _ in range(4)]
            for j in range(3): self.cnf.append([-u[j + 1], u[j]])      # unary
            for d in range(16):
                for e in range(16):
                    base = [-lit(din[3 - j], (d >> j) & 1) for j in range(4)] + [-lit(dout[3 - j], (e >> j) & 1) for j in range(4)]
                    if (d, e) not in T:
                        self.cnf.append(base)
                    else:
                        w = T[(d, e)]
                        for j in range(4): self.cnf.append(base + [u[j] if j < w else -u[j]])
            hws += u
        self.hw.append(hws)
        p, q, rr = SHIFTS[(self.start + r) % 4]
        for wd in range(4):
            out = lin_word(Y[32 * wd: 32 * wd + 32], p, q, rr)
            for j in range(32):
                a, b, c = out[j]; self.xor4(a, b, c, self.x[r + 1][32 * wd + j])
    def constrain(self, k, bounds, windows="all"):
        R, s0 = self.R, self.start
        xs = [v for ws in self.hw for v in ws]; N, K = len(xs), k + 1
        Tt = self.new(); self.cnf.append([Tt])
        c = [[None] * (K + 1) for _ in range(N + 1)]
        lit = lambda i, j: Tt if j <= 0 else (-Tt if i == 0 or j > i else c[i][j])
        for i in range(1, N + 1):
            xi = xs[i - 1]
            for j in range(1, min(i, K) + 1):
                c[i][j] = self.new(); pp, qq, z = lit(i - 1, j), lit(i - 1, j - 1), c[i][j]
                self.cnf.extend([[-pp, z], [-xi, -qq, z], [-z, pp, xi], [-z, pp, qq]])
        b = [128 * r for r in range(R + 1)]
        if N >= K: self.cnf.append([-c[N][K]])
        nwin = 0
        if windows != "none":
            for s in range(R):
                for e in range(s, R):
                    if s == 0 and e == R - 1: continue
                    pre, post = s, R - 1 - e
                    m = k - bounds[str(s0 % 4)][pre] - bounds[str((s0 + e + 1) % 4)][post]
                    if m < 0: return None
                    lo, hi = b[s], b[e + 1]; added = False
                    for j in range(0, K):
                        t = j + m + 1
                        if t > K or t > hi: break
                        self.cnf.append([-lit(hi, t), lit(lo, j + 1)]); added = True
                    nwin += added
        self.meta = {"model": "T-model (bitsliced-equivalent)", "start": s0, "rounds": R, "k": k, "bounds": bounds, "windows": windows,
                     "nvars": self.nv, "nclauses": len(self.cnf), "n_windows": nwin,
                     "prefix_reg": {str(b[r]): {str(t): c[b[r]][t] for t in range(1, min(b[r], K) + 1)} for r in range(1, R + 1)},
                     "hw_per_round": self.hw, "states": self.x}
        return True
    def fix_trail(self, trail):
        for r, st in enumerate(trail):
            ws = [int(h, 16) for h in st["in"]]
            for wd in range(4):
                for j in range(32):
                    v = self.x[r][32 * wd + j]; self.cnf.append([v if (ws[wd] >> j) & 1 else -v])
    def decode(self, pos):
        val = lambda vec: sum(1 << i for i, v in enumerate(vec) if v in pos)
        return [{"in": [f"{val(self.x[r][32*wd:32*wd+32]):08x}" for wd in range(4)]} for r in range(self.R + 1)]

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int); ap.add_argument("--k", type=int); ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--bounds"); ap.add_argument("--windows", default="all"); ap.add_argument("--out"); ap.add_argument("--fixtrail"); ap.add_argument("--table", action="store_true")
    a = ap.parse_args()
    if a.table:
        import collections
        print("feasible pairs:", len(T), "weights:", sorted(collections.Counter(T.values()).items()))
        for d in range(16): print(f"{d:x}: " + " ".join(f"{T.get((d,e),'.'):>1}" for e in range(16)))
        sys.exit(0)
    m = Model(a.rounds, a.start)
    bounds = json.load(open(a.bounds)) if a.bounds else {str(s): [0] + [2 * r for r in range(1, 17)] for s in range(4)}
    if a.fixtrail: m.fix_trail(json.load(open(a.fixtrail))["trail"])
    if m.constrain(a.k, bounds, a.windows) is None:
        print(json.dumps({"status": "trivially UNSAT"})); sys.exit(0)
    with open(a.out + ".cnf", "w") as f:
        f.write(f"p cnf {m.nv} {len(m.cnf)}\n")
        for cl in m.cnf: f.write(" ".join(map(str, cl)) + " 0\n")
    json.dump(m.meta, open(a.out + ".meta.json", "w"))
    print(json.dumps({x: m.meta[x] for x in ("model", "start", "rounds", "k", "windows", "nvars", "nclauses", "n_windows")}))
