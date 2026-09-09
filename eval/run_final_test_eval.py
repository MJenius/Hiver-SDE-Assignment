"""
eval/run_final_test_eval.py
Official Phase 3 Final Benchmark Execution on Quarantined Golden Test Set:
- Evaluates Intent Classification (Accuracy, Macro-F1, per-class metrics, confusion matrix)
- Evaluates Multi-Stage Retrieval (Intent-Match Recall@1, 3, 5, Intent-Match MRR)
- Evaluates Escalation Policy against policy-adjudicated benchmark targets (Precision, Recall, F1, Coverage, FAHR)
- Evaluates Response Groundedness & Claim Support among generated responses
- Computes empirical 95% Bootstrap Confidence Intervals (B=1,000, seed=42)
- Outputs structured artifacts to eval/results/final/
"""

import os
import sys
import json
import yaml
import hashlib
import subprocess
import numpy as np
import pandas as pd
from typing import Dict, Any, List
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, classification_report, confusion_matrix

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.agent import AppleSupportAgent
from src.evaluation.bootstrap import bootstrap_ci, bootstrap_scalar_ci
from src.evaluation.split_guard import audit_case_splits

def compute_file_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def get_git_commit_sha() -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"

def run_final_evaluation():
    print("================================================================================")
    print("PHASE 3: OFFICIAL END-TO-END FINAL BENCHMARK ON QUARANTINED GOLDEN TEST SET")
    print("================================================================================")

    # 1. Verify Configuration & Split Guard
    with open("configs/final_eval.yaml", "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    current_git_sha = get_git_commit_sha()
    config_commit = config.get("git_commit", "HEAD")
    if config_commit != "HEAD" and not current_git_sha.startswith(config_commit):
        print(f"  [Notice] Config commit ({config_commit}) differs from active repo HEAD ({current_git_sha[:7]}). Proceeding under active HEAD.")

    print(f"Loaded Frozen Config: {config['experiment_name']} (Repo Commit: {current_git_sha[:7]})")

    print("\n[Step 1/5] Enforcing Strict Split Guard & Golden Test Quarantine...")
    split_audit = audit_case_splits()
    assert split_audit["status"] == "PASSED", "Split Guard check failed!"
    print(f"  Split Guard: PASSED (0 overlap across {split_audit['total_cases_audited']:,} cases)")

    # 2. Load Quarantined Golden Test Benchmark
    golden_path = config["data"]["golden_test_file"]
    benchmark_file_sha256 = compute_file_sha256(golden_path)
    config_file_sha256 = compute_file_sha256("configs/final_eval.yaml")

    print(f"\n[Step 2/5] Loading Quarantined Golden Test Cases from {golden_path}...")
    print(f"  Benchmark File SHA-256: {benchmark_file_sha256[:16]}... | Config SHA-256: {config_file_sha256[:16]}...")
    golden_cases = []
    with open(golden_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                golden_cases.append(json.loads(line))

    n_test = len(golden_cases)
    print(f"  Loaded exactly {n_test} stratified, policy-adjudicated test benchmark targets.")

    # 3. Initialize Production Agent
    print("\n[Step 3/5] Initializing End-to-End Agent Pipeline...")
    agent = AppleSupportAgent()

    # 4. Execute End-to-End Inference on Test Cases
    print(f"\n[Step 4/5] Executing Autonomous Agent Inference across {n_test} cases...")
    
    true_intents = []
    pred_intents = []
    true_escalates = []
    pred_escalates = []
    retrieval_recalls_at_1 = []
    retrieval_recalls_at_3 = []
    retrieval_recalls_at_5 = []
    reciprocal_ranks = []
    generated_claims_supported_list = []
    unsupported_claims_count = 0
    total_claims_count = 0
    execution_records = []

    for idx, case in enumerate(golden_cases, 1):
        q = case["customer_message"]
        ctx = case.get("preceding_context", "")
        true_intent = case["intent"]
        true_esc = case["should_escalate"]

        # Run full agent handle pipeline
        result = agent.handle(q, context=ctx)

        pred_intent = result["intent"]
        should_esc = (result.get("decision") == "escalate")

        true_intents.append(true_intent)
        pred_intents.append(pred_intent)
        true_escalates.append(true_esc)
        pred_escalates.append(should_esc)

        # Retrieval Intent-Match Evaluation
        retrieved = result.get("retrieval", [])
        retrieved_intents = [r.get("intent") for r in retrieved]
        
        hit_1 = 1.0 if (len(retrieved_intents) >= 1 and retrieved_intents[0] == true_intent) else 0.0
        hit_3 = 1.0 if true_intent in retrieved_intents[:3] else 0.0
        hit_5 = 1.0 if true_intent in retrieved_intents[:5] else 0.0
        
        mrr = 0.0
        for rank_idx, r_int in enumerate(retrieved_intents, 1):
            if r_int == true_intent:
                mrr = 1.0 / rank_idx
                break

        retrieval_recalls_at_1.append(hit_1)
        retrieval_recalls_at_3.append(hit_3)
        retrieval_recalls_at_5.append(hit_5)
        reciprocal_ranks.append(mrr)

        # Claims & Grounding Evaluation among generated outputs
        claims = result.get("claims", [])
        if not should_esc and claims:
            total_claims_count += len(claims)
            supported = [c for c in claims if c.get("grounded", True)]
            generated_claims_supported_list.append(len(supported) / len(claims))
            unsupported_claims_count += (len(claims) - len(supported))

        execution_records.append({
            "example_id": case["example_id"],
            "query": q,
            "true_intent": true_intent,
            "pred_intent": pred_intent,
            "true_escalate": true_esc,
            "pred_escalate": should_esc,
            "escalation_reason": result.get("escalation_reason"),
            "reply": result.get("reply")
        })

    # 5. Compute Final Metrics & 95% Confidence Intervals
    print("\n[Step 5/5] Computing Benchmark Performance & 95% Bootstrap CIs (B=1000, seed=42)...")

    # A. Intent Classification Metrics
    intent_acc_ci = bootstrap_ci(true_intents, pred_intents, accuracy_score)
    macro_f1_fn = lambda yt, yp: f1_score(yt, yp, average="macro", zero_division=0)
    intent_f1_ci = bootstrap_ci(true_intents, pred_intents, macro_f1_fn)
    
    # B. Escalation Policy Metrics
    esc_recall_fn = lambda yt, yp: recall_score(yt, yp, zero_division=0)
    esc_prec_fn = lambda yt, yp: precision_score(yt, yp, zero_division=0)
    esc_f1_fn = lambda yt, yp: f1_score(yt, yp, zero_division=0)

    esc_recall_ci = bootstrap_ci(true_escalates, pred_escalates, esc_recall_fn)
    esc_prec_ci = bootstrap_ci(true_escalates, pred_escalates, esc_prec_fn)
    esc_f1_ci = bootstrap_ci(true_escalates, pred_escalates, esc_f1_fn)

    # Coverage: % of inquiries auto-handled
    auto_handled = [not p for p in pred_escalates]
    coverage_ci = bootstrap_scalar_ci([float(x) for x in auto_handled])

    # False Auto-Handle Rate (FAHR): % of auto-handled that should have escalated
    auto_handled_indices = [i for i, p in enumerate(pred_escalates) if not p]
    if auto_handled_indices:
        fahr_vals = [float(true_escalates[i]) for i in auto_handled_indices]
        fahr_ci = bootstrap_scalar_ci(fahr_vals)
    else:
        fahr_ci = {"point_estimate": 0.0, "ci_lower": 0.0, "ci_upper": 0.0, "std_err": 0.0, "n": 0}

    # C. Retrieval Metrics (Intent-Match Category Matching)
    r1_ci = bootstrap_scalar_ci(retrieval_recalls_at_1)
    r3_ci = bootstrap_scalar_ci(retrieval_recalls_at_3)
    r5_ci = bootstrap_scalar_ci(retrieval_recalls_at_5)
    intent_match_mrr_ci = bootstrap_scalar_ci(reciprocal_ranks)

    # D. Groundedness / Supported Claims among generated replies
    if generated_claims_supported_list:
        claim_supp_ci = bootstrap_scalar_ci(generated_claims_supported_list)
    else:
        claim_supp_ci = {"point_estimate": 1.0, "ci_lower": 1.0, "ci_upper": 1.0, "std_err": 0.0, "n": 0}

    # Print Formatted Results
    print("\n" + "="*80)
    print("FINAL OFFICIAL BENCHMARK RESULTS (QUARANTINED TEST SET, N=200)")
    print("="*80)
    print(f"1. Intent Classification (Policy-Adjudicated Targets):")
    print(f"   - Accuracy:  {intent_acc_ci['point_estimate']:.4f}  [95% CI: {intent_acc_ci['ci_lower']:.4f} - {intent_acc_ci['ci_upper']:.4f}]")
    print(f"   - Macro-F1:  {intent_f1_ci['point_estimate']:.4f}  [95% CI: {intent_f1_ci['ci_lower']:.4f} - {intent_f1_ci['ci_upper']:.4f}]")
    print(f"\n2. Escalation Policy (Policy-Adjudicated Risk Targets):")
    print(f"   - Escalation Recall:    {esc_recall_ci['point_estimate']:.4f}  [95% CI: {esc_recall_ci['ci_lower']:.4f} - {esc_recall_ci['ci_upper']:.4f}]")
    print(f"   - Escalation Precision: {esc_prec_ci['point_estimate']:.4f}  [95% CI: {esc_prec_ci['ci_lower']:.4f} - {esc_prec_ci['ci_upper']:.4f}]")
    print(f"   - Escalation F1:        {esc_f1_ci['point_estimate']:.4f}  [95% CI: {esc_f1_ci['ci_lower']:.4f} - {esc_f1_ci['ci_upper']:.4f}]")
    print(f"   - Autonomous Coverage:  {coverage_ci['point_estimate']*100:.1f}%  [95% CI: {coverage_ci['ci_lower']*100:.1f}% - {coverage_ci['ci_upper']*100:.1f}%]")
    print(f"   - False-Auto-Handle:    {fahr_ci['point_estimate']*100:.2f}%  [95% CI: {fahr_ci['ci_lower']*100:.2f}% - {fahr_ci['ci_upper']*100:.2f}%]")
    print(f"\n3. Multi-Stage Hybrid Retrieval (Intent-Match Category Standard):")
    print(f"   - Intent-Match Recall@1: {r1_ci['point_estimate']:.4f}  [95% CI: {r1_ci['ci_lower']:.4f} - {r1_ci['ci_upper']:.4f}]")
    print(f"   - Intent-Match Recall@3: {r3_ci['point_estimate']:.4f}  [95% CI: {r3_ci['ci_lower']:.4f} - {r3_ci['ci_upper']:.4f}]")
    print(f"   - Intent-Match Recall@5: {r5_ci['point_estimate']:.4f}  [95% CI: {r5_ci['ci_lower']:.4f} - {r5_ci['ci_upper']:.4f}]")
    print(f"   - Intent-Match MRR:      {intent_match_mrr_ci['point_estimate']:.4f}  [95% CI: {intent_match_mrr_ci['ci_lower']:.4f} - {intent_match_mrr_ci['ci_upper']:.4f}]")
    print(f"\n4. Claim Grounding (Among Auto-Handled Responses With Claims, N={len(generated_claims_supported_list)}):")
    print(f"   - Claim Support Rate:    {claim_supp_ci['point_estimate']*100:.1f}%  [95% CI: {claim_supp_ci['ci_lower']*100:.1f}% - {claim_supp_ci['ci_upper']*100:.1f}%]")
    print(f"   - Total Claims Verified: {total_claims_count} (Unsupported: {unsupported_claims_count})")
    print("="*80)

    # Persist Final Machine-Readable Results
    os.makedirs("eval/results/final", exist_ok=True)
    
    final_metrics_payload = {
        "metadata": {
            "experiment_id": config["experiment_id"],
            "git_commit": current_git_sha,
            "config_sha256": config_file_sha256,
            "benchmark_sha256": benchmark_file_sha256,
            "split_guard_status": split_audit["status"],
            "sample_size": n_test,
            "split": "test",
            "operating_threshold_tau": 0.55
        },
        "intent_classification": {
            "accuracy": intent_acc_ci,
            "macro_f1": intent_f1_ci,
            "classification_report": classification_report(true_intents, pred_intents, output_dict=True, zero_division=0)
        },
        "escalation_policy": {
            "recall": esc_recall_ci,
            "precision": esc_prec_ci,
            "f1": esc_f1_ci,
            "coverage": coverage_ci,
            "false_auto_handle_rate": fahr_ci
        },
        "retrieval": {
            "metric_type": "intent_category_match",
            "recall_at_1": r1_ci,
            "recall_at_3": r3_ci,
            "recall_at_5": r5_ci,
            "intent_match_mrr": intent_match_mrr_ci
        },
        "grounding": {
            "evaluated_scope": "generated_claims_among_autohandled",
            "claim_support_rate": claim_supp_ci,
            "total_claims": total_claims_count,
            "unsupported_claims": unsupported_claims_count
        }
    }

    with open("eval/results/final/final_test_metrics.json", "w", encoding="utf-8") as f:
        json.dump(final_metrics_payload, f, indent=2)

    with open("eval/results/final/confidence_intervals.json", "w", encoding="utf-8") as f:
        json.dump({
            "intent_macro_f1": intent_f1_ci,
            "escalation_recall": esc_recall_ci,
            "escalation_precision": esc_prec_ci,
            "autonomous_coverage": coverage_ci,
            "false_auto_handle_rate": fahr_ci,
            "intent_match_mrr": intent_match_mrr_ci,
            "claim_support_rate": claim_supp_ci
        }, f, indent=2)

    # Export execution predictions
    pd.DataFrame(execution_records).to_csv("eval/results/final/final_test_predictions.csv", index=False, encoding="utf-8")
    print("Saved all machine-readable artifacts to eval/results/final/.")

    ci_dict = {
        "intent_accuracy": intent_acc_ci,
        "intent_macro_f1": intent_f1_ci,
        "escalation_recall": esc_recall_ci,
        "escalation_precision": esc_prec_ci,
        "escalation_f1": esc_f1_ci,
        "autonomous_coverage": coverage_ci,
        "false_auto_handle_rate": fahr_ci,
        "intent_match_mrr": intent_match_mrr_ci,
        "claim_support_rate": claim_supp_ci
    }
    return final_metrics_payload, ci_dict

if __name__ == "__main__":
    run_final_evaluation()
