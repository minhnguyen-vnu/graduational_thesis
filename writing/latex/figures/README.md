# Danh mục Hình vẽ & Sơ đồ Khóa luận (Thesis Figures Catalog)

Thư mục này chứa toàn bộ mã nguồn vector định dạng **TikZ (`.tex`)** và mã **Mermaid** trực quan tương ứng cho các hình vẽ trong Khóa luận tốt nghiệp.

---

## 1. Danh sách các file hình vẽ vector TikZ

| STT | Tên file TikZ | Mã hình | Tiêu đề hình vẽ trong Khóa luận | Chương |
| :---: | :--- | :---: | :--- | :---: |
| 1 | [`fig_1_1_stateful_authz_flaw.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_1_1_stateful_authz_flaw.tex) | **Hình 1.1** | Minh họa vòng đời lỗ hổng phân quyền có trạng thái (A1) | Chương 1 |
| 2 | [`fig_2_1_evomaster_pipeline.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_2_1_evomaster_pipeline.tex) | **Hình 2.1** | Kiến trúc tổng thể và chu trình sinh test của EvoMaster với Pha Security mở rộng | Chương 2 |
| 3 | [`fig_3_1_triple_sequence.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_3_1_triple_sequence.tex) | **Hình 3.1** | Sơ đồ chuỗi thực hiện bộ ba `[source / transition / follow-up]` và kích hoạt Oracle 970 | Chương 3 |
| 4 | [`fig_3_2_mr_a1_state_space.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_3_2_mr_a1_state_space.tex) | **Hình 3.2** | Không gian chuyển trạng thái phân quyền và Quan hệ kiểm thử suy biến MR-A1 | Chương 3 |
| 5 | [`fig_3_3_transition_inference.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_3_3_transition_inference.tex) | **Hình 3.3** | Quy trình nhận diện và xếp hạng Transition tự động từ đặc tả OpenAPI | Chương 3 |
| 7 | [`fig_4_1_evomaster_integration.tex`](file:///c:/KLTN/graduational_thesis/thesis/figures/fig_4_1_evomaster_integration.tex) | **Hình 4.1** | Sơ đồ cấu trúc các module mở rộng tích hợp trong mã nguồn EvoMaster | Chương 4 |

> **Lưu ý.** Các hình đều là sơ đồ TikZ. Ba tệp hình cũ (Hình 3.4 về D1, Hình 5.1 và 5.2) đã gỡ khỏi bản thảo ngày 2026-10-26.

---

## 2. Cách chèn hình vào bản thảo LaTeX (`thesis/chapters/chapterX.tex`)

Do các hình vẽ được viết trực tiếp bằng TikZ, bạn chỉ cần dùng lệnh `\input{figures/<tên_file>.tex}` mà không lo bị vỡ hạt hay mờ khi zoom:

```latex
\begin{figure}[htbp]
  \centering
  \input{figures/fig_3_1_triple_sequence.tex}
  \caption{Sơ đồ chuỗi thực hiện bộ ba $[source / transition / follow-up]$ và cơ chế kích hoạt Oracle 970.}
  \label{fig:triple_sequence}
\end{figure}
```

---

## 3. Bản xem trước trực quan (Mermaid Diagrams)

Dưới đây là mã sơ đồ Mermaid tương đương cho từng hình vẽ, hiển thị trực tiếp trên giao diện Markdown:

### Hình 1.1: Minh họa vòng đời lỗ hổng phân quyền có trạng thái
```mermaid
sequenceDiagram
    autonumber
    actor Victim as Nạn nhân (Victim)
    participant API as Cổng REST API
    participant DB as Database / Session Store
    actor Admin as Quản trị viên (Operator)

    Victim->>API: Gửi request ghi nhạy cảm (Token vai trò Admin)
    API->>DB: Kiểm tra quyền
    DB-->>API: Hợp lệ (Admin)
    API-->>Victim: 200 OK (Thao tác thành công)

    Admin->>API: Hạ vai trò nạn nhân xuống User (PUT /role)
    API->>DB: Cập nhật quyền: role = user
    DB-->>API: Đã cập nhật thành công

    Note over Victim,API: Tái sử dụng phiên / Token cũ
    Victim->>API: Gửi lại request ghi cũ bằng Token cũ
    Note over API,DB: Điểm nghẽn: Chỉ check chữ ký tĩnh, không check DB
    API-->>Victim: 200 OK (Lỗ hổng Stateful BAC A1!)
```

### Hình 2.1: Kiến trúc tổng thể và chu trình sinh test EvoMaster
```mermaid
flowchart LR
    Spec[Đặc tả OpenAPI / Swagger] --> GA[Pha Tìm kiếm GA / MIO Engine]
    SUT[Hệ thống mục tiêu SUT] <--> Executor[Bộ thực thi HTTP & Đo độ phủ]
    GA <--> Executor
    Executor --> Archive[(Test Archive 2xx Endpoints)]
    
    subgraph SecurityPhase [Pha Kiểm thử Bảo mật]
        Builder[RestSecurityBuilder Dựng bộ ba 970]
        Oracle[RestSecurityOracle Oracle 970 & D1]
        Sampler[RestSampler Ngân sách & Token]
        Sampler --> Builder
        Builder <--> Oracle
    end

    Archive --> Builder
    Archive --> Oracle
    Builder --> TestSuite[Bộ test JUnit / Python]
    Oracle --> Report[Báo cáo lỗ hổng Stateful BAC]
```

### Hình 3.1: Sơ đồ chuỗi bộ ba kiểm thử `[source / transition / follow-up]`
```mermaid
sequenceDiagram
    autonumber
    actor Fuzzer as EvoMaster (Oracle 970)
    participant API as REST API Target
    participant DB as Database

    rect rgb(240, 245, 255)
    Note over Fuzzer,DB: BƯỚC 1: SOURCE
    Fuzzer->>API: Request ghi nhạy cảm (Token nạn nhân ban đầu)
    API->>DB: Thực thi
    API-->>Fuzzer: 2xx OK (Lưu token & request signature)
    end

    rect rgb(255, 245, 255)
    Note over Fuzzer,DB: BƯỚC 2: TRANSITION
    Fuzzer->>API: Yêu cầu hạ quyền nạn nhân (Token Operator)
    API->>DB: Cập nhật quyền DB: role = user
    API-->>Fuzzer: 2xx OK
    end

    rect rgb(255, 240, 240)
    Note over Fuzzer,DB: BƯỚC 3: FOLLOW-UP & PHÁN QUYẾT
    Fuzzer->>API: Gửi lại request ở Source (Token cũ của nạn nhân)
    alt Trả về 403 Forbidden
        API-->>Fuzzer: 403 Forbidden -> AN TOÀN (Thỏa mãn MR-A1)
    else Trả về 2xx OK (Nghi vấn lỗ hổng)
        API-->>Fuzzer: 2xx OK -> Kích hoạt D1 Relogin Probe
        Fuzzer->>API: Probe request với Token mới của nạn nhân (User)
        alt Probe trả về 403 Forbidden
            API-->>Fuzzer: 403 Forbidden -> KÍCH HOẠT ORACLE 970 (True Positive)!
        else Probe trả về 2xx OK
            API-->>Fuzzer: 2xx OK -> Endpoint công khai (Ngăn ngừa Báo động giả)
        end
    end
    end
```

### Hình 3.2: Không gian trạng thái phân quyền và Quan hệ suy biến MR-A1
```mermaid
stateDiagram-v2
    [*] --> Q0: Khởi tạo phiên
    state "Q0: [DB: Privileged, Token: Valid]" as Q0
    Q0 --> Q0: Source Request (2xx OK)
    
    Q0 --> Q_trans: Transition (Operator hạ quyền)
    state "Q_trans: [DB: Demoted, Token: Stale]" as Q_trans
    
    Q_trans --> Q_safe: Follow-up (403 Forbidden)
    state "Q_safe: Hệ thống an toàn (MR-A1 Thỏa mãn)" as Q_safe
    
    Q_trans --> Q_vuln: Follow-up (200 OK)
    state "Q_vuln: Vi phạm MR-A1 (Kích hoạt 970)" as Q_vuln
```

### Hình 3.3: Quy trình nhận diện và xếp hạng Transition từ OpenAPI
```mermaid
flowchart TD
    Spec[Đặc tả OpenAPI / Swagger] --> Tokenizer[Bộ tách đặc trưng: p:token, f:token, v:verb]
    Tokenizer --> NB[Mô hình Naive Bayes - Jar P2e<br/>10.381 thao tác ghi / 230 APIs]
    Tokenizer -.-> Lex[Bộ từ vựng Lexicon - Jar AF2<br/>53 path / 45 param từ chuẩn RFC 7643]
    NB --> Engine[Động cơ chấm điểm & xếp hạng]
    Lex -.-> Engine
    
    Engine --> Op1[1. Endpoint Transition: opScore > 0]
    Engine --> Op2[2. Trường vai trò: roleField]
    Engine --> Op3[3. Trường nạn nhân: victimField]
    Engine --> Op4[4. Giá trị hạ quyền: Enum thấp / 0 / lowstr]
```

