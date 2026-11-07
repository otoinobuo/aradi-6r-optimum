# Model identification: the bit-sliced six-round optimum of ARADI is also 82

This note settles which weight definition Table 4 of ePrint 2024/1324 uses for
the six-round entry, and shows that the "84 is really the bit-sliced value"
reading does not hold: in the bit-sliced model `AradiBlockCipher` (weight =
number of active AND / Toffoli gates) the six-round single-key differential
optimum is **82**, not 84. Reference files are under `modelid/`.

## Result

**The bit-sliced six-round optimum is 82.** Both bounds:

- **Upper bound.** The weight-82 state trail (per-round AND profile
  `[18,6,18,16,8,16]`, plaintext word `2854044a`) fixed into CLAASP's real
  bit-sliced CNF (`AradiBlockCipher` + `SatXorDifferentialModel`) gives k=82 SAT
  / k=81 UNSAT (AND weight 82). The same state trail is weight 82 in CLAASP's
  S-box model as well (fixed: k=82 SAT / k=81 UNSAT). Solver-independent checks:
  designers'-formula weight 82, Monte-Carlo (2^22 pairs/round) ≈ 82.
- **Lower bound.** Weight 81 is UNSAT: the unconstrained T-model instance is
  UNSAT under `kissat` (4,935 s), and the 945-cube campaign
  (`w0 in [2,31]`, `w01 in [w0+2,49]`) is 945/945 UNSAT with `drat-trim`-verified
  binary DRAT proofs (0 SAT, 0 FAIL; `modelid/run_t6R_k81/`).

So 84 is optimal under **neither** weight definition — the S-box optimum is 82
and the bit-sliced optimum is 82 — and the "Table-4 84 is the bit-sliced value"
explanation is refuted; the six-round cell is wrong under the same definition.
That the two models agree at 82 is not a coincidence: the weight-82 state trail
uses only S-box transitions whose gate-level cost equals the DDT weight, so it is
realisable at the same cost bit-sliced.

**Caveat (reviewer-facing).** The bit-sliced lower bound rests on a hand-written
equivalence lemma (§1), so it is of a different standing from the S-box lower
bound, which is a DRAT proof over CLAASP's own component clauses. See §4.

## 1. Compressed model (T-model) and the equivalence lemma

CLAASP's bit-sliced SAT model places a `cnf_and_differential` on each Toffoli
AND gate (4 gates/round × 32 columns): `hw ⇔ (Δa ∨ Δb)`; if `hw=1` the output
difference is free, if `hw=0` it is 0. Weight = Σ hw. The linear layer and key
addition are deterministic.

**Lemma.** Fixing the state differences (the plaintext difference and each
round's `round_output` difference), the choice of the internal AND outputs in
each S-box column is independent per column, and that column's weight is at
least `T(din, dout)` = the minimum number of active ANDs that realise `din→dout`
with CLAASP's four gates (`x^=w&y, z^=x&y, y^=w&z, w^=x&z`), and `T` is
achievable. Hence the r-round minimum bit-sliced weight equals the minimum over
S-box-level trails `(α₀,…,α_r)` of `Σ_i T(din_i, dout_i)`.

`T` is obtained by full 16×16 enumeration (`tmodel.py --table`): 161 `(din,dout)`
pairs are possible (strictly containing the 97 pairs of the DDT support; the 64
DDT=0 pairs are gate-level possible), with weights `{0:1, 2:16, 3:32, 4:112}`.
Within the DDT support, `T ≥ 4 − log2(DDT)` always, strictly for many pairs.
**This is why the S-box lower bound cannot be reused for the bit-sliced model and
a bit-sliced-specific lower bound had to be proved separately.**

The T-model (`review/tmodel.py`) uses the same linear layer as `aradi_diff.py`
(checked identical to the designers' formula for all `i`), unary `u₁..u₄` per
S-box, the `T` value forced per `(din,dout)`, a bidirectional sequential counter,
and Matsui windows.

## 2. Cross-check: T-model against CLAASP's bit-sliced CNF

| Check | CLAASP bit-sliced CNF | T-model |
|---|---|---|
| 1R/2R/3R optima (start 0..3) | 2 / 8 / 14 (k=1,7,13 UNSAT, DRAT-verified, `modelid/small/summary.tsv`) | 2 / 8 / 14 (k=1,7,13 UNSAT) |
| 4R optimum (start 0..3) | k=31 UNSAT: 200 cubes × 4 starts = **800 cubes all UNSAT, DRAT VERIFIED** (`modelid/run_4R_k31_s*/`); k=32 SAT | k=31 UNSAT, k=32 SAT |
| 5R (start 0..3) | k=49: all UNSAT through **305 cubes, VERIFIED**, then stopped (switched to T-model, `modelid/run_5R_k49_s*/`) | k=49 UNSAT (window = proven 1–4R lower bounds), **DRAT VERIFIED (4)**, k=50 SAT (`modelid/tm5R/summary.tsv`) |
| known gate-level 84 trail (`bits_6R_k84_trail.json`, `[34,18,6,2,6,18]`) | k=84 SAT / k=83 UNSAT (fixed) | k=84 SAT / k=83 UNSAT (fixed) |
| S-box weight-82 trail (`claasp_6R_k82_free_trail.json`) | gate-level 88 | T-weight 88 (k=87 UNSAT / k=88 SAT, fixed) |

So the T-model matches CLAASP's bit-sliced CNF on the one-to-four-round optima
(the four-round case certified by an 800-cube DRAT campaign), on a partial
five-round check (305 of 1,568 cubes, all UNSAT), and on three known trails.

## 3. Bit-sliced lower bounds (all UNSAT + DRAT VERIFIED)

`B_bits[s][r]` (identical for all start indices `s=0..3`): 1R=2, 2R=8, 3R=14,
4R=32, 5R=50 — each an UNSAT-with-DRAT instance at weight = optimum−1. The 6R
window uses `6R ≥ 5R+1R = 52` (trivial). These are the window constraints used by
the pruning, so they are implied, not over-constraining.

**k=81 campaign** (`modelid/run_t6R_k81/`): 945/945 cubes UNSAT, all DRAT
VERIFIED; 0 SAT, 0 FAIL. The cube set and the summary set agree; each proof's
SHA-256 is recorded (`summary.tsv`: cube / solve_s / VERIFIED / sha256;
`detail.tsv`: verify_s, proof bytes, RSS). CPU: solve+proof 31.3 h, drat-trim
35.5 h, 66.8 h total (3 h 12 min wall, 21-way); hardest cube `w0_16_w01_29`
(740 s solve); proofs 57.7 GB total (deleted after verification); drat-trim peak
RSS 509 MB. Together with the unconstrained `kissat` UNSAT, this gives the
bit-sliced six-round optimum = 82.

## 4. Dependency of the claim (reviewer-facing)

The bit-sliced optimum = 82 rests on:

1. **Upper bound** — the weight-82 state trail fixed into **CLAASP's real
   bit-sliced CNF** gives k=82 SAT (AND weight 82); solver-independent checks:
   designers' formula 82, Monte-Carlo ≈ 82.
2. **Lemma (§1)** — the bit-sliced minimum weight equals the T-model minimum
   weight; `T` is the full enumeration of CLAASP's `cnf_and_differential`
   semantics over the four gates, with per-column independence.
3. **T-model ⇄ CLAASP consistency (§2)** — 1–4R optima agree (4R certified by
   CLAASP's own 800-cube DRAT), 5R proved in the T-model (CLAASP side matched
   through 305 cubes, then stopped), and three known trails agree (84 / 88 / 82).
4. **B_bits[1..5] = 2,8,14,32,50** (all start indices) — all UNSAT + DRAT.
5. **k=81 UNSAT** — 945 cubes all DRAT VERIFIED, plus the unconstrained `kissat`
   UNSAT.

The remaining soft spot is (2): the lemma is a hand proof. A fully machine-checked
route would cube-and-DRAT CLAASP's bit-sliced CNF directly at k=81, but the
four-round experience puts that at 100–1000× the cost. This is why the bit-sliced
optimum = 82 is reported as *supported (lemma-dependent)*, distinct from the
S-box optimum = 82, which is *certified* over CLAASP's own clauses.

## Artifacts

- `review/tmodel.py` (T-model build / fixing / table), `review/hybrid_bits.py`
  (CLAASP bit-sliced hybrid CNF, `--start`), `review/make_cubes_bits.py`,
  `review/cube_drat_one_6R.sh`, `review/cube_drat_sched.py`.
- `modelid/T_table.txt` (the 16×16 `T` table), `modelid/small/` (1–3R),
  `modelid/run_4R_k31_s*/` (4R, 800 cubes), `modelid/run_5R_k49_s*/` (partial 5R),
  `modelid/tm5R/` (5R T-model DRAT), `modelid/tm6R/` (6R CNF, unconstrained
  results, k=84 trail), `modelid/run_t6R_k81/` (the k=81 campaign:
  `summary.tsv` / `detail.tsv` / logs).
