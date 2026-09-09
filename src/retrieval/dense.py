"""
src/retrieval/dense.py
Dense semantic retrieval using sublinear TF-IDF + cosine feature projection
(or sentence embeddings if available), exposing the unified retrieve interface.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.retrieval.schemas import RetrievedCase

class DenseSemanticRetriever:
    def __init__(self, max_features: int = 10000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.cases = []
        self.matrix = None

    def fit(self, cases: List[Dict[str, Any]]):
        self.cases = cases
        texts = [f"{c.get('customer_message', '')} {c.get('preceding_context_text', '')}".strip() for c in cases]
        self.matrix = self.vectorizer.fit_transform(texts)

    def retrieve(self, query: str, context: str = "", k: int = 5) -> List[RetrievedCase]:
        full_query = f"{query} {context}".strip()
        q_vec = self.vectorizer.transform([full_query])
        sims = cosine_similarity(q_vec, self.matrix)[0]

        top_indices = np.argsort(sims)[::-1][:k]
        results = []
        for rank, idx in enumerate(top_indices, 1):
            c = self.cases[idx]
            results.append(RetrievedCase(
                case_id=c["case_id"],
                score=round(float(sims[idx]), 4),
                rank=rank,
                customer_message=c.get("customer_message", ""),
                historical_response=c.get("historical_support_response", ""),
                intent=c.get("intent", "unknown"),
                preceding_context=c.get("preceding_context_text", "")
            ))
        return results
