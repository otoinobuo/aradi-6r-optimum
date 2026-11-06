# 945 cube 全数 DRAT 検証 — 結果（6R k=81 混成 CNF の下界、証明付き）

日付: 2026-11-06 11:46 〜 13:39 JST（壁時計 1 時間 54 分。最初の 1 時間は 6 並列、以後 18 並列＋メモリ監視）。

| 項目 | 値 |
|---|---|
| cube 数 | 945（`cubes_6R_k81/*.units` の集合と `summary.tsv` の集合が一致、重複なし） |
| kissat 判定 | 945 / 945 UNSATISFIABLE |
| drat-trim | **945 VERIFIED / 0 FAIL** |
| 総 CPU 時間 | 80,889 秒 = **22.47 時間**（解＋証明生成 11.88 h、drat-trim 検証 10.59 h） |
| 最難 cube | `w0_12_w01_29`: 解 286.0 秒、検証 260.9 秒、証明 307 MB、drat-trim 最大 RSS 490 MB |
| 証明の総量 | 36.3 GB（検証後に都度削除。各証明の sha256 は `summary.tsv` に記録） |
| メモリ | MemAvailable は常時 7.6〜9.3 GB、抑制（起動停止／SIGSTOP）の発動 0 回 |

手順（1 cube）: `cnf/hyb_6R_k81.cnf` ＋ `cubes_6R_k81/<cube>.units` を `run_cubes.sh` と同じ連結で再構成 → `kissat -q --unsat <cnf> <proof>`（binary DRAT、kissat 4.0.4）→ `drat-trim <cnf> <proof>`（marijnheule/drat-trim、`-D_GNU_SOURCE` ビルド）→ `s VERIFIED` を確認、sha256 を記録、proof と cnf を削除。
スクリプト: `review/drat_full_one.sh`（1 cube）、`review/drat_full_sched.py`（メモリ監視付きスケジューラ、最大 18 並列）、初期 6 並列は `review/drat_full_run.sh`。

ファイル: `summary.tsv`（cube名／解秒／VERIFIED|FAIL／proof sha256）、`detail.tsv`（kissat 判定／解秒／検証秒／proof バイト／drat-trim の最大 RSS と壁時計／時刻）、`logs/<cube>.drat-trim.log`（drat-trim 全出力）、`sched.log`、`run.log`。

結論: 混成 CNF（CLAASP 部品節 ＋ 双方向順序カウンタ ＋ Matsui 窓、重み ≤ 81）は 945 cube すべてで UNSAT が**機械検証済み**。
Matsui 境界 B_s[1..5]（s=0..3）の UNSAT も DRAT 済み（`review/drat5R`, `review/drat_small`）なので、6R 単一鍵差分の最適重み 82 の下界は証明付きで固まった。
