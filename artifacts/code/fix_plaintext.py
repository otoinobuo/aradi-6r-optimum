#!/usr/bin/env python3
"""混成 CNF に、与えたトレイル JSON の平文差分を単位節として足した CNF を書く。
使い方: fix_plaintext.py <base.cnf> <meta.json> <trail.json> <out.cnf>"""
import sys, json
base, meta, trail, out = sys.argv[1:5]
m = json.load(open(meta)); t = json.load(open(trail))["trail"]
ws = [int(h, 16) for h in t[0]["in"]]
x = (ws[0] << 96) | (ws[1] << 64) | (ws[2] << 32) | ws[3]
units = [(m["plaintext"][i] if (x >> (127 - i)) & 1 else -m["plaintext"][i]) for i in range(128)]
with open(base) as f:
    hdr = f.readline().split()
    body = f.read()
with open(out, "w") as f:
    f.write(f"p cnf {hdr[2]} {int(hdr[3]) + 128}\n"); f.write(body)
    for u in units: f.write(f"{u} 0\n")
print("wrote", out, "plaintext", t[0]["in"])
