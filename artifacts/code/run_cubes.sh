#!/usr/bin/env bash
# P1 用（SPECK128/12 終了後に本人 GO で実行）。cube を xargs -P で kissat --unsat に流す。
# 使い方: ./run_cubes.sh <base.cnf> <cubedir> <threads> <per-cube timeout sec> <results.tsv>
# 結果: results.tsv に  cube  status  seconds。SAT が出たら v 行を <cubedir>/<cube>.model に保存。
# 全 cube が UNSAT なら base.cnf は UNSAT（= 6R に重み ≤ k のトレイルは存在しない）。
set -u
BASE=$1; DIR=$2; P=$3; TO=$4; OUT=$5
KISSAT=${KISSAT:-$HOME/kissat/build/kissat}
export BASE DIR TO OUT KISSAT
run_one() {
  u=$1; nm=$(basename "$u" .units); tmp=$(mktemp "$DIR/tmp_${nm}_XXXX.cnf")
  nv=$(head -1 "$BASE" | awk '{print $3}'); nc=$(( $(head -1 "$BASE" | awk '{print $4}') + $(wc -l < "$u") ))
  { echo "p cnf $nv $nc"; tail -n +2 "$BASE"; cat "$u"; } > "$tmp"
  t0=$(date +%s.%N)
  res=$(timeout "$TO" nice -n "${NICE:-10}" "$KISSAT" -q --unsat "$tmp")
  rc=$?
  st=$(printf '%s\n' "$res" | awk '/^s /{print $2}'); [ -z "$st" ] && st=UNKNOWN
  [ "$st" = SATISFIABLE ] && printf '%s\n' "$res" | grep '^v ' > "$DIR/$nm.model"
  printf '%s\t%s\t%.1f\n' "$nm" "$st" "$(echo "$(date +%s.%N) - $t0" | bc)" >> "$OUT"
  rm -f "$tmp"
}
export -f run_one
ls "$DIR"/*.units | xargs -P "$P" -I{} bash -c 'run_one "$@"' _ {}
echo "done: $(grep -c UNSAT "$OUT") UNSAT / $(grep -c $'\tSATISFIABLE' "$OUT") SAT / $(grep -c UNKNOWN "$OUT") UNKNOWN of $(wc -l < "$OUT")"
