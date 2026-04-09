# Retrieval Tuning Report

Tiêu chí chọn cấu hình tốt nhất: ưu tiên `MRR`, sau đó `Hit@1`, sau đó latency thấp hơn.

| Label | MRR | Hit@1 | Hit@3 | Hit@5 | Avg Latency (ms) | Overrides |
| --- | --- | --- | --- | --- | --- | --- |
| grid_500_80_top4 | 0.919 | 0.861 | 0.972 | 1.000 | 196.47 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 500, "chunk_overlap": 80, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_500_120_top4 | 0.890 | 0.806 | 0.972 | 1.000 | 201.03 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 500, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| query_expansion | 0.884 | 0.778 | 1.000 | 1.000 | 193.55 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false}` |
| topk_4 | 0.884 | 0.778 | 1.000 | 1.000 | 193.77 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_900_160_top4 | 0.884 | 0.778 | 1.000 | 1.000 | 202.38 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 900, "chunk_overlap": 160, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_900_120_top4 | 0.884 | 0.778 | 1.000 | 1.000 | 202.83 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 900, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_700_120_top4 | 0.884 | 0.778 | 1.000 | 1.000 | 206.44 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_700_80_top4 | 0.884 | 0.778 | 1.000 | 1.000 | 209.10 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 80, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_700_160_top4 | 0.880 | 0.778 | 1.000 | 1.000 | 203.16 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 160, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| topk_5 | 0.875 | 0.750 | 1.000 | 1.000 | 193.59 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 5, "reranker_top_n": 10}` |
| reranker_only | 0.870 | 0.750 | 1.000 | 1.000 | 78.90 | `{"enable_query_expansion": false, "enable_hybrid_retrieval": false, "enable_reranker": true}` |
| baseline_dense | 0.870 | 0.750 | 1.000 | 1.000 | 83.11 | `{"enable_query_expansion": false, "enable_hybrid_retrieval": false, "enable_reranker": false}` |
| topk_6 | 0.861 | 0.722 | 1.000 | 1.000 | 196.60 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 700, "chunk_overlap": 120, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 6, "reranker_top_n": 12}` |
| grid_900_80_top4 | 0.838 | 0.694 | 1.000 | 1.000 | 205.08 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 900, "chunk_overlap": 80, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| grid_500_160_top4 | 0.836 | 0.694 | 0.972 | 1.000 | 204.28 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 500, "chunk_overlap": 160, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}` |
| full_optimized | 0.760 | 0.611 | 0.917 | 1.000 | 206.88 | `{"enable_query_expansion": true, "enable_hybrid_retrieval": true, "enable_reranker": true}` |
| hybrid_only | 0.743 | 0.556 | 0.944 | 1.000 | 82.20 | `{"enable_query_expansion": false, "enable_hybrid_retrieval": true, "enable_reranker": false}` |

## Best Config

- Label: `grid_500_80_top4`
- Overrides: `{"enable_query_expansion": true, "enable_hybrid_retrieval": false, "enable_reranker": false, "chunk_size": 500, "chunk_overlap": 80, "query_expansion_count": 4, "hybrid_alpha": 0.55, "top_k": 4, "reranker_top_n": 8}`
- MRR: 0.919
- Hit@1: 0.861
- Avg Retrieval Latency: 196.47 ms
