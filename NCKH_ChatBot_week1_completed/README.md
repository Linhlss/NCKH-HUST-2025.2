# NCKH ChatBot - Week 1 Completed

Dự án này là bản hoàn thành mốc **Tuần 1** cho đề tài:

**"Nghiên cứu tối ưu hóa tài nguyên Cloud cho hệ thống RAG đa người dùng (Multi-tenant): Tiếp cận bằng kỹ thuật tinh chỉnh tham số hiệu quả (PEFT/LoRA) nhằm cá nhân hóa Chatbot."**

## Mục tiêu hiện tại

Ở mốc tuần 1, hệ thống đã hoàn thiện phần lõi **RAG cơ bản**:

- Đọc tài liệu từ thư mục dữ liệu cục bộ.
- Hỗ trợ dữ liệu web qua file `data/links.txt`.
- Chunking và tạo chỉ mục vector bằng **ChromaDB**.
- Truy xuất ngữ cảnh và trả lời bằng **Ollama + LlamaIndex**.
- Có memory hội thoại cơ bản theo tenant/user.
- Có launcher `run_me.py` để khởi động nhanh.

## Cấu trúc thư mục

```text
.
├── config/
│   └── tenants.json
├── data/
│   ├── files/
│   └── links.txt
├── memory/
│   ├── README.txt
│   └── default/
├── project_root/
│   ├── main.py
│   ├── config.py
│   ├── models.py
│   ├── utils.py
│   ├── memory_store.py
│   ├── ingestion.py
│   ├── runtime_manager.py
│   ├── retrieval.py
│   ├── prompt_builder.py
│   ├── tools.py
│   └── llm_service.py
├── storage/
│   ├── README.txt
│   └── default/
├── requirements.txt
├── run_me.py
├── HANDOFF_WEEK1.md
└── README.md
```

## Cách chạy

### Cách 1: chạy bằng launcher

```bash
python run_me.py
```

### Cách 2: chạy trực tiếp entrypoint chính

```bash
python project_root/main.py
```

## Yêu cầu môi trường

- Python 3.10+
- Ollama đã cài và đang chạy
- Model mặc định trong Ollama, ví dụ `llama3`

Kiểm tra Ollama:

```bash
ollama list
```

Nếu chưa có model:

```bash
ollama pull llama3
```

## Cài thư viện

```bash
pip install -r requirements.txt
```

## Các lệnh nhanh khi chạy chatbot

Trong giao diện dòng lệnh, có thể dùng:

```text
/help
/status
/listdocs
/refresh
/resetmem
/time
/calc 2+3*4
/sources on
/sources off
```

## Trạng thái hiện tại

Bản này phù hợp để chốt **Tuần 1**:

- Có pipeline RAG cơ bản.
- Có dữ liệu mẫu và chỉ mục mẫu.
- Có thể dùng làm nền để Trung triển khai routing/workflow ở tuần 2.
- Có thể bàn giao cho Dương để chuẩn bị PEFT/LoRA sau khi workflow ổn định.

---

# Hướng dẫn riêng cho Trung

## Mục tiêu của Trung ở bước tiếp theo

Trung phụ trách **backend/system workflow**. Từ mốc tuần 1 này, công việc tiếp theo là nâng project từ dạng **single-pass RAG** thành **workflow nhiều bước**.

## Việc Trung nên làm trước

### 1. Thêm Routing

Mục tiêu:
- phân loại câu hỏi thành các nhóm như `tool`, `rag`, `general`, `out_of_scope`
- không phải câu nào cũng đi qua full RAG

Gợi ý file mới:

```text
project_root/router.py
project_root/workflow.py
```

### 2. Thêm Prompt Chaining

Mục tiêu:
- tách pipeline thành nhiều bước
- ví dụ:

```text
Input
-> Router
-> Retrieve context
-> Draft answer
-> Verify answer
-> Rewrite style
-> Output
```

### 3. Giữ nguyên các module tuần 1

Trung không nên phá các file này, chỉ nên mở rộng:

- `retrieval.py`
- `llm_service.py`
- `main.py`
- `tools.py`

### 4. Đề xuất hướng sửa cụ thể

#### `main.py`
- thay chỗ gọi thẳng `answer_with_augmented_llm()` bằng một workflow controller.

#### `llm_service.py`
- tách phần `draft_answer()` ra riêng.
- giữ `complete_with_retry()` để tái sử dụng.

#### `retrieval.py`
- thêm `query rewrite` và `reranking` đơn giản.

#### `ingestion.py`
- giữ metadata rõ ràng để sau này phục vụ multi-tenant/filtering.

## Thứ tự Trung nên làm

1. Tạo `router.py`
2. Tạo `workflow.py`
3. Nối `main.py` với workflow mới
4. Test lại `/status`, `/listdocs`, câu hỏi bám tài liệu
5. Chỉ sau khi workflow ổn mới bàn giao cho Dương làm LoRA

## Những gì chưa cần làm ngay

Ở thời điểm này Trung **chưa cần** làm ngay:
- parallelization
- orchestrator-workers
- dashboard
- FastAPI production

Ưu tiên là làm **routing + prompt chaining** trước.

---

# Hướng dẫn đưa project này lên GitHub

## Bước 1: tạo repository mới trên GitHub

Tên gợi ý:

```text
NCKH-Chatbot-RAG-Multitenant
```

## Bước 2: giải nén và mở terminal trong thư mục project

Ví dụ:

```bash
cd NCKH_ChatBot_week1_completed
```

## Bước 3: khởi tạo git

```bash
git init
git branch -M main
```

## Bước 4: thêm remote

Thay URL dưới đây bằng repo thật của nhóm:

```bash
git remote add origin https://github.com/<username>/<repo-name>.git
```

## Bước 5: commit code

```bash
git add .
git commit -m "Complete week 1 RAG baseline"
```

## Bước 6: đẩy lên GitHub

```bash
git push -u origin main
```

Nếu GitHub hỏi đăng nhập, dùng token cá nhân hoặc GitHub Desktop.

---

# Lưu ý quan trọng khi up GitHub

Không nên để các file sinh tự động hoặc dữ liệu tạm vào repo. Repo này đã có `.gitignore` mẫu để loại các file phổ biến như `__pycache__`, `.venv`, database tạm, log và file hệ điều hành.

Nếu nhóm không muốn public dữ liệu thật, có thể xóa hoặc thay các file trong `data/files/` trước khi push công khai.

## Gợi ý commit message tiếp theo

```text
Add routing workflow
Add prompt chaining pipeline
Prepare LoRA handoff for Duong
```

