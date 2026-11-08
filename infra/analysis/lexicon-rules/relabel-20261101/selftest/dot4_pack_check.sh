#!/bin/bash
cd "$(dirname "$0")/.." || exit 2
P=ban-giao-dot4
fail=0
node -e '
const fs=require("fs"),vm=require("vm");
const html=fs.readFileSync(process.argv[1],"utf8");
const core=html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];const C={};
vm.runInNewContext(core+"\nObject.assign(out,{readTable,parseFields,statusOf,blankLabel,SRC_COLS});",{out:C});
const recs=C.readTable(fs.readFileSync(process.argv[2],"utf8"),C.SRC_COLS);
let bad=0;const where=new Set();
for(const r of recs)for(const x of C.parseFields(r.truong))if(x.bad){bad++;where.add(r.stt);}
const r188=recs.find(r=>r.stt==="188");
const l=Object.assign(C.blankLabel(),{A:"existing",B:"other",C:"unclear"});
const st=C.statusOf(l,C.parseFields(r188.truong));
let f=0;
const ck=(ok,m)=>{console.log((ok?"PASS":"FAIL")+"  "+m);if(!ok)f++;};
ck(recs.length===823,"cong cu doc dot-4.csv: "+recs.length+" dong");
ck(recs.every((r,i)=>+r.stt===i+1),"stt lien tuc 1.."+recs.length);
ck(bad===2&&where.size===1&&where.has("188"),"truong khong doc duoc: "+bad+", chi o dong "+[...where].join(","));
ck(st==="done","dong 188 van gan xong duoc: "+st);
process.exit(f?1:0);
' "$P/CONG-CU-GAN-NHAN.html" "$P/du-lieu/dot-4.csv" || fail=1
for n in 2 3; do
  out=$(node selftest/check_returned.js "$P/CONG-CU-GAN-NHAN.html" "$P/da-gan/dot-$n.csv" "$P/da-gan/ket-qua-dot-$n.csv")
  echo "$out" | grep -q "stt thieu: 0" && echo "$out" | grep -q "stt thua: 0" && echo "$out" | grep -q "stt lap: 0" \
    && echo "$out" | grep -q "method va path khop file dot: co" && echo "$out" | grep -q "loi 0, trong 0" \
    && echo "$out" | grep -q "trung tung byte voi ban cong cu xuat lai (bo BOM): co" \
    && echo "PASS  da-gan dot $n: $(echo "$out" | grep '^xong')" || { echo "FAIL  da-gan dot $n"; echo "$out"; fail=1; }
done
exit $fail
