"""
src/splitting.py
Reusable, leakage-safe dataset splitting utilities.
Guarantees whole-conversation isolation: all cases and turns belonging to a conversation_id
are strictly assigned to exactly one partition (train, dev, val, or test).
"""

import hashlib
from typing import List, Dict, Any, Tuple

def get_conversation_hash(conversation_id: str, seed: int = 42) -> float:
    """
    Computes a deterministic normalized hash in [0.0, 1.0) for a conversation_id.
    """
    key = f"{seed}_{conversation_id}".encode("utf-8")
    hex_digest = hashlib.sha256(key).hexdigest()
    int_val = int(hex_digest[:8], 16)
    return int_val / 0xFFFFFFFF

def partition_conversations(
    conversation_ids: List[str],
    train_ratio: float = 0.70,
    dev_ratio: float = 0.10,
    val_ratio: float = 0.10,
    test_ratio: float = 0.10,
    seed: int = 42
) -> Dict[str, List[str]]:
    """
    Partitions conversation IDs into 4 disjoint subsets using deterministic hashing.
    Ensures 0% conversation-level leakage across splits.
    Notice test_ratio occupies [1.0 - test_ratio, 1.0), maintaining compatibility
    with Phase 1's test split threshold of 0.90!
    """
    total_ratio = train_ratio + dev_ratio + val_ratio + test_ratio
    assert abs(total_ratio - 1.0) < 1e-6, "Split ratios must sum to 1.0"
    
    splits = {
        "train": [],
        "dev": [],
        "val": [],
        "test": []
    }
    
    dev_threshold = train_ratio
    val_threshold = train_ratio + dev_ratio
    test_threshold = train_ratio + dev_ratio + val_ratio

    for c_id in sorted(conversation_ids):
        h = get_conversation_hash(c_id, seed)
        if h < dev_threshold:
            splits["train"].append(c_id)
        elif h < val_threshold:
            splits["dev"].append(c_id)
        elif h < test_threshold:
            splits["val"].append(c_id)
        else:
            splits["test"].append(c_id)
            
    return splits

def verify_split_leakage(splits: Dict[str, List[str]]) -> bool:
    """
    Verifies that no conversation ID appears in more than one partition.
    """
    seen = set()
    for split_name, ids in splits.items():
        for cid in ids:
            if cid in seen:
                return False
            seen.add(cid)
    return True
