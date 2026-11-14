import csv, json, os, sys
import score_thi_nodup as S

D, N = S.D, S.N
REVIEW = ("opus_soat_lai", "sonnet_soat_lai")


def main():
    m2 = S.read_model(S.M2)
    mn = S.read_model(S.NEW)
    ops = {r["row_id"]: S.to_op(r) for r in (json.loads(l) for l in open(os.path.join(S.NOP, "op-thi.jsonl")) if l.strip())}
    lab = {r["row_id"]: r for r in csv.DictReader(open(os.path.join(S.NOP, "nhan-thi-cuoi.csv")))}
    after = {k for k, r in lab.items() if r["T"] == "1"}
    changed = {k for k in after if lab[k]["nguon"] in REVIEW}
    before = after - changed
    S.check(len(after) == 153 and len(changed) == 4 and len(before) == 149, "153 op T sau soat lai, 4 op doi sang T, 149 truoc")
    for name, m, feats in (("M2", m2, D.op_feats), ("bo-lap", mn, N.op_feats_nodup)):
        sc = {k: S.score(m, feats(o)) for k, o in ops.items()}
        pos = {k for k, s in sc.items() if s > 0}
        for tag, T in (("truoc", before), ("sau", after)):
            k = len(T & pos)
            lo, hi = S.cp(k, len(T))
            S.say("%-6s %-5s bat %d/%d = %.1f%%, CP 95%% %.1f-%.1f%%; diem > 0 %d, nhan N %d" % (
                name, tag, k, len(T), 100.0 * k / len(T), 100 * lo, 100 * hi, len(pos), len(pos - T)))
        S.say("%-6s 4 op doi nhan: %s" % (name, sorted("%s %.3f" % (k, sc[k]) for k in changed)))
    if S.fails:
        sys.exit(1)


main()
