# MODEL_ID — ビットスライス版 `AradiBlockCipher`（重み = AND ゲート数）の 6R 最適は 84 か（k=83 の決着）

日付: 2026-11-06 ／ 場所: `~/explore/aradi/review/modelid/` ／ 本番 SPECK・`~/speck-probe` には不介入（probe の kissat 1 本は走行中のまま）。

## 結論

**ビットスライス版 `AradiBlockCipher`（重み = AND ゲート数）の 6R 最適重みは 82。** k=83 SAT・k=82 SAT（トレイルを CLAASP の実ビットスライス CNF で固定検証）、k=81 UNSAT（T モデル無制約 kissat ＋ cube 945 本すべて UNSAT・DRAT VERIFIED）。
よって「Table 4 の 84 はビットスライス版で計算された最適値」という説明は**成立しない**。84 は S-box 版（最適 82）でもビットスライス版（最適 82）でも最適値ではなく、Table 4 の 6R は同じ定義のまま誤り。
両モデルの 6R 最適が一致（82）するのは偶然ではなく、重み 82 の状態トレイル（段別 [18,6,18,16,8,16]）が使う S-box 遷移がすべて T = DDT 重みとなる組だけで構成されているため（gate-level でも同じコストで実現できる）。

- 発見: T モデル（下記）無制約 k=83（Matsui 窓 = 証明済み bitsliced 下界）が kissat で **SAT（3,207 秒）**。
- 検証: 復号した状態トレイル（`modelid/tm6R/t6R_k83_trail.json`）を **CLAASP の実ビットスライス CNF（`AradiBlockCipher` + `SatXorDifferentialModel`）に全固定 → k=83 SAT／k=82 UNSAT**、AND 重み段別 [18, 7, 18, 16, 8, 16] = 83（`bits_fixed.py`）。
  設計者式（DDT）での重みも 83、乱数実測（2^22 組/段）≈ 83.6。
- トレイル（w‖x‖y‖z、16 進）: 平文 0‖42a12250‖0‖0 → 0‖40200200‖0‖0 → 0‖c1304288‖0‖80204000 → b0304101‖b0104101‖0‖0 → 00202120‖0‖0‖0 → 08690029‖0‖0‖0 → e4497639‖0‖e408f639‖0。
  S-box 版の 82 トレイル族（段別 [18,6,18,16,8,16]）と同形で、第 2 段だけ gate-level では 7。
- 続いて T モデル無制約 k=82 も **SAT（458 秒）**。復号トレイル（`modelid/tm6R/t6R_k82_trail.json`、段別 [18,6,18,16,8,16] = 82）を CLAASP の実ビットスライス CNF に全固定 → **k=82 SAT／k=81 UNSAT（AND 重み 82）**。同じ状態トレイルは S-box 版（DDT）でも 82（CLAASP S-box モデル固定 k=82 SAT／k=81 UNSAT）。
  平文 0‖2854044a‖0‖0 → 0‖08040040‖0‖0 → 0‖18260851‖0‖0 → 16062820‖16022820‖0‖0 → 00040424‖0‖0‖0 → 210d2005‖0‖0‖0 → 3c892ec7‖0‖1c813ec7‖0。
- k=81: T モデル無制約（窓付き）が UNSAT（4,935 秒）、cube 945 本（w0 ∈ [2,31], w01 ∈ [w0+2,49]）すべて UNSAT・drat-trim VERIFIED（§5）。→ **bitsliced 6R 最適 = 82**（下界は補題＋証明済み bitsliced 下界＋DRAT に依拠）。

## 方式

### 1. 圧縮モデル（T モデル）と同値補題

CLAASP のビットスライス版 SAT モデルは、各 Toffoli AND ゲート（1 ラウンド 4 ゲート × 32 列）に `cnf_and_differential` を置く:
hw ⇔ (Δa ∨ Δb)、hw=1 なら出力差分は自由、hw=0 なら出力差分 0。重み = Σ hw。線形層・鍵加算は決定的。

**補題.** 状態差分（平文差分と各段の round_output 差分）を固定すると、各 S-box 列の内部 AND 出力の選択は列ごとに独立で、その列の重みは
T(din, dout) = 「CLAASP の順（x^=w&y, z^=x&y, y^=w&z, w^=x&z）の 4 ゲートで din→dout を実現する最小の活性 AND 数」以上であり、T は達成可能。
よって bitsliced モデルの r 段最小重み = S-box レベルのトレイル (α₀,…,α_r) 上の Σ_i T(din_i, dout_i) の最小値。
T は 16×16 の全列挙で得る（`tmodel.py --table`）: 可能な (din,dout) は 161 組（DDT の支持 97 組を真に含む。DDT=0 の 64 組も gate-level では可能）、重みは {0:1, 2:16, 3:32, 4:112}。
DDT 支持内では常に T ≥ 4−log2(DDT)（等号でない組が多数）。**このため S-box 版の下界は bitsliced には流用できず、bitsliced 専用の下界を別途証明した。**

T モデル（`review/tmodel.py`）: `aradi_diff.py` と同じ線形層（設計者式と全 i で一致確認済み）、S-box ごとに unary の u₁..u₄、(din,dout) ごとに T の値を強制、双方向順序カウンタ、Matsui 窓。

### 2. T モデルと CLAASP ビットスライス CNF の整合（クロスチェック）

| 検査 | CLAASP bitsliced CNF | T モデル |
|---|---|---|
| 1R/2R/3R 最適（start 0..3） | 2/8/14（k=1,7,13 UNSAT を DRAT 検証、`modelid/small/summary.tsv`） | 2/8/14（k=1,7,13 UNSAT 0.1/0.8/3.0 s） |
| 4R 最適（start 0..3） | k=31 UNSAT: cube 200 本 × 4 start = **800 本すべて UNSAT・DRAT VERIFIED**（CPU 解 4.8 h＋検証 3.4 h、`modelid/run_4R_k31_s*/`）、k=32 SAT | k=31 UNSAT 19 s、k=32 SAT 5.9 s |
| 5R（start 0..3） | k=49: cube 305 本まで全 UNSAT・VERIFIED で中断（T モデルに切替、`modelid/run_5R_k49_s*/`） | k=49 UNSAT（窓=1〜4R 証明済み下界）各 46〜54 s、**DRAT VERIFIED 4 本**、k=50 SAT（`modelid/tm5R/summary.tsv`） |
| 既知の gate-level 84 トレイル（`bits_6R_k84_trail.json`、段別 [34,18,6,2,6,18]） | k=84 SAT／k=83 UNSAT（固定） | k=84 SAT／k=83 UNSAT（固定） |
| S-box 版 82 トレイル（`claasp_6R_k82_free_trail.json`） | gate-level 88 | T 重み 88（k=87 UNSAT／k=88 SAT 固定） |
| T モデル無制約 6R k=84 の解（段別 [34,18,6,2,6,18]、平文 e6d5174c‖0‖0‖0） | 固定して k=84 SAT／k=83 UNSAT（gate 重み 84） | SAT 29 s |

### 3. 下界（bitsliced 専用、すべて UNSAT＋DRAT VERIFIED）

B_bits[s][r]（開始添字 s=0..3 共通）: 1R=2, 2R=8, 3R=14, 4R=32, 5R=50。
6R の窓用: 6R ≥ 5R+1R = 52（自明）。cube 範囲: w0 ∈ [2, 83−50=33], w01 ∈ [w0+2, 83−32=51] → 1,040 cube。

### 4. 6R k=83 本番

`modelid/tm6R/t6R_k83.cnf`（63,459 変数・393,131 節・窓 20）を 1,040 cube に分割、`kissat --unsat` + DRAT、drat-trim で全数検証、21 並列（drat-trim は同時 6 本に制限、MemAvailable ガード）。
並行して無制約 k=83（窓付き、2 時間）。

k=83 cube キャンペーンは 330/1,040 cube（w0 ≤ 9 帯）まで全 UNSAT・DRAT VERIFIED の時点で、無制約 k=83 が SAT になったため停止（`modelid/run_t6R_k83/summary.tsv`、CPU 解 7.8 h＋検証 10.0 h）。
UNSAT だった cube は「w0 ≤ 9 帯には重み ≤83 の bitsliced トレイルが無い」ことの証明（発見トレイルは w0=18）。

## 5. 正確な最適値の探索（進行中）

- k=82: cube キャンペーンは 122/992 cube（w0 ≤ 4 帯）全 UNSAT・VERIFIED の時点で、無制約 k=82 が SAT になったため停止（`modelid/run_t6R_k82/`）。
- k=81: T モデル cube キャンペーン（w0 ∈ [2,31], w01 ∈ [w0+2,49] → 945 cube）、`kissat --unsat` + DRAT、21 並列（`modelid/run_t6R_k81/`）＋無制約 k=81（3 時間）。全 UNSAT なら bitsliced 6R 最適 = 82。

- 無制約 k=81（窓付き、証明なし）: **UNSATISFIABLE（kissat 4.0.4、4,935 秒）**。→ bitsliced 6R 最適 = 82（kissat 判定）。DRAT 付きの確定は cube キャンペーンで取得中。

- k=81 cube キャンペーン（`modelid/run_t6R_k81/`）: **945/945 UNSAT・DRAT VERIFIED、SAT 0・FAIL 0**。cube 集合と summary の集合は一致、各証明の sha256 を記録（`summary.tsv`: cube名／解秒／VERIFIED／sha256、`detail.tsv`: 検証秒・proof バイト・RSS）。
  CPU: 解＋証明生成 31.3 h、drat-trim 35.5 h、合計 66.8 h（壁時計 3 時間 12 分、21 並列）。最難 cube `w0_16_w01_29` 解 740 秒。証明合計 57.7 GB（検証後に削除）。drat-trim 最大 RSS 509 MB、OOM ガード発動 0 回。

## 6. 主張の依存関係（査読向け）

bitsliced 6R 最適 = 82 は次に依拠する:
1. 上界: 重み 82 の状態トレイルを **CLAASP の実ビットスライス CNF** に全固定して k=82 SAT（AND 重み 82）。ソルバ非依存の検算: 設計者式で DDT 重み 82、乱数実測 ≈82。
2. 補題（§1）: bitsliced モデルの最小重み = T モデルの最小重み。T は CLAASP の `cnf_and_differential` の意味論（hw ⇔ 入力差分活性、活性なら出力自由）を 4 ゲートに適用した全列挙。独立性は「列ごとの AND 出力が他列に影響しない」ことから従う。
3. T モデルと CLAASP bitsliced CNF の整合: 1〜4R の最適が一致（4R は CLAASP CNF 側も 800 cube DRAT）、5R は T モデルで証明（CLAASP CNF 側は 305 cube まで一致して中断）、既知トレイル 3 本の重み一致（84・88・82/83）。
4. 下界 B_bits[1..5] = 2,8,14,32,50（全開始添字）: すべて UNSAT＋DRAT。窓制約はこれらの含意なので過剰制約ではない。
5. k=81 UNSAT: 945 cube すべて DRAT VERIFIED（＋無制約 kissat の UNSAT）。
弱点として残るのは 2（補題は手証明。機械検証したければ T モデル k=81 UNSAT の代わりに CLAASP bitsliced CNF の k=81 を直接 cube+DRAT すればよいが、4R の経験では 100〜1000 倍のコスト）。

## 生成物

- `review/tmodel.py`（T モデル生成・固定・表）、`review/hybrid_bits.py`（CLAASP bitsliced の混成 CNF、`--start`）、`review/make_cubes_bits.py`、`review/cube_drat_one_6R.sh`、`review/cube_drat_sched.py`
- `modelid/T_table.txt`（T の 16×16 表）、`modelid/small/`（1〜3R）、`modelid/run_4R_k31_s*/`（4R 800 cube）、`modelid/run_5R_k49_s*/`（中断分）、`modelid/tm5R/`（5R T モデル DRAT）、`modelid/tm6R/`（6R CNF・無制約結果・k=84 トレイル）、`modelid/run_t6R_k83/`（本番 summary.tsv／detail.tsv／logs）
- `modelid/sat_lottery/`（CLAASP bitsliced CNF での k=83 SAT 方向くじ、482/2,628 本・SAT なしで中断）
