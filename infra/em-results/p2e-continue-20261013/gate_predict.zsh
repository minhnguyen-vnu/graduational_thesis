#!/usr/bin/env zsh
set -u
E=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results
M=$E/p2e-continue-20261013/merged.csv
expected_of () {
  local tier=$1 arm=$2 seed=$3 reset=$4 csv cs cd
  if [ "$reset" = "1" ]; then csv=$E/tier${tier}-reset-trials/runs.csv; cs=8; cd=9; else csv=$E/tier${tier}-trials/runs.csv; cs=7; cd=8; fi
  awk -F, -v a="$arm" -v s="$seed" -v cs="$cs" -v cd="$cd" '$1==a && $3==s {print $cs","$cd; exit}' $csv
}
logof () {
  local t=$1 a=$2 s=$3 r=$4 jar f
  jar=$(awk -F, -v t=tier$t -v a=$a -v s=$s -v r=$r '$1==t && $2==a && $3==s && $4==r {print $NF}' $M)
  f=t$t-$a-seed$s-r$r.log
  if [[ $jar == P2e* ]]; then echo "$jar $E/p2e-continue-20261013/logs/$f"
  elif [ -f $E/p2d-af2fired-probe-20261013/logs/$f ]; then echo "$jar $E/p2d-af2fired-probe-20261013/logs/$f"
  else echo "$jar $E/p2d-night-20261012/remeasure/logs/$f"; fi
}
one () {
  local t=$1 garm=$2 arm=$3 s=$4 r=$5
  local exp=$(expected_of $t $garm $s $r); local exp_st=${exp%%,*} exp_970=${exp##*,}
  local jl=($(logof $t $arm $s $r)); local log=${jl[2]}
  local obs_st=$(grep -v "proven by an attempt with" $log | grep -o "statuses [0-9?/]*" | awk '{print $2}' | paste -sd';' -); [ -z "$obs_st" ] && obs_st=NA
  local obs_970=$(awk -F, -v t=tier$t -v a=$arm -v s=$s -v r=$r '$1==t && $2==a && $3==s && $4==r {print $5}' $M)
  local v=MATCH; [ "$obs_st" != "$exp_st" -o "$obs_970" != "$exp_970" ] && v=MISMATCH
  echo "tier$t $garm s=$s r=$r jar=${jl[1]} exp=$exp_st/$exp_970 obs=$obs_st/$obs_970 $v"
}
for s in 1 2 3; do one 1 vuln vuln $s 0; done
for s in 1 2 3; do one 1 fixed fixed $s 0; done
for s in 1 2 3; do one 2 ours-vuln ours-vuln $s 0; done
for s in 1 2 3; do one 2 ours-fixed ours-fixed $s 0; done
for s in 1 2 3; do one 1 fixed-reset fixed $s 1; done
one 1 vuln-reset vuln 1 1
for s in 1 3 2; do one 2 ours-fixed-reset ours-fixed $s 1; done
one 2 ours-vuln-reset ours-vuln 15 1
one 2 ours-vuln-reset ours-vuln 1 1
