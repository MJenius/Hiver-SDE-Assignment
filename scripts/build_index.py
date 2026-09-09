"""
scripts/build_index.py
Builds and serializes the canonical historical case retrieval index over TRAIN only.
Guarantees 0% leakage: NEVER indexes cases from dev, val, or test.
Outputs data/index_manifest.json and serialized retrieval index.
"""

import os
import sys
import json
import pickle
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.retrieval.hybrid import HybridRetriever

CASES_PATH = "data/processed/cases.jsonl"
INDEX_PATH = "data/retrieval_index.pkl"
MANIFEST_PATH = "data/index_manifest.json"

def build_index(max_cases: int = 30000):
    print("=== Building Canonical Retrieval Index (TRAIN Split Only) ===")
    train_cases = []

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            if c["split"] == "train":
                train_cases.append({
                    "case_id": c["case_id"],
                    "conversation_id": c["conversation_id"],
                    "customer_message": c["customer_message"],
                    "preceding_context_text": c["preceding_context_text"],
                    "historical_support_response": c["historical_support_response"],
                    "intent": c.get("intent", "unknown")
                })
                if len(train_cases) >= max_cases:
                    break

    print(f"Loaded {len(train_cases):,} TRAIN cases for indexing.")
    
    retriever = HybridRetriever(lexical_weight=0.5)
    retriever.fit(train_cases)

    print(f"Saving serialized retriever to {INDEX_PATH}...")
    with open(INDEX_PATH, "wb") as f:
        pickle.dump(retriever, f)

    manifest = {
        "index_name": "AppleSupport Canonical Retrieval Index",
        "index_version": "1.0",
        "built_at": datetime.utcnow().isoformat() + "Z",
        "indexed_split": "train",
        "total_cases_indexed": len(train_cases),
        "source_cases_file": CASES_PATH,
        "models": {
            "lexical": "BM25 (k1=1.5, b=0.75)",
            "dense": "Sublinear TF-IDF (1-2 grams, max_features=10000)",
            "fusion": "Reciprocal Rank Fusion (rrf_k=60, weight=0.5)"
        }
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Index manifest saved to {MANIFEST_PATH}.")

if __name__ == "__main__":
    build_index()
