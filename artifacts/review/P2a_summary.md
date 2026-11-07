# P2a — SAT-direction search for S-box trails below the Table-4 7R/8R entries (result: inconclusive within budget)

Target: CLAASP S-box model (hybrid CNF = CLAASP component clauses + bidirectional
sequential counter + Matsui windows), single-key, `start=0`. Goal: find a trail
lighter than the Table-4 entries — weight ≤ 105 at seven rounds, ≤ 121 at eight
rounds. This was **not** a certified optimality (UNSAT) search; a search that
finds nothing is *inconclusive*, **not** a confirmation of Table 4.

## Result (one line each)

- **7R: no trail of weight ≤ 105 was found within the time budget (6 h wall,
  up to 18-way, 111.6 CPU-hours) → "k ≤ 105 undecided".** 0 SAT.
- **8R: no trail of weight ≤ 121 was found within the time budget (4 h wall,
  5-way, 20.0 CPU-hours) → "k ≤ 121 undecided".** 0 SAT; only ~1/3 of the cubes
  were attempted.

## Setup

| | 7R | 8R |
|---|---|---|
| bounds.json | adds 6R: `s=0`: 82 (certified), `s=1..3`: 52 (= `B_s[5]+2`, proven lower bound) | further adds 7R: `s=0`: 84, `s=1..3`: 54 (= 6R lower bound + 2) |
| CNF | `cnf/hyb_7R_k105.cnf` (104,964 vars, 406,288 clauses, 27 windows) | `cnf/hyb_8R_k121.cnf` (135,212 vars, 525,980 clauses, 35 windows) |
| cubes | `make_cubes.py --split2` → 1,378 (`w0∈[2,53]`, `w01∈[w0+2,55]`), ascending | 2,211 (`w0∈[2,67]`, `w01∈[w0+2,69]`), priority `w0=6,18,8,16,2` then ascending |
| solver | kissat 4.0.4 (default settings, no `--unsat`), nice 10 | same |
| budget | pass 1: 240 s/cube, 18-way; pass 2 (undecided only, priority `w0=6,18,8,16`): 900 s/cube, 18-way; 6 h total | 180 s/cube, 5-way, 4 h total |
| unconstrained | hybrid k=105 and bare CLAASP k=105, 2 h each → both undecided | (none) |

## 7R k=105

| Pass | Cubes | UNSAT | Undecided | SAT | CPU s |
|---|---|---|---|---|---|
| pass 1 (240 s) | 1,378 | 786 | 592 | 0 | 197,893 |
| pass 2 (900 s; 278 of the 592 undecided, by priority) | 278 | 143 | 135 | 0 | 189,578 |
| unconstrained ×2 (7,200 s) | 2 | 0 | 2 | 0 | 14,400 |
| **total** | | **929 UNSAT, 449 undecided** | | **0** | **401,871 (111.6 h)** |

After both passes, `w0 ≤ 7` and `w0 ≥ 41` are entirely UNSAT (so any weight-≤105
7R trail would have first-round weight in 8..40 — a kissat verdict, not a DRAT
proof). The undecided cubes concentrate in the `w0 = 10..30` bands. Priority band
`w0=6` (14 cubes) went fully UNSAT in pass 2; `w0=18` (24) is 10 UNSAT / 14
undecided.

## 8R k=121

| Cubes | UNSAT | Undecided | SAT | Not started | CPU s |
|---|---|---|---|---|---|
| 749 / 2,211 | 398 | 351 | 0 | 1,462 | 71,986 (20.0 h) |

Per `w0` band (UNSAT/undecided): 2: 64/2, 3: 64/1, 4: 53/11, 5: 52/11, 6: 38/24,
7: 38/23, 8: 19/41, 9: 19/40, 10: 14/44, 11: 13/44, 12: 2/30 (partial), 16: 11/41,
18: 11/39. `w0 ≥ 13` (except 12, 16, 18) not started.

## How to read this

- "Undecided" = neither SAT nor UNSAT within budget. The absence of a SAT does
  **not** mean no trail of weight ≤ 105 / ≤ 121 exists.
- Many `w0 = 10..30` cubes do not settle even at 900 s, so finding a ≤105 7R
  trail would need (a) a longer budget on that band, (b) a structured seed (e.g.
  extend the 6R weight-82 profile `[18,6,18,16,8,16]` by one round and fix it),
  or (c) bare CLAASP k=105 run for much longer.
- By contrast the 6R weight-82 SAT appeared in 141–173 s unconstrained / 7 s per
  cube, whereas 7R k=105 did not appear even in 2 h unconstrained. Table-4's 7R =
  106 may well be optimal, but this search decides neither way.
- The 8R budget was small and 2/3 of the cubes were never attempted; this is only
  a light probe.

## Artifacts

- `cnf/hyb_7R_k105.*`, `cnf/hyb_8R_k121.*`, `cubes_7R_k105/`, `cubes_8R_k121/`,
  `bounds.json` (6R/7R rows added; the ≤6R CNFs are byte-identical and unchanged;
  original was `bounds_6R_campaign.json`).
- `review/p2a/7R_k105/results.tsv`, `review/p2a/7R_k105_pass2/results.tsv`,
  `review/p2a/8R_k121/results.tsv` (cube / status / seconds), each `sched.log`,
  `review/p2a/pass2.log`.
- `review/p2a/hyb_7R_k105_free.time`, `review/p2a/claasp_7R_k105_free.json`
  (the 2 h unconstrained runs, undecided).
- Scripts: `review/sat_sched.py` (SAT-direction cube scheduler, memory-guarded),
  `review/p2a_pass2.sh`.
