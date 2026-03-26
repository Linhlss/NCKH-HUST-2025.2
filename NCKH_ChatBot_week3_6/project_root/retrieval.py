from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

from project_root.config import MAX_SOURCE_NODES
from project_root.models import TenantRuntime


def extract_node_text(result: Any) -> str:
    node = getattr(result, "node", result)
    if hasattr(node, "get_content"):
        try:
            return node.get_content().strip()
        except Exception:
            return ""
    return str(node).strip()


def extract_node_metadata(result: Any) -> Dict[str, Any]:
    node = getattr(result, "node", result)
    return dict(getattr(node, "metadata", {}) or {})


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
        raw_score = float(getattr(item, "score", 0.0) or 0.0)
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


def retrieve_context(runtime: TenantRuntime, question: str, retrieval_query: str | None = None) -> Tuple[str, List[str]]:
    effective_query = retrieval_query or question
    try:
        raw_nodes = runtime.retriever.retrieve(effective_query)
    except Exception:
        return "", []

    hints = file_hints_from_question(question)
    nodes = prioritize_nodes_by_file_hint(list(raw_nodes), hints, effective_query)

    context_blocks: List[str] = []
    sources: List[str] = []

    for i, item in enumerate(nodes[:MAX_SOURCE_NODES], start=1):
        text = extract_node_text(item)[:1400]
        meta = extract_node_metadata(item)
        score = float(getattr(item, "score", 0.0) or 0.0)
        src = format_source(meta, score)
        context_blocks.append(f"[Dữ liệu {i}] ({src})\n{text}")
        sources.append(src)

    return "\n\n".join(context_blocks), list(dict.fromkeys(sources))
