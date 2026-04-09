from __future__ import annotations

import os
import re
from typing import Dict, List, Sequence

_MODEL = None
_MODEL_ERROR: str | None = None


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"\w+", (text or "").lower()))


def _fallback_score(query: str, content: str) -> float:
    query_tokens = {token for token in _tokenize(query) if len(token) > 1}
    if not query_tokens:
        return 0.0
    content_tokens = _tokenize(content)
    return len(query_tokens & content_tokens) / max(len(query_tokens), 1)


def _get_model():
    global _MODEL, _MODEL_ERROR
    if _MODEL is not None or _MODEL_ERROR is not None:
        return _MODEL
    if os.getenv("ENABLE_CROSS_ENCODER", "false").strip().lower() != "true":
        _MODEL_ERROR = "Cross-encoder disabled in offline/runtime-safe mode."
        return None

    try:
        from sentence_transformers import CrossEncoder

        _MODEL = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", local_files_only=True)
    except Exception as exc:
        _MODEL_ERROR = str(exc)
        _MODEL = None

    return _MODEL


def rerank(query: str, docs: Sequence[dict]) -> List[dict]:
    docs = [dict(item) for item in docs]
    if not docs:
        return []

    model = _get_model()
    if model is None:
        for item in docs:
            item["score"] = _fallback_score(query, str(item.get("content", "")))
        return sorted(docs, key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)

    pairs = [[query, str(item.get("content", ""))] for item in docs]
    scores = model.predict(pairs)

    for item, score in zip(docs, scores):
        item["score"] = float(score)

    return sorted(docs, key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
