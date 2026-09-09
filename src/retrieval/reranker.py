"""
src/retrieval/reranker.py
Two-stage retrieval reranker.
Takes top-K candidate cases from Hybrid/Dense retrieval and scores them using
exact n-gram overlap and token Jaccard similarity against the query to re-rank.
"""

from typing import List, Dict, Any
from src.retrieval.schemas import RetrievedCase
from src.retrieval.bm25 import tokenize

class SimpleReranker:
    def __init__(self, top_candidates: int = 15):
        self.top_candidates = top_candidates

    def rerank(self, query: str, context: str, candidates: List[RetrievedCase], top_k: int = 5) -> List[RetrievedCase]:
        q_tokens = set(tokenize(f"{query} {context}"))
        if not q_tokens or not candidates:
            return candidates[:top_k]

        scored = []
        for c in candidates:
            doc_tokens = set(tokenize(f"{c.customer_message} {c.historical_response}"))
            intersection = len(q_tokens.intersection(doc_tokens))
            union = len(q_tokens.union(doc_tokens))
            jaccard = (intersection / union) if union > 0 else 0.0
            
            # Blend initial retrieval score with reranker score
            blended_score = 0.6 * c.score + 0.4 * jaccard
            scored.append((blended_score, c))

        scored.sort(key=lambda x: x[0], reverse=True)
        reranked = []
        for rank, (score, c) in enumerate(scored[:top_k], 1):
            reranked.append(RetrievedCase(
                case_id=c.case_id,
                score=round(float(score), 4),
                rank=rank,
                customer_message=c.customer_message,
                historical_response=c.historical_response,
                intent=c.intent,
                preceding_context=c.preceding_context
            ))
        return reranked
