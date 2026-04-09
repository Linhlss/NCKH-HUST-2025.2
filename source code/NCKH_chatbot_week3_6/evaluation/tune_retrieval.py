from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

TUNING_STORAGE_ROOT = Path("/tmp/retrieval_tuning_storage")
os.environ.setdefault("STORAGE_ROOT_OVERRIDE", str(TUNING_STORAGE_ROOT))
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from evaluation.evaluate_retrieval import evaluate_variant, load_cases


def _score(result: dict) -> tuple[float, float, float]:
    overall = result["overall_retrieval"]
    return (
        float(overall.get("mrr", 0.0) or 0.0),
        float(overall.get("hit_at_1", 0.0) or 0.0),
        -float(overall.get("avg_retrieval_latency_ms", 0.0) or 0.0),
    )


def _render_markdown(results: list[dict], best: dict) -> str:
    lines = [
        "# Retrieval Tuning Report",
        "",
        "Tiêu chí chọn cấu hình tốt nhất: ưu tiên `MRR`, sau đó `Hit@1`, sau đó latency thấp hơn.",
        "",
        "| Label | MRR | Hit@1 | Hit@3 | Hit@5 | Avg Latency (ms) | Overrides |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]

    for item in results:
        overall = item["overall_retrieval"]
        lines.append(
            f"| {item['label']} | {overall['mrr']:.3f} | {overall['hit_at_1']:.3f} | "
            f"{overall['hit_at_3']:.3f} | {overall['hit_at_5']:.3f} | {overall['avg_retrieval_latency_ms']:.2f} | "
            f"`{json.dumps(item['profile_overrides'], ensure_ascii=False)}` |"
        )

    lines.extend(
        [
            "",
            "## Best Config",
            "",
            f"- Label: `{best['label']}`",
            f"- Overrides: `{json.dumps(best['profile_overrides'], ensure_ascii=False)}`",
            f"- MRR: {best['overall_retrieval']['mrr']:.3f}",
            f"- Hit@1: {best['overall_retrieval']['hit_at_1']:.3f}",
            f"- Avg Retrieval Latency: {best['overall_retrieval']['avg_retrieval_latency_ms']:.2f} ms",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Tune retrieval config for runtime_profile variant.")
    parser.add_argument("--dataset", default="evaluation/test_queries.json")
    parser.add_argument("--json-out", default="evaluation/artifacts/retrieval_tuning.json")
    parser.add_argument("--md-out", default="evaluation/retrieval_tuning.md")
    args = parser.parse_args()

    shutil.rmtree(TUNING_STORAGE_ROOT, ignore_errors=True)
    TUNING_STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

    cases = load_cases(Path(args.dataset))

    stage1 = [
        ("baseline_dense", {"enable_query_expansion": False, "enable_hybrid_retrieval": False, "enable_reranker": False}),
        ("query_expansion", {"enable_query_expansion": True, "enable_hybrid_retrieval": False, "enable_reranker": False}),
        ("hybrid_only", {"enable_query_expansion": False, "enable_hybrid_retrieval": True, "enable_reranker": False}),
        ("reranker_only", {"enable_query_expansion": False, "enable_hybrid_retrieval": False, "enable_reranker": True}),
        ("full_optimized", {"enable_query_expansion": True, "enable_hybrid_retrieval": True, "enable_reranker": True}),
    ]

    results: list[dict] = []
    for label, overrides in stage1:
        result = evaluate_variant(cases, "runtime_profile", profile_overrides=overrides)
        result["label"] = label
        results.append(result)

    best_stage1 = max(results, key=_score)
    base_overrides = {
        **dict(best_stage1.get("profile_overrides") or {}),
        "chunk_size": 700,
        "chunk_overlap": 120,
        "query_expansion_count": 4,
        "hybrid_alpha": 0.55,
    }

    topk_results: list[dict] = []
    for top_k in [4, 5, 6]:
        overrides = {
            **base_overrides,
            "top_k": top_k,
            "reranker_top_n": max(top_k * 2, 8),
        }
        result = evaluate_variant(cases, "runtime_profile", profile_overrides=overrides)
        result["label"] = f"topk_{top_k}"
        results.append(result)
        topk_results.append(result)

    best_topk = max(topk_results, key=_score)
    selected_top_k = int(best_topk["profile_overrides"]["top_k"])

    for chunk_size, chunk_overlap in itertools.product([500, 700, 900], [80, 120, 160]):
        overrides = {
            **base_overrides,
            "chunk_size": chunk_size,
            "chunk_overlap": chunk_overlap,
            "top_k": selected_top_k,
            "reranker_top_n": max(selected_top_k * 2, 8),
        }
        result = evaluate_variant(cases, "runtime_profile", profile_overrides=overrides)
        result["label"] = f"grid_{chunk_size}_{chunk_overlap}_top{selected_top_k}"
        results.append(result)

    results.sort(key=_score, reverse=True)
    best = results[0]

    json_path = Path(args.json_out)
    md_path = Path(args.md_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {"selection_rule": "max(mrr, hit_at_1, -latency)", "best": best, "results": results}
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(_render_markdown(results, best), encoding="utf-8")

    print(f"Saved tuning results to {json_path}")
    print(f"Saved tuning markdown to {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
