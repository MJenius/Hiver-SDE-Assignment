"""
tests/test_invariants.py
Automated invariant tests for dataset schemas, taxonomy validation,
golden set sampling invariants, and zero leakage assertions.
"""

import os
import json
import yaml
import pytest

def test_data_manifest_integrity():
    assert os.path.exists("docs/data_manifest.json")
    with open("docs/data_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["sha256"] == "cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0"
    assert manifest["total_rows"] == 2811774

def test_taxonomy_yaml_validation():
    assert os.path.exists("configs/intents.yaml")
    with open("configs/intents.yaml", "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    assert "intents" in cfg
    intents = cfg["intents"]
    assert len(intents) == 10
    
    intent_ids = set()
    for item in intents:
        assert "id" in item
        assert "name" in item
        assert "inclusion_criteria" in item
        assert "exclusion_criteria" in item
        assert "positive_examples" in item
        assert len(item["positive_examples"]) >= 2
        intent_ids.add(item["id"])
        
    assert "unknown" in intent_ids
    assert "battery_performance" in intent_ids
    assert "os_update_issues" in intent_ids

def test_golden_candidates_invariants():
    candidate_path = "eval/golden/candidates/golden_candidates.jsonl"
    assert os.path.exists(candidate_path)
    
    records = []
    with open(candidate_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    assert len(records) == 200, f"Expected exactly 200 golden candidates, got {len(records)}"
    
    # Verify no duplicate case IDs or conversation IDs across items
    case_ids = [r["case_id"] for r in records]
    assert len(case_ids) == len(set(case_ids)), "Duplicate case_id found in golden candidates"
    
    # Verify required schema fields
    required_fields = [
        "example_id", "case_id", "conversation_id", "customer_message",
        "candidate_intent", "reference_historical_response"
    ]
    for r in records:
        for f in required_fields:
            assert f in r and r[f] is not None
            assert len(str(r[f])) > 0

def test_hard_candidates_invariants():
    hard_path = "eval/hard/candidates/hard_candidates.jsonl"
    assert os.path.exists(hard_path)
    records = []
    with open(hard_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))
                
    assert len(records) == 100, f"Expected 100 hard candidates, got {len(records)}"
    for r in records:
        assert "ambiguity_type" in r
        assert r["ambiguity_type"] in ("multi_intent", "short", "context_dependent", "vague", "typo_heavy")
def test_split_guard_enforcement():
    from src.evaluation.split_guard import audit_case_splits
    res = audit_case_splits("data/processed/cases.jsonl")
    assert res["status"] == "PASSED"
    assert res["conversation_overlap"] == 0
    assert res["case_overlap"] == 0
    assert res["tweet_overlap"] == 0
