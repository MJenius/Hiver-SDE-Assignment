# Case Store & Data Contract: Phase 2

## 1. Core Architectural Contract
The Case Store serves as the canonical processed layer for all Phase 2 modeling and evaluation.
Raw CSV parsing is performed strictly once during preprocessing. Experiments interact exclusively with serialized `ProcessedCase` entities.

```
Raw CSV (twcs.csv) 
       ↓ 
[scripts/prepare_cases.py]
       ↓
data/processed/
  ├── cases.parquet           (Compact columnar storage for high-speed batch access)
  ├── cases.jsonl             (Universal inspectable streaming format)
  ├── conversations.jsonl     (Full DAG graph & derived paths)
  └── dataset_metadata.json   (Provenance, row counts, split hashes)
```

---

## 2. Distinction Between Fundamental Concepts
To prevent conflation, the system strictly separates:
* **A. Customer Query**: The specific customer turn text requiring a support resolution.
* **B. Conversation Context**: Chronologically ordered ancestor turns strictly along the specific dialogue path preceding this query. Parallel sibling branches are excluded.
* **C. Historical Support Response**: Historical brand response(s) provided directly to this turn. Treated as reference behavior, not infallible ground truth.
* **D. Retrieval Evidence**: Top-$K$ relevant historical cases retrieved from the `train` partition used to ground the generator.
* **E. Evaluation Example**: A quarantined test case evaluated on intent classification, retrieval ranking, escalation safety, and response groundedness.

---

## 3. Case Schema Specification

| Field Name | Type | Description |
|---|---|---|
| `case_id` | str | Deterministic unique ID: `conv_{conversation_id}_turn_{turn_id}` |
| `conversation_id` | str | Parent conversation root ID (used for whole-conversation leakage checks) |
| `split` | str | Partition membership (`train`, `dev`, `val`, `test`) |
| `customer_tweet_id` | str | Unique tweet ID of the customer turn |
| `customer_message` | str | Raw customer text |
| `preceding_context_turns`| list | List of dicts representing previous turns along this path |
| `preceding_context_text` | str | Clean string representation of preceding path turns |
| `historical_support_turns`| list | Direct subsequent support turns along this path |
| `historical_support_response`| str | Text of reference support responses |
| `has_reference_response` | bool | `True` if at least one historical support reply exists |
| `path_turn_ids` | list | Full root-to-leaf turn ID path sequence |
| `is_branched` | bool | Whether parent conversation contains branch forks |
| `turn_index_in_path` | int | 0-indexed turn position in the dialogue path |
