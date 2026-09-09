# What Is Misleading About Our Headline Numbers?

In AI engineering, reporting high aggregate metrics without dissecting their operational caveats and boundary conditions is dangerous. This document rigorously critiques each of our system's top headline results, identifying what is potentially misleading, how the metrics can be misinterpreted, and what the real operational reality is.

---

## 1. "93.55% Escalation Recall"

### What sounds impressive
A 93.55% recall metric (95% CI: [88.12%, 98.72%]) suggests that the agent catches almost every single sensitive, risky, or human-requiring issue, preventing dangerous customer outcomes.

### What is misleading about it
1. **It is achieved through high conservatism**: Our escalation policy flags 56.5% of all incoming requests for human escalation. When a system flags more than half of all incoming volume, achieving a 93.5% recall is much easier than doing so with a lean escalation volume.
2. **26 Unnecessary Escalations (False Positives)**: Out of 113 escalated cases in the stratified benchmark, 26 were completely benign troubleshooting queries where a customer simply phrased their issue ambiguously without standard keywords (e.g., *"facing problems with iPhone x contacted the customer care twice"*). These queries fell to `unknown` intent and were automatically routed to a human agent, burdening human staff.
3. **The 6.45% Misses are High-Risk**: The remaining 6.45% missed escalations ($N=6$ cases) were not minor queries—they were transactional order cancellation and duplicate charge requests where customers explicitly asked to stop an erroneous purchase. A system that misses 6 duplicate charge inquiries out of 200 cases cannot be deployed without active transaction guardrails.

---

## 2. "43.5% Autonomous Coverage" vs. "27.9% Natural Coverage"

### What sounds impressive
Automating 43.5% (95% CI: [37.0%, 50.5%]) of customer inquiries sounds like an immediate ~40% reduction in support operational costs.

### What is misleading about it
1. **Coverage $\neq$ Resolution (Solve Rate)**: Automated coverage merely means the system generated a grounded reply rather than handing off to a human. In the historical Twitter dataset, an automated reply often just prompts the user for diagnostic info or provides a support URL. We cannot verify whether the customer's technical issue was truly solved.
2. **Stratified Benchmark vs. Natural Traffic**: The 43.5% coverage is measured on a class-stratified 200-case benchmark containing equal representation of actionable classes (~20 cases each). In unconstrained natural inbound traffic (where over 53% of queries are unstructured greetings or ambient complaints), the agent's safe coverage drops to **27.93%**.
3. **False Auto-Handle Rate (FAHR) is 6.90%**: Within that 43.5% automated slice ($N=87$ cases), 6 cases (6.90%, 95% CI: [2.30%, 12.64%]) should have been escalated immediately to a human. Thus, roughly 1 in every 14 automated replies was an erroneous deflection that frustrated a customer needing transactional intervention.

---

## 3. "100.0% Claim Support Rate"

### What sounds impressive
A claim support rate of 100% implies that the LLM generation never hallucinates, inventing zero false procedures or fake URLs.

### What is misleading about it
1. **Evaluated Strictly Among Auto-Handled Responses**: The 100% claim support rate applies strictly to the 87 generated responses that passed the confidence and retrieval gates. Escalated cases produce zero claims and are not counted.
2. **Strict Template/Rule Guarding**: The system only generates responses using retrieved historical Apple support snippets and verified `apple.co` URLs. If retrieval confidence or intent match is uncertain, the agent refuses to generate and escalates. High groundedness is achieved by refusing to generate when uncertain, not because the generative model possesses omniscient factual truth.
3. **Grounding on Outdated Workarounds**: Groundedness only measures whether the output faithfully reflects the *retrieved source material*. In a historical corpus from 2017, a response can be 100% grounded in historical agent advice while still offering an outdated workaround (e.g. temporary iOS 11 text replacement bugs). A grounded reply is not guaranteed to be a modern, valid technical solution.

---

## 4. "0.8668 Intent Macro-F1"

### What sounds impressive
A Macro-F1 of 0.8668 across 10 classes suggests near-production level intent understanding.

### What is misleading about it
1. **Class-Balanced Diagnostic, Not Traffic-Weighted**: The benchmark enforces balanced support (~20 per class). In natural traffic, macro-averaging can mask acute degradation in dominant long-tail classes.
2. **Single-Intent Simplification**: Customer support queries often express compound needs (e.g., parental controls on in-app billing). The classifier is forced to pick a single dominant label, masking multi-intent ambiguity.
3. **Evaluation on Cleaned Inbound Single-Turn Tweets**: Intent accuracy was evaluated on single customer turns where Twitter handles were normalized. In production, inputs contain images, corrupted links, voice transcripts, and multi-language snippets, where standalone text F1 degrades significantly.

---

## 5. "Intent-Match MRR = 0.1000"

### What is honest and why it matters
Rather than hiding poor retrieval performance behind dense embedding claims, our evaluation measured strict top-5 Mean Reciprocal Rank (MRR = 0.1000) of the first retrieved case matching the benchmark intent category.
* **Why it is low**: Hybrid BM25 + TF-IDF retrieval frequently matches high-frequency iPhone troubleshooting documents even when the query is about Apple Watch or Mac, due to dominant iPhone term frequencies in the corpus.
* **Operational Implication**: This metric measures intent category overlap, NOT semantic resolution precision. Retrieval works adequately as a broad topic pool for LLM context grounding, but cannot be trusted as an automated single-answer lookup without LLM synthesis and entity filtering.

---

## Summary Matrix

| Metric | Headline Claim | What Is Misleading | What to Measure in Production |
|---|---|---|---|
| **Escalation Recall** | 93.55% | Achieved via high conservatism (56.5% escalation rate); misses 6 transactional order changes | Customer churn on missed escalations; human agent burnout from false escalations |
| **Autonomous Coverage** | 43.5% (Stratified) / 27.9% (Natural) | Conflates outbound deflection with actual resolution; 6.90% false auto-handle rate | 7-day repeat contact rate; customer CSAT / CES (Customer Effort Score) |
| **Claim Support Rate** | 100.0% | Refuses to generate on uncertainty; grounds on 2017 historical tweets that may be outdated | Technical accuracy verified against live Apple Knowledge Base (2026) |
| **Intent Macro-F1** | 0.8668 | Evaluated on class-balanced single turns; masks multi-intent and cross-device ambiguities | Multi-turn conversational intent shift and slot-filling accuracy |
| **Intent-Match MRR** | 0.1000 | Evaluates broad intent category alignment, not human-adjudicated resolution precedent | Hit@3 on device-family-constrained candidate pools |
