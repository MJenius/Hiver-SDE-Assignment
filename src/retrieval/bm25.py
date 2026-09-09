"""
src/retrieval/bm25.py
Pure-Python, zero-dependency BM25 retrieval engine optimized for customer support text.
Implements Okapi BM25 ranking (k1=1.5, b=0.75) over tokenized customer inquiries and context.
"""

import math
import re
from typing import List, Dict, Any, Optional
from collections import Counter
from src.retrieval.schemas import RetrievedCase

def tokenize(text: str) -> List[str]:
    if not isinstance(text, str):
        return []
    # Lowercase and split on non-alphanumeric
    tokens = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", text.lower())
    # Exclude @mentions and pure urls
    return [t for t in tokens if not t.startswith("http")]

class BM25Retriever:
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.doc_len = []
        self.avg_doc_len = 0.0
        self.corpus_size = 0
        self.doc_freqs = Counter()
        self.idf = {}
        self.cases = []
        self.term_freqs = []

    def fit(self, cases: List[Dict[str, Any]]):
        """
        Builds the BM25 inverted index over historical training cases.
        """
        self.cases = cases
        self.corpus_size = len(cases)
        total_len = 0
        self.doc_len = []
        self.term_freqs = []
        self.doc_freqs = Counter()

        for c in cases:
            text = f"{c.get('customer_message', '')} {c.get('preceding_context_text', '')}"
            tokens = tokenize(text)
            t_len = len(tokens)
            self.doc_len.append(t_len)
            total_len += t_len

            tf = Counter(tokens)
            self.term_freqs.append(tf)
            for term in tf.keys():
                self.doc_freqs[term] += 1

        self.avg_doc_len = (total_len / self.corpus_size) if self.corpus_size > 0 else 0.0

        # Precompute IDF
        for term, freq in self.doc_freqs.items():
            # Standard Lucene/Okapi IDF formula
            self.idf[term] = math.log(1.0 + (self.corpus_size - freq + 0.5) / (freq + 0.5))

    def retrieve(self, query: str, context: str = "", k: int = 5) -> List[RetrievedCase]:
        full_query = f"{query} {context}".strip()
        q_tokens = tokenize(full_query)
        if not q_tokens or self.corpus_size == 0:
            return []

        scores = [0.0] * self.corpus_size

        for term in q_tokens:
            if term not in self.idf:
                continue
            idf_val = self.idf[term]
            for doc_idx, tf_dict in enumerate(self.term_freqs):
                if term in tf_dict:
                    freq = tf_dict[term]
                    d_len = self.doc_len[doc_idx]
                    denom = freq + self.k1 * (1.0 - self.b + self.b * (d_len / self.avg_doc_len))
                    scores[doc_idx] += idf_val * ((freq * (self.k1 + 1.0)) / denom)

        # Top-k selection
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        
        results = []
        for rank, idx in enumerate(top_indices, 1):
            c = self.cases[idx]
            results.append(RetrievedCase(
                case_id=c["case_id"],
                score=round(float(scores[idx]), 4),
                rank=rank,
                customer_message=c.get("customer_message", ""),
                historical_response=c.get("historical_support_response", ""),
                intent=c.get("intent", "unknown"),
                preceding_context=c.get("preceding_context_text", "")
            ))
        return results
