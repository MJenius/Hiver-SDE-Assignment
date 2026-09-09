"""
tests/test_splitting.py
Tests for conversation-level splitting guarantees and zero-leakage invariants.
"""

import pytest
from src.splitting import (
    get_conversation_hash,
    partition_conversations,
    verify_split_leakage
)

def test_deterministic_hashing():
    h1 = get_conversation_hash("115854", seed=42)
    h2 = get_conversation_hash("115854", seed=42)
    h3 = get_conversation_hash("115854", seed=99)
    assert h1 == h2
    assert h1 != h3
    assert 0.0 <= h1 < 1.0

def test_split_disjoint_and_coverage():
    c_ids = [f"conv_{i}" for i in range(1000)]
    splits = partition_conversations(c_ids, train_ratio=0.7, dev_ratio=0.1, val_ratio=0.1, test_ratio=0.1, seed=42)
    
    assert verify_split_leakage(splits) is True
    
    total_assigned = len(splits["train"]) + len(splits["dev"]) + len(splits["val"]) + len(splits["test"])
    assert total_assigned == 1000
    
    # Check approximate distribution
    assert 650 <= len(splits["train"]) <= 750
    assert 70 <= len(splits["dev"]) <= 130
    assert 70 <= len(splits["val"]) <= 130
    assert 70 <= len(splits["test"]) <= 130
