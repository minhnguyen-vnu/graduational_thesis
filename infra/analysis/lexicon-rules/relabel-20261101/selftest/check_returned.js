const fs = require("fs");
const vm = require("vm");

const [tool, src, res] = process.argv.slice(2);
const html = fs.readFileSync(tool, "utf8");
const core = html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const C = {};
vm.runInNewContext(core + "\nObject.assign(out,{parseCSV,toCSV,readTable,parseFields,validate,statusOf,exportText,importLabels,SRC_COLS});", { out: C });

const srcText = fs.readFileSync(src, "utf8");
const resText = fs.readFileSync(res, "utf8");
const rows = C.readTable(srcText, C.SRC_COLS);
const resRecs = C.readTable(resText, ["stt", "method", "path", "A", "B", "C", "U", "victim", "role", "order", "ghi_chu"]);

const srcStt = rows.map(r => r.stt);
const resStt = resRecs.map(r => r.stt);
const dup = resStt.filter((s, i) => resStt.indexOf(s) !== i);
const missing = srcStt.filter(s => !resStt.includes(s));
const extra = resStt.filter(s => !srcStt.includes(s));
console.log("dong trong file dot: " + rows.length);
console.log("dong trong file ket qua: " + resRecs.length);
console.log("stt thieu: " + (missing.length ? missing.join(",") : "0"));
console.log("stt thua: " + (extra.length ? extra.join(",") : "0"));
console.log("stt lap: " + (dup.length ? dup.join(",") : "0"));

let labels;
try {
  labels = C.importLabels(rows, resText);
  console.log("method va path khop file dot: co");
} catch (e) {
  console.log("method va path khop file dot: KHONG, " + e.message);
  process.exit(1);
}

const count = { done: 0, part: 0, bad: 0, empty: 0 };
const problems = [];
for (const r of rows) {
  const l = labels[r.stt];
  const fields = C.parseFields(r.truong);
  const st = l ? C.statusOf(l, fields) : "empty";
  count[st]++;
  if (st !== "done") {
    const errs = l ? C.validate(l, fields) : ["khong co dong ket qua"];
    problems.push(r.stt + " [" + st + "] " + r.method + " " + r.path + " :: " + errs.join(" | "));
  }
}
console.log("xong " + count.done + ", do dang " + count.part + ", loi " + count.bad + ", trong " + count.empty);
for (const p of problems) console.log("  " + p);

const reExport = C.exportText(rows, labels);
const body = resText.charCodeAt(0) === 0xFEFF ? resText.slice(1) : resText;
console.log("co BOM: " + (resText.charCodeAt(0) === 0xFEFF ? "co" : "khong"));
console.log("trung tung byte voi ban cong cu xuat lai (bo BOM): " + (reExport === body ? "co" : "khong"));
