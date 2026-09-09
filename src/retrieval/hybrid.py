"""
src/retrieval/hybrid.py
Hybrid lexical (BM25) and dense semantic retriever with Reciprocal Rank Fusion (RRF)
and convex score combination.
"""

from typing import List, Dict, Any, Optional
from src.retrieval.schemas import RetrievedCase
from src.retrieval.bm25 import BM25Retriever
from src.retrieval.dense import DenseSemanticRetriever

class HybridRetriever:
    def __init__(self, lexical_weight: float = 0.5, rrf_k: int = 60):
        self.lexical_retriever = BM25Retriever()
        self.dense_retriever = DenseSemanticRetriever()
        self.lexical_weight = lexical_weight
        self.rrf_k = rrf_k
        self.cases = []

    def fit(self, cases: List[Dict[str, Any]]):
        self.cases = cases
        print(f"  Fitting BM25 retriever over {len(cases):,} cases...")
        self.lexical_retriever.fit(cases)
        print(f"  Fitting Dense semantic retriever over {len(cases):,} cases...")
        self.dense_retriever.fit(cases)

    def retrieve(self, query: str, context: str = "", k: int = 5) -> List[RetrievedCase]:
        # Over-sample to blend candidate pools
        pool_size = max(k * 4, 20)
        lex_results = self.lexical_retriever.retrieve(query, context, k=pool_size)
        dense_results = self.dense_retriever.retrieve(query, context, k=pool_size)

        # Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        case_map: Dict[str, RetrievedCase] = {}

        for r in lex_results:
            rrf_scores[r.case_id] = rrf_scores.get(r.case_id, 0.0) + self.lexical_weight * (1.0 / (self.rrf_k + r.rank))
            case_map[r.case_id] = r

        for r in dense_results:
            rrf_scores[r.case_id] = rrf_scores.get(r.case_id, 0.0) + (1.0 - self.lexical_weight) * (1.0 / (self.rrf_k + r.rank))
            if r.case_id not in case_map:
                case_map[r.case_id] = r

        sorted_cases = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:k]
        
        final_results = []
        for rank, (cid, score) in enumerate(sorted_cases, 1):
            orig = case_map[cid]
            final_results.append(RetrievedCase(
                case_id=cid,
                score=round(float(score), 5),
                rank=rank,
                customer_message=orig.customer_message,
                historical_response=orig.historical_response,
                intent=orig.intent,
                preceding_context=orig.preceding_context
            ))
        return final_results
