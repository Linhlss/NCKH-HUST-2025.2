from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from models import TenantProfile
from tools import detect_direct_tool

_ROUTE_TOOL = "tool"
_ROUTE_RAG = "rag"
_ROUTE_GENERAL = "general"
_ROUTE_OUT_OF_SCOPE = "out_of_scope"

_RAG_KEYWORDS = {
    "quy chế", "qcdt", "học phần", "tín chỉ", "đào tạo", "thời khóa biểu", "tkb",
    "môn học", "lịch học", "file", "tài liệu", "pdf", "xlsx", "doc", "docx",
    "quy định", "ngành", "điểm", "học phí", "biểu mẫu", "source", "nguồn", "văn bản",
}
_GENERAL_PATTERNS = [
    r"^(xin chào|chào|hello|hi)\b",
    r"\b(bạn là ai|who are you)\b",
    r"\b(cảm ơn|thanks|thank you)\b",
    r"\b(giải thích|explain)\b",
    r"\b(tóm tắt|summarize)\b",
    r"\b(viết|write)\b",
]
_OUT_OF_SCOPE_PATTERNS = [
    r"\b(hack|crack|malware|virus|ddos)\b",
    r"\b(bom|vũ khí|weapon|ma túy|drug synthesis)\b",
]


@dataclass
class RouterResult:
    route: str
    reason: str
    direct_answer: Optional[str] = None


_FILE_HINT_RE = re.compile(r"[\w\-.]+\.(?:pdf|docx|doc|xlsx|xls|txt|md)", re.IGNORECASE)


def _looks_like_rag_question(question: str) -> bool:
    q = question.lower()
    if _FILE_HINT_RE.search(question):
        return True
    return any(keyword in q for keyword in _RAG_KEYWORDS)


def _looks_general(question: str) -> bool:
    q = question.strip().lower()
    return any(re.search(pattern, q) for pattern in _GENERAL_PATTERNS)


def _looks_out_of_scope(question: str) -> bool:
    q = question.strip().lower()
    return any(re.search(pattern, q) for pattern in _OUT_OF_SCOPE_PATTERNS)


def route_question(question: str, profile: TenantProfile, user_id: str) -> RouterResult:
    direct = detect_direct_tool(question, profile, user_id)
    if direct:
        return RouterResult(route=_ROUTE_TOOL, reason="Khớp tool trực tiếp.", direct_answer=direct)

    if _looks_out_of_scope(question):
        return RouterResult(route=_ROUTE_OUT_OF_SCOPE, reason="Nội dung bị đánh dấu ngoài phạm vi hỗ trợ.")

    if _looks_like_rag_question(question):
        return RouterResult(route=_ROUTE_RAG, reason="Câu hỏi có dấu hiệu cần dữ liệu nội bộ/tài liệu.")

    if _looks_general(question):
        return RouterResult(route=_ROUTE_GENERAL, reason="Câu hỏi mang tính hội thoại hoặc kiến thức chung.")

    # Mặc định: ưu tiên general để tránh đẩy mọi câu hỏi vào full RAG.
    return RouterResult(route=_ROUTE_GENERAL, reason="Không có dấu hiệu bắt buộc phải dùng RAG.")
