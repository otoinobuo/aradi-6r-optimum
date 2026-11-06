MAIN lower bound: 6-round S-box model, weight <= 81 is UNSAT.
945-cube cube-and-conquer campaign, each cube solved by kissat 4.0.4 with a
binary DRAT proof and checked by drat-trim. CERTIFIED over CLAASP's own
component clauses (no re-modelling). Result: 945/945 VERIFIED, 0 FAIL.
22.47 CPU-hours total (11.88 h solve+proof, 10.59 h drat-trim), 1h54m wall;
hardest cube w0_12_w01_29 (286 s solve, 261 s verify, 307 MB proof). The raw
proofs (36.3 GB) were deleted after verification; SHA-256 and logs are kept.

summary.tsv  (945 rows, TAB-separated, no header):
  col 1  cube name  (w0_<first-round weight>_w01_<first-two-round weight>)
  col 2  kissat solve+proof seconds
  col 3  drat-trim verdict: VERIFIED  (SAT / FAIL would appear here otherwise)
  col 4  SHA-256 of the (deleted) binary DRAT proof for that cube

detail.tsv  (945 rows, TAB-separated, no header):
  col 1  cube name
  col 2  kissat status (UNSATISFIABLE for all 945)
  col 3  solve seconds
  col 4  drat-trim verify seconds
  col 5  proof size in bytes
  col 6  /usr/bin/time fields (maxrss_kb=..., wall=...)
  col 7  timestamp

results_6R_k81.tsv  earlier no-proof run of the same 945 cubes (cube, status,
                    seconds) used as the fast all-UNSAT sanity check.
REPORT.md           campaign report.
sched.log, run.log  scheduler / run logs.
logs_sample/        two representative per-cube drat-trim logs showing the
                    "s VERIFIED" verdict and the resolution-step counts.

To re-check any cube: regenerate its CNF (deterministic; see ../../REPRODUCE.md),
rerun kissat --unsat with a proof, run drat-trim, and compare the proof SHA-256
and the VERIFIED verdict against summary.tsv.
