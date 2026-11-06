#!/usr/bin/env python3
"""設計者の式（Toffoli 4 段 + 線形層）を numpy で直接実装し、トレイルの各段の差分遷移確率を乱数で実測する。"""
import json, sys, math
import numpy as np
SH = [(11, 8, 14), (10, 9, 11), (9, 4, 14), (8, 9, 7)]
M16 = np.uint32(0xffff)
def rot16(v, c):
    return ((v << np.uint32(c)) | (v >> np.uint32(16 - c))) & M16
def L(word, i):
    a, b, c = SH[i % 4]
    u, l = word >> np.uint32(16), word & M16
    return ((u ^ rot16(u, a) ^ rot16(l, c)) << np.uint32(16)) | (l ^ rot16(l, a) ^ rot16(u, b))
def sbox_layer(w, x, y, z):
    x = x ^ (w & y); z = z ^ (x & y); y = y ^ (z & w); w = w ^ (x & z)
    return w, x, y, z
def round_fn(w, x, y, z, i):
    w, x, y, z = sbox_layer(w, x, y, z)
    return L(w, i), L(x, i), L(y, i), L(z, i)
d = json.load(open(sys.argv[1])); trail = d["trail"]; N = 1 << int(sys.argv[2]) if len(sys.argv) > 2 else 1 << 22
rng = np.random.default_rng(1)
total = 0.0
for r in range(len(trail) - 1):
    cur = [np.uint32(int(h, 16)) for h in trail[r]["in"]]
    nxt = [np.uint32(int(h, 16)) for h in trail[r + 1]["in"]]
    hits = 0
    for chunk in range(N >> 20):
        s = [rng.integers(0, 2**32, size=1 << 20, dtype=np.uint32) for _ in range(4)]
        o1 = round_fn(*s, r); o2 = round_fn(*[a ^ b for a, b in zip(s, cur)], r)
        eq = np.ones(1 << 20, dtype=bool)
        for a, b, c in zip(o1, o2, nxt):
            eq &= (a ^ b) == c
        hits += int(eq.sum())
    w = -math.log2(hits / N) if hits else float("inf")
    print(f"round {r}: hits {hits}/2^{int(math.log2(N))}  -> -log2 p ≈ {w:.2f}")
    total += w
print("empirical total ≈", round(total, 2))
