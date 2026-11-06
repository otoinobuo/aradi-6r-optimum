#!/usr/bin/env bash
# 第 1 パス完了（DONE）後、UNKNOWN cube（先行第 2 パス pass2a で試したものは除外）を優先順で第 2 パスへ
D=/home/otoi/explore/aradi/review/p2a; A=/home/otoi/explore/aradi
until [ -f $D/7R_k105/DONE ]; do sleep 30; done
if grep -q "found=None" $D/7R_k105/DONE; then
  mkdir -p $D/7R_k105_pass2/cubes
  awk -F'\t' '$2=="UNKNOWN"{print $1}' $D/7R_k105/results.tsv | python3 -c '
import sys, os
tried=set()
p="/home/otoi/explore/aradi/review/p2a/7R_k105_pass2a/results.tsv"
if os.path.exists(p): tried={l.split("\t")[0].split("_",1)[1] for l in open(p)}
names=[l.strip() for l in sys.stdin if l.strip() not in tried]
pri={6:0,18:1,8:2,16:3}
key=lambda n:(pri.get(int(n.split("_")[1]),10), int(n.split("_")[1]), int(n.split("_")[3]))
for i,n in enumerate(sorted(names,key=key)): print(f"{i:04d}_{n}")' > $D/7R_k105_pass2/order.txt
  while read nm; do ln -sf $A/cubes_7R_k105/${nm#*_}.units $D/7R_k105_pass2/cubes/$nm.units; done < $D/7R_k105_pass2/order.txt
  budget=$(( $(date -d "2026-11-06 19:52:00" +%s) - $(date +%s) )); [ $budget -lt 600 ] && budget=600
  echo "pass2 start $(date +%FT%T) cubes=$(wc -l < $D/7R_k105_pass2/order.txt) budget=$budget" >> $D/pass2.log
  nice -n 10 python3 $A/review/sat_sched.py $A/cnf/hyb_7R_k105.cnf $D/7R_k105_pass2/cubes $D/7R_k105_pass2 18 900 $budget >> $D/pass2.log 2>&1
  echo "pass2 end $(date +%FT%T) $(cat $D/7R_k105_pass2/DONE)" >> $D/pass2.log
else
  echo "pass1 found SAT; pass2 skipped" >> $D/pass2.log
fi
