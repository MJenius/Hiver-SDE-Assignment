# Data Model Specification

## 1. Hierarchy & Core Entities

The system defines an explicit 5-tier entity hierarchy to avoid conflating raw messages with dialogue or evaluation units:

`
[Tweet] -> [Turn] -> [Conversation] -> [Case] -> [Evaluation Example]
`

### 1.1 Tweet (Atomic Record)
The raw row from the Kaggle dataset (	wcs.csv):
* 	weet_id (str): Unique identifier.
* uthor_id (str): Identifier of the author (anonymized customer ID or brand handle, e.g. AmazonHelp).
* inbound (bool): True if authored by a customer targeting a brand; False if authored by the brand support handle.
* created_at (str): UTC timestamp string (e.g. Tue Nov 07 16:53:24 +0000 2017).
* 	ext (str): Raw text of the tweet.
* esponse_tweet_id (str / null): Comma-separated tweet IDs responding to this tweet (often forward pointers).
* in_response_to_tweet_id (str / null): Tweet ID to which this tweet responds (backward pointer).

### 1.2 Turn (Dialogue Node)
A normalized utterance within an active interaction:
* 	urn_id (str): Equivalent to 	weet_id.
* speaker_role (enum: customer | support): Derived deterministically from inbound (True -> customer, False -> support).
* uthor_id (str): Anonymized ID or brand handle.
* 	imestamp (datetime): Parsed UTC timestamp.
* 	ext (str): Sanitized text.
* parent_tweet_id (str / null): Immediate parent reference.

### 1.3 Conversation (Dialogue Graph Component)
A connected, temporally ordered directed acyclic graph (DAG) of Turns initiated by a customer or brand inquiry:
* conversation_id (str): Root tweet ID or deterministic component hash.
* rand (str): Canonical brand handle involved in the dialogue.
* start_time (datetime): Timestamp of first turn.
* end_time (datetime): Timestamp of last turn.
* 	urns (List[Turn]): Chronologically sorted sequence of turns along the primary dialogue path.
* is_branched (bool): Indicates if multiple support turns responded to the same customer query.
* customer_id (str): The unique customer author ID in the conversation.

### 1.4 Case (The Atomic Grounding & Retrieval Unit)
A **Case** represents a single actionable interaction slice within a Conversation:
`
Case = Customer Turn (requiring reply) + Preceding Context (if any) + Reference Historical Response(s)
`
Fields:
* case_id (str): conv_{conversation_id}_turn_{turn_id}
* conversation_id (str): Parent conversation reference.
* customer_turn (Turn): The specific customer message requiring support intervention.
* context_turns (List[Turn]): Preceding conversation turns providing dialogue context (empty if first turn).
* eference_support_turns (List[Turn]): The actual historical response(s) provided by the brand.
* has_reference_response (bool): True if at least one support response exists for this customer turn.
* has_observable_resolution_evidence (bool): True if subsequent turns demonstrate issue handling (e.g. confirmation, links, concrete instruction) rather than a dead-end deflection.

### 1.5 Evaluation Example (Benchmark Unit)
The unit evaluated by the golden evaluation protocol and LLM judges:
* example_id (str): eval_gold_{index}
* case_id (str): Underlying case identifier.
* conversation_id (str): Parent conversation identifier (ensuring whole-conversation leakage gating).
* customer_message (str): Customer text requiring action.
* preceding_context (str): Formatted preceding dialogue context.
* intent (str): Ground-truth human-annotated intent from the taxonomy.
* should_escalate (bool): Ground-truth decision on whether an automated agent should escalate to human.
* escalation_reason (str / null): Justification for escalation (e.g., equires_authenticated_access, sentiment_crisis, policy_exception, insufficient_information).
* evidence_sufficient (enum: yes | 
o | uncertain): Whether historical support cases provide sufficient grounded resolution patterns to formulate an automated answer.
* mbiguity_type (enum: 
one | ague | multi_intent | short | context_dependent | 	ypo_heavy | conflicting_resolution).
* 
otes (str): Annotator commentary.

---

## 2. Invariant Rules
1. **No Mixed Splits**: All Cases and Evaluation Examples originating from the same conversation_id MUST reside in the same split (Train, Dev, Golden, or Hard).
2. **Directional Integrity**: A customer turn must never have speaker_role = support.
3. **Temporal Monotonicity**: For any turn $ and child turn {i+1}$, (T_i) \le timestamp(T_{i+1})$.
