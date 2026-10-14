import csv, os

HERE = os.path.dirname(os.path.abspath(__file__))

RULES = [
    ("cred", "theo L1", "tao credential moi (token, key, client, app) khong phai A (§3)",
     [7, 98, 103, 104, 123, 125, 132, 135, 136, 157, 158]),
    ("role-def", "theo L2", "truong dinh nghia quyen cua nhom quyen; §3 chi loai description/name khi tao role",
     list(range(10, 33))),
    ("subject-key", "theo L2", "client, API key, token la chu the theo §3 A; thao tac tac dong len chinh no",
     [1, 8, 9, 78, 79, 80, 81, 83, 96, 97, 105, 106, 109, 110, 111, 124, 128, 129, 133, 137, 138]),
    ("not-acted", "theo L1", "danh tinh khong bi thao tac tac dong: loi moi, xac thuc, doc, tai nguyen cua nguoi dung, thanh toan",
     [2, 4, 5, 6, 35, 36, 37, 51, 58, 59, 74, 90, 91, 92, 93, 95, 99, 112, 113, 114, 115, 118, 119, 120, 121, 122,
      130, 134, 139, 140, 141, 144, 145, 146, 147, 148, 149, 150, 153, 159, 160, 161]),
    ("acted", "theo L1", "danh tinh chu the da ton tai bi them/bo khoi quan he quyen hoac bi thao tac truc tiep",
     [3, 47, 49, 52, 53, 75, 76, 77, 87, 131, 142, 151, 152]),
    ("perm-field", "theo L1", "truong quyet dinh quyen cua chu the (thanh vien, key, client)",
     [34, 38, 39, 40, 41, 42, 43, 44, 45, 46, 48, 50, 56, 57, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73,
      85, 86, 88, 89, 107, 108, 126, 127, 156]),
    ("perm-field", "theo L2", "truong quyet dinh quyen cua chu the",
     [82, 84, 116, 117, 143, 155]),
    ("admin", "theo L1", "boolean trao quyen quan tri la admin (§3)", [33]),
    ("role-single", "theo L2", "mot gia tri quyen la role (§3)", [100]),
    ("contact-role", "theo L1", "vai tro lien he nghiep vu, khong phai quyen truy cap", [101, 102]),
    ("id-kind", "theo L1", "gia tri la dinh danh day du, khong phai ten dang nhap", [94, 154]),
]

OVERRIDE = {54: "perms/READ_ONLY/ACCOUNT_HOLDER/", 55: "perms/READ_ONLY/ACCOUNT_HOLDER/"}


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "disagreements.csv"))))
    decided = {}
    for code, side, why, idx in RULES:
        for i in idx:
            assert i not in decided, i
            decided[i] = (code, side, why)
    for i in OVERRIDE:
        decided[i] = ("order", "khac ca hai", "READ_ONLY thap nhat, ACCOUNT_HOLDER cao nhat trong enum")
    missing = [i for i in range(1, len(rows) + 1) if i not in decided]
    assert not missing, missing
    out = []
    for i, r in enumerate(rows, 1):
        code, side, why = decided[i]
        final = OVERRIDE.get(i) or (r["L1"] if side == "theo L1" else r["L2"])
        out.append(dict(r, n=i, final=final, rule=code, chosen=side, reason=why))
    w = csv.DictWriter(open(os.path.join(HERE, "adjudication.csv"), "w", newline=""),
                       ["n", "row_id", "field", "op", "type", "enum", "L1", "L2", "final", "chosen", "rule", "reason"],
                       extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
    from collections import Counter
    print(Counter(o["chosen"] for o in out))


main()
