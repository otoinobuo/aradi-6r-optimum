# REPRODUCE — independent verification of the six-round lower bound

This is the minimal path for a primary verifier to re-establish and check the
certified main result (S-box model, six-round optimum = 82). Script names and
arguments are the real ones from `code/`. All sizes/times are from the 24-core
compute host used for the campaign.

## 0. Tools

- `kissat` 4.0.4 (tag `rel-4.0.4`): build from
  https://github.com/arminbiere/kissat ; binary at `build/kissat`.
- `drat-trim`: build from https://github.com/marijnheule/drat-trim with
  `-D_GNU_SOURCE`. **The DRAT driver scripts (`cube_drat_one_6R.sh`,
  `drat_full_one.sh`) contain an absolute `DT=...` path to a drat-trim binary
  from the original host; edit it to your build before running.** The runner
  scripts also default `KISSAT=$HOME/kissat/build/kissat`.
- CLAASP at the pinned commit (next step).

## 1. CLAASP at the pinned commit

```
git clone https://github.com/Crypto-TII/claasp.git
cd claasp && git checkout f2239d639ae5c4a013947ce9121c6f4464584758   # == f2239d6, VERSION v3.2.0
```

Make CLAASP importable. The canonical path is a full SageMath + CLAASP install
(the project's documented route); the component clauses this archive relies on
come from CLAASP's own `build_xor_differential_trail_model` ->
`create_numerical_cnf` -> `numerical_cnf_to_dimacs`, which depend on SageMath
only for `SBox` DDT and a few small helpers. On a host without SageMath the same
clauses were produced with the minimal pure-Python Sage stub bundled here at `code/sagestub/` (put it on `PYTHONPATH` ahead of `claasp`, as the `code/` scripts do) plus `espresso` from
classabbyamp/espresso-logic (built with `-std=gnu17`); the S-box CNF produced
this way was checked by full 2^12 enumeration to realise exactly
`{DDT != 0} x {hw = unary(4 - log2 DDT)}` (97 models), and the one-to-five-round
optima match Table 4, so either route yields the same CNF. Point the `code/`
scripts at your CLAASP (they import `claasp`).

## 2. Hybrid CNF for six rounds, weight <= 81

```
python hybrid_cnf.py --rounds 6 --k 81 --bounds bounds/bounds.json \
       --windows all --out hyb_6R_k81
```

Produces `hyb_6R_k81.cnf` and `hyb_6R_k81.meta.json` (the prefix-sum register
ids per round boundary). `bounds/bounds.json` holds the Matsui bounds
`B_s[r]` (starting index `s mod 4`); `B[1..5] = 2,8,14,32,50` for every `s`.
The build is deterministic — re-generating gives a byte-identical CNF.

## 3. Cube-and-conquer split

```
python make_cubes.py --meta hyb_6R_k81.meta.json --outdir cubes_6R_k81 --split2
```

gives the **945** cubes (`w0 in [2,31]`, `w01 in [w0+2,49]`), each a `.units`
file. (`--pos` subdivides further by the first-round active-S-box column if any
cube needs it.)

## 4. Solve each cube UNSAT with a DRAT proof, verify with drat-trim

Fast sanity run without proofs (all must be `UNSATISFIABLE`):

```
NICE=10 ./run_cubes.sh hyb_6R_k81.cnf cubes_6R_k81 <threads> 7200 results_6R_k81.tsv
```

Certified run (per cube: `kissat --unsat <cnf> <proof>` then `drat-trim`):

```
# single cube:
./cube_drat_one_6R.sh hyb_6R_k81.cnf cubes_6R_k81 <outdir> <cube-name>
# whole campaign with a memory-guarded scheduler:
python cube_drat_sched.py hyb_6R_k81.cnf cubes_6R_k81 <outdir> <maxparallel>
```

Each cube appends to `<outdir>/summary.tsv` a row
`cube <solve_s> VERIFIED <proof_sha256>` and to `detail.tsv` a row with the
kissat status, verify seconds, proof bytes and max RSS. A run counts only on a
`drat-trim` `s VERIFIED` verdict. The reference campaign: **945/945 VERIFIED, 0
FAIL**, 22.47 CPU-hours, hardest cube `w0_12_w01_29` (286 s solve / 261 s
verify / 307 MB proof). The reference tables are in `certs/sbox_6R_k81/`.

## 5. Confirm the union and read the verdict

The 945 cubes cover the whole feasible region (their `(w0,w01)` pairs are
exactly the integer points of the region), so all-UNSAT means the six-round
weight-<=81 instance is UNSAT, i.e. the optimum is >= 82.

```
awk -F'\t' '{c[$3]++} END{for(k in c) print k, c[k]}' certs/sbox_6R_k81/summary.tsv
# expect: VERIFIED 945
```

## 6. Matsui bounds B[1..5] (dependency of the window pruning)

Each is an UNSAT-with-DRAT instance at weight = optimum-1 for a window; the SAT
side at the optimum is the small JSON trail. Logs are in `certs/matsui/`
(`drat_small/` for 1-4R at all starting indices, `drat5R/` for 5R k=49 at
`s=0..3`). To re-make a 5R bound, e.g.:

```
python aradi_diff.py --rounds 5 --k 49 --start <s> --dump   # -> CNF; solve with kissat --unsat + DRAT, check with drat-trim
```

(`claasp_1..4R` bounds use CLAASP CNFs directly; see `bounds/claasp_repro_1_5.txt`.)

## 7. Upper bound (weight-82 trail)

Re-fix the trail's seven state differences in the unconstrained CLAASP model and
confirm the weight, then re-check solver-independently:

```
python claasp_run.py --rounds 6 --k 82 --trail trails/t6R_k82_trail.json   # expect SAT, total_weight 82
python claasp_run.py --rounds 6 --k 81 --trail trails/t6R_k82_trail.json   # expect UNSAT
python verify_trail.py trails/t6R_k82_trail.json                           # designers' formula -> 82
python verify_empirical.py trails/t6R_k82_trail.json                       # Monte-Carlo -> ~82
python claasp_certificate.py                                               # 0 violated clauses in the unconstrained CNF
```

## 8. Bit-sliced cross-check (lemma-dependent — read this caveat)

The bit-sliced lower bound (`certs/bitsliced_6R_k81/`, 945/945 DRAT-verified,
66.8 CPU-hours) is produced in the **T-model** (`code/tmodel.py`,
`code/hybrid_bits.py`, `code/make_cubes_bits.py`), which `review/MODEL_ID.md` proves
equivalent to CLAASP's bit-sliced model by a **hand-written lemma** — validated
against the real bit-sliced CNF on the 1-5R optima and three known trails
(`code/bits_fixed.py`, `code/claasp_fixed_check.py`), but **not itself a DRAT
proof over CLAASP's own bit-sliced clauses**. The bit-sliced upper bound is a
DRAT-free fixing check: the weight-82 state trail in CLAASP's real bit-sliced
CNF gives SAT at 82, UNSAT at 81. Treat the bit-sliced optimum = 82 as
*supported* (lemma + certified bit-sliced sub-bounds + DRAT in the equivalent
model), whereas the S-box optimum = 82 is *certified* over CLAASP's own clauses.
See `review/MODEL_ID.md` for the lemma and the cross-checks, and
`review/P2a_summary.md` for the (inconclusive) 7R/8R lower searches.

## Licence

The licence for this archive is to be stated separately by the author; it is
not fixed here.
