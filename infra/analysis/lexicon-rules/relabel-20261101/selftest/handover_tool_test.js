const fs = require("fs");
const os = require("os");
const path = require("path");
const vm = require("vm");
const { chromium } = require(process.env.PW_CORE || path.join(os.homedir(), ".hermes/hermes-agent/node_modules/playwright-core"));

const HERE = path.resolve(__dirname, "..");
const TOOL = path.join(HERE, "ban-giao", "CONG-CU-GAN-NHAN.html");
const DATA = path.join(HERE, "ban-giao", "du-lieu");
const CHROME = process.env.CHROME || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const TMP = fs.mkdtempSync(path.join(os.tmpdir(), "gannhan-"));
let fails = 0;

function check(name, ok, detail) {
  console.log((ok ? "PASS  " : "FAIL  ") + name + (detail ? "  " + detail : ""));
  if (!ok) fails++;
}

const html = fs.readFileSync(TOOL, "utf8");
const core = html.match(/<script id="core">([\s\S]*?)<\/script>/)[1];
const C = {};
vm.runInNewContext(core + "\nObject.assign(out,{parseCSV,toCSV,readTable,parseFields,validate,statusOf,exportText,importLabels,blankLabel,isCore,SRC_COLS});", { out: C });

const want = { "dot-1-thu.csv": 20, "dot-2.csv": 323, "dot-3.csv": 134 };
for (const [f, n] of Object.entries(want)) {
  const text = fs.readFileSync(path.join(DATA, f), "utf8");
  const recs = C.readTable(text, C.SRC_COLS);
  check("core doc " + f + " du so dong", recs.length === n, recs.length + "/" + n);
  let bad = 0, total = 0;
  for (const r of recs) for (const x of C.parseFields(r.truong)) { total++; if (x.bad) bad++; }
  check("core " + f + " moi dong truong tach duoc", bad === 0, "hong " + bad + "/" + total);
  check("core " + f + " doc roi ghi lai trung tung byte", C.toCSV(C.parseCSV(text)) === text);
  const stt = recs.map(r => Number(r.stt));
  check("core " + f + " stt chay 1..n", stt.every((v, i) => v === i + 1));
}

const F = C.parseFields("path:id string\nbody:role string enum[viewer|editor|admin]\nbody:name string");
const L = o => Object.assign(C.blankLabel(), o);
const has = (errs, s) => errs.some(e => e.includes(s));
check("validate: dong trong bao thieu A", has(C.validate(L({}), F), "Chưa chọn A"));
check("validate: dong core hop le khong loi", C.validate(L({ A: "existing", B: "role_set", C: "down", victim: ["path:id"], role: ["body:role"], order: "viewer<editor<admin" }), F).length === 0);
check("validate: unordered hop le", C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:role"], order: "unordered" }), F).length === 0);
check("validate: ngang muc bang = hop le", C.validate(L({ A: "self", B: "perm", C: "down", victim: ["self"], role: ["body:role"], order: "viewer=editor<admin" }), F).length === 0);
check("validate: role co enum ma order trong bi bao", has(C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:role"] }), F), "điền order"));
check("validate: order co gia tri ngoai enum bi bao", has(C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:role"], order: "viewer<owner" }), F), "không nằm trong enum"));
check("validate: order lap gia tri bi bao", has(C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:role"], order: "viewer<viewer" }), F), "lặp"));
check("validate: order sai cu phap bi bao", has(C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:role"], order: "viewer<<admin" }), F), "cú pháp"));
check("validate: order khi role khong co enum bi bao", has(C.validate(L({ A: "existing", B: "role_set", C: "down", role: ["body:name"], order: "a<b" }), F), "chỉ điền khi"));
check("validate: ba cot them khi khong du dieu kien bi bao", has(C.validate(L({ A: "group", B: "role_set", C: "down", victim: ["path:id"] }), F), "Ba cột thêm"));
check("validate: victim ngoai danh sach truong bi bao", has(C.validate(L({ A: "existing", B: "perm", C: "up", victim: ["path:uid"] }), F), "victim có trường"));
check("validate: ma la bi bao", has(C.validate(L({ A: "someone", B: "other", C: "unclear" }), F), "không có trong phiếu"));
check("validate: member_remove la ma core", C.isCore(L({ A: "existing", B: "member_remove" })));

const rows = [{ stt: "1", method: "PUT", path: "/u/{id}", fields: F }, { stt: "2", method: "POST", path: "/x,\"y\"", fields: [] }];
const labs = { "1": L({ A: "existing", B: "role_set", C: "down", U: "1", victim: ["path:id"], role: ["body:role"], order: "viewer<admin", ghi_chu: "dòng 1, có \"ngoặc\"\nvà xuống dòng" }), "2": L({ A: "none", B: "other", C: "unclear" }) };
const back = C.importLabels(rows, C.exportText(rows, labs));
check("xuat roi nap lai giu nguyen nhan", JSON.stringify(back) === JSON.stringify(labs));
let threw = "";
try { C.importLabels([{ stt: "1", method: "PUT", path: "/khac" }, rows[1]], C.exportText(rows, labs)); } catch (e) { threw = e.message; }
check("nap ket qua lech method/path bi tu choi", threw.includes("không khớp"), threw);

(async () => {
  const browser = await chromium.launch({ executablePath: CHROME, headless: true });
  const errors = [];
  const open = async ctx => {
    const page = await ctx.newPage();
    page.on("pageerror", e => errors.push(String(e)));
    page.on("console", m => { if (m.type() === "error") errors.push(m.text()); });
    page.on("dialog", d => d.accept());
    await page.goto("file://" + TOOL);
    return page;
  };
  const ctx = await browser.newContext({ acceptDownloads: true });
  let page = await open(ctx);
  const pilot = path.join(DATA, "dot-1-thu.csv");
  await page.setInputFiles("#srcIn", pilot);
  check("ui: mo dot thu hien 20 dong", (await page.locator("#list li").count()) === 20);
  check("ui: cot victim khoa khi chua du dieu kien", await page.locator('input[data-c="victim"]').first().isDisabled());

  await page.check('input[name="fA"][value="none"]');
  await page.check('input[name="fB"][value="other"]');
  await page.check('input[name="fC"][value="unclear"]');
  check("ui: dong 1 xanh sau khi chon A B C", (await page.getAttribute('#list li[data-i="0"] .dot', "class")).includes("done"));
  check("ui: tien do 1/20", (await page.textContent("#progress")).includes("Xong 1 / 20"));

  await page.click("#nextBtn");
  await page.check('input[name="fA"][value="existing"]');
  await page.check('input[name="fB"][value="role_set"]');
  await page.check('input[name="fC"][value="down"]');
  check("ui: cot victim mo khi du dieu kien", await page.locator('input[data-c="victim"][data-k="path:id"]').isEnabled());
  await page.check('input[data-c="victim"][data-k="path:id"]');
  check("ui: order khoa khi chua chon role co enum", await page.locator("#orderIn").isDisabled());
  await page.check('input[data-c="role"][data-k="body:role"]');
  check("ui: order mo khi role co enum", await page.locator("#orderIn").isEnabled());
  check("ui: dong 2 do khi thieu order", (await page.getAttribute('#list li[data-i="1"] .dot', "class")).includes("bad"));
  const chips = page.locator("#chips button");
  const v1 = await chips.nth(0).textContent(), v2 = await chips.nth(1).textContent();
  await chips.nth(0).click();
  await chips.nth(1).click();
  const order = await page.inputValue("#orderIn");
  check("ui: bam hai gia tri enum ra order v1<v2", order === v1 + "<" + v2, order);
  check("ui: dong 2 xanh khi du", (await page.getAttribute('#list li[data-i="1"] .dot', "class")).includes("done"));
  await page.check('input[name="fB"][value="other"]');
  check("ui: doi B sang ma khac thi xoa ba cot them", (await page.textContent("#vSum")) === "(trống)" && (await page.inputValue("#orderIn")) === "");
  check("ui: doi B sang ma khac thi khoa lai cot victim", await page.locator('input[data-c="victim"][data-k="path:id"]').isDisabled());
  await page.check('input[name="fB"][value="role_set"]');
  await page.check('input[data-c="victim"][data-k="path:id"]');
  await page.check('input[data-c="role"][data-k="body:role"]');
  await page.fill("#orderIn", v1 + " < " + v2);
  await page.locator("#orderIn").blur();
  check("ui: go tay order co khoang trang duoc chuan hoa", (await page.inputValue("#orderIn")) === v1 + "<" + v2);
  await page.check("#uIn");
  await page.fill("#noteIn", "thử ghi chú, có dấu phẩy");

  const [dl] = await Promise.all([page.waitForEvent("download"), page.click("#expBtn")]);
  const out = path.join(TMP, dl.suggestedFilename());
  await dl.saveAs(out);
  check("ui: ten file xuat", dl.suggestedFilename() === "ket-qua-dot-1-thu.csv", dl.suggestedFilename());
  const res = C.readTable(fs.readFileSync(out, "utf8"), ["stt", "A", "B", "C", "U", "victim", "role", "order", "ghi_chu"]);
  check("ui: file xuat co 20 dong", res.length === 20);
  check("ui: file xuat dong 1 dung nhan", res[0].A === "none" && res[0].B === "other" && res[0].C === "unclear" && res[0].U === "0" && !res[0].victim);
  check("ui: file xuat dong 2 dung nhan", res[1].A === "existing" && res[1].B === "role_set" && res[1].C === "down" && res[1].U === "1" &&
    res[1].victim === "path:id" && res[1].role === "body:role" && res[1].order === v1 + "<" + v2 && res[1].ghi_chu === "thử ghi chú, có dấu phẩy");
  const src = C.readTable(fs.readFileSync(pilot, "utf8"), C.SRC_COLS);
  check("ui: file xuat giu method/path cua tung stt", res.every((r, i) => r.stt === src[i].stt && r.method === src[i].method && r.path === src[i].path));

  await page.reload();
  await page.setInputFiles("#srcIn", pilot);
  check("ui: mo lai cung file thi khoi phuc phan da lam", (await page.textContent("#progress")).includes("Xong 2 / 20") && (await page.textContent("#msg")).includes("Đã mở lại"));

  const ctx2 = await browser.newContext({ acceptDownloads: true });
  const p2 = await open(ctx2);
  await p2.setInputFiles("#srcIn", pilot);
  check("ui: trinh duyet moi bat dau trong", (await p2.textContent("#progress")).includes("Xong 0 / 20"));
  await p2.setInputFiles("#resIn", out);
  check("ui: nap ket qua da luu tren trinh duyet moi", (await p2.textContent("#progress")).includes("Xong 2 / 20"));
  const lines = fs.readFileSync(out, "utf8").split("\r\n");
  lines[1] = lines[1].replace(/^1,(\w+),/, "1,$1,/sai");
  const badOut = path.join(TMP, "ket-qua-sai.csv");
  fs.writeFileSync(badOut, lines.join("\r\n"));
  await p2.setInputFiles("#resIn", badOut);
  check("ui: nap file ket qua khong khop bi tu choi", (await p2.getAttribute("#msg", "class")).includes("err") && (await p2.textContent("#progress")).includes("Xong 2 / 20"));

  for (const [f, n] of [["dot-2.csv", 323], ["dot-3.csv", 134]]) {
    const ctx3 = await browser.newContext();
    const p3 = await open(ctx3);
    await p3.setInputFiles("#srcIn", path.join(DATA, f));
    const cnt = await p3.locator("#list li").count();
    await p3.click("#nextBtn");
    check("ui: mo " + f + " hien du dong, chuyen dong duoc", cnt === n && (await p3.textContent(".rowhead .n")).startsWith("Dòng 2 /"), cnt + "/" + n);
    await ctx3.close();
  }
  check("ui: khong co loi JavaScript", errors.length === 0, errors.slice(0, 3).join(" | "));
  await browser.close();
  console.log("KET QUA " + (fails ? "TRUOT " + fails : "DAT"));
  process.exit(fails ? 1 : 0);
})().catch(e => { console.log("FAIL  loi chay test  " + e.message); process.exit(1); });
