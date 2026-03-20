def rewrite_answer(answer, docs):
    sources = list(set([d.get("source", "") for d in docs]))

    source_text = ", ".join(sources) if sources else "Hệ thống"

    return f"""📌 Trả lời:

{answer}

---
📚 Nguồn: {source_text}
"""