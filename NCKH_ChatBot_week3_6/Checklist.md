# Checklist Công Việc Còn Lại

Tài liệu này tổng hợp checklist theo mức ưu tiên để đẩy đề tài từ mức "hệ thống chạy được" lên mức "đủ mạnh cho NCKH".

## Mục tiêu tổng quát

- Hoàn thiện phần thực nghiệm và đánh giá để có kết quả đáng tin cậy.
- Tích hợp các kỹ thuật tối ưu retrieval vào pipeline chạy thật.
- Hoàn thiện hướng personalization bằng LoRA/PEFT cho từng tenant.
- Chứng minh được bài toán multi-tenant optimization bằng số liệu rõ ràng.
- Củng cố tenant isolation và tính đúng đắn của hệ thống.
- Bổ sung monitoring, khả năng vận hành, và khả năng demo ổn định.
- Docker hóa và chuẩn hóa quy trình để dễ tái lập thí nghiệm.
- Làm sạch codebase và chuẩn hóa cấu trúc cho giai đoạn phát triển tiếp theo.

## 1. Hoàn thiện phần thực nghiệm và đánh giá

**Mục tiêu:** Xây dựng bộ đánh giá đủ lớn, đủ rõ, và đủ thuyết phục để so sánh các phương án RAG/personalization một cách khoa học.

- [ ] Mở rộng bộ `evaluation/test_queries.json` từ 2 câu lên tối thiểu 50-100 câu.
- [ ] Chia bộ test theo tenant, loại câu hỏi, và mức độ khó.
- [ ] Hoàn thiện script đánh giá retrieval với `Hit@3`, `Hit@5`, `MRR`.
- [ ] Bổ sung đánh giá answer-level: accuracy, groundedness, hallucination rate, completeness.
- [ ] Viết đầy đủ `retrieval_results.md`.
- [ ] Viết đầy đủ `error_analysis.md`.
- [ ] So sánh rõ: baseline RAG vs optimized RAG vs RAG + personalization.

## 2. Tích hợp retrieval optimization vào pipeline thật

**Mục tiêu:** Đưa các kỹ thuật tối ưu retrieval ra khỏi chế độ thử nghiệm riêng lẻ và tích hợp vào luồng chạy chính để cải thiện hiệu năng thực tế.

- [ ] Tích hợp `query_expansion` vào luồng truy hồi chính.
- [ ] Tích hợp `hybrid_retrieval` vào runtime thay vì để riêng lẻ.
- [ ] Tích hợp `reranker` sau bước retrieve ban đầu.
- [ ] Tạo cấu hình bật/tắt từng kỹ thuật để làm A/B testing.
- [ ] Thử nghiệm nhiều `chunk_size`, `chunk_overlap`, `top_k`.
- [ ] Chọn cấu hình tối ưu dựa trên metric thay vì cảm tính.

## 3. Hoàn thiện LoRA/PEFT personalization

**Mục tiêu:** Chuẩn hóa quy trình tạo dữ liệu, huấn luyện, lưu trữ, và sử dụng adapter để cá nhân hóa theo tenant một cách có thể lặp lại.

- [ ] Chuẩn hóa pipeline tạo dataset cho từng tenant.
- [ ] Làm sạch và rà soát chất lượng `generated_qa.json` và `lora_dataset.json`.
- [ ] Viết script train adapter LoRA thật cho từng tenant.
- [ ] Lưu adapter theo cấu trúc rõ ràng: `adapters/<tenant_id>/...`
- [ ] Tích hợp load adapter thật trong runtime theo `adapter_name`.
- [ ] Đánh giá trước/sau fine-tune.
- [ ] Viết `lora_training_report.md` với hyperparameters, dataset size, kết quả.

## 4. Chứng minh bài toán multi-tenant optimization

**Mục tiêu:** Đưa ra số liệu định lượng để chứng minh lợi ích tài nguyên và khả năng mở rộng của cách tiếp cận multi-tenant.

- [ ] Thiết kế benchmark số tenant tăng dần: 1, 5, 10, 20...
- [ ] Đo RAM/GPU/latency khi dùng shared base model.
- [ ] Đo RAM/GPU/latency khi mỗi tenant dùng model riêng.
- [ ] Đo RAM/GPU/latency khi dùng shared model + LoRA adapter.
- [ ] Tạo bảng so sánh chi phí tài nguyên giữa các phương án.
- [ ] Rút ra kết luận: tối ưu tài nguyên đạt được bao nhiêu phần trăm.

## 5. Củng cố tenant isolation và tính đúng đắn

**Mục tiêu:** Đảm bảo hệ thống không rò rỉ dữ liệu giữa các tenant và luôn trả lời trong đúng phạm vi được phép.

- [ ] Viết test kiểm tra không rò rỉ dữ liệu giữa tenants.
- [ ] Kiểm tra memory tách biệt hoàn toàn theo `tenant_id` và `user_id`.
- [ ] Kiểm tra retrieval chỉ lấy dữ liệu đúng tenant hoặc đúng scope cho phép.
- [ ] Tạo test case hỏi chéo tenant để đảm bảo hệ thống không trả sai dữ liệu.
- [ ] Ghi lại kết quả trong phần báo cáo về data isolation.

## 6. Monitoring và vận hành

**Mục tiêu:** Theo dõi được tài nguyên, độ trễ, và trạng thái hệ thống để phục vụ demo, đánh giá, và vận hành ổn định.

- [ ] Thêm module monitoring đúng nghĩa cho RAM, CPU, GPU, latency.
- [ ] Log thời gian build index, load runtime, query latency.
- [ ] Theo dõi số document, số node, số request theo tenant.
- [ ] Làm dashboard hoặc log summary dễ đọc cho demo.
- [ ] Bổ sung `monitoring.py` nếu nhóm muốn bám sát roadmap.

## 7. Docker hóa và tái lập thí nghiệm

**Mục tiêu:** Giúp người khác có thể clone repo, cấu hình môi trường, và chạy lại toàn bộ pipeline một cách nhất quán.

- [ ] Viết `Dockerfile` cho API/runtime.
- [ ] Viết `docker-compose.yml` cho app + dependencies.
- [ ] Chuẩn hóa biến môi trường trong `.env`.
- [ ] Viết hướng dẫn chạy lại toàn bộ pipeline từ đầu.
- [ ] Đảm bảo người khác clone repo về có thể chạy được.

## 8. Làm sạch codebase và chuẩn hóa cấu trúc

**Mục tiêu:** Giảm phần mã thử nghiệm rời rạc, gom pipeline về cấu trúc rõ ràng, và hạn chế lỗi khi demo hoặc mở rộng sau này.

- [ ] Xóa hoặc tách rõ các module prototype chưa dùng trực tiếp.
- [ ] Gom các thành phần retrieval tối ưu vào một pipeline thống nhất.
- [ ] Chuẩn hóa tên tenant, dữ liệu, thư mục adapter, thư mục eval.
- [ ] Kiểm tra import, cấu hình, đường dẫn để tránh lỗi khi demo.
- [ ] Bổ sung test cơ bản cho API và workflow.
