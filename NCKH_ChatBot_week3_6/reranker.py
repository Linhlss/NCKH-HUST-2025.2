
from sentence_transformers import CrossEncoder

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, docs):
    pairs = [[query, d["content"]] for d in docs]
    scores = model.predict(pairs)

    for i, s in enumerate(scores):
        docs[i]["score"] = float(s)

    return sorted(docs, key=lambda x: x["score"], reverse=True)
