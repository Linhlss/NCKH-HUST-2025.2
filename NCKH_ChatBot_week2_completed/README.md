
# Week 3 Plan — Evaluation, Optimization & Multi-Tenant Preparation

## Objectives
Tuần 3 tập trung vào:
1. Đánh giá Pipeline 3 (multi‑step RAG).
2. Tối ưu retrieval (chunking + reranking).
3. Chuẩn bị LoRA adapters cho từng tenant.
4. Chuẩn bị multi‑tenant runtime.
5. Thêm monitoring hệ thống.

---

# Weekly Timeline

| Day | Goal |
|---|---|
| Day 1 | Setup evaluation framework |
| Day 2 | Retrieval optimization |
| Day 3 | Re‑ranking implementation |
| Day 4 | Pipeline evaluation |
| Day 5 | LoRA training |
| Day 6 | Multi‑tenant integration |
| Day 7 | Monitoring & benchmarking |

---

# Member Responsibilities

## 1. Kiên — Data & RAG Engineer

### Tasks
- Create evaluation dataset `evaluation/test_queries.json`
- Build retrieval evaluation script
- Test chunk sizes (300 / 500 / 800)
- Test chunk overlap (50 / 100)
- Rebuild vector index
- Implement reranker module
- Measure Hit@3, Hit@5, MRR

### Deliverables
- evaluation/retrieval_results.md
- error_analysis.md

---

## 2. Dương — AI/ML Specialist

### Tasks
- Implement evaluation pipeline `eval_pipeline.py`
- Measure metrics:
  - accuracy
  - hallucination rate
  - groundedness
  - answer completeness
- Compare Baseline RAG vs Pipeline 3
- Prepare LoRA datasets
- Train LoRA adapters:
  - bank_adapter
  - shop_adapter

### Deliverables
- evaluation_results.md
- lora_training_report.md

---

## 3. Trung — Cloud & Backend Developer

### Tasks
- Implement tenant runtime manager
- Load vector DB per tenant
- Load LoRA adapter per tenant
- Add workflow logging
- Implement monitoring (RAM, GPU, latency)
- Dockerize system

### Deliverables
- runtime_manager.py
- monitoring.py
- docker-compose.yml

---

## 4. Linh — Product & Documentation

### Tasks
- Build Streamlit dashboard
- Update architecture diagram
- Prepare research documentation
- Prepare demo scenarios

### Deliverables
- architecture_diagram.png
- demo_script.md
- report_sections.tex

---

# Week 3 Deliverables

1. Evaluation report
2. Retrieval optimization report
3. LoRA adapters
4. Multi‑tenant runtime
5. Monitoring logs

Expected result:

Pipeline 3 → fully evaluated  
Retrieval → optimized  
LoRA adapters → trained  
Multi‑tenant runtime → working  
System monitoring → enabled
