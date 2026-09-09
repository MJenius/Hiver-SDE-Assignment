"""
src/intent_classifier.py
Production-style discriminative Intent Classifier supporting:
- Multi-class probability estimation across all 10 taxonomy categories
- Calibrated confidence thresholding
- Explicit fallback to "unknown" for low-confidence or ungrounded queries
- Structured dictionary output: {"intent": str, "confidence": float}
"""

import os
import re
import pickle
from typing import Dict, Any, Optional, List
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"@\w+", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

class IntentClassifier:
    def __init__(self, confidence_threshold: float = 0.40, max_features: int = 8000, C: float = 1.5):
        self.confidence_threshold = confidence_threshold
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=(1, 2),
            sublinear_tf=True,
            stop_words="english"
        )
        self.model = LogisticRegression(C=C, max_iter=600, solver="lbfgs")
        self.classes_ = []

    def fit(self, texts: List[str], labels: List[str]):
        cleaned = [clean_text(t) for t in texts]
        X = self.vectorizer.fit_transform(cleaned)
        self.model.fit(X, labels)
        self.classes_ = list(self.model.classes_)

    def predict(self, message: str, context: str = "") -> Dict[str, Any]:
        full_query = f"{message} {context}".strip()
        cleaned = clean_text(full_query)
        if not cleaned:
            return {"intent": "unknown", "confidence": 0.0}

        X = self.vectorizer.transform([cleaned])
        probs = self.model.predict_proba(X)[0]
        max_idx = int(np.argmax(probs))
        top_conf = float(probs[max_idx])
        top_intent = self.classes_[max_idx]

        # Explicit fallback if below operational confidence threshold
        if top_conf < self.confidence_threshold:
            return {
                "intent": "unknown",
                "confidence": round(top_conf, 4),
                "provisional_intent": top_intent
            }

        return {
            "intent": top_intent,
            "confidence": round(top_conf, 4)
        }

    def save(self, filepath: str = "data/intent_classifier.pkl"):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "wb") as f:
            pickle.dump(self, f)

    @classmethod
    def load(cls, filepath: str = "data/intent_classifier.pkl") -> "IntentClassifier":
        with open(filepath, "rb") as f:
            return pickle.load(f)
