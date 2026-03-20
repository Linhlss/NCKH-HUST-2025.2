
import json

def hit_at_k(results, relevant_docs, k):
    top_k = [r.get("source", "") for r in results[:k]]
    return int(any(doc in top_k for doc in relevant_docs))

def mrr(results, relevant_docs):
    for i, r in enumerate(results):
        if r.get("source", "") in relevant_docs:
            return 1 / (i + 1)
    return 0

def evaluate(retrieve_fn, dataset_path):
    with open(dataset_path, encoding="utf-8") as f:
        data = json.load(f)

    hit3 = hit5 = mrr_score = 0

    for item in data:
        query = item["query"]
        relevant = item["relevant_docs"]

        results = retrieve_fn(query)

        hit3 += hit_at_k(results, relevant, 3)
        hit5 += hit_at_k(results, relevant, 5)
        mrr_score += mrr(results, relevant)

    n = len(data)
    return {
        "Hit@3": hit3 / n,
        "Hit@5": hit5 / n,
        "MRR": mrr_score / n
    }

if __name__ == "__main__":
    print("Plug your retrieve() function before running.")
