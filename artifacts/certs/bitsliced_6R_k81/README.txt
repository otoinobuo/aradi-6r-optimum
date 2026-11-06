CROSS-CHECK lower bound: 6-round bit-sliced model, weight <= 81 is UNSAT.
945-cube campaign in the T-model (the compressed model proved equivalent to
CLAASP's bit-sliced AradiBlockCipher by a hand-written lemma; see
../../review/MODEL_ID.md). Result: 945/945 VERIFIED, 0 FAIL.
66.8 CPU-hours (31.3 h solve+proof, 35.5 h drat-trim), 3h12m wall; hardest cube
~740 s solve. Raw proofs (57.7 GB) deleted after verification.

IMPORTANT CAVEAT: unlike the S-box campaign in ../sbox_6R_k81/, this lower bound
is a DRAT proof in the T-model, NOT over CLAASP's own bit-sliced clauses, so it
additionally rests on the equivalence lemma. It is "supported", not "certified"
in the same sense. The bit-sliced UPPER bound (weight-82 trail fixed in CLAASP's
real bit-sliced CNF -> k=82 SAT / k=81 UNSAT) is a direct check, DRAT-free.

summary.tsv  (945 rows, TAB): cube | solve_s | VERIFIED | proof_sha256
detail.tsv   (945 rows, TAB): cube | status | solve_s | verify_s | proof_bytes
                              | time-fields | timestamp
sched.log    scheduler log.
DONE         final tally line (VERIFIED=945 SAT=0 FAIL=0 rows=945 ...).
logs_sample/ representative per-cube drat-trim logs ("s VERIFIED").

Column meanings and the re-check procedure are as in ../sbox_6R_k81/README.txt.
