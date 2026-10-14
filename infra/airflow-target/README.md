# Target Airflow — CVE-2026-82310 (kiểm tay, chưa chạy máy)

Kết quả và số liệu: `../analysis/cve-survey/airflow-handcheck-20260920.md`.
Log từng bước: `../em-results/airflow-handcheck-20260919-235138/`.

## Dựng

```
docker build --build-arg FAB_VERSION=3.8.1 -t airflow-fab-vuln .
docker build --build-arg FAB_VERSION=3.9.0 -t airflow-fab-fixed .
docker run -d --name airflow-vuln -p 8082:8080 \
 -e AIRFLOW__CORE__AUTH_MANAGER=airflow.providers.fab.auth_manager.fab_auth_manager.FabAuthManager \
 -e AIRFLOW__API_AUTH__JWT_SECRET=thesis-airflow-jwt-secret \
 -e AIRFLOW__CORE__LOAD_EXAMPLES=False \
 airflow-fab-vuln bash -c "airflow db migrate && airflow fab-db migrate && \
   airflow users create -u admin -p adminpass -f a -l a -r Admin -e a@x.com && \
   airflow users create -u victim -p victimpass -f v -l v -r Op -e v@x.com && airflow api-server"
```

Cổng 8082 bản dính, 8083 bản vá. Mật khẩu ở đây là dữ liệu thử của target, không phải bí mật thật.

## Hai file spec

- Core API: `curl localhost:8082/openapi.json`, 88 path.
- API của FAB auth manager: gói cài sẵn, chép ra `fab-openapi-3.8.1.yaml`, 8 path, có
  `PATCH /auth/fab/v1/users/{username}` và `POST /auth/token`.

EvoMaster nhận một spec. Muốn chạy máy thì phải ghép hai file này; bản ghép là của ta, phải khai.

## Script

`probe.sh` bộ ba hạ vai trò kèm restart, `a1probe.sh` bản ngắn, `../em-results/airflow-handcheck-*/window.sh`
đo cửa sổ cache, `cve.sh` đường `active=0`.

## Sai lệch đã khai

`airflow-merged-nodelete.json` bỏ `DELETE /auth/fab/v1/users/{username}` và `DELETE /auth/fab/v1/roles/{name}`
khỏi spec ghép. Lý do: trong lần chạy thử 2026-09-20 00:05 fuzzer xoá chính hai tài khoản nó đang dùng, log ghi
`Failed to login for admin` rồi `No auth token for admin`, nên không còn chứng chỉ để dựng bộ ba. Airflow không có
endpoint reset như Tier-1. Việc bỏ hai operation này là của ta, phải viết vào phần hạn chế.
