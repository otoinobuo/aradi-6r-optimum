# The six-round differential optimum of ARADI is 82: a machine-checked lower bound

This archive is the reproducible evidence bundle for the result that the best
single-key differential trail of the NSA block cipher ARADI over **six rounds
has weight 82, not 84**. The value 84 is printed in bold (i.e. claimed optimal)
in Table 4 of Bellini et al., *CLAASPing ARADI: Automated Analysis of the ARADI
Block Cipher* (INDOCRYPT 2024; IACR ePrint 2024/1324). Using that paper's own
CLAASP model we show a weight-82 trail exists and no trail of weight 81 or less
exists. This is a single corrected table cell supported by a verified
certificate, **not an attack** on the cipher.

Author: **Nobuo Otoi**, `ba-cybersecurity.com`, Tokyo, Japan.
ORCID: 0009-0001-1445-3612. Independent cybersecurity researcher.

The manuscript (`main.pdf`, deposited alongside this archive) contains the full
argument; this README describes only the artifacts and how they support it.

## 1. What is proved

Two differential-weight definitions are in play, because CLAASP offers two
cipher objects for ARADI. We separate what is **certified** from what is only
**supported (lemma-dependent)**.

### Main result — certified (S-box model)

In the **S-box model** (`AradiBlockCipherSBox` + `SatXorDifferentialModel`;
this is the model of §6.1 / Listing 1.6 of ePrint 2024/1324, i.e. the one that
reproduces Table 4), the six-round single-key differential optimum is **82**:

- **Upper bound:** a weight-82 trail exists. It is a satisfying assignment of
  CLAASP's S-box model found by `kissat`, re-verified by the designers'
  round-function formula (82) and by Monte-Carlo estimation over 2^22 pairs per
  round (~82). The per-round S-box weights are `[18, 6, 18, 16, 8, 16] = 82`;
  plaintext difference `0x000000002854044a0000000000000000`.
- **Lower bound (machine-checked):** no trail of weight <= 81 exists. The
  weight-<=81 instance is a hybrid CNF (see §5), split by cube-and-conquer into
  **945** subproblems, every one UNSAT. All 945 UNSAT results carry a binary
  DRAT proof verified by `drat-trim` (`VERIFIED`, 0 failures). The twenty
  one-to-five-round Matsui bounds `B[1..5] = 2, 8, 14, 32, 50` that the pruning
  relies on are likewise UNSAT with verified DRAT proofs. **Here the DRAT proofs
  are over CLAASP's own component clauses**, so the lower bound does not depend
  on any re-modelling by us.

### Cross-check — supported but lemma-dependent (bit-sliced model)

In the **bit-sliced model** (`AradiBlockCipher`, where the weight counts active
AND / Toffoli gates) the six-round optimum is **also 82**:

- **Upper bound:** the same state trail, fixed into CLAASP's real bit-sliced
  CNF, gives SAT at 82 and UNSAT at 81 (AND-gate profile `[18,6,18,16,8,16]`).
- **Lower bound:** weight 81 is UNSAT by the same cube-and-conquer method
  (945/945 cubes DRAT-verified) **in a compressed "T-model"**. The T-model is
  proved equivalent to CLAASP's bit-sliced model by a **hand-written lemma**
  (validated against the real bit-sliced CNF on the one-to-five-round optima and
  on three known trails). **Unlike the S-box lower bound, this one is not a DRAT
  proof over CLAASP's own bit-sliced clauses; it additionally rests on that
  equivalence lemma, and we flag it as such.**

### Consequence

84 is not optimal under **either** weight definition, so the "84 is really the
bit-sliced value" defence is refuted: the bit-sliced six-round optimum is 82
too. The seven- and eight-round values 106 and 122 of Table 4 are **reproduced
as upper bounds and thereby confirmed** (not corrected). Lower searches below
these were inconclusive within our time budget and are claimed neither way.

## 2. Directory layout

```
README.md             this file
REPRODUCE.md          minimal steps for an independent verifier
MANIFEST.sha256       SHA-256 of every file in this archive

code/                 generators and checkers (see code/ notes below)
trails/               differential trails as JSON (trails/README.txt = provenance)
bounds/               Matsui lower bounds B_s[1..5] and the 1-5R reproduction log
certs/
  sbox_6R_k81/        MAIN lower bound: 945-cube DRAT campaign (S-box model)
  bitsliced_6R_k81/   cross-check lower bound: 945-cube DRAT campaign (T-model)
  matsui/             DRAT logs for B[1..5] and a 6R sample of per-cube proofs
review/               MODEL_ID.md, P2a_summary.md (result write-ups)
```

The raw proof files (`.drat`) and the full CNFs are **not** included: they are
regenerable and were tens of GB in total (36.3 GB for the S-box campaign, 57.7
GB for the bit-sliced one). What is kept is, per cube, the solve time, the
`drat-trim` verdict and the SHA-256 of the deleted proof (the `summary.tsv` /
`detail.tsv` files), plus representative `drat-trim` logs showing the
`s VERIFIED` verdict. This matches §"Verification and reproducibility" of the
manuscript.

## 3. `code/` contents

S-box model and hybrid CNF (from the main working directory):
`aradi_diff.py` (independent ARADI differential model, used for Matsui bounds
and as a cross-check), `hybrid_cnf.py` (hybrid CNF generator: CLAASP component
clauses + bidirectional sequential counter + Matsui windows), `make_cubes.py`
(cube splitter), `run_cubes.sh` (cube runner), `claasp_run.py` (CLAASP-model ->
DIMACS -> kissat driver, `--trail` fixes a trail), `claasp_certificate.py`
(checks a fixed solution against the unconstrained CNF, 0 violated clauses),
`verify_trail.py` (designers'-formula weight re-check, solver-independent),
`verify_empirical.py` (Monte-Carlo weight estimate).

Bit-sliced cross-check (from `review/`): `hybrid_bits.py`, `tmodel.py`
(T-model + the T table), `bits_fixed.py`, `bits_free.py`, `make_cubes_bits.py`,
`decode_hybrid.py`, `claasp_fixed_check.py`, `count2R.py`, `fix_plaintext.py`.

DRAT drivers: `cube_drat_one_6R.sh` (one cube: base+units -> `kissat --unsat`
with proof -> `drat-trim`), `cube_drat_sched.py` (scheduler, memory-guarded),
`drat_full_one.sh` / `drat_full_sched.py` (the S-box full-campaign variant).
`sat_sched.py` / `p2a_pass2.sh` are the SAT-direction schedulers used for the
7R/8R upper-bound searches.

Note: the DRAT drivers refer to a `drat-trim` binary by an absolute path left
over from the compute host; a verifier must edit that path to their own build
(see REPRODUCE.md).

## 4. Trails (`trails/`)

See `trails/README.txt` for a one-line provenance of each file. The certified
weight-82 trail of Table 1 of the manuscript is `trails/t6R_k82_trail.json`
(plaintext word `2854044a`, per-round `[18,6,18,16,8,16]`); it is optimal in
both models. `trails/claasp_6R_k82_free_trail.json` and
`claasp_6R_k83_free_trail.json` are two further weight-82 trails from CLAASP's
S-box model. `trails/bits_6R_k84_trail.json` is the known weight-84 trail (for
context). `claasp_{1..5}R_k*.json` are the one-to-five-round optimum (and
optimum-minus-one) instances that give `B[1..5]`. `claasp_7R_k106_free.json` and
`claasp_8R_k122_free.json` are the Table-4-confirming upper bounds.

## 5. Proof method

The lower bound is a hybrid CNF with three parts:

1. the component clauses CLAASP itself emits for the six-round S-box model
   (`build_xor_differential_trail_model` with no weight counter), so the set of
   satisfying assignments is exactly CLAASP's set of valid trails;
2. a **bidirectional** sequential counter over the per-S-box Hamming-weight
   variables, asserting total weight <= 81;
3. Matsui-style window clauses: for each sub-window the prefix / suffix weight
   is bounded below by the corresponding `B` value, which prunes without
   removing any trail of weight <= 81.

Because part 1 is verbatim CLAASP, a counting / encoding bug could at worst make
the instance spuriously UNSAT; this is ruled out because the *same* hybrid CNF
with the bound raised to 82 is satisfiable and returns a weight-82 trail. The
weight-<=81 instance is partitioned by the first- and second-round weights
(`w0 in [2,31]`, `w01 in [w0+2,49]`), giving 945 cubes, each solved by
`kissat --unsat` with binary DRAT logging and checked by `drat-trim`; a run is
accepted only on the `VERIFIED` verdict.

## 6. Proofs deleted; hashes and logs kept

The 36.3 GB (S-box) and 57.7 GB (bit-sliced) of binary DRAT proofs were deleted
after verification. Retained per cube: solve seconds, `drat-trim` verdict,
proof SHA-256 and proof byte size (`certs/*/summary.tsv` and `detail.tsv`), plus
representative `drat-trim` logs in each `logs_sample/`. Regeneration is
deterministic (the CNFs and cubes rebuild byte-for-byte), so any cube's proof
can be reproduced and its SHA-256 re-checked against the table.

## 7. Dependencies

- **CLAASP** — https://github.com/Crypto-TII/claasp , commit
  `f2239d639ae5c4a013947ce9121c6f4464584758` (`f2239d6`), `VERSION` = `v3.2.0`.
  The working checkout was clean (no local modifications to CLAASP). The CNF is
  produced by CLAASP's own code; the SAT path was run with a minimal pure-Python
  SageMath stub in place of a full SageMath install (CLAASP's SAT path touches
  only `SBox` DDT / small helpers; the stub is bundled here under `code/sagestub/` for audit), and `espresso` from classabbyamp/espresso-
  logic. A full SageMath + CLAASP install at the pinned commit is the canonical
  path and is expected to give identical clauses; see REPRODUCE.md.
- **kissat** — https://github.com/arminbiere/kissat , version 4.0.4
  (tag `rel-4.0.4`, commit `8af8e56f174b778aef3aa45af9f739b2a5f492c2`).
- **drat-trim** — https://github.com/marijnheule/drat-trim , built with
  `-D_GNU_SOURCE` (binary reports the 2015-2024 Marijn Heule / CMU build).

## 8. Honest use of AI

The research question ("is the six-round entry of Table 4 optimal?"), the claims
made here, and the check of every number against the primary result files were
decided and carried out by the author, Nobuo Otoi. The search for trails and the
SAT/UNSAT computations were executed by an AI coding assistant (Claude Code)
under the author's direction. The lower bound does not rest on the assistant's
or the solver's word: each UNSAT result is an independent DRAT certificate
checked by `drat-trim`, and the upper bound is a trail re-verified by the
designers' formula and by Monte-Carlo estimation. The assistant's own reading of
the work is not treated as a review or as independent evidence.

## 9. Manuscript and DOI

The accompanying manuscript is `main.pdf`. A DOI for this archive is
**to be assigned** on deposit. The licence is stated separately (see the end of
REPRODUCE.md); it is not fixed in this README.
