#!/usr/bin/env bash
# 1 cube: base+units 再構成 → kissat --unsat <cnf> <proof> → drat-trim → summary.tsv に 1 行、proof/cnf は削除
set -u
nm=$1
A=/home/otoi/explore/aradi; D=$A/review/drat_full
BASE=$A/cnf/hyb_6R_k81.cnf; U=$A/cubes_6R_k81/$nm.units
KISSAT=$HOME/kissat/build/kissat
DT=/tmp/claude-1000/-home-otoi-explore-aradi/696d3d9c-fd8e-4655-94e1-2ae1b7081df8/scratchpad/tools/drat-trim/drat-trim
cnf=$D/tmp/$nm.cnf; proof=$D/tmp/$nm.drat
# 既に VERIFIED なら飛ばす（再開用）
grep -q "^$nm	.*	VERIFIED	" $D/summary.tsv 2>/dev/null && exit 0
nv=$(head -1 "$BASE" | awk '{print $3}'); nc=$(( $(head -1 "$BASE" | awk '{print $4}') + $(wc -l < "$U") ))
{ echo "p cnf $nv $nc"; tail -n +2 "$BASE"; cat "$U"; } > "$cnf"
t0=$(date +%s.%N)
st=$(nice -n 10 "$KISSAT" -q --unsat "$cnf" "$proof" 2>>$D/logs/$nm.err | awk '/^s /{print $2}')
t1=$(date +%s.%N)
[ -z "$st" ] && st=UNKNOWN
if [ "$st" = UNSATISFIABLE ]; then
  nice -n 10 /usr/bin/time -f "maxrss_kb=%M wall=%e" -o $D/logs/$nm.time "$DT" "$cnf" "$proof" > $D/logs/$nm.drat-trim.log 2>&1
  v=$(grep -oE 's (VERIFIED|NOT VERIFIED)' $D/logs/$nm.drat-trim.log | head -1)
  [ "$v" = "s VERIFIED" ] && res=VERIFIED || res=FAIL
else
  res=FAIL; echo "kissat status: $st" > $D/logs/$nm.drat-trim.log
fi
t2=$(date +%s.%N)
sha=$( [ -f "$proof" ] && sha256sum "$proof" | cut -c1-64 || echo -)
bytes=$( [ -f "$proof" ] && stat -c %s "$proof" || echo 0)
solve=$(printf '%.1f' "$(echo "$t1 - $t0" | bc)"); check=$(printf '%.1f' "$(echo "$t2 - $t1" | bc)")
{ flock 9
  printf '%s\t%s\t%s\t%s\n' "$nm" "$solve" "$res" "$sha" >> $D/summary.tsv
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$nm" "$st" "$solve" "$check" "$bytes" "$(cat $D/logs/$nm.time 2>/dev/null | tr '\n' ' ')" "$(date +%FT%T)" >> $D/detail.tsv
} 9>$D/.lock
rm -f "$cnf" "$proof"
