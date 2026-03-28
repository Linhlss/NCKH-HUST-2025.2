from __future__ import annotations

import re
from typing import List


def _normalize_spaces(text: str) -> str:
    return " ".join(text.split()).strip()


def expand_query(query: str, max_queries: int = 4) -> List[str]:
    base = _normalize_spaces(query)
    if not base:
        return []

    candidates = [
        base,
        f"giải thích {base}",
        f"thông tin về {base}",
    ]

    lowered = base.lower()
    if re.search(r"\b(điều|chương|mục|quy chế|qcdt)\b", lowered):
        candidates.append(f"trích nội dung văn bản cho {base}")
    else:
        candidates.append(f"{base} là gì")

    deduped: List[str] = []
    for item in candidates:
        normalized = _normalize_spaces(item)
        if normalized and normalized not in deduped:
            deduped.append(normalized)

    return deduped[: max(1, max_queries)]
