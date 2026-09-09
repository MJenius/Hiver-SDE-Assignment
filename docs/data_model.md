# Data Model Specification

## 1. Hierarchy & Core Entities

The system defines an explicit 5-tier entity hierarchy to avoid conflating raw messages with dialogue or evaluation units:

```
[Tweet] -> [Turn] -> [Conversation] -> [Case] -> [Evaluation Example]
```

### 1.1 Tweet (Atomic Record)
The raw row from the Kaggle dataset (`twcs.csv`):
* `tweet_id` (str): Unique identifier.
* `author_id` (str): Identifier of the author (anonymized customer ID or brand handle, e.g. `AppleSupport`).
* `inbound` (bool): `True` if authored by a customer targeting a brand; `False` if authored by the brand support handle.
* `created_at` (str): UTC timestamp string (e.g. `Tue Nov 07 16:53:24 +0000 2017`).
* `text` (str): Raw text of the tweet.
* `response_tweet_id` (str / null): Comma-separated tweet IDs responding to this tweet (often forward pointers).
* `in_response_to_tweet_id` (str / null): Tweet ID to which this tweet responds (backward pointer).

### 1.2 Turn (Dialogue Node)
A normalized utterance within an active interaction:
* `turn_id` (str): Equivalent to `tweet_id`.
* `speaker_role` (enum: `customer` | `support`): Derived deterministically from `inbound` (`True` -> `customer`, `False` -> `support`).
* `author_id` (str): Anonymized ID or brand handle.
* `timestamp` (datetime): Parsed UTC timestamp.
* `text` (str): Sanitized text.
* `in_response_to_tweet_id` (str / null): Parent tweet reference.
* `response_tweet_id` (str / null): Child response reference.

### 1.3 Conversation (Dialogue Graph & Derived Paths)
A connected, temporally ordered directed acyclic graph (DAG) of Turns initiated by a customer inquiry:
```
Conversation
├── conversation_id: Root customer tweet ID
├── brand: Brand support handle
├── customer_id: Initiating customer author ID
├── turns: Chronologically sorted unique turns
├── is_branched: True if any node has multiple child responses
├── turn_count: Total unique turns in the DAG
├── graph: Adjacency list mapping parent_turn_id -> [child_turn_id_1, ...]
└── derived_paths: List of distinct root-to-leaf turn sequences [[root, t1, t2], [root, t3], ...]
```

### 1.4 Case (The Atomic Grounding & Retrieval Unit)
A **Case** represents a single actionable interaction slice along an isolated dialogue path:
```
Case = Customer Turn (requiring reply) + Preceding Path Context + Historical Reference Response(s)
```
Fields:
* `case_id` (str): `conv_{conversation_id}_turn_{turn_id}`
* `conversation_id` (str): Parent conversation reference.
* `customer_turn` (Turn): The specific customer message requiring support intervention.
* `context_turns` (List[Turn]): Preceding turns **strictly along the same dialogue path** (preventing parallel sibling branch context mixing).
* `reference_support_turns` (List[Turn]): Historical response(s) provided directly to this turn along this path.
* `has_reference_response` (bool): `True` if at least one support response exists for this customer turn.

### 1.5 Evaluation Example (Benchmark Unit)
The unit evaluated by the golden evaluation protocol and LLM judges:
* `example_id` (str): `eval_gold_{index}`
* `case_id` (str): Underlying case identifier.
* `conversation_id` (str): Parent conversation identifier (ensuring whole-conversation leakage gating).
* `customer_message` (str): Customer text requiring action.
* `preceding_context` (str): Path-isolated preceding dialogue context.
* `intent` (str): Ground-truth human-annotated intent from the taxonomy.
* `should_escalate` (bool): Ground-truth decision on whether an automated agent should escalate to human.
* `escalation_reason` (str / null): Justification for escalation (e.g., `requires_authenticated_access`, `hardware_damage_repair`, `sentiment_crisis`).
* `evidence_sufficient` (enum: `yes` | `no` | `uncertain`): Whether historical precedents provide adequate evidence to resolve the query safely.
* `ambiguity_type` (enum: `none` | `vague` | `multi_intent` | `short` | `context_dependent` | `typo_heavy`).
* `notes` (str): Annotator commentary.

---

## 2. Invariant Rules
1. **No Mixed Splits**: All Cases and Evaluation Examples originating from the same `conversation_id` MUST reside in the same split (Train, Dev, Golden, or Hard / Stress).
2. **Directional Integrity**: A customer turn must never have `speaker_role = support`.
3. **Path Isolation**: The preceding context for turn $T_n$ must consist solely of ancestors of $T_n$ in the thread DAG. Turns from disjoint sibling branches are strictly excluded.
