# Bắt lỗi khi gán giá trị vào gene — duyệt 2026-09-25 00:50 ("cứ làm đi"), áp tự động sau chuỗi post-fallback

Patch `gene-set-guard-20260925.patch`, trên cây sha `00f98d29`. Hàm mới `trySetFromStringValue` trả `false` khi
`setFromStringValue` ném lỗi; thay 4 lời gọi ở `setAllRoleFieldsTo` (2), `setInQueryParamsTopLevel`, `setInParams`.
`applyDeclaredBindings` giữ nguyên: giá trị người dùng khai mà gán không được thì vẫn nên lộ ra.

Lý do: jar `PF` trên Airflow chết exit 1 (`em-results/postfallback-selftest-20260925-b/airflow-seed1.log`):
`setAllRoleFieldsTo` gặp `ObjectGene` phần tử của `roles[]`, `ObjectGene.unsafeSetFromStringValue` parse `admin`
như JSON và ném `JsonParseException`.

Ảnh hưởng: một lượt chạy chỉ khác jar `PF` khi jar `PF` đã ném lỗi ở một trong 4 chỗ này, tức là lượt đó crash.
Vì thế chuỗi chỉ chạy gate, không chạy lại seeds: các dòng seeds 1–10 của `postfallback-chain-20260925/`
không có lượt crash thì mang sang jar mới. Rủi ro: một lỗi khác ở chỗ gán gene cũng bị nuốt, không còn crash.

Self-test `selftest/gene-set-guard.sh`: jar `PF` crash trong `setAllRoleFieldsTo` (đọc log cũ); Airflow seed 1 exit 0;
không có `terminated abruptly`; có ít nhất một dòng `Privilege-restore`; Tier-1 bản lỗi 970, bản đã vá không 970.
Chuỗi: `em-results/genesetguard-chain-20260925/chain.sh`, chờ `CHAIN DONE` của chuỗi post-fallback, rồi áp,
tập rollback, build, hai self-test, gate, Vikunja, sao lưu.
