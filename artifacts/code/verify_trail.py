#!/usr/bin/env python3
"""aradi_diff.py と独立に、設計者論文 §3.1 の式だけから差分トレイルの重みを検算する。
S-box は Mandal 他 (2025/1976) Table 3 の整数表、線形層は (u,l) -> (u^S^a(u)^S^c(l), l^S^a(l)^S^b(u))。"""
import json, sys
SBOX = [0, 1, 2, 3, 4, 13, 15, 6, 8, 11, 5, 14, 12, 7, 10, 9]   # 入力 = w<<3|x<<2|y<<1|z
SH = [(11, 8, 14), (10, 9, 11), (9, 4, 14), (8, 9, 7)]
M16 = 0xffff
rot16 = lambda v, c: ((v << c) | (v >> (16 - c))) & M16
def L(word, i):
    a, b, c = SH[i % 4]
    u, l = word >> 16, word & M16
    return ((u ^ rot16(u, a) ^ rot16(l, c)) << 16) | (l ^ rot16(l, a) ^ rot16(u, b))
def sbox_layer(w, x, y, z):
    W = X = Y = Z = 0
    for i in range(32):
        v = ((w >> i) & 1) << 3 | ((x >> i) & 1) << 2 | ((y >> i) & 1) << 1 | ((z >> i) & 1)
        o = SBOX[v]
        W |= ((o >> 3) & 1) << i; X |= ((o >> 2) & 1) << i; Y |= ((o >> 1) & 1) << i; Z |= (o & 1) << i
    return W, X, Y, Z
def ddt_count(din, dout):
    return sum(1 for a in range(16) if SBOX[a] ^ SBOX[a ^ din] == dout)
d = json.load(open(sys.argv[1]))
trail = d["trail"]; start = 0
total = 0
import random
for r in range(len(trail) - 1):
    cur = [int(h, 16) for h in trail[r]["in"]]
    nxt = [int(h, 16) for h in trail[r + 1]["in"]]
    # 線形層の逆像（対合なので L 自身）
    mid = [L(v, start + r) for v in nxt]
    assert all(L(L(v, start + r), start + r) == v for v in nxt)
    wr = 0
    for i in range(32):
        din = sum(((cur[j] >> i) & 1) << (3 - j) for j in range(4))
        dout = sum(((mid[j] >> i) & 1) << (3 - j) for j in range(4))
        c = ddt_count(din, dout)
        if c == 0: raise SystemExit(f"round {r} col {i}: impossible {din:x}->{dout:x}")
        wr += {16: 0, 4: 2, 2: 3}[c]
    # 実験的検算: 乱数 2^14 ペアでこの段の差分遷移（S-box 層のみ）の確率を測る
    ok = 0; N = 1 << 14
    for _ in range(N):
        w, x, y, z = (random.getrandbits(32) for _ in range(4))
        o1 = sbox_layer(w, x, y, z); o2 = sbox_layer(w ^ cur[0], x ^ cur[1], y ^ cur[2], z ^ cur[3])
        if [a ^ b for a, b in zip(o1, o2)] == mid: ok += 1
    import math
    emp = -math.log2(ok / N) if ok else float('inf')
    print(f"round {r}: weight {wr}  (empirical -log2 p ≈ {emp:.2f} over 2^14 pairs)" if wr <= 12 else f"round {r}: weight {wr}  (empirical skipped, too small p)")
    total += wr
print("total weight", total)
