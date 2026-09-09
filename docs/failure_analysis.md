# Systematic Failure Analysis (Top 5 Real Failure Modes)

This document provides an empirical post-mortem of the five primary failure modes discovered during the final evaluation on the quarantined golden test set ($N=200$). Rather than treating errors as random noise, each failure mode is analyzed with concrete example IDs, root cause diagnosis, operational impact, and verifiable remediations.

All examples are cataloged in [`eval/results/final/failure_cases.jsonl`](../eval/results/final/failure_cases.jsonl).

---

## Failure Mode Breakdown Summary

| ID | Failure Mode | Severity | Frequency in Final Eval | Primary Cause |
|---|---|---|---|---|
| **FM-01** | Transactional Order/Billing False Auto-Handle | **Critical (P0)** | 6 cases (6.9% of auto-handled) | Escalation policy lacked transaction action triggers for order cancel/double charges |
| **FM-02** | Multi-Intent Query Collapse | **Medium (P2)** | 11 cases (5.5% of test set) | Single-label classifier forces compound inquiries into a single category |
| **FM-03** | Conversational Underspecification Over-Escalation | **Low-Medium (P3)** | 26 cases (13.0% of test set) | Vague user phrasing drops confidence below $\tau=0.55$, triggering early human escalation |
| **FM-04** | Cross-Device Retrieval Mismatch (Entity Drift) | **Medium (P2)** | Test MRR: 0.1000 | Dense + BM25 hybrid search retrieves high-volume iPhone articles for Apple Watch / Mac |
| **FM-05** | Historical Workaround Deprecation Risk | **Medium (P2)** | Corpus-wide property | Historical 2017 tweets contain transient workarounds (e.g. iOS 11 text replacement) |

---

## Detailed Failure Mode Analysis

### FM-01: Transactional Order Modification False Auto-Handle (Critical)
* **Example ID**: `eval_gold_163`
  * **Customer Query**: *"@AppleSupport I made a mistake and I ordered twice. how to cancel the first order"*
  * **True Intent**: `store_orders_shipping` | **Pred Intent**: `store_orders_shipping`
  * **Ground Truth Escalation**: `True` (Reason: `transaction_modification_required`)
  * **Model Action**: `Auto-Handled` (`pred_escalate: False`)
  * **System Output**: *"You can check the status of your order online or view standard shipping times here: https://apple.co/order-status..."*
* **Root Cause**: The intent classifier correctly recognized the order context, but the rule-based escalation policy only checked for keywords like `"refund"`, `"lawsuit"`, or explicit account compromises. It did not catch transactional action phrases such as `"ordered twice"`, `"cancel order"`, or `"wrong email"`. Because the confidence was high ($>0.85$) and relevant order articles were retrieved, the agent auto-responded with generic static help links instead of escalating to human commerce support.
* **Operational Impact**: The customer receives an unhelpful generic tracking link instead of real-time cancellation assistance before the order enters warehouse fulfillment.
* **Remediation**:
  1. Add regex action triggers for transaction mutations: `\b(cancel|duplicate|ordered twice|wrong (email|address|card)|charged twice)\b`.
  2. Require human handoff for any query containing active order numbers paired with modification verbs.

---

### FM-02: Multi-Intent Query Collapse (Medium)
* **Example ID**: `eval_gold_054`
  * **Customer Query**: *"@AppleSupport I don't want my kid downloading apps without my permission. How can I lock the app store or require password?"*
  * **True Intent**: `apple_id_icloud_security` (Parental restrictions / Screen Time)
  * **Pred Intent**: `app_store_billing_subscriptions`
  * **Model Action**: Classified as App Store Billing due to heavy keyword matching on *"downloading apps"*, *"app store"*, and *"purchase"*.
* **Root Cause**: Single-label classification assumes mutual exclusivity. When customers describe a security boundary (parental control) within a commercial app marketplace, standard classification collapses the intent to the dominant surface vocabulary.
* **Operational Impact**: Retrieves app billing guidance instead of Screen Time / Family Sharing parental control documentation.
* **Remediation**: Introduce multi-label classification or hierarchical intent routing (Product Area $\rightarrow$ Action Type).

---

### FM-03: Conversational Underspecification Over-Escalation (Conservative Inefficiency)
* **Example ID**: `eval_gold_015`
  * **Customer Query**: *"@AppleSupport facing problems with iPhone x contacted the customer care twice"*
  * **True Intent**: `hardware_repair_screen_physical` (or diagnostic clarification)
  * **Pred Intent**: `unknown` | **Pred Escalation**: `True` (Reason: `unknown_intent`)
* **Root Cause**: Customer tweets often lack symptom nouns (*"broken screen"*, *"battery dying"*). Because our classifier relies on semantic intent patterns, conversational narratives without symptoms fall below the decision boundary ($\tau = 0.55$) and trigger the conservative fallback rule: `intent == unknown -> escalate`.
* **Operational Impact**: While safe (escalation recall remains at 93.55%), this drives 26 unnecessary human handoffs across the test set, reducing autonomous coverage.
* **Remediation**: Add an autonomous Clarification State: before initiating human escalation for underspecified queries, prompt the user with a structured diagnostic triage question (*"Could you tell us what specific issue you are experiencing with your iPhone X?"*).

---

### FM-04: Cross-Device Retrieval Mismatch & Entity Drift (Medium)
* **Example ID**: `eval_gold_040`
  * **Customer Query**: *"Out of nowhere, my Apple Watch S2 was dying. It is losing battery even while powered off."*
  * **True Intent**: `battery_charging_power`
  * **Pred Intent**: `battery_charging_power`
  * **Retrieved Article**: Top-ranked articles focus on iPhone Low Power Mode and general iOS battery tips.
* **Root Cause**: Over 78% of the AppleSupport historical dataset references iPhones. In unconstrained hybrid retrieval (BM25 + TF-IDF), high-frequency token overlaps for generic battery terms overwhelm the specific `"Apple Watch S2"` entity, causing low reciprocal rank (MRR = 0.1000 on test set).
* **Operational Impact**: The user receives troubleshooting steps that reference iPhone settings rather than watchOS settings.
* **Remediation**: Implement an Entity Filter in the retrieval pipeline that extracts the hardware device (`iPhone`, `Apple Watch`, `Mac`, `iPad`) and restricts candidate documents to that device taxonomy.

---

### FM-05: Historical Workaround Deprecation & Freshness Risk (Methodological)
* **Example Case**: Historical tweets concerning iOS 11 keyboard replacement bugs (e.g. the letter 'I' auto-replacing with symbols in November 2017).
* **Root Cause**: Historical customer support corpora are frozen in time. In late 2017, Apple Support advised users to set up a temporary Text Replacement workaround (`Settings > General > Keyboard > Text Replacement`) before iOS 11.1.1 was released.
* **Operational Impact**: If a modern agent grounds responses directly on historical high-similarity tweets without temporal decay or validity checking, it risks providing outdated or counter-productive workarounds.
* **Remediation**:
  1. Enforce knowledge base curation: deprecate transient workaround cases once official OS patches are documented.
  2. Add knowledge expiration metadata to historical case indexes.
