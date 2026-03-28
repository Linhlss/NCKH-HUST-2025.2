from __future__ import annotations

import hashlib
import re
from typing import Any, Dict, List, Tuple

from query_expansion import expand_query
from reranker import rerank

from project_root.config import MAX_SOURCE_NODES
from project_root.models import TenantProfile, TenantRuntime


def extract_node_text(result: Any) -> str:
    if isinstance(result, dict):
        if "content" in result:
            return str(result.get("content", "")).strip()
        if "text_preview" in result:
            return str(result.get("text_preview", "")).strip()

    node = getattr(result, "node", result)
    if hasattr(node, "get_content"):
        try:
            return node.get_content().strip()
        except Exception:
            return ""
    return str(node).strip()


def extract_node_metadata(result: Any) -> Dict[str, Any]:
    if isinstance(result, dict):
        return dict(result.get("metadata") or {})
    node = getattr(result, "node", result)
    return dict(getattr(node, "metadata", {}) or {})


def extract_node_score(result: Any) -> float:
    if isinstance(result, dict):
        return float(result.get("score", 0.0) or 0.0)
    return float(getattr(result, "score", 0.0) or 0.0)


def extract_node_id(result: Any) -> str:
    if isinstance(result, dict):
        raw = result.get("id")
        if raw:
            return str(raw)

    node = getattr(result, "node", result)
    node_id = getattr(node, "node_id", "")
    if node_id:
        return str(node_id)

    meta = extract_node_metadata(result)
    source = str(meta.get("source_ref") or meta.get("file_name") or meta.get("source_url") or "")
    text = extract_node_text(result)
    return hashlib.sha1(f"{source}::{text[:200]}".encode("utf-8", errors="ignore")).hexdigest()


def file_hints_from_question(question: str) -> List[str]:
    patterns = re.findall(
        r"[\w\-.]+\.(?:pdf|docx|doc|xlsx|xls|txt|md)",
        question,
        flags=re.IGNORECASE,
    )
    return [p.lower() for p in patterns]


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.lower()))


def prioritize_nodes_by_file_hint(nodes: List[Any], hints: List[str], query: str = "") -> List[Any]:
    if not hints and not query:
        return nodes

    query_terms = _tokenize(query)

    def score_item(item: Any) -> Tuple[int, int, float]:
        meta = extract_node_metadata(item)
        file_name = str(meta.get("file_name") or meta.get("source_ref") or "").lower()
        matched = any(h in file_name for h in hints)
        text = extract_node_text(item)[:1200]
        overlap = len(query_terms & _tokenize(text)) if query_terms else 0
        raw_score = extract_node_score(item)
        return (1 if matched else 0, overlap, raw_score)

    return sorted(nodes, key=score_item, reverse=True)


def format_source(meta: Dict[str, Any], score: float) -> str:
    file_name = meta.get("file_name")
    source_ref = meta.get("source_ref")
    source_url = meta.get("source_url")
    scope = meta.get("tenant_scope", "unknown")

    main = file_name or source_ref or source_url or "Nguồn không xác định"
    parts = [main, f"scope={scope}", f"score={score:.3f}"]

    for key in ["page_label", "page", "sheet_name", "loaded_at"]:
        if meta.get(key):
            parts.append(f"{key}={meta[key]}")

    return " | ".join(parts)


def _dense_search(runtime: TenantRuntime, query: str, top_k: int) -> List[dict]:
    retriever = runtime.index.as_retriever(similarity_top_k=top_k)
    raw_nodes = list(retriever.retrieve(query))
    items: List[dict] = []
    for node in raw_nodes:
        items.append(
            {
                "id": extract_node_id(node),
                "content": extract_node_text(node),
                "metadata": extract_node_metadata(node),
                "score": extract_node_score(node),
                "raw": node,
            }
        )
    return items


def _merge_best(items: List[dict]) -> List[dict]:
    best: Dict[str, dict] = {}
    for item in items:
        item_id = extract_node_id(item)
        previous = best.get(item_id)
        if previous is None or float(item.get("score", 0.0) or 0.0) > float(previous.get("score", 0.0) or 0.0):
            best[item_id] = item
    merged = list(best.values())
    merged.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
    return merged


def _expanded_queries(question: str, retrieval_query: str, profile: TenantProfile) -> List[str]:
    base_query = retrieval_query or question
    if not profile.enable_query_expansion:
        return [base_query]
    return expand_query(base_query, max_queries=profile.query_expansion_count)


def retrieve_ranked_items(
    runtime: TenantRuntime,
    question: str,
    retrieval_query: str | None = None,
    profile: TenantProfile | None = None,
) -> List[dict]:
    profile = profile or runtime.profile
    candidate_top_k = max(profile.top_k * 3, profile.reranker_top_n, MAX_SOURCE_NODES, 8)

    aggregated: List[dict] = []
    for query in _expanded_queries(question, retrieval_query or question, profile):
        dense_items = _dense_search(runtime, query, candidate_top_k)
        if profile.enable_hybrid_retrieval and runtime.hybrid_retriever is not None:
            query_items = runtime.hybrid_retriever.search(
                query=query,
                dense_items=dense_items,
                top_k=candidate_top_k,
                alpha=profile.hybrid_alpha,
            )
        else:
            query_items = dense_items
        aggregated.extend(query_items)

    ranked = _merge_best(aggregated)
    ranked = prioritize_nodes_by_file_hint(ranked, file_hints_from_question(question), retrieval_query or question)

    if profile.enable_reranker:
        rerank_pool = ranked[: max(profile.reranker_top_n, profile.top_k)]
        reranked = rerank(retrieval_query or question, rerank_pool)
        remainder = ranked[len(rerank_pool) :]
        ranked = reranked + remainder

    return ranked


def retrieve_context(runtime: TenantRuntime, question: str, retrieval_query: str | None = None) -> Tuple[str, List[str]]:
    try:
        ranked = retrieve_ranked_items(runtime, question, retrieval_query=retrieval_query, profile=runtime.profile)
    except Exception:
        return "", []

    context_blocks: List[str] = []
    sources: List[str] = []

    for i, item in enumerate(ranked[:MAX_SOURCE_NODES], start=1):
        text = extract_node_text(item)[:1400]
        meta = extract_node_metadata(item)
        score = extract_node_score(item)
        src = format_source(meta, score)
        context_blocks.append(f"[Dữ liệu {i}] ({src})\n{text}")
        sources.append(src)

    return "\n\n".join(context_blocks), list(dict.fromkeys(sources))
