# ARADI: the six-round differential optimum is 82

A machine-checked proof that the best single-key differential trail of the NSA block
cipher **ARADI** over **six rounds has weight 82**, not the 84 printed as optimal in
Table 4 of *CLAASPing ARADI* (E. Bellini et al., INDOCRYPT 2024 / IACR ePrint
2024/1324). Everything is computed in the authors' own CLAASP model: a weight-82 trail
exists, and no trail of weight 81 or less exists. The lower bound is a cube-and-conquer
split into **945 UNSAT subproblems, each carrying a DRAT certificate verified by
`drat-trim`**.

This is a single corrected table cell supported by a reproducible certificate — **not an
attack** on the cipher.

## Contents
- [`main.pdf`](main.pdf) — the manuscript (6 pp); source [`main.tex`](main.tex)
- [`artifacts/`](artifacts/) — code, trails, bounds, and certificate summaries
  - [`artifacts/README.md`](artifacts/README.md) — what is certified vs. supported
  - [`artifacts/REPRODUCE.md`](artifacts/REPRODUCE.md) — minimal steps to re-verify

## Archive / cite
Deposited on Zenodo with **DOI [10.5281/zenodo.24025026](https://doi.org/10.5281/zenodo.24025026)**
(concept DOI, resolves to the latest version).

Author: **Nobuo Otoi** (ba-cybersecurity.com, Tokyo, Japan), ORCID
[0009-0001-1445-3612](https://orcid.org/0009-0001-1445-3612).
