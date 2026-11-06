DRAT certificates for the Matsui lower bounds B[1..5] = 2,8,14,32,50 (which the
window pruning of the 6R hybrid CNF depends on), plus a 6R sample of per-cube
proofs from the main S-box campaign.

Each bound is an UNSAT-with-DRAT instance at weight = optimum-1 for an r-round
window at starting index s (s = round index mod 4); the SAT side at the optimum
is the small trail JSON in ../../trails/. Only the drat-trim logs and summary
tables are kept here (raw .drat and .cnf omitted; all are regenerable).

drat5R/        5-round bound B[5]=50: k=49 UNSAT at each starting index s=0..3.
  summary.tsv  rows: start=<s> | kissat=UNSATISFIABLE | solve_s | drat_trim=s VERIFIED
               | check_s | proof_bytes
  our_5R_k49_s<s>.drat-trim.log   drat-trim log for each (shows "s VERIFIED").

drat_small/    1-to-4-round bounds B[1..4]=2,8,14,32 at the relevant starting
               indices. claasp_* = CLAASP CNF (s=0); our_* = author's model
               (s=1,2,3). k = optimum-1 (1R k1, 2R k7, 3R k13, 4R k31), all
               UNSAT.
  summary.tsv  per-instance verdict table.
  *.drat-trim.log   one drat-trim log per instance ("s VERIFIED").

sbox_6R_sample/  four representative 6R cubes from the main campaign
               (../sbox_6R_k81/), re-solved with proofs as a spot check,
               including the hardest cube w0_12_w01_29 (307 MB proof).
  summary.tsv  cube | kissat=UNSATISFIABLE | solve_s | drat_trim= | check_s
               | proof_bytes   (the VERIFIED verdict is in each .drat-trim.log)
  *.drat-trim.log   drat-trim log per cube ("s VERIFIED").

The twenty Matsui-bound instances behind the manuscript are: 5R at s=0..3 (4)
plus the 1-to-4R bounds at the starting indices used (16) = 20.
