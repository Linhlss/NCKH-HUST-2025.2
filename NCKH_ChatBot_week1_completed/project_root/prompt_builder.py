from __future__ import annotations

from llama_index.core import PromptTemplate

from models import TenantProfile


def build_augmented_prompt(
    profile: TenantProfile,
    question: str,
    memory_text: str,
    retrieved_context: str,
    tool_result: str = "",
) -> str:
    template = PromptTemplate(
        """
Bạn là chuyên gia AI cao cấp của hệ thống Multi-tenant Agentic RAG.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}
- Gợi ý ngôn ngữ: {language_hint}

[QUY TẮC NGÔN NGỮ]
1. Nhận diện ngôn ngữ câu hỏi hiện tại.
2. Bắt buộc trả lời đúng bằng chính ngôn ngữ đó.
3. Không tự ý chuyển sang tiếng Anh nếu người dùng không dùng tiếng Anh.

[QUY TẮC NỘI DUNG]
1. Ưu tiên dùng dữ liệu thật trong [KẾT QUẢ CÔNG CỤ] và [NGỮ CẢNH TRUY XUẤT].
2. Không dùng placeholder như [insert topic here].
3. Nếu dữ liệu không đủ, phải nói rõ phần nào chưa đủ.
4. Trả lời có cấu trúc, rõ ràng, chuyên nghiệp.
5. Không bịa nguồn.

[LỊCH SỬ HỘI THOẠI]
{memory_text}

[KẾT QUẢ CÔNG CỤ]
{tool_result}

[NGỮ CẢNH TRUY XUẤT]
{retrieved_context}

[CÂU HỎI HIỆN TẠI]
{question}

[CHỈ THỊ CUỐI]
Trả lời ngay bằng đúng ngôn ngữ của câu hỏi. Nếu thiếu dữ liệu, hãy nói rõ thiếu ở đâu.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        language_hint=profile.language_hint,
        memory_text=memory_text or "Không có lịch sử.",
        tool_result=tool_result or "Không có.",
        retrieved_context=retrieved_context or "Không có.",
        question=question,
    )


def append_sources(answer: str, sources: list[str], show_sources: bool) -> str:
    if not show_sources or not sources:
        return answer
    unique_sources = list(dict.fromkeys(sources))
    return answer.strip() + "\n\nNguồn sử dụng:\n- " + "\n- ".join(unique_sources)