import csv, os
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))

RULES = [
    ("subject-key", "theo L1", "token, key, client la chu the (§3); thao tac xoa, khoa, bat tat chinh no",
     [13, 18, 42, 43, 44, 45, 56, 57, 58, 72]),
    ("role-def", "theo L2", "truong dinh nghia quyen cua role, ca khi tao (§3)", [47, 48, 49]),
    ("perm-field", "theo L2", "truong quyet dinh quyen cua chu the", [1, 10, 12, 14]),
    ("perm-field", "theo L1", "truong quyet dinh quyen cua chu the", [9, 11, 30]),
    ("perm-scope", "theo L2", "danh sach tai nguyen ma quyen ap dung, khong phai quyen", [28]),
    ("active", "theo L2", "trang thai tai khoan cua chu the", [15, 16]),
    ("acted", "theo L2", "chu the da ton tai bi them vao quan he, doi chu, doi mat khau hoac bi sua",
     [17, 31, 34, 50, 51, 52, 53, 54, 55]),
    ("acted", "theo L1", "chu the da ton tai bi them vao quan he hoac bi sua", [38, 39, 40, 41, 63, 64, 70]),
    ("reset-target", "theo L2", "tai khoan bi dat lai mat khau; ca hai luot da gan C cho S505-0008, S606-0001",
     [35, 65, 66]),
    ("not-acted", "theo L1", "danh tinh khong bi thao tac tac dong: loi moi, phan cong nghiep vu, tai nguyen cua nguoi dung",
     [2, 3, 4, 5, 6, 7, 8, 19, 20, 21, 22, 23, 24, 25, 26, 27, 33, 36, 37, 46]),
    ("tenant", "theo L1", "khach hang la to chuc thue bao (§3 loai orgId)", [67, 68, 69]),
    ("role-single", "theo L2", "mot gia tri quyen la role (§3)", [59, 61]),
    ("role-single", "theo L1", "mot gia tri quyen la role (§3)", [71]),
    ("id-kind", "theo L2", "ten truong la dinh danh", [29, 32]),
    ("id-kind", "theo L2", "gia tri la ten nguoi dung hoac khoa nhom", [60, 62]),
]


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "disagreements.csv"))))
    decided = {}
    for code, side, why, idx in RULES:
        for i in idx:
            assert i not in decided, i
            decided[i] = (code, side, why)
    missing = [i for i in range(1, len(rows) + 1) if i not in decided]
    assert not missing, missing
    out = []
    for i, r in enumerate(rows, 1):
        code, side, why = decided[i]
        final = r["L1"] if side == "theo L1" else r["L2"]
        out.append(dict(r, n=i, final=final, rule=code, chosen=side, reason=why))
    w = csv.DictWriter(open(os.path.join(HERE, "adjudication.csv"), "w", newline=""),
                       ["n", "row_id", "field", "op", "type", "enum", "L1", "L2", "final", "chosen", "rule", "reason"],
                       extrasaction="ignore")
    w.writeheader()
    w.writerows(out)
    print(Counter(o["chosen"] for o in out))


main()
