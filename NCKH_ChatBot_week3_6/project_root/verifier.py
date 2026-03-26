def verify_answer(answer, docs):
    if not docs:
        return True

    context = " ".join([d.get("content", "") for d in docs])

    if len(answer.strip()) < 15:
        return False

    overlap = sum(1 for w in answer.split() if w in context)

    return overlap >= 3