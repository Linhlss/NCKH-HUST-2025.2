from __future__ import annotations

import math
import re
from typing import Dict, List, Sequence


def _tokenize(text: str) -> List[str]:
    return re.findall(r"\w+", (text or "").lower())


def _normalize_scores(values: Sequence[float]) -> List[float]:
    values = list(values)
    if not values:
        return []
    low = min(values)
    high = max(values)
    if math.isclose(low, high):
        return [1.0 if high > 0 else 0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


class HybridRetriever:
    def __init__(self, documents: Sequence[dict]):
        self.documents = list(documents)
        self.doc_tokens = [_tokenize(doc.get("content", "")) for doc in self.documents]
        self.doc_lengths = [len(tokens) for tokens in self.doc_tokens]
        self.avg_doc_len = (sum(self.doc_lengths) / len(self.doc_lengths)) if self.doc_lengths else 0.0

        self.doc_freqs: Dict[str, int] = {}
        for tokens in self.doc_tokens:
            for token in set(tokens):
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def _idf(self, token: str) -> float:
        doc_count = len(self.documents)
        freq = self.doc_freqs.get(token, 0)
        return math.log(1 + (doc_count - freq + 0.5) / (freq + 0.5)) if doc_count else 0.0

    def _bm25_scores(self, query: str, k1: float = 1.5, b: float = 0.75) -> List[float]:
        query_tokens = _tokenize(query)
        if not query_tokens or not self.documents:
            return [0.0 for _ in self.documents]

        scores: List[float] = []
        for tokens in self.doc_tokens:
            token_freq: Dict[str, int] = {}
            for token in tokens:
                token_freq[token] = token_freq.get(token, 0) + 1

            doc_len = len(tokens) or 1
            score = 0.0
            for token in query_tokens:
                freq = token_freq.get(token, 0)
                if not freq:
                    continue
                idf = self._idf(token)
                denom = freq + k1 * (1 - b + b * (doc_len / (self.avg_doc_len or 1.0)))
                score += idf * (freq * (k1 + 1)) / denom
            scores.append(score)
        return scores

    def search(
        self,
        query: str,
        dense_items: Sequence[dict],
        top_k: int = 10,
        alpha: float = 0.5,
    ) -> List[dict]:
        dense_score_map = {str(item.get("id", "")): float(item.get("score", 0.0) or 0.0) for item in dense_items}

        bm25_scores = self._bm25_scores(query)
        norm_bm25 = _normalize_scores(bm25_scores)

        dense_scores = [dense_score_map.get(str(doc.get("id", "")), 0.0) for doc in self.documents]
        norm_dense = _normalize_scores(dense_scores)

        merged: List[dict] = []
        for idx, doc in enumerate(self.documents):
            combined = alpha * norm_bm25[idx] + (1.0 - alpha) * norm_dense[idx]
            if combined <= 0 and not dense_scores[idx] and not bm25_scores[idx]:
                continue
            merged.append(
                {
                    **doc,
                    "bm25_score": bm25_scores[idx],
                    "dense_score": dense_scores[idx],
                    "score": combined,
                }
            )

        merged.sort(key=lambda item: float(item.get("score", 0.0) or 0.0), reverse=True)
        return merged[:top_k]
