# Formal Evaluation Plan & Metric Formulations

## 1. Evaluation Overview
This document specifies the exact evaluation framework, metric formulations, baseline standards, and LLM-as-judge meta-evaluation protocols to be employed in Phase 2.
No fabricated metrics or placeholder scores are reported here; this document establishes the mathematical contracts before modeling begins.

---

## 2. Partition Hierarchy & Separation of Sets
1. **Development Set (`dev`)**: 10% partition (~5,000 conversations) used for prompt iteration, retriever threshold tuning, and error diagnosis.
2. **Validation Set**: 10% sub-sample from development used for hyperparameter selection and baseline validation.
3. **Golden Evaluation Set (`eval/golden/final/`)**: Exactly 200 hand-labelled, verified examples held out completely from development.
4. **Hard / Stress Evaluation Set (`eval/hard/`)**: 100 naturally occurring challenging examples specifically targeting multi-intent, ultra-short, typo-heavy, and context-dependent cases.

---

## 3. Metric Formulations by System Component

### 3.1 Intent Classification
* **Accuracy**:
  $$\text{Accuracy} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(y_i = \hat{y}_i)$$
* **Macro-Averaged F1 Score**:
  $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} F1_c$$
  where $F1_c = \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$. Macro-F1 prevents dominant classes from concealing poor performance on rare intents.
* **Per-Class Precision, Recall, Confusion Matrix**: Monitored across all 10 taxonomy categories.

### 3.2 Historical Case Retrieval
* **Recall@K ($K \in \{1, 3, 5\}$)**:
  $$\text{Recall@K} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{rank}(\text{relevant}_i) \le K)$$
* **Mean Reciprocal Rank (MRR)**:
  $$\text{MRR} = \frac{1}{N} \sum_{i=1}^N \frac{1}{\text{rank}_i}$$

### 3.3 Escalation Decision Logic
* **Escalation Precision**: Proportion of flagged escalations that legitimately required human advisor intervention.
* **Escalation Recall**: Proportion of true risk/unsupported queries that were safely escalated.
* **Coverage (Automation Rate)**: Proportion of queries handled automatically without escalation:
  $$\text{Coverage} = \frac{\text{Auto-Handled Cases}}{N_{\text{total}}}$$
* **False-Auto-Handle Rate (High-Risk Metric)**: Proportion of auto-handled queries that should have been escalated:
  $$\text{FAHR} = \frac{\sum \mathbb{I}(\hat{e}_i = \text{Auto} \land e_i^* = \text{Escalate})}{\sum \mathbb{I}(\hat{e}_i = \text{Auto})}$$

### 3.4 Reply Quality & LLM-as-Judge Protocols
* **Groundedness Score (1-5 Rubric)**: Extent to which claims in the generated draft are grounded in retrieved historical precedents or verified Apple diagnostic steps, penalizing hallucination.
* **Unsupported Claim Rate (UCR)**: Percentage of generated sentences making factual or policy assertions not present in retrieved context.
* **Resolution Actionability (1-5 Rubric)**: Whether the response provides concrete, executable troubleshooting instructions.
* **Brand Consistency (1-5 Rubric)**: Professional, empathetic, concise AppleCare tone.

---

## 4. Meta-Evaluation: Judge Agreement & Bias Controls
* **Human-vs-LLM Judge Agreement**: Measured via Cohen’s Kappa ($\kappa$) and Pearson correlation ($r$) on a 50-example audit sample.
* **Position Bias Mitigation**: In pairwise LLM-as-judge comparisons, every pair $(A, B)$ is evaluated twice with swapped positions $(A, B)$ and $(B, A)$; ties or contradictions are explicitly flagged.
* **Self-Evaluation Guardrail**: The generation LLM must NEVER evaluate its own outputs; judge models must be structurally independent.
