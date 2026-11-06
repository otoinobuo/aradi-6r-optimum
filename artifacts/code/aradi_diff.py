#!/usr/bin/env python3
"""ARADI（NSA 2024, ePrint 2024/1240）の最適差分トレイルを SAT で探す。
構造: 16 段、各段 = 鍵 XOR → S-box 層 η（Toffoli 4 段、32 本の 4-bit S-box）→ 線形層 L_{i mod 4}。
差分は S-box 層だけが確率的。DDT から各 S-box の重み（2 または 3）を付ける。
重みの順序カウンタと Matsui 境界は speck_diff.py と同じ。
"""
import argparse, json, time
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

SHIFTS = [(11, 8, 14), (10, 9, 11), (9, 4, 14), (8, 9, 7)]   # (a, b, c) 設計者論文 2024/1240 §3.1 の表（i mod 4）


def sbox(v):
    # v = (w, x, y, z) bits packed as w<<3|x<<2|y<<1|z
    w, x, y, z = (v >> 3) & 1, (v >> 2) & 1, (v >> 1) & 1, v & 1
    x ^= w & y
    z ^= x & y
    y ^= z & w
    w ^= x & z
    return w << 3 | x << 2 | y << 1 | z


SB = [sbox(v) for v in range(16)]
DDT = [[0] * 16 for _ in range(16)]
for a in range(16):
    for d in range(16):
        DDT[d][SB[a] ^ SB[a ^ d]] += 1
# 重み: 16→0, 4→2, 2→3
WT = {16: 0, 4: 2, 2: 3}


def lin_word(bits, p, q, r):
    """32-bit 語 (a||b, a が上位 16bit) の線形写像 l_i。bits[j] = ビット j（j=0 が LSB）。
    l(a,b) = (a ⊕ S^p(a) ⊕ S^r(b), b ⊕ S^p(b) ⊕ S^q(a))。S^c = 16-bit 左循環シフト。
    返り値: 出力ビット j ごとの入力ビット添字 3 つ。"""
    a = bits[16:32]  # a_k = bits[16+k]
    b = bits[0:16]
    rot = lambda vec, c: [vec[(k - c) % 16] for k in range(16)]  # (vec <<< c)_k = vec_{k-c}
    Sa_p, Sa_q, Sb_p, Sb_r = rot(a, p), rot(a, q), rot(b, p), rot(b, r)
    out = [None] * 32
    for k in range(16):
        out[16 + k] = (a[k], Sa_p[k], Sb_r[k])
        out[k] = (b[k], Sb_p[k], Sa_q[k])
    return out


class Model:
    def __init__(self, R, start=0):
        self.R, self.start = R, start
        self.pool = IDPool()
        self.cnf = CNF()
        # 状態 128 bit: 語順 W,X,Y,Z、各語 32 bit（添字 0 が LSB）
        self.x = [[self.v(f"x{r}_{i}") for i in range(128)] for r in range(R + 1)]
        self.w = []
        for r in range(R):
            self.round(r)
        self.cnf.append(self.x[0][:])

    def v(self, name):
        return self.pool.id(name)

    def xor4(self, p, q, r, s):
        for bits in range(16):
            if bin(bits).count("1") % 2 == 1:
                self.cnf.append([(-x if (bits >> j) & 1 else x) for j, x in enumerate((p, q, r, s))])

    def round(self, r):
        X = self.x[r]
        Y = [self.v(f"y{r}_{i}") for i in range(128)]   # S-box 層の出力差分
        ws = []
        for c in range(32):
            din = [X[c], X[32 + c], X[64 + c], X[96 + c]]      # (w, x, y, z)
            dout = [Y[c], Y[32 + c], Y[64 + c], Y[96 + c]]
            w2, w3 = self.v(f"w2_{r}_{c}"), self.v(f"w3_{r}_{c}")
            lit = lambda var, bit: var if bit else -var
            for d in range(16):
                for e in range(16):
                    base = [-lit(din[3 - j], (d >> j) & 1) for j in range(4)] + \
                           [-lit(dout[3 - j], (e >> j) & 1) for j in range(4)]
                    cnt = DDT[d][e]
                    if cnt == 0:
                        self.cnf.append(base)
                    else:
                        wt = WT[cnt]
                        self.cnf.append(base + [w2 if wt >= 2 else -w2])
                        self.cnf.append(base + [w3 if wt == 3 else -w3])
            ws += [w2, w2, w3]
        self.w.append(ws)
        p, q, rr = SHIFTS[(self.start + r) % 4]
        for wd in range(4):
            word = Y[32 * wd: 32 * wd + 32]
            out = lin_word(word, p, q, rr)
            for j in range(32):
                a, b, c = out[j]
                self.xor4(a, b, c, self.x[r + 1][32 * wd + j])

    def constrain(self, k, bounds):
        R = self.R
        xs = [w for ws in self.w for w in ws]
        N, K = len(xs), k + 1
        T = self.v("TRUE")
        self.cnf.append([T])
        c = [[None] * (K + 1) for _ in range(N + 1)]
        lit = lambda i, j: T if j <= 0 else (-T if i == 0 or j > i else c[i][j])
        for i in range(1, N + 1):
            xi = xs[i - 1]
            for j in range(1, min(i, K) + 1):
                c[i][j] = self.v(f"c{i}_{j}")
                pp, qq, z = lit(i - 1, j), lit(i - 1, j - 1), c[i][j]
                self.cnf.extend([[-pp, z], [-xi, -qq, z], [-z, pp, xi], [-z, pp, qq]])
        b = [0]
        for ws in self.w:
            b.append(b[-1] + len(ws))
        if N >= K:
            self.cnf.append([-c[N][K]])
        for s in range(R):
            for e in range(s, R):
                if s == 0 and e == R - 1:
                    continue
                pre, post = s, R - 1 - e
                if pre >= len(bounds) or post >= len(bounds):
                    continue
                m = k - bounds[pre] - bounds[post]
                if m < 0:
                    self.cnf.append([])
                    return
                lo, hi = b[s], b[e + 1]
                for j in range(0, K):
                    t = j + m + 1
                    if t > K or t > hi:
                        break
                    self.cnf.append([-lit(hi, t), lit(lo, j + 1)])

    def decode(self, model):
        pos = set(l for l in model if l > 0)
        val = lambda vec: sum(1 << i for i, x in enumerate(vec) if x in pos)
        trail = []
        for r in range(self.R + 1):
            st = [f"{val(self.x[r][32*wd:32*wd+32]):08x}" for wd in range(4)]
            trail.append({"in": st})
        return trail


def check_trail(trail, start=0):
    """独立検算: 各段の入力差分から、S-box 層で到達可能な出力差分のうち線形層を経て次段入力に一致するものを探し重みを足す。"""
    total = 0
    for r in range(len(trail) - 1):
        words = [int(h, 16) for h in trail[r]["in"]]
        nxt = [int(h, 16) for h in trail[r + 1]["in"]]
        p, q, rr = SHIFTS[(start + r) % 4]
        # 線形層は全単射なので逆像を計算: l は対合(involution)と論文にある → l(nxt) が S-box 出力
        def lin_apply(word):
            bits = [(word >> j) & 1 for j in range(32)]
            out = lin_word(bits, p, q, rr)
            return sum((bits_tuple_xor(bits, out[j]) << j) for j in range(32))
        def bits_tuple_xor(bits, idx):
            return bits[idx[0]] ^ bits[idx[1]] ^ bits[idx[2]]
        # lin_word returns indices into the bit list; emulate on values
        def lin_val(word):
            bits = [(word >> j) & 1 for j in range(32)]
            idx = lin_word(list(range(32)), p, q, rr)
            return sum(((bits[idx[j][0]] ^ bits[idx[j][1]] ^ bits[idx[j][2]]) << j) for j in range(32))
        y = [lin_val(nw) for nw in nxt]      # 対合なので逆像 = 順像
        # 対合であることを検算
        for nw in nxt:
            assert lin_val(lin_val(nw)) == nw, "linear map not involutory?"
        for c in range(32):
            d = sum(((words[wd] >> c) & 1) << (3 - wd) for wd in range(4))
            e = sum(((y[wd] >> c) & 1) << (3 - wd) for wd in range(4))
            cnt = DDT[d][e]
            if cnt == 0:
                raise ValueError(f"round {r} col {c}: impossible S-box transition {d:x}->{e:x}")
            total += WT[cnt]
    return total


def solve(R, k, bounds, solver_name, start=0):
    t0 = time.time()
    m = Model(R, start)
    m.constrain(k, bounds)
    with Solver(name=solver_name, bootstrap_with=m.cnf.clauses) as s:
        ok = s.solve()
        dt = time.time() - t0
        if ok:
            trail = m.decode(s.get_model())
            return True, dt, trail, check_trail(trail, start)
        return False, dt, None, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", required=True)
    ap.add_argument("--k", type=int)
    ap.add_argument("--bounds", default="")
    ap.add_argument("--search", action="store_true")
    ap.add_argument("--start", type=int, default=0, help="最初の段の添字（L_{i mod 4} の選択）")
    ap.add_argument("--solver", default="cadical195")
    ap.add_argument("--dump")
    ap.add_argument("--shifts", help="線形層のシフト量を上書き。例 11,8,4;10,9,11;9,4,14;8,9,7")
    args = ap.parse_args()
    if args.shifts:
        SHIFTS[:] = [tuple(int(t) for t in grp.split(",")) for grp in args.shifts.split(";")]
    known = [0] + [int(t) for t in args.bounds.split(",") if t != ""]
    if args.dump:
        m = Model(int(args.rounds), args.start)
        m.constrain(args.k, known)
        m.cnf.to_file(args.dump)
        print(json.dumps({"vars": m.cnf.nv, "clauses": len(m.cnf.clauses)}))
        return
    if args.search:
        lo, hi = (int(t) for t in args.rounds.split("-"))
        bounds = [0]
        for R in range(1, hi + 1):
            if R < lo and R < len(known):
                bounds.append(known[R]); continue
            k = bounds[-1] + bounds[1] if len(bounds) > 1 else 0
            while True:
                ok, dt, trail, w = solve(R, k, bounds, args.solver, args.start)
                print(json.dumps({"R": R, "k": k, "sat": ok, "sec": round(dt, 2)}), flush=True)
                if ok:
                    print(json.dumps({"R": R, "optimal": w, "trail": trail}), flush=True)
                    bounds.append(w); break
                k += 1
        print(json.dumps({"bounds": bounds}), flush=True)
    else:
        R = int(args.rounds)
        ok, dt, trail, w = solve(R, args.k, known, args.solver, args.start)
        print(json.dumps({"R": R, "k": args.k, "sat": ok, "sec": round(dt, 2), "weight": w, "trail": trail}), flush=True)


if __name__ == "__main__":
    main()
