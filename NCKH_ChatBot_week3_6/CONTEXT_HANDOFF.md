# NCKH_chatbot_week3_6 - AI SaaS Chatbot System

## 1. Tổng quan đề tài

Đây là project chatbot RAG đa tenant, hướng đến bài toán chatbot cá nhân hóa cho môi trường doanh nghiệp/học vụ.

Project đang bám theo roadmap 4 pipeline:

1. Pipeline 1: Dataset Generation
2. Pipeline 2: LoRA Training
3. Pipeline 3: Chatbot Runtime
4. Pipeline 4: Multi-tenant Orchestration

Mục tiêu tổng thể:

- xây dựng chatbot có retrieval đúng theo tenant
- hỗ trợ memory theo tenant/user
- chuẩn bị personalization bằng LoRA/PEFT
- đánh giá hệ thống bằng benchmark đủ mạnh cho NCKH
- chứng minh lợi ích của hướng multi-tenant optimization

File roadmap/tham chiếu:

- `/Users/thao/Downloads/Project_roadmap.pdf`
- `/Users/thao/Documents/NCKH_chatbot_week3_6/Checklist.md`
- `/Users/thao/Documents/NCKH_chatbot_week3_6/README.md`

## 2. Cấu trúc project hiện tại

Các thư mục/file quan trọng:

- `project_root/`: runtime chính, API, workflow, retrieval, runtime manager
- `pipeline1/`: tạo dataset QA và export LoRA dataset
- `evaluation/`: benchmark retrieval/answer-level, artifacts, reports
- `config/tenants.json`: cấu hình tenant, retrieval flags, model, adapter
- `storage/`: vector DB hiện tại
- `storage_tuning/`: storage riêng cho tuning/rebuild index
- `memory/`: lịch sử hội thoại theo tenant/user
- `streamlit_app.py`: UI quản lý/chat

## 3. Tình trạng tổng quát hiện tại

### 3.1 Những phần đã làm được

- Đã có runtime multi-tenant cơ bản: tenant config, memory theo tenant/user, vector DB theo tenant, API và Streamlit UI.
- Đã có evaluation dataset 54 câu, chia theo tenant/category/difficulty.
- Đã có retrieval benchmark, error analysis, answer-level framework.
- Đã tích hợp checklist 2 vào runtime thật:
  - `query_expansion`
  - `hybrid_retrieval`
  - `reranker`
  - config bật/tắt từng kỹ thuật
  - benchmark optimized runtime
- Đã chốt config retrieval thực dụng dựa trên metric:
  - `enable_query_expansion = true`
  - `enable_hybrid_retrieval = true`
  - `enable_reranker = true`
  - `top_k = 4`
  - `chunk_size = 700`
  - `chunk_overlap = 120`
  - `query_expansion_count = 4`
  - `hybrid_alpha = 0.55`
  - `reranker_top_n = 8`

### 3.2 Các metric retrieval sau tối ưu

Artifact mới nhất:

- `evaluation/retrieval_results_optimized.md`
- `evaluation/error_analysis_optimized.md`
- `evaluation/artifacts/retrieval_metrics_optimized.json`
- `evaluation/retrieval_tuning_summary.md`

Kết quả optimized runtime:

- `Hit@1 = 0.611`
- `Hit@3 = 0.917`
- `Hit@5 = 1.000`
- `MRR = 0.760`

So với runtime trước tối ưu:

- `Hit@1: 0.306 -> 0.611`
- `Hit@3: 0.611 -> 0.917`
- `Hit@5: 0.806 -> 1.000`
- `MRR: 0.497 -> 0.760`

## 4. Các file code đã sửa / quan trọng để tiếp tục

### Runtime và retrieval

- `project_root/retrieval.py`
- `project_root/runtime_manager.py`
- `project_root/config.py`
- `project_root/models.py`
- `project_root/llm_service.py`
- `project_root/api_helpers.py`

### Logic retrieval optimization

- `query_expansion.py`
- `hybrid_retrieval.py`
- `reranker.py`

### UI / config

- `streamlit_app.py`
- `config/tenants.json`

### Evaluation / tuning

- `evaluation/evaluate_retrieval.py`
- `evaluation/tune_retrieval.py`
- `evaluation/retrieval_results_runtime_only.md`
- `evaluation/retrieval_results_optimized.md`
- `evaluation/error_analysis_optimized.md`
- `evaluation/retrieval_tuning_summary.md`

## 5. Trạng thái theo từng checklist

### Checklist 1. Hoàn thiện phần thực nghiệm và đánh giá

Trạng thái: gần xong nhưng chưa đóng hoàn toàn.

Đã làm:

- mở rộng `evaluation/test_queries.json` lên 54 câu
- chia theo tenant/category/difficulty
- có retrieval metrics `Hit@3`, `Hit@5`, `MRR` và thêm `Hit@1`, latency, route accuracy
- có `retrieval_results.md`
- có `error_analysis.md`
- có framework answer-level trong `evaluation/evaluate_answers.py`

Còn thiếu:

- chạy answer-level benchmark thật hoàn chỉnh, hiện vẫn bị chặn khi phụ thuộc LLM/runtime ở một số bối cảnh
- làm bảng so sánh rõ kiểu:
  - baseline RAG
  - optimized RAG
  - RAG + personalization

Kết luận:

- Checklist 1 chưa nên đóng hoàn toàn.

### Checklist 2. Tích hợp retrieval optimization vào pipeline thật

Trạng thái: đã xong phần triển khai và benchmark thực dụng, gần mức đóng.

Đã làm:

- tích hợp `query_expansion` vào retrieval thật
- tích hợp `hybrid_retrieval` vào runtime
- tích hợp `reranker` vào sau retrieve
- có config bật/tắt từng kỹ thuật
- đã thử `top_k = 4/5/6` trên bundle tối ưu
- đã chọn config retrieval mặc định bằng metric thay vì cảm tính

Còn thiếu để đóng tuyệt đối:

- chạy full sweep exhaustive cho `chunk_size/chunk_overlap`
- cập nhật report tuning cuối cùng nếu muốn chốt checklist 2 ở mức tối đa

Lưu ý:

- `evaluation/tune_retrieval.py` đã có hạ tầng chạy tuning với `storage_tuning/`
- sweep exhaustive tốn thời gian vì phải rebuild index thật cho từng cấu hình

### Checklist 3. Hoàn thiện LoRA/PEFT personalization

Trạng thái: mới có nền, chưa hoàn thiện.

Đã có:

- `pipeline1/` tạo QA dataset và export `lora_dataset.json`
- UI có không gian LoRA cơ bản trong `streamlit_app.py`
- tenant config đã có trường `adapter_name`

Còn thiếu lớn:

- chuẩn hóa pipeline1 theo tenant, không dùng output global
- đưa bước `Manual Validation` thành một phần chính thức của pipeline
- script train LoRA thật
- cấu trúc `adapters/<tenant_id>/...`
- load adapter thật trong runtime
- đánh giá trước/sau fine-tune
- `lora_training_report.md`

Kết luận:

- Checklist 3 là bước quan trọng tiếp theo sau khi retrieval backbone đã tương đối ổn.

### Checklist 4. Chứng minh bài toán multi-tenant optimization

Trạng thái: gần như chưa làm.

Đã có nền:

- tenant runtime manager
- vector DB theo tenant
- memory theo tenant/user
- khái niệm adapter per tenant ở mức config

Còn thiếu:

- benchmark 1, 5, 10, 20 tenant
- đo RAM/GPU/latency giữa các phương án
- bảng so sánh tài nguyên
- kết luận định lượng về tiết kiệm tài nguyên

### Checklist 5. Củng cố tenant isolation và tính đúng đắn

Trạng thái: mới có nền kiến trúc, chưa có test chính thức.

Đã có:

- memory tách theo `tenant_id/user_id`
- runtime/index theo tenant

Còn thiếu:

- test chống rò rỉ dữ liệu giữa tenant
- test retrieval chỉ đúng tenant/scope
- test case hỏi chéo tenant
- phần báo cáo data isolation

### Checklist 6. Monitoring và vận hành

Trạng thái: có nền log/status, chưa hoàn chỉnh.

Đã có:

- log build runtime
- log RAM delta
- status API/UI

Còn thiếu:

- monitoring module đúng nghĩa cho RAM/CPU/GPU/latency
- dashboard/log summary riêng cho demo
- `monitoring.py` đúng roadmap

### Checklist 7. Docker hóa và tái lập thí nghiệm

Trạng thái: chưa làm.

Còn thiếu:

- `Dockerfile`
- `docker-compose.yml`
- `.env` chuẩn
- hướng dẫn tái lập toàn bộ pipeline

### Checklist 8. Làm sạch codebase và chuẩn hóa cấu trúc

Trạng thái: làm một phần nhỏ, chưa xong.

Đã có:

- các logic retrieval tối ưu đã được gom vào runtime thật thay vì để rời

Còn thiếu:

- dọn module prototype cũ chưa dùng
- chuẩn hóa output pipeline1 theo tenant
- chuẩn hóa naming/thư mục adapter/eval
- bổ sung test cơ bản cho API/workflow

## 6. Đánh giá riêng Pipeline 1 theo roadmap

Pipeline 1 mới hoàn thiện một phần.

Đã có:

- segmentation
- QA generation
- export LoRA dataset
- runner cơ bản

Chưa hoàn chỉnh:

- manual validation chưa nối chính thức vào flow
- chưa tenant-aware
- chưa nối gọn sang Pipeline 2
- chưa có metadata/dataset management đủ sạch

Muốn hoàn thiện Pipeline 1 thật sự:

- cần chủ yếu Checklist 3
- và một phần Checklist 8

## 7. Việc nên làm tiếp theo theo thứ tự ưu tiên

### Ưu tiên 1: đóng nốt Checklist 2 ở mức tối đa

Làm:

- chạy full sweep `chunk_size/chunk_overlap` bằng `evaluation/tune_retrieval.py`
- cập nhật `evaluation/retrieval_tuning_summary.md`
- nếu có config tốt hơn thì cập nhật lại `config/tenants.json`

### Ưu tiên 2: hoàn thiện Checklist 1

Làm:

- chạy answer-level benchmark thật
- tạo bảng so sánh:
  - baseline RAG
  - optimized RAG
  - RAG + personalization

### Ưu tiên 3: bắt đầu Checklist 3

Làm:

- refactor `pipeline1/` theo tenant
- nối `validate.py` vào flow chính
- viết train script LoRA thật
- tạo `adapters/<tenant_id>/...`
- load adapter vào runtime

## 8. Cách chạy / benchmark quan trọng

### Retrieval optimized hiện tại

Chạy benchmark optimized:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python evaluation/evaluate_retrieval.py \
  --dataset evaluation/test_queries.json \
  --variants runtime_profile \
  --json-out evaluation/artifacts/retrieval_metrics_optimized.json \
  --report-out evaluation/retrieval_results_optimized.md \
  --error-out evaluation/error_analysis_optimized.md
```

### Tuning retrieval

Script:

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 PYTHONDONTWRITEBYTECODE=1 ./venv/bin/python evaluation/tune_retrieval.py \
  --dataset evaluation/test_queries.json \
  --json-out evaluation/artifacts/retrieval_tuning_final.json \
  --md-out evaluation/retrieval_tuning_final.md
```

Lưu ý:

- tuning dùng `storage_tuning/`
- rebuild index thật cho từng config nên chạy lâu

## 9. Các rủi ro / lưu ý khi chuyển máy

- Máy mới cần đủ dependency trong `venv` hoặc cài lại từ `requirements.txt`
- Nếu không có mạng hoặc cache model, project đang có fallback để benchmark/runtime không chết ngay, nhưng kết quả có thể khác so với model embedding chuẩn
- Các benchmark retrieval nên chạy với:
  - `HF_HUB_OFFLINE=1`
  - `TRANSFORMERS_OFFLINE=1`
  - `PYTHONDONTWRITEBYTECODE=1`
- Chú ý `storage/` và `storage_tuning/` là quan trọng nếu muốn tái hiện benchmark

## 10. Kết luận handoff

Project hiện ở trạng thái:

- Retrieval/runtime multi-tenant đã khá mạnh và usable
- Checklist 2 gần như hoàn chỉnh
- Checklist 1 gần xong nhưng thiếu phần answer-level/report so sánh cuối
- Checklist 3 trở đi vẫn là phần lớn công việc còn lại

Nếu tiếp tục trên máy khác, nên đi theo thứ tự:

1. hoàn tất sweep tuning để đóng checklist 2
2. hoàn tất answer-level và bảng so sánh để đóng checklist 1
3. chuyển sang Checklist 3 để làm personalization/LoRA thật
