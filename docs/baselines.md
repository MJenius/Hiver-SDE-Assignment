# Baseline Specifications

## 1. Overview
Before implementing complex generative agents or fine-tuned LLMs, the system must be compared against established, deterministic baselines to prove that architectural complexity adds measurable value.

---

## 2. Baseline 0: Majority-Class Classifier & Canned Escalation
* **Component**: Intent Classification & Escalation.
* **Input**: Customer raw text query.
* **Inference Procedure**:
  * Predicts the most frequent class in the training partition for all queries (`os_update_issues`).
  * Escalates 100% of queries requiring private authentication, or applies a constant rule (always escalate / never escalate).
* **Purpose**: Sets the lower-bound trivial metric baseline. Any viable model must decisively outperform Baseline 0 on Macro-F1.
* **Limitations**: Zero sensitivity to lexical cues; zero discrimination between easy and hard cases.

---

## 3. Baseline 1: TF-IDF + Regularized Logistic Regression
* **Component**: Intent Classification & Heuristic Retrieval.
* **Input**: Lowercased customer query stripped of Twitter handles.
* **Training Procedure**:
  * Feature extraction via `TfidfVectorizer(max_features=5000, ngram_range=(1, 2), sublinear_tf=True)`.
  * Multi-class classification via `LogisticRegression(C=1.0, solver="lbfgs", max_iter=500)`.
* **Escalation Logic**: Escalate if maximum predicted class probability $P(\hat{y} \mid x) < \tau$ (e.g. $\tau = 0.55$).
* **Retrieval Procedure**: Cosine similarity over TF-IDF vectors of historical customer queries in the training set to retrieve top-1 nearest neighbor response.
* **Strengths**: Highly fast, deterministic, reproducible in seconds, completely transparent.
* **Limitations**: Fails on synonyms, typos, multi-turn context, and indirect language.

---

## 4. Baseline 2: Dense Semantic Nearest-Neighbor (Bi-Encoder Embeddings)
* **Component**: Intent Classification, Retrieval, and Retrieval-Grounded Response.
* **Input**: Customer query encoded into a dense vector via lightweight sentence embeddings (e.g., `all-MiniLM-L6-v2`).
* **Inference Procedure**:
  * Intent: Majority vote of $K=5$ nearest historical neighbors in cosine distance space.
  * Retrieval: Top-1 nearest neighbor response drafted directly as the proposed reply.
  * Escalation: Escalate if cosine similarity to nearest neighbor is below a minimum threshold ($\text{sim} < 0.65$), or if nearest historical turn escalated to DM.
* **Strengths**: Captures semantic similarity and paraphrase invariance beyond lexical keyword overlap.
* **Limitations**: Susceptible to retrieving contextually irrelevant answers if query mentions peripheral entities.
