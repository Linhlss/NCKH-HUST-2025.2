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


def build_query_rewrite_prompt(
    profile: TenantProfile,
    question: str,
    memory_text: str,
) -> str:
    template = PromptTemplate(
        """
Bạn đang làm bước QUERY REWRITE cho chatbot tài liệu nội bộ.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}

[LỊCH SỬ HỘI THOẠI]
{memory_text}

[CÂU HỎI GỐC]
{question}

[MỤC TIÊU]
Viết lại câu truy vấn ngắn gọn để retrieval hiệu quả hơn.
- Giữ nguyên ý nghĩa gốc.
- Nếu câu hỏi đã rõ, trả lại gần như nguyên văn.
- Nếu câu hỏi tham chiếu mơ hồ như "nó", "cái đó", hãy tự làm rõ dựa trên lịch sử.
- Ưu tiên giữ các từ khóa tài liệu, tên file, quy chế, môn học, tín chỉ, học phí nếu có.
- Không trả lời câu hỏi.
- Chỉ xuất ra đúng 1 dòng truy vấn đã viết lại, không giải thích.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        memory_text=memory_text or "Không có lịch sử.",
        question=question,
    )


def build_rag_draft_prompt(
    profile: TenantProfile,
    question: str,
    rewritten_query: str,
    memory_text: str,
    retrieved_context: str,
) -> str:
    template = PromptTemplate(
        """
Bạn đang ở bước DRAFT ANSWER của prompt chaining.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}
- Gợi ý ngôn ngữ: {language_hint}

[LỊCH SỬ HỘI THOẠI]
{memory_text}

[CÂU HỎI GỐC]
{question}

[TRUY VẤN ĐÃ VIẾT LẠI]
{rewritten_query}

[NGỮ CẢNH TRUY XUẤT]
{retrieved_context}

[YÊU CẦU]
- Soạn câu trả lời nháp dựa chủ yếu trên ngữ cảnh truy xuất.
- Nếu ngữ cảnh không đủ, phải nói rõ thiếu dữ liệu nào.
- Không bịa thêm quy định, số liệu, hay nguồn.
- Trả lời đúng ngôn ngữ của người dùng.
- Chưa cần quá chau chuốt về văn phong, ưu tiên đúng ý và bám nguồn.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        language_hint=profile.language_hint,
        memory_text=memory_text or "Không có lịch sử.",
        question=question,
        rewritten_query=rewritten_query,
        retrieved_context=retrieved_context or "Không có ngữ cảnh truy xuất.",
    )


def build_general_draft_prompt(
    profile: TenantProfile,
    question: str,
    memory_text: str,
) -> str:
    template = PromptTemplate(
        """
Bạn đang ở bước DRAFT ANSWER cho câu hỏi general.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}
- Gợi ý ngôn ngữ: {language_hint}

[LỊCH SỬ HỘI THOẠI]
{memory_text}

[CÂU HỎI]
{question}

[YÊU CẦU]
- Trả lời trực tiếp, hữu ích, đúng ngôn ngữ của người dùng.
- Không giả vờ đã dùng tài liệu nội bộ.
- Nếu người dùng thật ra cần dữ liệu nội bộ, hãy nói ngắn gọn rằng họ nên hỏi rõ tài liệu/chủ đề.
- Đây là bản nháp, ưu tiên đúng ý trước.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        language_hint=profile.language_hint,
        memory_text=memory_text or "Không có lịch sử.",
        question=question,
    )


def build_verification_prompt(
    question: str,
    draft_answer: str,
    retrieved_context: str,
) -> str:
    template = PromptTemplate(
        """
Bạn đang ở bước VERIFY ANSWER.

[CÂU HỎI]
{question}

[BẢN NHÁP]
{draft_answer}

[NGỮ CẢNH TRUY XUẤT]
{retrieved_context}

[YÊU CẦU]
Hãy kiểm tra bản nháp với ngữ cảnh và tạo ra một bản đã hiệu chỉnh:
- Giữ lại các ý có thể được hỗ trợ bởi ngữ cảnh.
- Xóa hoặc giảm mức khẳng định đối với các ý không được hỗ trợ rõ.
- Nếu ngữ cảnh không đủ, nói rõ giới hạn dữ liệu.
- Không thêm thông tin mới ngoài ngữ cảnh.
- Trả ra trực tiếp bản trả lời đã hiệu chỉnh, không giải thích quy trình kiểm tra.
- Bắt buộc giữ đúng ngôn ngữ của câu hỏi.
""".strip()
    )
    return template.format(
        question=question,
        draft_answer=draft_answer,
        retrieved_context=retrieved_context or "Không có ngữ cảnh truy xuất.",
    )


def build_style_rewrite_prompt(
    profile: TenantProfile,
    question: str,
    answer_text: str,
    use_internal_context: bool,
) -> str:
    style_note = (
        "Vì đây là câu trả lời có dùng tài liệu nội bộ, hãy ưu tiên cấu trúc rõ ràng, bám dữ liệu, và thừa nhận thiếu dữ liệu nếu có."
        if use_internal_context
        else "Vì đây là câu trả lời general, hãy giữ ngắn gọn, tự nhiên và trực tiếp."
    )

    template = PromptTemplate(
        """
Bạn đang ở bước STYLE REWRITE.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}
- Gợi ý ngôn ngữ: {language_hint}

[CÂU HỎI GỐC]
{question}

[CÂU TRẢ LỜI CẦN VIẾT LẠI]
{answer_text}

[HƯỚNG DẪN VĂN PHONG]
{style_note}

[YÊU CẦU]
- Viết lại cho rõ ràng, tự nhiên và chuyên nghiệp.
- Không thêm thông tin mới.
- Giữ nguyên ý nghĩa.
- Bắt buộc trả lời đúng ngôn ngữ của câu hỏi gốc.
- Không được mở đầu bằng các câu như "Here is the rewritten answer", "Dưới đây là câu trả lời đã viết lại", hoặc giải thích quy trình.
- Chỉ trả về câu trả lời cuối cùng.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        language_hint=profile.language_hint,
        question=question,
        answer_text=answer_text,
        style_note=style_note,
    )


def append_sources(answer: str, sources: list[str], show_sources: bool) -> str:
    if not show_sources or not sources:
        return answer
    unique_sources = list(dict.fromkeys(sources))
    return answer.strip() + "\n\nNguồn sử dụng:\n- " + "\n- ".join(unique_sources)


def build_general_prompt(
    profile: TenantProfile,
    question: str,
    memory_text: str,
) -> str:
    template = PromptTemplate(
        """
Bạn là trợ lý AI thân thiện và chính xác của hệ thống Multi-tenant Agentic RAG.

[HỒ SƠ KHÁCH HÀNG]
- Tên hiển thị: {display_name}
- Persona: {persona}
- Gợi ý ngôn ngữ: {language_hint}

[QUY TẮC]
1. Trả lời đúng ngôn ngữ của người dùng.
2. Với câu hỏi kiến thức chung hoặc hội thoại, không giả vờ có dữ liệu nội bộ nếu không dùng RAG.
3. Nếu câu hỏi cần dữ liệu tài liệu nội bộ mà chưa có, hãy đề nghị người dùng hỏi rõ tên tài liệu hoặc chủ đề cần tra cứu.
4. Trả lời ngắn gọn, rõ ràng, hữu ích.

[LỊCH SỬ HỘI THOẠI]
{memory_text}

[CÂU HỎI HIỆN TẠI]
{question}

[CHỈ THỊ CUỐI]
Trả lời trực tiếp bằng đúng ngôn ngữ của câu hỏi hiện tại.
""".strip()
    )
    return template.format(
        display_name=profile.display_name,
        persona=profile.persona,
        language_hint=profile.language_hint,
        memory_text=memory_text or "Không có lịch sử.",
        question=question,
    )


def build_out_of_scope_answer(question: str) -> str:
    return (
        "Xin lỗi, câu hỏi này hiện nằm ngoài phạm vi hỗ trợ an toàn hoặc ngoài phạm vi chatbot tài liệu nội bộ. "
        "Bạn có thể hỏi về tài liệu nội bộ, quy chế, thời khóa biểu, hoặc các câu hỏi kiến thức chung an toàn. "
        f"Câu hỏi vừa nhận: {question}"
    )


def build_prompt(query, docs, history=None):
    context = "\n\n".join([d["content"] for d in docs])

    history_text = ""
    if history:
        history_text = "\n".join(
            [f"User: {h['query']}\nBot: {h['response']}" for h in history]
        )

    return f"""
Lịch sử:
{history_text}

Context:
{context}

Câu hỏi:
{query}

Trả lời:
"""