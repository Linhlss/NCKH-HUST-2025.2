# Checklist Công Việc Theo Thứ Tự Ưu Tiên

Tài liệu này là checklist chính thức để đưa project từ mức:

- `framework nghiên cứu đã có`

lên mức:

- `systems-and-application paper có thể bảo vệ được`

Checklist này bám trực tiếp theo:

- [Yeu cau va Muc dich paper.md](/Users/thao/Documents/paper%20NCKH%20/source%20code/NCKH_chatbot_week3_6/docs/Yeu%20cau%20va%20Muc%20dich%20paper.md)

Mục tiêu là giữ cách chia theo thứ tự công việc cần làm trước, nhưng toàn bộ nội dung phải khớp với định vị paper hiện tại:

1. `Adaptive Multi-Path Inference`
2. `Shared Models and LoRA-based Personalization`
3. `Multi-tenant serving, tenant isolation, và systems efficiency`
4. `Reproducibility đủ tốt cho journal`

## Checklist 1. Làm cho hệ thống đúng với title paper

**Mục tiêu:**  
Biến title paper thành thứ được phản ánh thật trong hệ thống, không chỉ là mô tả ý tưởng.

Title hiện tại nhấn mạnh 2 ý rất mạnh:

- `Adaptive Multi-Path Inference`
- `Shared Models and LoRA-based Personalization`

Vì vậy checklist đầu tiên phải làm cho 2 ý này trở thành sự thật ở mức runtime.

### 1.1. Chuẩn hóa adaptive multi-path inference

- [ ] Xác định rõ các path đang có trong hệ thống:
  - `tool`
  - `retrieval`
  - `general`
  - `out_of_scope`
- [ ] Chuẩn hóa vai trò của từng path
- [ ] Ghi log route decision cho mỗi query
- [ ] Ghi log lý do chọn route theo dạng chuẩn hóa
- [ ] Bổ sung `route score` hoặc `confidence score`
- [ ] Xác định feature đầu vào cho route decision
- [ ] Cho phép chạy chế độ `adaptive`
- [ ] Cho phép chạy chế độ `fixed retrieval`
- [ ] Cho phép chạy chế độ `fixed general`
- [ ] Cho phép chạy chế độ `fixed tool` khi phù hợp

### 1.2. Đưa LoRA vào runtime chính

- [ ] Thiết kế cơ chế `tenant_id -> adapter`
- [ ] Chuẩn hóa nơi lưu adapter theo tenant
- [ ] Tích hợp load adapter vào luồng runtime chính
- [ ] Có fallback nếu tenant chưa có adapter
- [ ] Cho phép bật/tắt personalization theo tenant
- [ ] Phân biệt rõ `base-only` và `base+LoRA`
- [ ] Log trạng thái personalization cho từng tenant
- [ ] Đảm bảo workflow chính dùng được personalization thật

### 1.3. Làm rõ mối quan hệ giữa shared model và personalization

- [ ] Xác định shared base model nào là lõi phục vụ chung
- [ ] Xác định adapter nào thuộc tenant nào
- [ ] Mô tả rõ khi nào dùng base-only
- [ ] Mô tả rõ khi nào dùng base+LoRA
- [ ] Đảm bảo thiết kế này có thể trình bày thành contribution trong paper

**Kết quả mong muốn của Checklist 1:**

- Có thể nói chắc chắn rằng hệ thống thật sự có `adaptive multi-path inference`
- Có thể nói chắc chắn rằng hệ thống thật sự dùng `shared base model + LoRA-based personalization`

## Checklist 2. Chứng minh tenant isolation và multi-tenant serving

**Mục tiêu:**  
Sau khi system đúng với title paper, bước tiếp theo là chứng minh đây thật sự là một hệ thống multi-tenant đúng nghĩa.

### 2.1. Chuẩn hóa tenant serving

- [ ] Chuẩn hóa tenant identification từ request
- [ ] Chuẩn hóa tenant runtime manager
- [ ] Tách rõ phần shared và phần tenant-specific
- [ ] Chuẩn hóa vector DB / storage theo tenant
- [ ] Chuẩn hóa memory theo `tenant_id` và `user_id`
- [ ] Chuẩn hóa adapter per tenant
- [ ] Kiểm tra config tenant có nhất quán không

### 2.2. Kiểm thử tenant isolation

- [ ] Viết test retrieval chỉ lấy đúng tài liệu tenant
- [ ] Viết test source attribution đúng tenant scope
- [ ] Viết test memory isolation
- [ ] Viết test cross-tenant queries
- [ ] Viết test tenant không thấy dữ liệu tenant khác
- [ ] Ghi lại các failure cases nếu phát hiện leakage
- [ ] Tạo báo cáo isolation summary

### 2.3. Chuẩn hóa cơ chế bảo vệ leakage

- [ ] Kiểm tra metadata tenant trong ingestion
- [ ] Kiểm tra metadata tenant trong retrieval
- [ ] Kiểm tra route có làm bypass isolation không
- [ ] Kiểm tra personalization không làm lẫn tenant
- [ ] Bổ sung guard nếu cần trong runtime và retrieval

**Kết quả mong muốn của Checklist 2:**

- Có bằng chứng kỹ thuật và test rằng hệ thống là multi-tenant thật
- Có thể viết section riêng trong paper về tenant isolation

## Checklist 3. Xây benchmark và ablation đủ sức bảo vệ paper

**Mục tiêu:**  
Sau khi system đã đúng claim cơ bản, phải xây benchmark đủ mạnh để reviewer tin contribution.

### 3.1. Nâng benchmark dataset

- [ ] Tăng số lượng test cases
- [ ] Tăng số lượng hard cases
- [ ] Thêm câu hỏi mơ hồ / nhiễu / gần nghĩa
- [ ] Thêm cross-tenant leakage cases
- [ ] Thêm personalization-specific cases
- [ ] Thêm routing-specific cases
- [ ] Chia benchmark theo tenant
- [ ] Chia benchmark theo difficulty
- [ ] Chia benchmark theo category
- [ ] Chia benchmark theo path phù hợp

### 3.2. Hoàn thiện retrieval evaluation

- [ ] Hoàn thiện `Hit@k`
- [ ] Hoàn thiện `MRR`
- [ ] Đánh giá route accuracy
- [ ] Đánh giá retrieval latency
- [ ] Thêm breakdown theo tenant
- [ ] Thêm breakdown theo difficulty
- [ ] Thêm breakdown theo route type

### 3.3. Hoàn thiện answer-level evaluation

- [ ] Đánh giá accuracy
- [ ] Đánh giá groundedness
- [ ] Đánh giá hallucination rate
- [ ] Đánh giá completeness
- [ ] So sánh quality giữa adaptive và fixed path
- [ ] So sánh quality giữa base-only và base+LoRA

### 3.4. Viết ablation study

- [ ] `adaptive` vs `fixed retrieval`
- [ ] `adaptive` vs `fixed general`
- [ ] `adaptive` vs `fixed tool` khi phù hợp
- [ ] `base-only` vs `base+LoRA`
- [ ] `dense only` vs `dense + hybrid`
- [ ] `dense + hybrid` vs `dense + hybrid + reranker`
- [ ] `adaptive without personalization` vs `adaptive with personalization`

**Kết quả mong muốn của Checklist 3:**

- Có benchmark đủ mạnh để chứng minh novelty
- Có ablation đủ rõ để thấy mỗi thành phần đóng góp gì

## Checklist 4. Chứng minh systems value bằng số liệu tài nguyên

**Mục tiêu:**  
Đây là bước biến bài của bạn thành một `systems-and-application paper` thực sự, thay vì chỉ là một chatbot có nhiều module.

### 4.1. Đo hiệu năng theo path

- [ ] Đo latency của `tool path`
- [ ] Đo latency của `retrieval path`
- [ ] Đo latency của `general path`
- [ ] So sánh latency giữa adaptive và fixed path
- [ ] Đo chi phí verification / rewrite nếu có

### 4.2. Đo hiệu năng theo số tenant

- [ ] Benchmark khi có 1 tenant
- [ ] Benchmark khi có nhiều tenant
- [ ] So sánh latency khi số tenant tăng
- [ ] So sánh memory footprint khi số tenant tăng
- [ ] So sánh runtime overhead của adapter switching

### 4.3. Đo lợi ích của shared model

- [ ] So sánh shared base model với giả lập `per-tenant model`
- [ ] Đo RAM / GPU / throughput của shared serving
- [ ] Đo chi phí personalization trên shared serving
- [ ] Tạo bảng quality vs cost vs latency

### 4.4. Chuẩn hóa system-level artifacts

- [ ] Ghi lại resource metrics vào artifact
- [ ] Tạo bảng benchmark paper-ready
- [ ] Tạo summary report cho systems performance
- [ ] Gắn các kết quả này với contribution statement trong paper

**Kết quả mong muốn của Checklist 4:**

- Có bằng chứng định lượng cho giá trị systems của kiến trúc
- Reviewer thấy rõ lợi ích của multi-tenant shared serving

## Checklist 5. Làm sạch repo và chuẩn hóa reproducibility

**Mục tiêu:**  
Sau khi lõi nghiên cứu đã đủ mạnh, chuẩn hóa repo để phục vụ viết paper, chia sẻ artifact, và tái lập kết quả.

### 5.1. Làm sạch source code

- [ ] Dọn `venv`
- [ ] Dọn `__pycache__`
- [ ] Dọn local runtime artifacts
- [ ] Tách rõ source code và evaluation artifacts
- [ ] Tách rõ data dùng nghiên cứu và data dùng cá nhân
- [ ] Rà lại `.gitignore`

### 5.2. Chuẩn hóa docs

- [ ] Viết `README.md` gốc cho repo
- [ ] Bỏ absolute path trong docs
- [ ] Viết hướng dẫn cài đặt tối giản
- [ ] Viết hướng dẫn chạy benchmark
- [ ] Viết hướng dẫn train/test personalization
- [ ] Viết hướng dẫn tái tạo kết quả paper
- [ ] Giữ `Yeu cau va Muc dich paper` làm file định hướng nội bộ

### 5.3. Chuẩn hóa môi trường và artifact

- [ ] Chuẩn hóa requirements / package config
- [ ] Chuẩn hóa `.env.example`
- [ ] Chuẩn hóa script chạy experiment
- [ ] Chuẩn hóa output reports
- [ ] Chuẩn hóa artifact naming
- [ ] Đảm bảo Docker / launcher chạy được ổn định

### 5.4. Hoàn thiện Docker như môi trường chuẩn cho paper

- [ ] Xác định Docker là môi trường chuẩn cho runtime chính
- [ ] Xác định Docker là môi trường chuẩn cho benchmark dùng trong paper
- [ ] Đảm bảo benchmark chính chạy hoàn toàn bằng Docker
- [ ] Đảm bảo adaptive vs fixed-path evaluation chạy được bằng Docker
- [ ] Đảm bảo personalization workflow có thể tái lập bằng Docker
- [ ] Đảm bảo artifact output khi chạy trong Docker là nhất quán
- [ ] Viết rõ câu lệnh Docker để tái tạo các kết quả chính của paper
- [ ] Kiểm tra khả năng chạy lại trên máy khác chỉ với Docker + Ollama
- [ ] Phân biệt rõ Docker là môi trường chuẩn, `venv` là môi trường dev phụ trợ

### 5.5. Chuẩn hóa presentation support cho paper

- [ ] Chuẩn hóa sơ đồ kiến trúc
- [ ] Chuẩn hóa sơ đồ roadmap
- [ ] Chuẩn hóa bảng benchmark
- [ ] Chuẩn hóa bảng ablation
- [ ] Chuẩn hóa bảng systems metrics

**Kết quả mong muốn của Checklist 5:**

- Repo đủ sạch để hỗ trợ nộp journal
- Có thể tái lập và trình bày kết quả nhất quán

## Những việc chưa cần làm sớm

Các việc sau không sai, nhưng nên để sau:

- [ ] Cải thiện UI demo quá nhiều
- [ ] Làm dashboard đẹp hơn trước khi benchmark lõi xong
- [ ] Viết model mới từ đầu
- [ ] Phát minh thuật toán LoRA mới
- [ ] Đổi toàn bộ framework chỉ vì muốn “đẹp hơn”

## Tóm tắt rất ngắn

Thứ tự hợp lý nhất bây giờ là:

1. Làm cho system đúng title paper
2. Chứng minh tenant isolation và multi-tenant behavior
3. Làm benchmark và ablation đủ mạnh
4. Chứng minh systems efficiency
5. Làm sạch repo và reproducibility

Nếu 5 checklist này hoàn thành theo đúng thứ tự, project sẽ đi từ mức:

- `có framework`

lên mức:

- `có evidence đủ mạnh cho systems-and-application paper`
