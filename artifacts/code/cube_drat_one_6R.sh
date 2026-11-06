#!/usr/bin/env bash
# cube_drat_one.sh <base.cnf> <cubedir> <outdir> <cube>: base+units → kissat --unsat + DRAT → drat-trim → summary.tsv。SAT なら model 保存。
set -u
BASE=$1; CD=$2; D=$3; nm=$4
KISSAT=$HOME/kissat/build/kissat
DT=/tmp/claude-1000/-home-otoi-explore-aradi/696d3d9c-fd8e-4655-94e1-2ae1b7081df8/scratchpad/tools/drat-trim/drat-trim
mkdir -p $D/tmp $D/logs
grep -q "^$nm	.*	\(VERIFIED\|SAT\)	" $D/summary.tsv 2>/dev/null && exit 0
cnf=$D/tmp/$nm.cnf; proof=$D/tmp/$nm.drat; U=$CD/$nm.units
nv=$(head -1 "$BASE" | awk '{print $3}'); nc=$(( $(head -1 "$BASE" | awk '{print $4}') + $(wc -l < "$U") ))
{ echo "p cnf $nv $nc"; tail -n +2 "$BASE"; cat "$U"; } > "$cnf"
t0=$(date +%s.%N)
nice -n 10 "$KISSAT" -q --unsat "$cnf" "$proof" > $D/tmp/$nm.out 2>>$D/logs/$nm.err
st=$(awk '/^s /{print $2}' $D/tmp/$nm.out); [ -z "$st" ] && st=UNKNOWN
t1=$(date +%s.%N); res=FAIL; sha=-; bytes=0
if [ "$st" = UNSATISFIABLE ]; then
  # drat-trim は proof サイズに比例して RAM を食うので、同時実行数を DT_SLOTS 本に制限（flock セマフォ）
  SL=/home/otoi/explore/aradi/review/modelid/.dtslots; mkdir -p $SL; DT_SLOTS=${DT_SLOTS:-6}; got=0
  while [ $got = 0 ]; do for i in $(seq 0 $((DT_SLOTS-1))); do exec {fd}>$SL/slot$i; if flock -n $fd; then got=1; break; fi; exec {fd}>&-; done; [ $got = 0 ] && sleep 3; done
  nice -n 10 /usr/bin/time -f "maxrss_kb=%M wall=%e" -o $D/logs/$nm.time "$DT" "$cnf" "$proof" > $D/logs/$nm.drat-trim.log 2>&1
  flock -u $fd; exec {fd}>&-
  grep -qE 's VERIFIED' $D/logs/$nm.drat-trim.log && res=VERIFIED
  sha=$(sha256sum "$proof" | cut -c1-64); bytes=$(stat -c %s "$proof")
elif [ "$st" = SATISFIABLE ]; then
  res=SAT; grep '^v ' $D/tmp/$nm.out > $D/$nm.model
fi
t2=$(date +%s.%N)
{ flock 9
  printf '%s\t%.1f\t%s\t%s\n' "$nm" "$(echo "$t1 - $t0" | bc)" "$res" "$sha" >> $D/summary.tsv
  printf '%s\t%s\t%.1f\t%.1f\t%s\t%s\t%s\n' "$nm" "$st" "$(echo "$t1 - $t0" | bc)" "$(echo "$t2 - $t1" | bc)" "$bytes" "$(cat $D/logs/$nm.time 2>/dev/null | tr '\n' ' ')" "$(date +%FT%T)" >> $D/detail.tsv
} 9>$D/.lock
rm -f "$cnf" "$proof" $D/tmp/$nm.out
