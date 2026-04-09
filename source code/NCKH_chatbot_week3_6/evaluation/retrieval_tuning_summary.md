# Retrieval Tuning Summary

## Config được chọn cho checklist 2

- `enable_query_expansion = true`
- `enable_hybrid_retrieval = false`
- `enable_reranker = false`
- `top_k = 4`
- `chunk_size = 500`
- `chunk_overlap = 80`
- `query_expansion_count = 4`
- `hybrid_alpha = 0.55`
- `reranker_top_n = 8`

## Cơ sở chọn cấu hình

- Sweep exhaustive cho checklist 2 cho thấy cấu hình tốt nhất là `query_expansion` đơn với `chunk_size=500`, `chunk_overlap=80`, `top_k=4`.
- So với runtime mặc định trước khi bật optimization, cấu hình tốt nhất nâng metric retrieval từ:
  - `Hit@1`: `0.306` -> `0.861`
  - `Hit@3`: `0.611` -> `0.972`
  - `Hit@5`: `0.806` -> `1.000`
  - `MRR`: `0.497` -> `0.919`
- Trên bundle tốt nhất, `top_k = 4` là lựa chọn tối ưu theo rule `MRR -> Hit@1 -> latency`.

## Artifact liên quan

- `evaluation/retrieval_results_runtime_only.md`: runtime trước khi bật config tối ưu.
- `evaluation/retrieval_results_optimized.md`: runtime sau khi bật config tối ưu cuối cùng.
- `evaluation/error_analysis_optimized.md`: lỗi còn lại sau tối ưu.
- `evaluation/retrieval_tuning_final.md`: toàn bộ sweep và cấu hình tốt nhất.
