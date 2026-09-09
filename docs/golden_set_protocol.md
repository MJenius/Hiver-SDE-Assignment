# Golden Evaluation Set Protocol & Benchmark Specification

## 1. Objective & Design Philosophy
The Golden Evaluation Set (`eval/golden/final/golden_test.jsonl`) serves as the definitive held-out test benchmark for the AI Customer Support Agent.

To ensure empirical credibility and avoid common evaluation pitfalls:
1. **Quarantined Test Set**: The golden test set is drawn strictly from the held-out `test` partition (`split == "test"`). Model weights, prompts, and retrieval indices never access or fit to these examples.
2. **Stratified Representation**: The set is deliberately curated across all 10 intent categories, length profiles, and difficulty tiers.
3. **Target Size**: Exactly 200 evaluation examples.
4. **Policy-Adjudicated Benchmark Targets**: The evaluation fields (`intent`, `should_escalate`, `evidence_sufficient`) represent programmatically adjudicated policy benchmark targets derived from candidate intent heuristics and domain safety rules, rather than verified manual human annotations.

---

## 2. Sampling Stratification Methodology
The 200 examples are drawn from the test partition of reconstructed two-sided AppleSupport conversations (`seed=42`) using programmatic stratification:
* **Intent Representation**: ~15 to 22 examples per technical intent (~180 total across 9 intents), plus ~20 examples for `unknown` / out-of-distribution.
* **Turn Context Distribution**:
  * 65% initiating turns (Turn 1, no prior context).
  * 35% follow-up turns (Turn 3+, requiring preceding context for resolution).
* **Length Profiles**:
  * Short (< 50 chars): ~25%
  * Medium (50–140 chars): ~50%
  * Long (> 140 chars): ~25%
* **Ambiguity & Hard-Case Quota**:
  * Clean / Unambiguous: ~60% (120 examples)
  * Ambiguous / Hard: ~40% (80 examples, including multi-intent, typo-heavy, and vague queries).

---

## 3. Evaluation Schema Specification

Every golden evaluation record conforms to the following schema:

| Field Name | Type | Allowed Values / Format | Description |
|---|---|---|---|
| `example_id` | str | `eval_gold_{001-200}` | Unique identifier. |
| `case_id` | str | `conv_{id}_turn_{id}` | Underlying reconstructed Case identifier. |
| `conversation_id` | str | String | Conversation DAG ID (enforcing whole-conversation split). |
| `customer_message` | str | String | Customer utterance requiring AI handling. |
| `preceding_context` | str | String / Empty | Chronologically formatted previous turns in thread. |
| `intent` | str | Enum (10 taxonomy IDs) | Primary policy-adjudicated benchmark intent target. |
| `should_escalate` | bool | `True` / `False` | Policy-adjudicated benchmark escalation target. |
| `escalation_reason` | str | String / Null | Operational justification if escalated (e.g., `requires_authenticated_access`, `hardware_damage_repair`, `sentiment_crisis`). |
| `evidence_sufficient` | str | `yes` \| `no` \| `uncertain` | Whether historical precedents provide adequate evidence to resolve the query safely. |
| `ambiguity_type` | str | `none` \| `vague` \| `multi_intent` \| `short` \| `context_dependent` \| `typo_heavy` | Structural ambiguity classification. |
| `reference_historical_response` | str | String | Reference historical agent response from Twitter dataset. |
| `notes` | str | String | Benchmark adjudication notes and boundary metadata. |

---

## 4. Proposed Human-in-the-Loop Scaling Protocol
For future production deployment requiring full biological human verification:
1. **Intra-Annotator Consistency Check**:
   * An initial batch of 40 examples is annotated.
   * After a 48-hour washout period, the same 40 examples are re-annotated blindly without viewing initial labels.
   * Compute percentage agreement and Cohen’s Kappa $\kappa$:
     $$\kappa = \frac{P_o - P_e}{1 - P_e}$$
   * Target threshold: $\kappa \ge 0.80$ (substantial agreement).
2. **Guideline Refinement Loop**: Any disagreement during the test check triggers an explicit refinement of `configs/intents.yaml` inclusion/exclusion criteria.
3. **Independent Adjudication**: When secondary human annotators are onboarded, conflicting annotations are adjudicated by senior consensus rather than majority vote.
