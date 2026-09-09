# Formal Evaluation Plan & Metric Formulations

## 1. Evaluation Overview
This document specifies the evaluation framework, metric formulations, baseline standards, and meta-evaluation protocols across the project lifecycle.

To maintain strict epistemic transparency, this framework clearly delineates between:
* **Implemented Evidence**:
  * 200-case quarantined policy-adjudicated benchmark targets (`eval/golden/final/golden_test.jsonl`) from the held-out test split.
  * Empirical 95% Bootstrap Confidence Intervals ($B=1,000$).
  * Automated whole-conversation split guard enforcing 0 leakage across 81,767 cases.
  * Multi-stage hybrid retrieval with lexical/Jaccard reranking.
* **Proposed Protocols (Future Human-in-the-Loop Roadmap)**:
  * Biological human golden label curation across 200 cases.
  * Dual-annotator inter-rater agreement study on 50 overlapping cases.
  * Formal human-vs-LLM judge calibration study.

---

## 2. Partition Hierarchy & Separation of Sets
1. **Training Set (`train`)**: 70% partition (~21,000 conversations) used for baseline fitting and retrieval index construction.
2. **Development Set (`dev`)**: 10% partition (~3,000 conversations) used for retriever threshold exploration and diagnostic inspections.
3. **Validation Set (`val`)**: 10% partition (~3,000 conversations) used for hyperparameter calibration, context ablation, and escalation threshold selection.
4. **Quarantined Final Test Benchmark (`eval/golden/final/`)**: Exactly 200 stratified evaluation cases from the held-out `test` split (`split == "test"`), evaluated exactly once with frozen configuration.
5. **Hard / Stress Evaluation Set (`eval/hard/`)**: 100 naturally occurring challenging examples targeting multi-intent, ultra-short, and context-dependent cases.

---

## 3. Metric Formulations by System Component

### 3.1 Intent Classification (Policy-Adjudicated Benchmark)
* **Accuracy**:
  $$\text{Accuracy} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(y_i = \hat{y}_i)$$
* **Macro-Averaged F1 Score**:
  $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} F1_c$$
  where $F1_c = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$. Macro-F1 prevents dominant classes from concealing poor performance on rare intents.
* **Per-Class Precision, Recall, Confusion Matrix**: Monitored across all 10 taxonomy categories.

### 3.2 Historical Case Retrieval
* **Recall@K ($K \in \{1, 3, 5\}$)**:
  $$\text{Recall@K} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{rank}(\text{matching\_intent}_i) \le K)$$
* **Intent-Match MRR**:
  $$\text{Intent-Match MRR} = \frac{1}{N} \sum_{i=1}^N \frac{1}{\text{rank}_i}$$
  *Limitation Note*: Measures reciprocal rank of the first retrieved case matching the benchmark intent category; does not measure human-adjudicated semantic solution relevance.

### 3.3 Escalation Decision Logic
* **Escalation Precision**: Proportion of flagged escalations that aligned with policy-adjudicated escalation targets.
* **Escalation Recall**: Proportion of policy-flagged risk/unsupported queries that were safely escalated.
* **Coverage (Automation Rate)**: Proportion of queries handled automatically without escalation:
  $$\text{Coverage} = \frac{\text{Auto-Handled Cases}}{N_{\text{total}}}$$
* **False-Auto-Handle Rate (High-Risk Metric)**: Proportion of auto-handled queries that should have been escalated:
  $$\text{FAHR} = \frac{\sum \mathbb{I}(\hat{e}_i = \text{Auto} \land e_i^* = \text{Escalate})}{\sum \mathbb{I}(\hat{e}_i = \text{Auto})}$$

### 3.4 Reply Quality & Grounding
* **Claim Support Rate**: Percentage of extracted factual claims that are supported by retrieved historical context:
  $$\text{Claim Support Rate} = \frac{\text{Supported Claims}}{\text{Total Extracted Claims}}$$
  *Distinction*: Evaluated strictly among generated responses with claims, distinguishing true factual fidelity from automated abstention/refusal.
* **Response Generation Rate vs Abstention Rate**: Tracks the proportion of cases where the agent attempts a grounded reply versus safely abstaining to human escalation.

---

## 4. Meta-Evaluation: LLM-as-Judge & Bias Controls
* **Position Bias Mitigation**: In pairwise LLM-as-judge comparisons, every pair $(A, B)$ is evaluated twice with swapped positions $(A, B)$ and $(B, A)$; contradictory pairs are resolved to ties.
* **Failure Handling**: Network timeouts and rate-limit errors (HTTP 429) are logged separately and NEVER counted as ties or quality preferences.
* **Proposed Human Agreement Protocol**: Future human validation will measure Cohen’s Kappa ($\kappa$) and Pearson correlation ($r$) on a 50-example sample once independent annotators are onboarded.
