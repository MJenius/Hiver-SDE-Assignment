# AI Customer Support Agent Benchmark — @AppleSupport

[![Tests](https://img.shields.io/badge/pytest-12%20passed-brightgreen.svg)]()
[![Dataset SHA-256](https://img.shields.io/badge/SHA--256-cd297fcf...-blue.svg)](docs/data_manifest.json)
[![Selected Brand](https://img.shields.io/badge/Brand-%40AppleSupport-black.svg)](docs/brand_selection.md)
[![Phase](https://img.shields.io/badge/Phase-3%20Final%20Complete-success.svg)]()

This repository implements an end-to-end, empirically grounded AI Customer Support Agent for `@AppleSupport` built on the Kaggle "Customer Support on Twitter" dataset (`data/twcs/twcs.csv`).

The system combines:
1. **Calibrated Intent Classification** across a 10-class operational taxonomy (`configs/intents.yaml`).
2. **Bounded-Context Historical Retrieval** via multi-stage hybrid search (BM25 + TF-IDF embeddings + RRF fusion + Lexical/Jaccard reranking).
3. **Safety-First Escalation Policy** with deterministic rule-based interception for sensitive domains and calibrated confidence thresholding ($\tau = 0.55$).
4. **Evidence-Grounded Response Generation** producing structured claims attributed directly to retrieved historical resolution cases, monitored by an independent claim auditor.
5. **Zero-Leakage Whole-Conversation Evaluation** across 4 strictly disjoint partitions (`train`, `dev`, `val`, `test`), baselines, and empirical 95% bootstrap confidence intervals ($B=1,000$).

---

## 1. Official Final Benchmark Results (Quarantined Test Set, $N=200$)

The agent was frozen in [`configs/final_eval.yaml`](configs/final_eval.yaml) and evaluated **exactly once** on the quarantined, held-out test set (`eval/golden/final/golden_test.jsonl`, $N=200$). 

> [!NOTE]
> **Dataset & Annotation Provenance Disclosure**: The 200 evaluation targets in `golden_test.jsonl` are programmatically adjudicated benchmark labels derived from weak-intent heuristics and policy rules over held-out test conversations (`split == "test"`), rather than fully independent manual human annotations. Metrics should be interpreted strictly as an automated policy-adjudicated benchmark evaluating pipeline consistency and risk interception, not as validated human ground truth.

All metrics are reported with empirical 95% Bootstrap Confidence Intervals ($B=1,000$, seed=42):

| Component / Metric | Point Estimate | 95% Bootstrap Confidence Interval | Evaluation Target Basis |
|---|---|---|---|
| **Intent Accuracy** | **0.8450** | [0.7950, 0.8950] | Adjudicated candidate intent (10 classes) |
| **Intent Macro-F1** | **0.8668** | [0.8228, 0.9047] | Class-balanced diagnostic macro average |
| **Escalation Recall** | **0.9355** | [0.8812, 0.9872] | Policy-adjudicated escalation targets |
| **Escalation Precision** | **0.7699** | [0.6893, 0.8500] | Policy-adjudicated escalation targets |
| **Escalation F1** | **0.8447** | [0.7861, 0.8959] | Harmonic mean |
| **Autonomous Coverage** | **43.50%** | [37.00%, 50.50%] | Stratified test benchmark ($N=87 / 200$) |
| **Natural Stream Coverage** | **27.93%** | [25.70%, 30.20%] | Unconstrained natural validation traffic ($N=1,500$) |
| **False Auto-Handle Rate (FAHR)** | **6.90%** | [2.30%, 12.64%] | Adjudicated risk handoffs missed ($N=6 / 87$) |
| **Intent-Match Top-5 MRR** | **0.1000** | [0.0600, 0.1400] | Target intent category match (not resolution precedent) |
| **Claim Support Rate** | **100.00%** | [100.00%, 100.00%] | Evaluated among auto-handled replies with claims ($N=87$) |

*Explicit Disclosure: These figures represent conservative policy-benchmark results, not validated human resolution rates.*

---

## 2. What Is Misleading About Our Headline Numbers?

In production AI engineering, transparently detailing failure boundaries is critical. Below is the honest critique of our headline results (detailed in [`docs/misleading_headlines.md`](docs/misleading_headlines.md)):

1. **"93.55% Escalation Recall" is achieved through high conservatism**:
   * The policy routes **56.5%** of all benchmark inquiries to humans. Flagging more than half of all volume naturally makes high recall easier.
   * **26 Unnecessary Escalations (False Positives)**: Out of 113 escalated cases, 26 were safe troubleshooting queries where customer phrasing lacked keywords (e.g., *"facing problems with iPhone x contacted the customer care twice"*), falling to `unknown` intent and triggering human handoff.
   * **The 6.45% Misses are High-Risk**: The 6 missed escalations were transactional order cancellation or double charge requests (e.g. `eval_gold_163`: *"I made a mistake and I ordered twice. how to cancel the first order"*), which received generic order-tracking links instead of commerce routing.
2. **"43.5% Coverage" $\neq$ True Resolution (Solve Rate)**:
   * Coverage reflects automated reply generation, not customer problem resolution.
   * The 43.5% coverage is measured on a class-stratified 200-case benchmark. In unconstrained natural inbound traffic, coverage drops to **27.93%** due to ambient greetings and rants.
   * Within the 43.5% auto-handled slice ($N=87$), 6 cases (6.90%) should have been escalated immediately to a human.
3. **"100.0% Claim Support Rate" is Guarded by Refusal**:
   * Measured strictly among generated auto-handled responses with claims. The agent achieves high support by refusing to generate when intent confidence is low or retrieval scores fall below threshold ($\tau = 0.05$).
   * Grounding only verifies fidelity to the 2017 historical Twitter corpus; it does not ensure that 2017 temporary workarounds represent valid 2026 AppleCare solutions.
4. **"Intent-Match MRR = 0.1000" Reflects Corpus Imbalance**:
   * Measures the reciprocal rank of the first retrieved document matching the broad intent category, NOT human-verified solution relevance.
   * Dense + BM25 hybrid search frequently matches high-frequency iPhone troubleshooting documents even when the customer asks about Apple Watch or Mac.

---

## 3. Systematic Failure Analysis (Top 5 Real Failure Modes)

All failure modes discovered on the test set are cataloged with concrete IDs and remediations in [`docs/failure_analysis.md`](docs/failure_analysis.md) and [`eval/results/final/failure_cases.jsonl`](eval/results/final/failure_cases.jsonl):

* **FM-01: Transactional Order Modification False Auto-Handle (P0)**: Customer asked to cancel a duplicate order (`eval_gold_163`). Classifier accurately predicted `store_orders_shipping`, but escalation rules lacked action verbs for cancellations, outputting a generic tracking link. *Remediation: Add regex action triggers for transaction mutations.*
* **FM-02: Multi-Intent Query Collapse (P2)**: Customer inquired about parental controls over in-app purchases (`eval_gold_054`). Single-label classifier collapsed the query to `app_store_billing_subscriptions`, missing security boundaries. *Remediation: Hierarchical intent routing.*
* **FM-03: Conversational Underspecification Over-Escalation (P3)**: Vague phrasing without hardware symptoms (`eval_gold_015`) dropped classifier confidence below $\tau=0.55$, causing safe but inefficient human handoff. *Remediation: Autonomous clarification turn.*
* **FM-04: Cross-Device Entity Drift in Retrieval (P2)**: Apple Watch S2 battery drain (`eval_gold_040`) retrieved iPhone Low Power Mode documentation due to dominant iPhone term frequencies. *Remediation: Device taxonomy entity filtering.*
* **FM-05: Historical Workaround Deprecation Risk (P2)**: 2017 temporary workarounds for iOS 11 keyboard replacement bugs risk being served without freshness decay. *Remediation: Knowledge base temporal validity tagging.*

---

## 4. Complete Ablation Matrix (Validation Set Weak-Label Benchmark)

Evaluated across the held-out validation set ($N=1,500$ queries for escalation, $N=3,000$ for classification) against weak-supervision heuristic targets:

| Configuration | Intent Macro-F1 (Weak Label) | Coverage (Auto-Handle) | Escalation Recall | Groundedness (1-5) | Actionability (1-5) |
|---|---|---|---|---|---|
| **A. Baseline 0 (Majority)** | 0.0722 | 0.00% | 1.000 | 1.0 | 1.0 |
| **B. Baseline 1 (TF-IDF LogReg)** | 0.8546 | 0.00% | 1.000 | 2.2 | 2.1 |
| **C. Baseline 2 (Semantic 1-NN)** | 0.3838 | 45.00% | 0.620 | 2.8 | 2.7 |
| **D. LLM-Only (Zero Retrieval)** | — | 100.00% | 0.000 | 3.53 | 3.53 |
| **E. RAG (No Escalation)** | 0.8800 | 100.00% | 0.000 | 3.40 | 3.13 |
| **F. RAG + Policy Escalation** | 0.8800 | 27.93% | 0.991 | 4.60 | 4.50 |
| **G. Complete System (+ Evidence Checker)** | **0.8800** | **27.93%** | **0.991** | **4.80** | **4.60** |

---

## 5. Single-Command Reproducibility (< 2 Minutes)

### Step 1: Environment Setup
Ensure Python 3.10+ is installed:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### Step 2: Run All Invariant & Unit Tests
```powershell
python -m pytest tests/ -v
```
*(All 12 invariant, schema, and split guard tests pass in ~1.5s).*

### Step 3: Run the Official Unified Benchmark
```powershell
python scripts/run_final_evaluation.py
```
*(Verifies split guard disjointness across 81,767 cases, evaluates the quarantined test set $N=200$, computes $B=1,000$ bootstrap CIs, and prints the summary report in ~120s with zero external API dependencies).*

---

## 6. Key Documentation & Artifacts
* **Audit & Methodology**:
  * [`docs/phase3_audit.md`](docs/phase3_audit.md): Pre-implementation audit and remediation of circularity and split leakage.
  * [`docs/annotation_quality.md`](docs/annotation_quality.md): Annotation protocol and calibration study design.
  * [`docs/final_leakage_audit.md`](docs/final_leakage_audit.md): Complete split leakage audit verifying 0 overlap across 81,767 cases.
  * [`docs/experiment_registry.md`](docs/experiment_registry.md): Traceability matrix from EXP-DATA-01 to EXP-TEST-FINAL.
  * [`docs/decision_log.md`](docs/decision_log.md): 20 substantive engineering decisions.
* **Results & Failure Corpora**:
  * [`docs/misleading_headlines.md`](docs/misleading_headlines.md): Critical analysis of headline metrics.
  * [`docs/failure_analysis.md`](docs/failure_analysis.md): Top 5 real failure modes with root causes.
  * [`eval/results/final/final_test_metrics.json`](eval/results/final/final_test_metrics.json): Machine-readable metrics.
  * [`eval/results/final/confidence_intervals.json`](eval/results/final/confidence_intervals.json): 95% bootstrap confidence intervals.
  * [`eval/results/final/failure_cases.jsonl`](eval/results/final/failure_cases.jsonl): Empirical failure case records.
