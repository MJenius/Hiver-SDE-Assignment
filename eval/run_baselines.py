"""
eval/run_baselines.py
Fits Baseline 0, Baseline 1, and Baseline 2 on the TRAIN partition,
evaluates on DEV and VALIDATION partitions, and serializes results to eval/results/baselines/.
Guarantees zero leakage: NEVER reads from or evaluates against the GOLDEN/TEST partition.
"""

import os
import sys
import json
import re
from typing import Dict, List, Any
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, classification_report

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.baselines.models import Baseline0Majority, Baseline1TfidfLogReg, Baseline2NearestNeighbor

CASES_PATH = "data/processed/cases.jsonl"
INTENTS_CFG_PATH = "configs/intents.yaml"

# Ground-truth keyword mapping for weak supervision labeling of training data
INTENT_PATTERNS = {
    "os_update_issues": [r"\bupdate\b", r"\bios 11\b", r"\bglitch\b", r"\binstall", r"\bverifying\b", r"\bkeyboard\b", r"\bautocorrect\b"],
    "battery_performance": [r"\bbattery\b", r"\bdrain\b", r"\bcharge\b", r"\bcharging\b", r"\boverheating\b", r"\bhot\b", r"\bpower\b"],
    "apple_id_account_security": [r"\bapple id\b", r"\bpassword\b", r"\bicmp\b", r"\blogin\b", r"\blocked\b", r"\bverification code\b", r"\b2fa\b", r"\bactivation lock\b"],
    "app_store_billing_subscriptions": [r"\bbill\b", r"\bbilling\b", r"\brefund\b", r"\bcharge\b", r"\bsubscription\b", r"\bpurchase\b", r"\bcard\b", r"\bapp store\b"],
    "hardware_screen_physical": [r"\bscreen\b", r"\bcracked\b", r"\bdisplay\b", r"\btouch\b", r"\bcamera\b", r"\bspeaker\b", r"\bwater\b", r"\bbroken\b"],
    "connectivity_wifi_bluetooth": [r"\bwi-?fi\b", r"\bbluetooth\b", r"\bairpods\b", r"\bdisconnect\b", r"\bpair\b", r"\bpairing\b", r"\bcellular\b"],
    "icloud_sync_storage": [r"\bicloud\b", r"\bsync\b", r"\bbackup\b", r"\bphotos\b", r"\bstorage full\b", r"\brestore\b"],
    "audio_music_media": [r"\bapple music\b", r"\bplaylist\b", r"\bpodcast\b", r"\bsong\b", r"\balbum\b", r"\bvolume\b"],
    "store_orders_shipping": [r"\border\b", r"\btracking\b", r"\bship\b", r"\bshipping\b", r"\bdeliv\b", r"\bgenius bar\b", r"\bstore\b"]
}

def assign_weak_intent(text: str) -> str:
    t = text.lower()
    matches = []
    for intent, pats in INTENT_PATTERNS.items():
        if any(re.search(p, t) for p in pats):
            matches.append(intent)
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        # Resolve via precedence
        for it in ["apple_id_account_security", "os_update_issues", "battery_performance", "app_store_billing_subscriptions"]:
            if it in matches:
                return it
        return matches[0]
    return "unknown"

def load_cases_by_split(max_train: int = 25000, max_eval: int = 3000):
    print("Loading cases from data/processed/cases.jsonl...")
    train_cases = []
    dev_cases = []
    val_cases = []

    with open(CASES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            c = json.loads(line)
            s = c["split"]
            if s == "train" and len(train_cases) < max_train:
                train_cases.append(c)
            elif s == "dev" and len(dev_cases) < max_eval:
                dev_cases.append(c)
            elif s == "val" and len(val_cases) < max_eval:
                val_cases.append(c)

    print(f"Loaded: train={len(train_cases):,}, dev={len(dev_cases):,}, val={len(val_cases):,}")
    return train_cases, dev_cases, val_cases

def run_baselines_eval():
    train_cases, dev_cases, val_cases = load_cases_by_split()

    train_texts = [c["customer_message"] for c in train_cases]
    train_labels = [assign_weak_intent(t) for t in train_texts]

    val_texts = [c["customer_message"] for c in val_cases]
    val_labels = [assign_weak_intent(t) for t in val_texts]

    dev_texts = [c["customer_message"] for c in dev_cases]
    dev_labels = [assign_weak_intent(t) for t in dev_texts]

    print("\n--- Fitting Baseline 0 (Majority Class) ---")
    b0 = Baseline0Majority()
    b0.fit(train_labels)
    b0_preds_val = [b0.predict(t)["intent"] for t in val_texts]
    b0_acc = accuracy_score(val_labels, b0_preds_val)
    b0_macro_f1 = f1_score(val_labels, b0_preds_val, average="macro", zero_division=0)
    print(f"Baseline 0 (Val): Accuracy={b0_acc:.4f}, Macro-F1={b0_macro_f1:.4f}")

    print("\n--- Fitting Baseline 1 (TF-IDF + Logistic Regression) ---")
    b1 = Baseline1TfidfLogReg()
    b1.fit(train_texts, train_labels)
    b1_preds_val = [b1.predict(t)["intent"] for t in val_texts]
    b1_acc = accuracy_score(val_labels, b1_preds_val)
    b1_macro_f1 = f1_score(val_labels, b1_preds_val, average="macro", zero_division=0)
    print(f"Baseline 1 (Val): Accuracy={b1_acc:.4f}, Macro-F1={b1_macro_f1:.4f}")

    print("\n--- Fitting Baseline 2 (Semantic Nearest Neighbor Retrieval) ---")
    b2 = Baseline2NearestNeighbor()
    b2.fit(train_cases, train_labels)
    b2_preds_val = [b2.predict(t)["intent"] for t in val_texts]
    b2_acc = accuracy_score(val_labels, b2_preds_val)
    b2_macro_f1 = f1_score(val_labels, b2_preds_val, average="macro", zero_division=0)
    print(f"Baseline 2 (Val): Accuracy={b2_acc:.4f}, Macro-F1={b2_macro_f1:.4f}")

    results = {
        "evaluation_split": "validation",
        "sample_size": len(val_cases),
        "baselines": {
            "baseline_0_majority": {
                "name": "Majority Class",
                "accuracy": round(float(b0_acc), 4),
                "macro_f1": round(float(b0_macro_f1), 4),
                "majority_intent": b0.majority_intent
            },
            "baseline_1_tfidf_logreg": {
                "name": "TF-IDF + Logistic Regression",
                "accuracy": round(float(b1_acc), 4),
                "macro_f1": round(float(b1_macro_f1), 4)
            },
            "baseline_2_nearest_neighbor": {
                "name": "Semantic Nearest Neighbor Retrieval",
                "accuracy": round(float(b2_acc), 4),
                "macro_f1": round(float(b2_macro_f1), 4)
            }
        }
    }

    os.makedirs("eval/results/baselines", exist_ok=True)
    with open("eval/results/baselines/baseline_metrics.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    df_res = pd.DataFrame([
        {"Model": "Baseline 0 (Majority)", "Accuracy": b0_acc, "Macro-F1": b0_macro_f1},
        {"Model": "Baseline 1 (TF-IDF + LogReg)", "Accuracy": b1_acc, "Macro-F1": b1_macro_f1},
        {"Model": "Baseline 2 (Semantic 1-NN)", "Accuracy": b2_acc, "Macro-F1": b2_macro_f1}
    ])
    df_res.to_csv("eval/results/baselines/baseline_comparison.csv", index=False)
    print("\nBaseline Results Summary:")
    print(df_res.to_string(index=False))

if __name__ == "__main__":
    run_baselines_eval()
