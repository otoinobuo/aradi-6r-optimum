# ARADI 6R short note — submission handoff

Prepared by Claude Code (preparation only). **Every publishing action below is performed by Nobuo Otoi.** Nothing here has been published, submitted, or pushed. Venue decided in advance: Zenodo (DOI) + IACR ePrint (short note).

## Deposit bundle (mbp `~/work/aradi-trails/`)
- `main.pdf` (6 pp) / `main.tex` (source)
- `dist/aradi-6R-artifacts.zip` = `artifacts/` (101 files; `MANIFEST.sha256` inside, 101/101 verified)

## Zenodo (DOI) — values for the deposit form
- Upload type: Publication → Preprint (attach the artifact zip as an extra file, or make a separate Software/Dataset record and cross-link — your call)
- Title: **The six-round differential optimum of ARADI is 82: a machine-checked lower bound**
- Author: **Otoi, Nobuo** — ORCID **0009-0001-1445-3612** — affiliation **ba-cybersecurity.com, Tokyo, Japan**
- Keywords: ARADI; differential cryptanalysis; lightweight block cipher; SAT; DRAT certificate; machine-checked; CLAASP; Matsui bounds; lower bound
- License: **DECISION NEEDED** (recommend CC-BY-4.0 for the paper+artifacts; code under MIT if you prefer to split)
- Related identifiers: cites arXiv/ePrint 2024/1240 (ARADI) and 2024/1324 (CLAASPing ARADI); add the GitHub URL once the repo exists; add the ePrint URL once assigned
- Version: v1
- Description: the manuscript abstract (below)

## IACR ePrint (eprint.iacr.org)
- Submit `main.pdf`; area: secret-key cryptography / cryptanalysis
- Abstract: same as below
- You perform login + submission

## GitHub (public)
- Account: `otoinobuo` (security research; not `lanchesters`)
- Suggested repo name: `aradi-6r-differential-optimum` (or `aradi-trails`)
- Contents: the whole `~/work/aradi-trails` (main.tex, main.pdf, artifacts/)
- You create the repo and push: `git remote add origin <url> && git push -u origin main`

## Bookkeeping / backups
- **gate②**: no ARADI row exists in contrib_tasks yet; `gate_approved_by` is your field to set. I can draft the contribution-task row (contribution_class / statement / stands_on / advance_over_prior / success_criterion / anti_scope / manuscript_ref / venue_plan) for you to approve — say the word.
- **copilot backup**: queued; will push local commits to the copilot bare repo when copilot is back online (offline now).
- INDOCRYPT proceedings Table 4 visual check: paywalled; stated as a limitation in the manuscript.

## Abstract (for Zenodo description / ePrint)
The automated study of the NSA block cipher ARADI by Bellini et al. (CLAASPing ARADI, INDOCRYPT 2024) reports in its Table 4 that the best single-key differential trail over six rounds has weight 84, printed in bold to denote optimality. Using the authors' own CLAASP model of ARADI we show that this value is not optimal: a single-key differential trail of weight 82 exists over six rounds, and no trail of weight 81 or less exists. The upper bound is a weight-82 trail of CLAASP's S-box model, confirmed by re-fixing it in the model and by the designers' round-function formula; CLAASP's own search returns weight-82 trails directly, and Monte-Carlo estimation agrees. The lower bound is obtained by a hybrid CNF (CLAASP's own component clauses together with a bidirectional sequential-counter encoding of the weight and Matsui-style window constraints), split by cube-and-conquer into 945 subproblems, every one of which is UNSAT; all 945 UNSAT results, together with the twenty one-to-five-round Matsui bounds they rely on, carry a DRAT certificate verified by drat-trim. The six-round optimum of 82 is therefore the first machine-checked optimal differential weight reported for round-reduced ARADI. The same weight-82 trail is also optimal under CLAASP's bit-sliced (AND-gate-count) model, whose six-round optimum we likewise show to be 82, so 84 is not optimal in either weight definition. The seven- and eight-round upper bounds of 106 and 122 in Table 4 are reproduced and thereby confirmed. We report the result as a single corrected table cell supported by a reproducible certificate, not as a break of the cipher.
