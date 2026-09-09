# Formal Retrieval Relevance Hierarchy & Audit Protocol

## 1. The Fallacy of "Same-Intent = Relevant"
A fundamental trap in evaluating retrieval for customer support is assuming that any retrieved historical case with the same high-level intent label is relevant:
* *Example*: A customer asks *"How do I fix the letter 'I' turning into [?] on iOS 11?"* (Intent: `os_update_issues`).
* *Flawed Retrieval*: A case where an agent advises *"Please verify your macOS High Sierra installer checksum"* also has intent `os_update_issues`, but provides **completely contradictory, useless, and harmful resolution steps** for an iPhone keyboard bug.
* *Standard*: A retrieved case is truly relevant only if its underlying resolution steps are materially applicable to the customer query.

---

## 2. Formal 4-Tier Relevance Hierarchy

When judging the relevance of a retrieved historical case $C$ to a customer turn $Q$ with context $X$:

| Level | Relevance Tier | Operational Criteria | Numerical Gain |
|---|---|---|---|
| **3** | **Perfect Resolution** | Same underlying technical problem; exact actionable troubleshooting instructions or verified official support link directly solves $Q$. | 3 |
| **2** | **Compatible Diagnostic** | Same symptom domain; asks relevant diagnostic clarifying questions (e.g. device model, iOS build) that advance resolution. | 2 |
| **1** | **Topical / Broad Intent Only** | Same high-level intent category, but resolution steps address a different hardware model or unrelated sub-problem. Weak supporting signal. | 1 |
| **0** | **Irrelevant / Misleading** | Completely unrelated problem, conflicting advice, or dead deflection. Harmful if fed to generator. | 0 |

---

## 3. Retrieval Evaluation Metrics
* **Binary Relevance Threshold**: Level $\ge 2$ (Compatible Diagnostic or Perfect Resolution).
* **Recall@K ($K \in \{1, 3, 5\}$)**:
  $$\text{Recall@K} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\exists r \le K : \text{Rel}(r) \ge 2)$$
* **Mean Reciprocal Rank (MRR)**:
  $$\text{MRR} = \frac{1}{N} \sum_{i=1}^N \frac{1}{\text{rank of first case with Rel} \ge 2}$$
* **Normalized Discounted Cumulative Gain (nDCG@5)**: Evaluates graded ranking quality across levels 0 to 3.
