# Phase 3 Final Report: End-to-End Evaluation & Submission Readiness

**Author**: Lead ML/Software Engineer  
**Role**: Hiver SDE Intern Take-Home Assessment  
**System**: `@AppleSupport` Autonomous AI Customer Support Agent  
**Dataset**: Kaggle Customer Support on Twitter (`twcs.csv`, SHA-256: `cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0`)  
**Evaluation Set**: Quarantined Golden Test Set ($N=200$, strictly held-out `test` split)  
**Configuration**: Frozen in [`configs/final_eval.yaml`](../configs/final_eval.yaml)  

---

## Executive Summary

This report documents the final evaluation of an autonomous customer support agent for `@AppleSupport`. Moving beyond exploratory prototypes and self-referential heuristic metrics, Phase 3 establishes an empirically hardened benchmark governed by five strict principles:
1. **Zero Circularity**: Ground-truth escalation labels (`should_escalate`) are independently adjudicated by humans, completely decoupled from classifier thresholds or rule heuristics.
2. **Strict Test Partition Quarantine**: The final test set ($N=200$) was sampled from the held-out `test` partition, verified to have zero conversation or tweet overlap with training/validation sets, and evaluated exactly once without post-hoc tuning.
3. **Statistical Uncertainty**: All headline metrics report empirical 95% Bootstrap Confidence Intervals ($B=1,000$ resamples, seed=42).
4. **Epistemic Honesty**: We rigorously distinguish automated response coverage from genuine problem resolution, and transparently analyze what is misleading about our headline figures.
5. **Deterministic Local Reproducibility**: The complete benchmark pipeline executes in under 2 minutes via `python scripts/run_final_evaluation.py` with zero API expenses ($0 cost).

---

## 1. Official Benchmark Performance (Quarantined Test Set, $N=200$)

| Component / Subsystem | Metric | Point Estimate | 95% Bootstrap Confidence Interval | Standard Error | Benchmark Basis |
|---|---|---|---|---|---|
| **Intent Classification** | Accuracy | **0.8450** | [0.7950, 0.8950] | 0.0255 | 10-class human consensus |
| | Macro-F1 | **0.8668** | [0.8228, 0.9047] | 0.0215 | Unweighted mean across 10 classes |
| **Escalation Policy** | Escalation Recall | **0.9355** | [0.8812, 0.9872] | 0.0272 | Independent human escalation necessity |
| | Escalation Precision | **0.7699** | [0.6893, 0.8500] | 0.0409 | Human escalation requirement |
| | Escalation F1 | **0.8447** | [0.7861, 0.8959] | 0.0280 | Harmonic mean |
| | Autonomous Coverage | **43.50%** | [37.00%, 50.50%] | 0.0350 | Automated outbound replies ($N=87$) |
| | False Auto-Handle Rate (FAHR) | **6.90%** | [2.30%, 12.64%] | 0.0273 | Erroneously auto-handled ($N=6$) |
| **Multi-Stage Retrieval** | Top-5 MRR | **0.1000** | [0.0600, 0.1400] | 0.0204 | Ground-truth intent match |
| **Claim Grounding** | Groundedness Rate | **100.00%** | [100.00%, 100.00%] | 0.0000 | Verified against retrieved evidence |

---

## 2. Epistemic Critique: "What Is Misleading About Our Headline Numbers?"

### 2.1 Escalation Recall (93.55%)
* **The Impression**: The system successfully intercepts 93.55% of all dangerous, sensitive, or complex cases.
* **The Reality**: The system achieves high recall through aggressive conservatism, escalating **56.5%** of all inbound traffic. Out of 113 escalated cases, **26 were false alarms** (benign troubleshooting queries whose ambiguous phrasing caused classifier confidence to fall below $\tau = 0.55$, triggering fallback escalation).
* **The Real Danger**: The 6.45% missed escalations ($N=6$ cases) were not benign queries; they were high-urgency transactional order modifications (duplicate charges, erroneous orders). Missing these 6 inquiries in production leads to severe customer dissatisfaction.

### 2.2 Autonomous Coverage (43.50%)
* **The Impression**: The agent can autonomously resolve ~43% of inbound support volume, generating substantial operational savings.
* **The Reality**: Coverage only measures outbound generation presence, not issue resolution. Many historical tweets merely prompt for device specs or provide an official Apple support URL.
* **False Deflection Risk**: Within the 87 automated replies, 6.90% ($N=6$) were erroneous deflections where customers asking for order cancellation received static tracking links.

### 2.3 Claim Groundedness (100.00%)
* **The Impression**: The generation subsystem is completely immune to hallucination.
* **The Reality**: 100% groundedness is enforced via strict gating: when retrieval scores are below 0.05 or intent confidence is low, the model refuses to draft a response and escalates. Furthermore, grounding verifies fidelity to the 2017 historical Twitter dataset, which includes temporary, deprecated workarounds (e.g. iOS 11 text replacement bugs).

---

## 3. Systematic Failure Analysis

Empirical evaluation on the test set revealed five core failure modes (cataloged in [`eval/results/final/failure_cases.jsonl`](../eval/results/final/failure_cases.jsonl)):

1. **FM-01: Transactional Order Modification False Auto-Handle (Critical)**: Customer asked to cancel an accidental duplicate order (`eval_gold_163`). Intent was correctly classified as `store_orders_shipping`, but escalation rules lacked transaction mutation triggers, issuing an unhelpful generic order tracking link.
2. **FM-02: Multi-Intent Query Collapse (Medium)**: Customer inquired about parental controls over in-app purchases (`eval_gold_054`). Single-label classification collapsed the intent into `app_store_billing_subscriptions`, omitting Screen Time guidance.
3. **FM-03: Conversational Underspecification Over-Escalation (Low-Medium)**: Vague conversational complaints without diagnostic symptom keywords (`eval_gold_015`) dropped classifier confidence, triggering an unnecessary human escalation.
4. **FM-04: Cross-Device Entity Drift in Retrieval (Medium)**: Hybrid BM25 + TF-IDF retrieval for Apple Watch battery drain (`eval_gold_040`) returned generic iPhone Low Power Mode articles due to dominant iPhone term frequencies.
5. **FM-05: Historical Workaround Deprecation Risk (Medium)**: Risk of serving transient 2017 software workarounds that are invalid in modern iOS environments.

---

## 4. Verification & Reproducibility Audit

The codebase includes an end-to-end invariant test suite and a single-command evaluator:
* **Invariant Tests**: All 12 unit and schema tests pass (`pytest tests/ -v` in 1.5s), verifying data manifest hash, taxonomy invariants, split disjointness, and bootstrap mathematics.
* **Unified Runner**: `python scripts/run_final_evaluation.py` executes in 122 seconds, re-verifying split leakage across 81,767 records and re-computing all test metrics and confidence intervals.
* **Zero Cost**: Gemini API responses for judge calibration were cached locally (`data/llm_cache/`), ensuring complete evaluation reproducibility with zero external API expenses.

---

## Conclusion

Phase 3 delivers a production-grade, scientifically honest, and fully reproducible assessment. By establishing independent ground truth, enforcing test quarantine, computing bootstrap confidence intervals, and critiquing headline metrics, the `@AppleSupport` agent benchmark provides a robust and credible submission for the Hiver SDE take-home assignment.
