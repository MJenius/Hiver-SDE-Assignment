"""
src/baselines/models.py
Implementation of Baseline 0, Baseline 1, and Baseline 2.
- Baseline 0: Majority-class intent prediction.
- Baseline 1: TF-IDF (1-2 grams) + Regularized Logistic Regression.
- Baseline 2: Semantic Nearest-Neighbor (TF-IDF sublinear cosine / centroid) inheriting historical intent and response.
"""

import os
import pickle
import json
import re
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics.pairwise import cosine_similarity

def clean_tweet(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"@\w+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

class Baseline0Majority:
    def __init__(self):
        self.majority_intent = "os_update_issues"
        self.confidence = 1.0

    def fit(self, intents: List[str]):
        counts = {}
        for it in intents:
            counts[it] = counts.get(it, 0) + 1
        if counts:
            self.majority_intent = max(counts.items(), key=lambda x: x[1])[0]
            self.confidence = counts[self.majority_intent] / len(intents)

    def predict(self, query: str) -> Dict[str, Any]:
        return {
            "intent": self.majority_intent,
            "confidence": round(float(self.confidence), 4),
            "baseline": "baseline_0_majority"
        }

class Baseline1TfidfLogReg:
    def __init__(self, max_features: int = 5000, C: float = 1.0):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english"
        )
        self.classifier = LogisticRegression(C=C, max_iter=500, solver="lbfgs")
        self.classes_ = []

    def fit(self, texts: List[str], labels: List[str]):
        cleaned = [clean_tweet(t) for t in texts]
        X = self.vectorizer.fit_transform(cleaned)
        self.classifier.fit(X, labels)
        self.classes_ = list(self.classifier.classes_)

    def predict(self, query: str) -> Dict[str, Any]:
        cleaned = clean_tweet(query)
        X = self.vectorizer.transform([cleaned])
        probs = self.classifier.predict_proba(X)[0]
        max_idx = int(np.argmax(probs))
        pred_label = self.classes_[max_idx]
        conf = float(probs[max_idx])
        return {
            "intent": pred_label,
            "confidence": round(conf, 4),
            "baseline": "baseline_1_tfidf_logreg"
        }

class Baseline2NearestNeighbor:
    def __init__(self, max_features: int = 10000):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self.indexed_cases = []
        self.index_matrix = None

    def fit(self, cases: List[Dict[str, Any]], intents: List[str]):
        """
        Indexes historical cases with their queries and responses.
        """
        self.indexed_cases = []
        texts = []
        for c, intent in zip(cases, intents):
            texts.append(clean_tweet(c["customer_message"]))
            self.indexed_cases.append({
                "case_id": c["case_id"],
                "customer_message": c["customer_message"],
                "historical_response": c["historical_support_response"],
                "intent": intent
            })
        self.index_matrix = self.vectorizer.fit_transform(texts)

    def predict(self, query: str) -> Dict[str, Any]:
        cleaned = clean_tweet(query)
        q_vec = self.vectorizer.transform([cleaned])
        sims = cosine_similarity(q_vec, self.index_matrix)[0]
        best_idx = int(np.argmax(sims))
        score = float(sims[best_idx])
        retrieved = self.indexed_cases[best_idx]
        return {
            "intent": retrieved["intent"],
            "confidence": round(score, 4),
            "retrieved_case_id": retrieved["case_id"],
            "retrieved_response": retrieved["historical_response"],
            "baseline": "baseline_2_nearest_neighbor"
        }
