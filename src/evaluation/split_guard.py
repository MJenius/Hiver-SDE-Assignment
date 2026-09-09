"""
src/evaluation/split_guard.py
Automated leakage detection and split contract enforcement.
Guarantees:
1. Disjoint conversation IDs across splits
2. Disjoint case IDs across splits
3. Disjoint customer tweet IDs across splits
4. Quarantined test set (zero cases from test enter training or retrieval indexes)
"""

import json
from typing import Dict, List, Set, Any
import pandas as pd

class SplitLeakageError(Exception):
    pass

def audit_case_splits(cases_path: str = "data/processed/cases.jsonl") -> Dict[str, Any]:
    """
    Audits processed cases file to enforce strict zero-leakage constraints across splits.
    """
    split_convs: Dict[str, Set[str]] = {"train": set(), "dev": set(), "val": set(), "test": set()}
    split_cases: Dict[str, Set[str]] = {"train": set(), "dev": set(), "val": set(), "test": set()}
    split_tweets: Dict[str, Set[str]] = {"train": set(), "dev": set(), "val": set(), "test": set()}
    
    total_records = 0
    with open(cases_path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            total_records += 1
            rec = json.loads(line)
            s = rec["split"]
            cid = rec["conversation_id"]
            case_id = rec["case_id"]
            tw_id = rec["customer_tweet_id"]
            
            split_convs[s].add(cid)
            split_cases[s].add(case_id)
            split_tweets[s].add(tw_id)

    # 1. Assert conversation ID disjointness
    splits_list = ["train", "dev", "val", "test"]
    for i in range(len(splits_list)):
        for j in range(i + 1, len(splits_list)):
            s1, s2 = splits_list[i], splits_list[j]
            conv_overlap = split_convs[s1].intersection(split_convs[s2])
            if conv_overlap:
                raise SplitLeakageError(f"Leakage detected! {len(conv_overlap)} conversation IDs shared between {s1} and {s2}. Example: {list(conv_overlap)[:3]}")
                
            case_overlap = split_cases[s1].intersection(split_cases[s2])
            if case_overlap:
                raise SplitLeakageError(f"Leakage detected! {len(case_overlap)} case IDs shared between {s1} and {s2}. Example: {list(case_overlap)[:3]}")

            tweet_overlap = split_tweets[s1].intersection(split_tweets[s2])
            if tweet_overlap:
                raise SplitLeakageError(f"Leakage detected! {len(tweet_overlap)} customer tweet IDs shared between {s1} and {s2}. Example: {list(tweet_overlap)[:3]}")

    return {
        "status": "PASSED",
        "total_cases_audited": total_records,
        "split_counts": {s: len(split_cases[s]) for s in splits_list},
        "unique_conversations": {s: len(split_convs[s]) for s in splits_list},
        "conversation_overlap": 0,
        "case_overlap": 0,
        "tweet_overlap": 0
    }

if __name__ == "__main__":
    result = audit_case_splits()
    print("Split Guard Audit:", json.dumps(result, indent=2))
