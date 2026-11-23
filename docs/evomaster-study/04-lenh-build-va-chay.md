# Lệnh build và chạy EvoMaster upstream

Ví dụ lấy từ lượt chạy ngày 2026-11-22: commit upstream `dd063b4f9f`, jar `evomaster-upstream-master-b6307c2d.jar`,
output ở `infra/em-results/upstream-b6307c2d-20261122/`.

## 1. Cập nhật mã upstream

```bash
cd /Users/minhnguyen/IdeaProjects/EvoMaster-upstream
git pull origin master
git log -1 --format='%h %ci %s'
```

`git log` in ra commit sẽ build, để ghi lại. Bỏ bước này nếu muốn giữ commit hiện tại.

## 2. Build jar

```bash
cd /Users/minhnguyen/IdeaProjects/EvoMaster-upstream
JAVA_HOME=$(/usr/libexec/java_home -v 17) mvn -f pom.xml -pl core -am package -DskipTests
```

| Phần lệnh | Nghĩa |
|---|---|
| `JAVA_HOME=$(/usr/libexec/java_home -v 17)` | Maven chạy bằng JDK 17. Không có nó, Maven của Homebrew dùng JDK 27 |
| `-f pom.xml` | File mô tả dự án |
| `-pl core -am` | Chỉ build module `core` và các module `core` phụ thuộc |
| `package` | Biên dịch rồi đóng jar |
| `-DskipTests` | Biên dịch test nhưng không chạy |

Không dùng `-Dmaven.test.skip=true`: cờ này bỏ cả biên dịch test, nên `client-java/ci-utils` không sinh jar test và
`client-java/sql` dừng với `Could not find artifact org.evomaster:evomaster-ci-utils:jar:tests:6.2.1-SNAPSHOT`.

Build mất khoảng 2,5 phút. Output trong `core/target/`:

| File | Dùng |
|---|---|
| `evomaster.jar`, ~118 MB | jar chạy được: mã EvoMaster cộng mọi thư viện |
| `evomaster-core-6.2.1-SNAPSHOT.jar`, ~13 MB | chỉ mã `core`, không chạy `java -jar` được |
| `evomaster-core-6.2.1-SNAPSHOT-tests.jar` | test của `core` đã biên dịch |
| `original-evomaster.jar` | `evomaster.jar` của lần build trước, bị thay sau mỗi lần build |

## 3. Chép jar ra tên cố định

```bash
cd /Users/minhnguyen/IdeaProjects/EvoMaster-upstream
SHA=$(shasum -a 256 core/target/evomaster.jar | cut -c1-8)
cp core/target/evomaster.jar evomaster-upstream-master-$SHA.jar
shasum -a 256 evomaster-upstream-master-$SHA.jar > evomaster-upstream-master-$SHA.jar.sha256
cat evomaster-upstream-master-$SHA.jar.sha256
```

- `shasum -a 256` tính dấu vân tay 64 ký tự hex của file. Hai file khác nhau một byte cho hai chuỗi khác hẳn.
- `cut -c1-8` lấy 8 ký tự đầu làm tên. Jar ngày 2026-11-22 cho `b6307c2d`.
- `>` ghi kết quả vào file `.sha256` thay vì in ra màn hình.
- Lần build sau ghi đè `core/target/evomaster.jar`; bản chép thì giữ nguyên.

Kiểm jar còn nguyên:

```bash
shasum -a 256 -c evomaster-upstream-master-b6307c2d.jar.sha256
```

In `OK` nếu đúng, `FAILED` nếu file đã đổi.

## 4. Chạy một lượt

Chạy từ thư mục luận văn. Mỗi lượt một thư mục output mới.

```bash
cd /Users/minhnguyen/IdeaProjects/graduational-thesis
mkdir infra/em-results/<thu-muc>
```

### reports-api bản lỗi (:8080)

```bash
curl -s -X POST http://localhost:8080/reset

JAVA_HOME=$(/usr/libexec/java_home -v 17) java -Xmx2g \
  -jar /Users/minhnguyen/IdeaProjects/EvoMaster-upstream/evomaster-upstream-master-b6307c2d.jar \
  --blackBox true \
  --bbSwaggerUrl http://localhost:8080/v3/api-docs \
  --bbTargetUrl http://localhost:8080 \
  --configPath infra/em-config/reports-auth.yaml \
  --outputFormat PYTHON_UNITTEST \
  --extraPhaseBudgetPercentage 0.6 \
  --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<thu-muc>/tests-seed1 \
  > infra/em-results/<thu-muc>/seed1.log 2>&1
```

### vampi-seeded bản lỗi (:5002)

```bash
curl -s http://localhost:5002/createdb

JAVA_HOME=$(/usr/libexec/java_home -v 17) java -Xmx2g \
  -jar /Users/minhnguyen/IdeaProjects/EvoMaster-upstream/evomaster-upstream-master-b6307c2d.jar \
  --blackBox true \
  --bbSwaggerUrl http://localhost:5002/openapi.json \
  --bbTargetUrl http://localhost:5002 \
  --configPath infra/em-config/vampi-seeded-auth.yaml \
  --outputFormat PYTHON_UNITTEST \
  --extraPhaseBudgetPercentage 0.6 \
  --ratePerMinute 120 --maxTime 150s --seed 1 \
  --outputFolder infra/em-results/<thu-muc>/tests-seed1 \
  > infra/em-results/<thu-muc>/seed1.log 2>&1
```

| Phần lệnh | Nghĩa |
|---|---|
| `curl ... /reset`, `/createdb` | Đưa dữ liệu app về trạng thái gốc trước lượt chạy |
| `JAVA_HOME=... java` | JVM 17 chạy jar. Không có nó, `/usr/bin/java` chạy JDK 21 |
| `-Xmx2g` | Heap tối đa 2 GB. Vượt thì JVM dừng với `OutOfMemoryError` |
| `--blackBox true` | Chỉ gọi API qua HTTP |
| `--bbSwaggerUrl` | Nơi lấy OpenAPI spec |
| `--bbTargetUrl` | Địa chỉ app nhận request |
| `--configPath` | Tài khoản và cách đăng nhập |
| `--outputFormat PYTHON_UNITTEST` | Ghi test ra Python `unittest` + `requests` |
| `--extraPhaseBudgetPercentage 0.6` | Pha SECURITY được 0,6 × `maxTime` = 90 s. Mặc định 0,1, tức 15 s |
| `--ratePerMinute 120` | Tối đa 120 request mỗi phút |
| `--maxTime 150s` | Thời gian pha SEARCH |
| `--seed 1` | Cố định ngẫu nhiên |
| `--outputFolder` | Nơi ghi test, `report.json`, `index.html` |
| `> seed1.log` | stdout vào file |
| `2>&1` | stderr đi theo stdout, cùng vào file |

Lượt reports-api ngày 2026-11-22 mất khoảng 6 phút: SEARCH 2m31s, MINIMIZATION 38s, SECURITY 1m47s, ADDITIONAL_ORACLES 23s.

Jar upstream không có oracle 970. Các lượt đo của luận văn thêm `--useExperimentalOracles true`; cờ này chỉ cần cho
970 trên jar của ta.

## 5. Xem log

Theo dõi khi đang chạy, ở terminal khác:

```bash
tail -f infra/em-results/<thu-muc>/seed1.log
```

Đọc sau khi chạy, bỏ mã màu và dòng tiến độ:

```bash
sed -E 's/\x1b\[[0-9;]*[A-Za-z]//g' infra/em-results/<thu-muc>/seed1.log \
  | grep -v -E 'Consumed search budget|Covered targets:|Time per test|Time since last' \
  | grep -v '^\s*$'
```

Dòng cần tìm:

| Dòng | Nghĩa |
|---|---|
| `EvoMaster version: 6.2.1-SNAPSHOT` | đúng jar upstream |
| `There are 9 usable RESTful API endpoints` | số endpoint đọc được từ spec |
| `Phase <TÊN> lasted: ...` | thời gian mỗi pha |
| `Phase 'SECURITY' has timed out after 90 seconds` | pha SECURITY dùng hết ngân sách |
| `Going to save 58 tests` | số test ghi ra |
| `Potential faults: 17` | số fault, xem chi tiết trong `report.json` |
| `EvoMaster process has completed successfully` | lượt chạy không lỗi |

Đọc `report.json` và file test: `05-doc-report-va-faults-test.md`.
