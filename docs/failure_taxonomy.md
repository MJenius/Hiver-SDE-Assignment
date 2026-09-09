# Initial Failure Mode Taxonomy: `@AppleSupport`

## 1. Overview
Grounded directly in empirical inspection of `@AppleSupport` customer dialogues, this document defines the primary anticipated failure modes that an automated AI support agent will encounter.
This taxonomy will be used in Phase 2 to systematically stress-test candidate models.

---

## 2. Core Failure Modes Grounded in Data

### 1. The "DM Link Deflection" Trap (Unsupported Policy / Hallucinated Resolution)
* **Description**: In 51.5% of historical interactions, Apple agents invited users to DM (`https://t.co/GDrqU22YpT`) to complete diagnostics privately.
* **Failure**: A retrieval-grounded LLM may hallucinate that sharing an expired or dead 2017 `t.co` link constitutes solving the issue, or fail to provide available public troubleshooting steps before escalating.
* **Mitigation**: Filter out raw diagnostic links from retrieval text; train agent to recognize when self-service steps can precede escalation.

### 2. Multi-Intent Ambiguity (Entangled Complaints)
* **Description**: Customers frequently combine multiple hardware and software failures in a single tweet (e.g. *"iOS 11 update killed my battery and now my iPhone 7 screen won't turn on"*).
* **Failure**: The classifier collapses the message into a single label and drafts an answer addressing only one symptom, ignoring the critical hardware failure.
* **Mitigation**: Multi-label intent extraction or structured triage prompts.

### 3. Context Blindness on Follow-Up Turns
* **Description**: Follow-up turns (e.g. *"Yes, tried resetting network settings, still no service"*) lack explicit brand or product entities.
* **Failure**: Without preceding dialogue context, a stateless classifier assigns `unknown` or misclassifies the turn as a greeting.
* **Mitigation**: Incorporate structured `preceding_context` turns into the case representation.

### 4. Hardware Repair vs. Software Troubleshooting Confusion (False Auto-Handle)
* **Description**: A user with a physically shattered screen or swelling battery is given software restart instructions instead of being escalated to AppleCare Genius Bar repair.
* **Failure**: High-risk **False Auto-Handle** that frustrates the customer and could create safety hazards (e.g., swollen lithium battery).
* **Mitigation**: Strict safety escalation rules for keywords like *bulging*, *swollen*, *smoke*, *spark*, *shattered*.

### 5. Historical Inconsistency & Outdated OS Guidance
* **Description**: Historical responses from late 2017 advise users on iOS 11.1 temporary workarounds (such as setting up Text Replacement for the "I" autocorrect bug).
* **Failure**: Recommending obsolete 2017 workarounds to modern queries rather than principled troubleshooting logic.
* **Mitigation**: Treat historical text strictly as reference behavior, not immutable policy truth.
