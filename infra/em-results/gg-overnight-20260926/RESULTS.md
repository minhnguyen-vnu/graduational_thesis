# Chuỗi đêm 09-26, jar `GG` — Airflow qua proxy

Jar `a6839ada5b839465` (`EvoMaster/evomaster-GG-a6839ada.jar`). `chain.sh` chạy từ 22:59. Giai đoạn 1: Airflow
seeds 1–2, lệnh giống từng cờ lượt Airflow của `selftest/gene-set-guard.sh`, trừ `--bbTargetUrl`: EvoMaster gọi
`capture_proxy.py` ở cổng 8182, proxy chuyển tới Airflow cổng 8082 và ghi mỗi request một dòng
(`airflow/seed<N>-traffic.jsonl`). Trích bằng `patch_users.py`.

Proxy đã sửa giữa seed 1 và seed 2 (23:10): bản đầu ghi thân response còn nén gzip, không đọc được và không ánh xạ
được token ra tên người gọi. Phần chuyển tiếp không đổi. Seed 1 chỉ dùng được method, path, thân request và mã.

## Seed 1

`exit=0`, 2407 request, 16 PATCH lên `/auth/fab/v1/users/*`, 5 bộ ba VOID. Mã bộ ba và dòng khôi phục trùng từng
dòng lượt `../genesetguard-chain-20260925/selftest-geneguard/airflow-seed1.log`.

Tám PATCH builder gửi sau khi chọn transition (23:17:54):

| Giờ | Path | Mã | Thân request |
|---|---|---|---|
| 23:17:56 | `/users/admin` | 403 | `email: null`, `roles: []`, `password` là object |
| 23:18:01 | `/users/admin` | 403 | `username: "D"`, `email: null`, `first_name: {}`, `roles: []` |
| 23:18:06 | `/users/victim` | 422 | `username: "ccB09"`, `first_name` là object, `roles: []` |
| 23:18:09 | `/users/victim?update_mask=` | 200 | `first_name: "3A"`, `roles: []`, `password: ""` |
| 23:18:12 | `/users/admin?update_mask=kpIrSTN49ERyX` | 403 | `username: "89"`, `roles: []` |
| 23:18:17 | `/users/victim` | 422 | `username: "OuN35SGe"`, `last_name` là object, `roles: []` |
| 23:18:20 | `/users/victim?update_mask=avAUSOTB2T` | 422 | `email: {}`, `first_name: null`, `roles: []` |
| 23:18:25 | `/users/victim` | 403 | `first_name`, `roles: []`, `password: "jM"` |

- Thân transition là thân ngẫu nhiên của `doInitialize`. Mọi lần 422 đều có một trường sai kiểu (object ở chỗ chuỗi,
  `{}` ở `email`).
- `roles` luôn là `[]`: gán `"user"` hay `"admin"` vào mảng object làm rỗng mảng.
- Lần 200 lúc 23:18:09 là dòng log `Privilege-restore accepted ... role 'administrator'`. Thân của nó gỡ mọi vai trò
  của `victim` và đặt mật khẩu rỗng.

Bản sửa: `infra/evomaster-ext/wip/transition-trim-20260926.md`.

## Seed 2

`exit=0`, 2393 request, 13 PATCH users, 2 bộ ba VOID trên nguồn
`PATCH /api/v2/dags/{dag_id}/dagRuns/{dag_run_id}/taskInstances`, cả hai nạn nhân `admin`, mã `200/403/200`
(người thao tác `victim`, `viewer` không có quyền sửa user). Ba lần khôi phục quyền cho `victim` do `admin`
(`admin`, `administrator`, `owner`) đều 422.

Proxy đã giải nén, nên đọc được thân response và người gọi. Ba PATCH `/users/victim` của `admin` lúc 23:42:04–08
đều 422, thân response nêu đúng trường sai kiểu:
`{"type":"string_type","loc":["body","email"],"msg":"Input should be a valid string","input":{"RfzgwwKDpnCBsgJ":"IZokTA",...}}`,
tương tự với `first_name`. Hai PATCH `/users/admin` của `victim` và `viewer`: 403 `Forbidden`.

## Dừng chuỗi

23:47:41, ngay sau khi seed 11 của Tier-1 bản lỗi bắt đầu: jar `TT` thay jar `GG` (`../transitiontrim-chain-20260926/`).
Seeds 11–20 của jar `GG` không có dòng nào; `runs.csv` chỉ có dòng tiêu đề.
