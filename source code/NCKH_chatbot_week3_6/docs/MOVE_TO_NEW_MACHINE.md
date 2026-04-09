# Move To New Machine

Tài liệu này dùng khi bạn muốn mang project sang máy khác để tiếp tục:

- dev code
- chạy runtime
- benchmark
- làm evaluation
- tiếp tục workflow personalization

Mục tiêu là chuyển máy theo đúng tinh thần hiện tại của project:

- `Docker-first`
- `venv-second`
- ưu tiên reproducibility cho paper

## 1. Nên chuyển gì

Nên chuyển toàn bộ thư mục project.

Nếu dùng Git:

1. commit code trên máy cũ
2. push lên repo
3. sang máy mới, clone repo

Nếu không dùng Git:

1. nén toàn bộ thư mục project
2. copy sang máy mới
3. giải nén rồi mở thư mục project

## 2. Có thể bỏ gì khi chuyển

Nếu muốn gọn hơn, có thể bỏ:

- `venv/`
- `__pycache__/`
- `.DS_Store`
- `logs/`
- `storage_tuning/`
- các local artifacts không cần thiết

Tùy nhu cầu:

- giữ `storage/` nếu muốn mang luôn index hiện tại
- bỏ `storage/` nếu chấp nhận rebuild lại

## 3. Trên máy mới cần có gì

Tối thiểu nên có:

1. Docker Desktop
2. Git hoặc công cụ giải nén
3. Ollama nếu muốn chạy inference thật
4. model Ollama cần dùng, ví dụ `llama3`

## 4. File nên có trong project

Trước khi chuyển máy, nên kiểm tra project có:

- `docker-compose.yml`
- `Dockerfile`
- `.env.example`
- `docs/CHECKLIST.md`
- `docs/Yeu cau va Muc dich paper.md`
- `docs/SETUP_AND_DEV_GUIDE.md`
- `docs/Huong sua Abstract va Introduction.md`

## 5. Cách khởi động trên máy mới

Từ thư mục project:

```bash
docker compose up --build -d dev
docker compose up -d api ui
```

Sau đó:

- API: `http://127.0.0.1:8000`
- UI: `http://127.0.0.1:8501`

Hoặc dùng workflow chuẩn hơn:

```bash
cp .env.example .env
make bootstrap
```

## 6. Vào môi trường dev

```bash
docker compose exec dev bash
```

Trong container `dev`, bạn có thể:

- chạy benchmark
- chạy evaluation
- chạy `pipeline1`, `pipeline2`, `pipeline3`
- test runtime/API
- sửa flow dev mà không cần phụ thuộc `venv`

## 7. Test nhanh sau khi chuyển máy

### Kiểm tra container

```bash
docker compose ps
```

### Kiểm tra API

Mở:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/status?tenant_id=default&user_id=guest`

### Kiểm tra UI

Mở:

- `http://127.0.0.1:8501`

## 8. Test benchmark đúng hướng paper

### Adaptive mode

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label adaptive_baseline
```

### Fixed retrieval mode

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_retrieval --fixed-route-mode retrieval
```

### Fixed general mode

```bash
docker compose exec dev python evaluation/run_real_benchmark.py --dataset evaluation/test_queries.json --label fixed_general --fixed-route-mode general
```

Hoặc dùng Makefile:

```bash
make benchmark-adaptive
make benchmark-fixed-retrieval
make benchmark-fixed-general
```

Các mode này quan trọng vì chúng bám trực tiếp vào Checklist 1.

## 9. Test workflow personalization

Ví dụ với tenant `default`:

```bash
docker compose exec dev python pipeline1/run_pipeline1.py --tenant-id default
docker compose exec dev python personalization/clean_dataset.py --tenant-id default
docker compose exec dev python pipeline2/train_lora.py --tenant-id default
docker compose exec dev python pipeline3/test_lora.py --tenant-id default --prompt "Chính sách nghỉ phép của công ty là gì?"
```

Lưu ý:

- workflow LoRA đã có thể chạy riêng
- nhưng việc tích hợp LoRA serving thật vào runtime chính vẫn là phần tiếp tục của Checklist 1

## 10. Nếu inference không chạy

Nguyên nhân thường gặp:

- Ollama chưa chạy trên host
- chưa pull model cần dùng

Ví dụ:

```bash
ollama pull llama3
```

Sau đó chạy lại:

```bash
docker compose up -d api ui
```

## 11. Cách làm việc khuyến nghị khi đổi máy

Mỗi khi sang máy mới:

1. lấy code về
2. copy `.env.example` thành `.env`
3. khởi động Docker
4. chạy `make bootstrap`
5. test API
6. test benchmark ở `adaptive` mode
7. nếu cần, test thêm `fixed-route` modes
8. tiếp tục dev trong `dev` container

## 12. Ghi nhớ ngắn

- không cần mang `venv`
- Docker là môi trường chuẩn khi chuyển máy
- `dev` container là nơi chạy lệnh và benchmark
- `api` và `ui` dùng để chạy hệ thống
- nếu cần chat thật, host phải có Ollama
