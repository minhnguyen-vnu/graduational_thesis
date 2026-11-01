#!/bin/bash
cd "$(dirname "$0")" || exit 2
set -e
OUT=ban-giao-gan-nhan-20261101
mkdir -p ban-giao/du-lieu
cp handover/pilot.csv ban-giao/du-lieu/dot-1-thu.csv
cp handover/test-queue.csv ban-giao/du-lieu/dot-2.csv
cp handover/train-queue.csv ban-giao/du-lieu/dot-3.csv
fail=0
for pair in pilot.csv:dot-1-thu.csv test-queue.csv:dot-2.csv train-queue.csv:dot-3.csv; do
  src=${pair%%:*}; dst=${pair##*:}
  want=$(grep " handover/$src\$" SEALS.txt | cut -d' ' -f1)
  got=$(shasum -a 256 "ban-giao/du-lieu/$dst" | cut -d' ' -f1)
  if [ -n "$want" ] && [ "$want" = "$got" ]; then echo "PASS  $dst trung SEALS.txt ($src)"; else echo "FAIL  $dst khong trung SEALS.txt ($src)"; fail=1; fi
done
[ $fail -eq 0 ] || exit 1
rm -rf "$OUT" "$OUT.zip"
mkdir "$OUT"
cp -R ban-giao/. "$OUT/"
zip -qrX "$OUT.zip" "$OUT"
rm -rf "$OUT"
shasum -a 256 "$OUT.zip"
unzip -l "$OUT.zip"
