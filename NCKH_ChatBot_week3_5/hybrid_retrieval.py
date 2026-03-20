
from rank_bm25 import BM25Okapi
import numpy as np

class HybridRetriever:
    def __init__(self, documents, embeddings, embed_fn):
        self.documents = documents
        self.embed_fn = embed_fn
        self.embeddings = embeddings
        tokenized = [doc["content"].split() for doc in documents]
        self.bm25 = BM25Okapi(tokenized)

    def search(self, query, top_k=10, alpha=0.5):
        tokenized_query = query.split()
        bm25_scores = self.bm25.get_scores(tokenized_query)

        query_vec = self.embed_fn(query)
        vec_scores = np.dot(self.embeddings, query_vec)

        bm25_scores = (bm25_scores - np.min(bm25_scores)) / (np.ptp(bm25_scores) + 1e-6)
        vec_scores = (vec_scores - np.min(vec_scores)) / (np.ptp(vec_scores) + 1e-6)

        scores = alpha * bm25_scores + (1 - alpha) * vec_scores
        top_idx = np.argsort(scores)[::-1][:top_k]

        return [self.documents[i] for i in top_idx]
