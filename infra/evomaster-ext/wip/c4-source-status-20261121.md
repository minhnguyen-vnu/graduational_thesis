# C4 chỉ kết luận trên mã của source (đề xuất, chưa áp), 2026-11-21

Trạng thái: đã áp P1 và P3 (mục 1, 4), chưa commit; P2 chưa làm (user chưa chọn hướng; quyết sau lượt đo lại).
Mục 3 của phần dọn không làm: chuyển ba trường thành giá trị trả về cần thêm một kiểu kết quả, trái yêu cầu giữ mã và
cú pháp đơn giản.

- Review (phiên Opus 5.5, 2026-11-21): P3 tương đương mã cũ. Luật "mọi call trước source phải 2xx" bỏ oan lát có call
  vô hại đã hỏng ở lần chạy gốc (reports-api seed 11); lý do loại cách mềm ở mục "Thiết kế đã chốt" sai, vì bộ ba chép
  lát bằng `copy()` nên giữ localId và mã gốc của từng call. User chọn cách mềm: mỗi call trước source phải cùng nhóm mã
  (`code / 100`) với chính nó trong bộ ba (`callsBeforeSourceMatchTriple`). Review cũng xếp chặn: khoá nạn nhân sau
  UNCONFIRMED có thể làm reports-api mất bộ ba (P2); user cho đo lại đầy đủ luôn.
- Jar `EvoMaster/evomaster-CS2-f3412dc8.jar` (sha256 `f3412dc87f1083a3…c9c0`, `.sha256` cạnh jar), mô hình như LF.
  Bản trước, `evomaster-CS-b187061e.jar` (luật mọi call trước phải 2xx), bị thay.
- Bản vá so với cây LF: `wip/c4-source-status-20261121.patch` (một file, `RestSecurityBuilder.kt`); cả cây so với HEAD
  `2c3f281f13`: `wip/c4-source-status-20261121-tree.patch`. Diễn tập rollback trên cây LF và trên cây CS: đạt.
- Self-test `selftest/c4-source-status-20261121.sh` (stub `c4src_stub.py`, kiểm `c4src_checks.py`, so dòng builder
  `c4src_compare.py`). Mỗi mode chạy jar CS và jar LF; mode `op-refused` kiểm nhánh transition 403 rồi đổi operator.
  Phần hồi quy chạy lại `logic-fix-20261118.sh` trên jar CS và so từng dòng quyết định của builder với lượt LF đã lưu
  (`em-results/logic-fix-selftest-20261118-014908/`). Kết quả jar CS2: `em-results/c4-source-status-selftest-20261121-170956.out`,
  57 PASS / 0 FAIL, exit 0; thêm mode `value-reject` (transition 400 rồi 200), `prior-harmless` (call trước hỏng ở cả
  bộ ba lẫn probe; jar CS cũ trượt mode này), kiểm mở khoá nạn nhân ở `source-200`. Khả năng trượt: đổi chỗ output hai jar làm 9 kiểm trượt; so lượt
  jar ND với lượt LF làm 12/12 mode trượt.
- Nhánh transition không có mã và nhánh 3xx không có mode nào chạy qua; tương đương với mã cũ chỉ bằng đọc mã
  (cả hai trả `NEXT`, không bật `victimRefused`).

## Lỗ trên jar LF

`reLoginProbeConfirmsPrivilegeRemoved` (`RestSecurityBuilder.kt`) đọc mã của call cuối có mã mà nạn nhân gửi
(`lastVictimStatus`), không đọc mã của source.

- Lỗ A. Call tạo tài nguyên trước source bị từ chối với token mới; `AbstractRestFitness.kt:1154–1162` đặt
  `stopping = true`, source không được gửi; 403 đến từ call tạo. C4 xác nhận nạn nhân mất một quyền ghi, chưa xác nhận
  source đòi đúng quyền đó. Sai theo chiều FP.
- Lỗ B. Call trước source không phải call tạo nên chuỗi không dừng; call đó bị từ chối, source chạy thiếu trạng thái và
  nhận 403 vì lý do khác vai trò. Sai theo chiều FP.
- Đếm trên jar LF: `infra/em-results/lf-wave1-20261118/c4_slices.py`, `c4_slices.out`.

## Thiết kế đã chốt

1. Lần đăng nhập lại chạy lại cả lát với token mới. Mọi call trước source phải 2xx (call không có mã tính là trượt) và
   source phải có mã; không thì INCONCLUSIVE, hàm gọi bỏ bộ ba với nhãn UNCONFIRMED (đường bỏ sẵn có).
   Source 2xx: false. Source khác 403: INCONCLUSIVE.
2. Đối chứng ẩn danh: cùng lát, các call trước giữ auth như lần đăng nhập lại, chỉ source gửi `HttpWsNoAuth`. Các call
   trước phải 2xx, source phải có mã và khác 403; không thì INCONCLUSIVE.
3. Xoá `lastVictimStatus`; bỏ tham số `victim` của `reLoginProbeConfirmsPrivilegeRemoved` và sửa chỗ gọi.
4. Thêm `callsBeforeSourceAllowed(run, ei)`.
5. Sửa comment `THESIS` của C4 cho khớp mã mới.

Cách mềm hơn (mỗi call trước cùng mã như lần chạy gốc) bị loại: lát không mang mã gốc.

Còn hở sau sửa: call trước 2xx với token mới nhưng tạo trạng thái khác bản gốc. Ghi thành hạn chế.

Cần xét cùng lúc: nạn nhân của bộ ba UNCONFIRMED vẫn bị khoá đến hết ứng viên (`privilegeReducedInPhase`), và source
PUT chạy trước POST (`guardedSources`). Một lát bị bỏ vẫn tiêu một nạn nhân.

## Mã đề xuất

```kotlin
            val confirmed = reLoginProbeConfirmsPrivilegeRemoved(victimSlice)
```

```kotlin
    private fun reLoginProbeConfirmsPrivilegeRemoved(victimSlice: RestIndividual): Boolean? {

        val probe = victimSlice.copy() as RestIndividual
        probe.modifySampleType(SampleType.SECURITY)
        val ei = fitness.computeWholeAchievedCoverageForPostProcessing(probe)
            ?: return reLoginProbeInconclusive("the probe could not be evaluated")
        if (!callsBeforeSourceAllowed(probe, ei)) {
            return reLoginProbeInconclusive("a call before the source of the replayed slice was not 2xx")
        }
        val sourceCode = statusIn(ei, probe.seeMainExecutableActions().last())
            ?: return reLoginProbeInconclusive("the source of the replayed slice recorded no status code")

        if (StatusGroup.G_2xx.isInGroup(sourceCode)) {
            return false
        }
        if (sourceCode != 403) {
            return reLoginProbeInconclusive("re-logging the victim in ended in $sourceCode on the source")
        }

        val control = victimSlice.copy() as RestIndividual
        control.modifySampleType(SampleType.SECURITY)
        control.seeMainExecutableActions().last().auth = HttpWsNoAuth()
        val cei = fitness.computeWholeAchievedCoverageForPostProcessing(control)
            ?: return reLoginProbeInconclusive("the anonymous control could not be evaluated")
        if (!callsBeforeSourceAllowed(control, cei)) {
            return reLoginProbeInconclusive("a call before the source of the anonymous control was not 2xx")
        }
        val anonymousCode = statusIn(cei, control.seeMainExecutableActions().last())
        LoggingUtil.getInfoLogger().info(
            "Stateful-authorization anonymous control: ${control.seeMainExecutableActions().last().getName()}" +
                "=${anonymousCode ?: "-"}"
        )
        if (anonymousCode == null) {
            return reLoginProbeInconclusive("the source sent without credentials recorded no status code")
        }
        if (anonymousCode == 403) {
            return reLoginProbeInconclusive("the source sent without credentials also ended in 403")
        }
        return true
    }

    private fun callsBeforeSourceAllowed(run: RestIndividual, ei: EvaluatedIndividual<RestIndividual>): Boolean {
        val actions = run.seeMainExecutableActions()
        for (i in 0 until actions.size - 1) {
            val code = statusIn(ei, actions[i]) ?: return false
            if (!StatusGroup.G_2xx.isInGroup(code)) {
                return false
            }
        }
        return true
    }
```

## Dọn cùng đợt: cấm cặp và rẽ nhánh theo mã transition

Mục 1, 3, 4 không đổi hành vi; cần self-test cho thấy mọi nhánh ra cùng kết quả như trước. Mục 2 đổi hành vi.

1. `refusedTransitionVictims` chứa ba lý do dưới một tên: transition từ chối mọi lần thử (`buildStatefulAuthzTriple`,
   qua `victimRefused`), source trả 401/403 cho nạn nhân (`tryReducedRoles`), transition trả 404
   (`executeStatefulAuthzTriple`). Lý do thứ hai không liên quan transition. Đổi tên hoặc tách lý do.
2. Khoá theo source 401/403 cấm nạn nhân trên mọi source của transition đó. Đúng trên reports-api (403 nghĩa là không
   ADMIN); app khác có thể 403 ở PUT mà vẫn làm được POST. Xét khoá theo (source, nạn nhân).
3. `victimRefused`, `lastSourceCode`, `lastTransitionCode` là trường của class dùng làm giá trị trả về giữa
   `tryReducedRoles` và `buildStatefulAuthzTriple`. Cho `tryReducedRoles` trả chúng qua giá trị trả về.
4. `tryReducedRoles` rẽ nhánh theo mã transition ở bốn chỗ rời nhau (2xx, 404 qua tập cấm, 401/403 hoặc từ chối giá trị,
   từ chối giá trị lần nữa); `transitionRejectedRoleValue()` đọc `lastTransitionCode` thay vì nhận mã. Gom thành một
   `when (code)`:

   | Mã transition (source 2xx) | Đánh dấu từ chối | Bước sau |
   |---|---|---|
   | 2xx | không | `STOP_VICTIM` |
   | 404 | không (cặp đã vào tập cấm) | `STOP_VICTIM` |
   | 401, 403 | có | `NEXT` (operator kế) |
   | 4xx/5xx khác | có | giá trị vai trò kế, cùng operator |
   | null, 3xx | không | `NEXT` |

## Kịch bản sửa (chờ user duyệt)

Ba bản vá, mỗi bản một biến:

| Bản vá | Nội dung | Đổi hành vi |
|---|---|---|
| P1 | C4 chỉ kết luận trên source (mục "Thiết kế đã chốt") | có |
| P2 | Giảm hiệu ứng khoá nạn nhân sau UNCONFIRMED | có; chọn sau bước 5 |
| P3 | Dọn mục 1, 3, 4 ở trên | không |

Mục 2 của phần dọn đổi hành vi nên không vào đợt này; ghi thành hạn chế.

0. Kiểm cây: `git -C EvoMaster diff` trùng byte với `wip/logic-fix-20261118-tree.patch`; jar LF đúng sha256.
1. Diễn tập rollback trên cây LF (skill `evomaster-build`).
2. P3, nếu user chọn làm: viết mã, đưa ra xem, chờ OK. Dựng jar. Self-test so chuỗi log builder của jar mới với jar LF
   trên cùng stub và cùng seed, theo khuôn `refactor-simplify-20261027.sh` (`refactor_compare.py`); khác một dòng là trượt.
3. P1: áp mã đã duyệt trong note, sửa comment `THESIS` của C4. Dựng jar, lưu `evomaster-CS-<sha8>.jar` và `.sha256`,
   lưu `wip/c4-source-status-20261121.patch` (so với cây trước P1) và `-tree.patch`. Diễn tập rollback lại.
4. Self-test `selftest/c4-source-status.sh`: stub mới, mỗi mode một kiểm, chạy cả jar mới và jar LF.

   | Mode stub | Jar mới | Jar LF |
   |---|---|---|
   | `len1`: lát chỉ có source | `anonymous control`, `Constructed` | như jar mới |
   | `chain`: POST tạo (đòi admin) rồi PUT source | `INCONCLUSIVE: a call before the source ...`, `UNCONFIRMED` | `Constructed` |
   | `prior-noncreate`: call trước không phải call tạo, bị từ chối; source 403 vì thiếu trạng thái | `UNCONFIRMED` | `Constructed` |
   | `anon-prefix`: stub ghi header từng request | lần ẩn danh: call trước mang Bearer, source không | mọi call không Bearer |
   | `source-200`: token mới vẫn 2xx ở source | `UNCONFIRMED`, nạn nhân được mở khoá | như jar mới |

   Mode `chain`, `prior-noncreate`, `anon-prefix` phải cho jar LF khác jar mới; không khác là trượt. Test in các dòng mã
   mới nó chạy qua.
5. Agent mới review bản vá (khi user đồng ý giao). Sau đó đo nhanh reports-api bản lỗi và bản vá, seeds 1–10, để quyết
   P2. Luật dừng viết vào `PROTOCOL.md` trước lượt chạy. Không ghi kết quả mong đợi.
6. P2 nếu cần: thiết kế, duyệt, self-test riêng như bước 4.
7. Đo lại đầy đủ 98 hàng ở phiên khác, một jar cho cả bốn target.
8. Sau khi có số: `docs/results.md`, `infra/evomaster-ext/jars.md`, `infra/evomaster-ext/README.md`,
   `docs/metamorphic-authz-relations.md` §5.6, chương luận văn. Commit khi user yêu cầu.
