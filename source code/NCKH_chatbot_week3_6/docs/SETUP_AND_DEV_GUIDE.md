# Setup And Dev Guide

Tài liệu này mô tả cách nên dùng repo theo đúng định vị hiện tại của đề tài:

`Adaptive Multi-Path Inference for Multi-Tenant LLM Systems with Shared Models and LoRA-based Personalization`

Repo này không nên được xem chỉ là một chatbot RAG để demo.  
Nó đang được phát triển theo hướng:

- systems-and-application paper
- multi-tenant LLM serving
- adaptive multi-path inference
- shared-model serving
- LoRA-based personalization

## 1. Cách nên hiểu repo ở giai đoạn hiện tại

Các khối chính của hệ thống:

- `project_root/`: runtime chính, router, workflow, retrieval, API, runtime manager
- `evaluation/`: benchmark, answer evaluation, retrieval evaluation, generated reports
- `pipeline1/`: chuẩn bị dữ liệu QA / instruction theo tenant
- `pipeline2/`: train LoRA prototype theo tenant
- `pipeline3/`: load / test LoRA adapter
- `personalization/`: dữ liệu, datasets, adapters, reports theo tenant
- `docs/`: định hướng paper, checklist, setup, chuyển máy
- `run_me.py`: launcher thống nhất

## 2. Môi trường chuẩn nên dùng

### Chuẩn chính thức

`Docker`

Docker nên được xem là môi trường chuẩn cho:

- runtime chính
- benchmark dùng trong paper
- so sánh `adaptive` vs `fixed-route`
- reproducibility
- chuyển máy

### Môi trường phụ trợ

`venv`

`venv` chỉ nên dùng để:

- debug nhanh
- thử script nhỏ
- phát triển cục bộ
- train/test exploratory ngoài luồng benchmark chính

Kết luận ngắn:

- `Docker-first`
- `venv-second`

## 3. Docker-first workflow

### Khởi động nhanh

Từ thư mục project:

```bash
docker compose up --build -d dev
docker compose up -d api ui
```

Sau đó:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`
- môi trường dev nằm trong service `dev`

### Cách chuẩn hơn với Makefile

Nếu muốn dùng workflow ngắn gọn và nhất quán hơn:

```bash
make bootstrap
```

Các lệnh hay dùng:

```bash
make ps
make dev-shell
make logs
make app-down
```

### Vào môi trường dev

```bash
docker compose exec dev bash
```

Trong container `dev`, bạn nên dùng để:

- chạy benchmark
- chạy evaluation scripts
- chạy `pipeline1`, `pipeline2`, `pipeline3`
- test các chế độ route khác nhau

## 4. Biến môi trường nên chốt bằng `.env`

Nếu đang làm việc giữa nhiều máy, nên copy:

```bash
cp .env.example .env
```

Các biến quan trọng:

- `OLLAMA_MODEL`
- `SHARED_OLLAMA_MODEL`
- `OLLAMA_BASE_URL`
- `API_PORT`
- `STREAMLIT_PORT`
- `ENABLE_PERSONALIZATION`
- `FIXED_ROUTE_MODE`

Khuyến nghị:

- để `FIXED_ROUTE_MODE=adaptive` cho runtime mặc định
- chỉ override sang `retrieval` hoặc `general` khi benchmark fixed-route

## 5. Các mode mới cần nhớ khi dev

Sau khi cập nhật Checklist 1, hệ thống đã bắt đầu có các khái niệm cần cho paper:

- `adaptive` route mode
- `fixed retrieval`
- `fixed general`
- `fixed tool`
- route telemetry
- personalization runtime state

Điều này có nghĩa là khi chạy benchmark hoặc API, bạn nên nghĩ theo hướng:

- so sánh route mode
- ghi nhận route decision
- ghi nhận adapter state
- ghi nhận shared-model serving state

## 6. Kiểm tra hệ thống sau khi khởi động

### API health

- `GET /health`
- `GET /status?tenant_id=default&user_id=guest`

### Chat runtime

- kiểm tra `/chat` với `tenant_id`
- kiểm tra metadata trả về:
  - `route_reason`
  - `route_score`
  - `route_mode`
- `route_candidates`
- `shared_model_name`
- `adapter_enabled`
- `adapter_available`

### UI

Kiểm tra các tab:

- `Preview`
- `Chat`
- `Trạng thái hệ thống`
- `Cấu hình tenant`
- `Không gian LoRA`

## 7. Chạy benchmark đúng với hướng paper

### Benchmark mặc định

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label adaptive_baseline
```

### Benchmark fixed retrieval

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_retrieval --fixed-route-mode retrieval
```

### Benchmark fixed general

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_general --fixed-route-mode general
```

### Cách nhanh bằng Makefile

```bash
make benchmark-adaptive
make benchmark-fixed-retrieval
make benchmark-fixed-general
```

Nếu muốn benchmark `tool`, cần chắc chắn các query tương ứng có direct tool match.

## 8. Workflow personalization hiện tại

### Chuẩn bị dữ liệu

Đặt file nguồn vào:

```text
personalization/data/<tenant_id>/files/
```

### Pipeline chuẩn

```bash
docker compose exec dev python pipeline1/run_pipeline1.py --tenant-id default
docker compose exec dev python personalization/clean_dataset.py --tenant-id default
docker compose exec dev python pipeline2/train_lora.py --tenant-id default
docker compose exec dev python pipeline3/test_lora.py --tenant-id default --prompt "Chính sách nghỉ phép của công ty là gì?"
```

### Lưu ý quan trọng

Hiện LoRA pipeline đã tồn tại, nhưng serving runtime chính vẫn đang dùng shared base model qua luồng chính.  
Việc nối LoRA serving thật vào runtime là một phần còn tiếp tục trong Checklist 1.

## 9. Khi nào nên dùng `run_me.py`

`run_me.py` phù hợp khi bạn muốn:

- bootstrap nhanh môi trường local
- chạy launcher thống nhất
- test runtime / API / UI nhanh

Ví dụ:

```bash
python3 run_me.py all --setup none
```

Tuy nhiên, với kết quả dùng trong paper, nên ưu tiên chạy benchmark bằng Docker trực tiếp.

## 10. Trạng thái ưu tiên hiện tại

Theo checklist mới, thứ tự ưu tiên là:

1. làm cho system đúng title paper
2. chứng minh tenant isolation và multi-tenant behavior
3. xây benchmark và ablation đủ mạnh
4. chứng minh systems efficiency
5. làm sạch repo và reproducibility

Điều này có nghĩa là ở giai đoạn hiện tại:

- không ưu tiên UI
- không ưu tiên dashboard đẹp
- không ưu tiên đổi framework
- ưu tiên route logic, personalization runtime, benchmark, và telemetry

## 11. File docs nên đọc theo thứ tự

Nếu quay lại project sau một thời gian hoặc chuyển máy, nên đọc:

1. `docs/Yeu cau va Muc dich paper.md`
2. `docs/CHECKLIST.md`
3. `docs/Huong sua Abstract va Introduction.md`
4. `docs/SETUP_AND_DEV_GUIDE.md`
5. `docs/MOVE_TO_NEW_MACHINE.md`

## 12. Ghi nhớ ngắn

- đây là repo cho một systems-and-application paper
- `adaptive` là trục chính, không phải phần phụ
- `RAG` là một path, không phải bản sắc duy nhất của hệ thống
- `Docker` là môi trường chuẩn cho benchmark và reproducibility
- `venv` chỉ là môi trường dev phụ trợ
