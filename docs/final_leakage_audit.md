# Final Split Integrity & Leakage Audit Report

This report provides the mathematical and empirical proof that zero leakage exists across the dataset partitions (`train`, `dev`, `val`, `test`) and that the **Final Golden Test Set** (`eval/golden/final/golden_test.jsonl`) is strictly quarantined.

---

## 1. Mathematical Guarantee: Whole-Conversation Hashing
Leakage in dialogue systems occurs when individual turns from the same thread or conversation DAG are split across train and test partitions.
To prevent this, our pipeline partitions data strictly on the **Root Conversation ID**:
$$\text{bucket} = \text{SHA256}(\text{conversation\_id} \,\|\, \text{seed}) \pmod{100}$$
* `train`: [0, 70) (70%)
* `dev`: [70, 80) (10%)
* `val`: [80, 90) (10%)
* `test`: [90, 100) (10%)

Because the partition function is a pure deterministic mapping of the root conversation DAG, all branched paths, customer tweets, and agent turns belonging to a conversation are guaranteed to reside within the same split partition.

---

## 2. Automated Split Guard Audit Results
Audited via `src/evaluation/split_guard.py` across all 81,767 materialized cases:

```json
{
  "status": "PASSED",
  "total_cases_audited": 81767,
  "split_counts": {
    "train": 57421,
    "dev": 8037,
    "val": 8344,
    "test": 7965
  },
  "unique_conversations": {
    "train": 35873,
    "dev": 5127,
    "val": 5175,
    "test": 5036
  },
  "conversation_overlap": 0,
  "case_overlap": 0,
  "tweet_overlap": 0,
  "golden_test_cases_audited": 200,
  "golden_test_in_train_overlap": 0,
  "golden_test_in_val_overlap": 0,
  "integrity_enforced": true
}
```

---

## 3. Strict Quarantining of Final Golden Test Cases
1. **Source Partition**: Exactly 200 stratified golden test cases in `eval/golden/final/golden_test.jsonl` originate from the `test` split.
2. **Retrieval Index Exclusions**: The canonical retrieval index (`data/retrieval_index.pkl`) was constructed exclusively using 30,000 cases from the `train` split (`data/index_manifest.json`). Zero cases from `dev`, `val`, or `test` were indexed.
3. **Parameter Tuning Isolation**:
   - The intent classifier (`src/intent_classifier.py`) was trained on `train` cases.
   - Context ablation (C1 vs C2 vs C3) and escalation confidence threshold sweeps ($\tau = 0.55$) were executed strictly on the `val` partition.
   - The final test benchmark is evaluated **exactly once** without post-hoc tuning.

The audit artifact is programmatically verified and persisted in `eval/results/integrity/leakage_audit.json`.
