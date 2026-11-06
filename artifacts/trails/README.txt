Provenance of each trail file. A "trail" lists, per step, the state difference
[w, x, y, z] (four 32-bit words, hex) at the S-box-layer input of each round
(7 states for 6 rounds). "S-box model" = AradiBlockCipherSBox weight
(4 - log2 DDT per active S-box); "bit-sliced model" = AradiBlockCipher weight
(active AND/Toffoli gates); "T-model" = our compressed bit-sliced-equivalent
model (see review/MODEL_ID.md).

CERTIFIED weight-82 trail of the manuscript (Table 1):
  t6R_k82_trail.json         T-model weight-82 SAT; plaintext word x=2854044a;
                             per-round [18,6,18,16,8,16]=82. This same state
                             trail is weight 82 in BOTH the S-box model (CLAASP
                             fixed k=82 SAT / k=81 UNSAT) and the bit-sliced
                             model (AND weight 82). It is the trail printed in
                             the manuscript (plaintext 0x..2854044a..).

Further weight-82 trails (S-box model, CLAASP SatXorDifferentialModel + kissat):
  claasp_6R_k82_free_trail.json   unconstrained search at bound 82 -> weight 82.
  claasp_6R_k83_free_trail.json   unconstrained search at bound 83 -> weight 82
                                  (a different weight-82 trail).
  ours_6R_k82_trail.json          weight-82 trail from the author's independent
                                  model (aradi_diff.py); re-checked in CLAASP.

Bit-sliced-side trails:
  t6R_k83_trail.json         T-model weight-83 SAT; plaintext x=42a12250;
                             per-round [18,7,18,16,8,16]=83. Fixed in CLAASP's
                             real bit-sliced CNF -> k=83 SAT / k=82 UNSAT.
  bits_6R_k84_trail.json     the known weight-84 trail, per-round
                             [34,18,6,2,6,18]=84 (84 in both models). Kept for
                             context: 84 IS achievable, it is just not optimal.

One-to-five-round Matsui bounds B[1..5] = 2,8,14,32,50 (S-box model, CLAASP):
  claasp_1R_k1.json          k=1 UNSAT  (so B[1] >= 2; optimum 2)
  claasp_2R_k7.json  / _k8   k=7 UNSAT, k=8 SAT   -> B[2] = 8
  claasp_3R_k13.json / _k14  k=13 UNSAT, k=14 SAT -> B[3] = 14
  claasp_4R_k31.json / _k32  k=31 UNSAT, k=32 SAT -> B[4] = 32
  claasp_5R_k49.json / _k50  k=49 UNSAT, k=50 SAT -> B[5] = 50
  (DRAT certificates for these UNSAT sides are in ../certs/matsui/.)

Table-4-confirming upper bounds (S-box model; reproduced, not corrected):
  claasp_7R_k106_free.json   7 rounds, weight 106 (matches Table 4).
  claasp_8R_k122_free.json   8 rounds, weight 122 (matches Table 4).

Word order: the 128-bit state is w||x||y||z, each 32 bits; CLAASP packs it as
(w<<96)|(x<<64)|(y<<32)|z with bit index 0 = MSB.
