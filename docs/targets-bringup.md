# Dựng bốn target trước một đợt chạy

Trang này giữ thứ tự dựng, lệnh dựng, lệnh kiểm tay và reseed của bốn target. Lý do của từng thay đổi trên target nằm
ở doc riêng của target (cột cuối bảng §1). Chạy EvoMaster: skill `em-batch`.

## 1. Target, container, cổng

| Target | Biến thể | Container | Image | Cổng host | Doc của target |
|---|---|---|---|---|---|
| reports-api | lỗi | `reports-api` | `reports-api:latest` `7c98b63bbfc4` | 8080 | `infra/reports-api/README.md` |
| reports-api | vá | `reports-api-fixed` | cùng image, `APP_SECURITY_STATEFUL_ROLE_CHECK=true` | 8081 | như trên |
| vampi-seeded | lỗi | `vampi-seeded` | `vampi-seeded:latest` `7ba9a98ac50e`, `statefulrolecheck=0` | 5002 | `infra/vampi-seeded/THESIS-SEED.md` |
| vampi-seeded | vá | `vampi-seeded-fixed` | cùng image, `statefulrolecheck=1` | 5003 | như trên |
| pyLoad | lỗi | `pyload-vuln` | `pyload-vuln` `25451c1a1bd6` | 8090 | `docs/tier2b-pyload-target.md` §3 |
| pyLoad | vá | `pyload-fixed` | `pyload-fixed` `5e2451ab380d` | 8091 | như trên |
| artifact-keeper | lỗi `e56d3aa7e2` hoặc vá `e64cc5c608` | `artifact-keeper-dev-backend`, `artifact-keeper-dev-db` | `src-backend` `024212a16242`, `postgres:16-alpine` | 8080 | `docs/artifact-keeper-target.md` §3 |

- Image ID đọc ngày 2026-11-11 bằng `docker image inspect`. Dòng 2 của `infra/em-results/m2-wave1-20261108/progress.log`
  ghi ngày tạo image reports-api (2026-09-09) và vampi-seeded (2026-08-06), khớp hai image trên. Lượt M2 không ghi
  image của pyLoad và artifact-keeper.
- Không dựng lại image. Image thiếu thì dựng theo doc của target và ghi ID mới vào bảng này.
- Reseed, spec và file auth của từng target: bảng Targets trong skill `em-batch`.

## 2. Ràng buộc

- reports-api bản lỗi và artifact-keeper cùng dùng cổng 8080. Một lúc chỉ một trong hai chạy.
- artifact-keeper chạy một biến thể một lúc. Mã nguồn được bind-mount vào container, `cargo watch` biên dịch lúc
  khởi động.
- Đổi biến thể artifact-keeper phải reseed `full` (xoá volume DB). DB của bản vá đã lên migration 131; bản lỗi gặp DB
  đó thì backend thoát với `Error: Migration(VersionMissing(131))` (log backend ngày 2026-11-08 06:17).
- Cổng 5000 bị AirPlay của macOS giữ.
- Container pyLoad không có volume. Trạng thái do fuzzer để lại nằm trong lớp ghi của container, và `/thesis/reset`
  chỉ ghi bảng `users`. Dựng container mới từ image thì đợt chạy bắt đầu từ đúng trạng thái của image.

## 3. Thứ tự

1. artifact-keeper: kiểm tay bản lỗi, kiểm tay bản vá, trả mã về bản lỗi, tắt backend để nhả cổng 8080 (§5).
2. reports-api, vampi-seeded, pyLoad: tạo container mới, kiểm tay, reseed (§4).

Lúc chạy batch, đổi chủ cổng 8080 theo §6.

## 4. reports-api, vampi-seeded, pyLoad

Tạo container mới từ image (xoá container cũ cùng tên trước):

```bash
docker rm -f reports-api reports-api-fixed vampi-seeded vampi-seeded-fixed pyload-vuln pyload-fixed
docker run -d --name reports-api        -p 8080:8080 reports-api:latest
docker run -d --name reports-api-fixed  -p 8081:8080 -e APP_SECURITY_STATEFUL_ROLE_CHECK=true reports-api:latest
docker run -d --name vampi-seeded       -p 5002:5000 vampi-seeded:latest
docker run -d --name vampi-seeded-fixed -p 5003:5000 -e statefulrolecheck=1 vampi-seeded:latest
docker run -d --name pyload-vuln        -p 8090:8000 pyload-vuln
docker run -d --name pyload-fixed       -p 8091:8000 pyload-fixed
```

Chờ app lên và kiểm spec trả 200. pyLoad dùng spec file `infra/pyload-cve/openapi-merged.json`, nên với pyLoad lệnh
kiểm trang `/login`:

```bash
for u in localhost:8080/v3/api-docs localhost:8081/v3/api-docs localhost:5002/openapi.json localhost:5003/openapi.json \
         localhost:8090/login localhost:8091/login; do
  echo "$u $(curl -s -o /dev/null -w '%{http_code}' --retry 40 --retry-delay 2 --retry-connrefused --retry-all-errors http://$u)"
done
```

Kiểm tay, so với bảng ground truth trong doc của target:

| Target | Lệnh |
|---|---|
| reports-api | khối Manual bug-demo trong `infra/reports-api/README.md`, chạy trên 8080 rồi trên 8081 |
| vampi-seeded | khối Ground truth trong `infra/vampi-seeded/THESIS-SEED.md`, `P=5002` rồi `P=5003` |
| pyLoad | `infra/pyload-cve/verify_ground_truth.sh` |

Kiểm tay làm đổi dữ liệu (xoá report, hạ vai trò). Reseed sau khi kiểm:

```bash
curl -s -X POST localhost:8080/reset;  curl -s -X POST localhost:8081/reset
curl -s localhost:5002/createdb;       curl -s localhost:5003/createdb
curl -s -X POST localhost:8090/thesis/reset; curl -s -X POST localhost:8091/thesis/reset
```

## 5. artifact-keeper

Mọi lệnh chạy từ `infra/artifact-keeper-target/src`. Đặt:

```bash
AKR=/Users/minhnguyen/IdeaProjects/graduational-thesis/infra/em-results/artifactkeeper-20261001
```

Bản lỗi. `git status --short` chỉ có hai dòng: `M docker/Dockerfile.backend.dev` (dòng mốc `THESIS`, protoc) và
`?? docker-compose.thesis.yml`. Cổng 8080 phải trống (`docker stop reports-api`).

```bash
git log -1 --format=%h          # e56d3aa7
bash $AKR/handcheck-clean.sh    # xoá volume DB, dựng postgres + backend, bootstrap tài khoản, chạy bộ ba bằng tay
```

So các dòng `[B]` tới `[F]` với cột Bản lỗi của bảng §4 trong `docs/artifact-keeper-target.md`.

Sang bản vá:

```bash
git checkout e64cc5c608 -- backend .sqlx
bash $AKR/handcheck-clean.sh    # backend biên dịch lại hai file đổi
```

So với cột Bản vá. `git checkout <commit> -- <path>` không xoá file mà commit đích không có, nên về bản lỗi phải gỡ
ba file bản vá thêm vào:

```bash
git checkout e56d3aa7e2 -- backend .sqlx
git rm -q -f .sqlx/query-2a944759e9099f39127761ded659acc311a441431867df5193620660f3650f6a.json \
  .sqlx/query-6bf5f9d4cf1d2ac56f678839c813d886c0b3bf09bf7570fa792fe3865e23de2f.json \
  backend/migrations/131_users_privileges_changed_at.sql
git status --short              # lại đúng hai dòng như trên
bash $AKR/reseed.sh full        # DB mới cho bản lỗi; dòng cuối: victim login is_admin=True
```

Mã bản lỗi có migration 130 và 132, không có 131. DB do bản lỗi dựng không có dòng 131:

```bash
docker exec artifact-keeper-dev-db sh -c \
  'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "select count(*) from _sqlx_migrations where version=131"'   # 0
```

Nhả cổng 8080 (ghi đủ hai `-f`: zsh không tách từ một biến chứa cả hai):

```bash
docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml stop backend postgres
```

Harness artifact-keeper (`ak_vuln.sh`, `ak_fixed.sh`) tự chạy `reseed.sh full` trước mỗi seed. Harness không đổi
biến thể; đổi biến thể bằng các lệnh `git` ở trên trước khi chạy harness của biến thể đó.

## 6. Đổi chủ cổng 8080 trong đợt chạy

Trước harness artifact-keeper:

```bash
docker stop reports-api
```

Sau harness artifact-keeper:

```bash
(cd infra/artifact-keeper-target/src && docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml stop backend postgres)
docker start reports-api && curl -s -X POST localhost:8080/reset
```

## 7. Tắt hết

```bash
docker stop reports-api reports-api-fixed vampi-seeded vampi-seeded-fixed pyload-vuln pyload-fixed
(cd infra/artifact-keeper-target/src && docker compose -f docker-compose.local-dev.yml -f docker-compose.thesis.yml stop backend postgres)
```
