"""
Single-command unified evaluation runner for Phase 3 submission.

Runs:
1. Split & leakage guard assertions across whole-conversation splits
2. Quarantined final policy benchmark evaluation (N=200)
3. 95% Bootstrap confidence intervals calculation (B=1,000)
4. Summary metrics output with failure analysis and provenance disclosures

Execution: Deterministic local benchmark given frozen artifacts and cached outputs (< 2 minutes).
"""

import sys
import json
import time
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from src.evaluation.split_guard import audit_case_splits, SplitLeakageError
from eval.run_final_test_eval import run_final_evaluation


def main():
    start_time = time.time()
    print("=" * 70)
    print("  HIVER SDE INTERN ASSIGNMENT - PHASE 3 FINAL EVALUATION RUNNER")
    print("=" * 70)

    # 1. Split Guard Verification
    print("\n[Step 1/3] Verifying Data Split Integrity & Quarantined Test Guard...")
    try:
        audit_res = audit_case_splits()
        print(f"  --> PASS: Zero leakage across {audit_res['total_cases_audited']:,} cases. Test partition strictly disjoint.")
    except SplitLeakageError as e:
        print(f"  --> FAIL: Split guard violation: {e}")
        sys.exit(1)

    # 2. Quarantined Final Test Benchmark Execution
    print("\n[Step 2/3] Executing Final Benchmark Evaluation & Bootstrap CIs (N=200, B=1000)...")
    metrics, ci_results = run_final_evaluation()

    # 3. Print Official Summary Report
    elapsed = time.time() - start_time
    print("\n" + "=" * 70)
    print("  OFFICIAL PHASE 3 BENCHMARK RESULTS (Quarantined Test Set N=200)")
    print("=" * 70)
    
    ic = metrics["intent_classification"]
    ep = metrics["escalation_policy"]
    ret = metrics["retrieval"]
    gr = metrics["grounding"]

    print("\n1. INTENT CLASSIFICATION (Policy-Adjudicated Targets, 10 Classes):")
    print(f"  - Accuracy:         {ci_results['intent_accuracy']['point_estimate']:.4f}  [95% CI: {ci_results['intent_accuracy']['ci_lower']:.4f} - {ci_results['intent_accuracy']['ci_upper']:.4f}]")
    print(f"  - Macro-F1:         {ci_results['intent_macro_f1']['point_estimate']:.4f}  [95% CI: {ci_results['intent_macro_f1']['ci_lower']:.4f} - {ci_results['intent_macro_f1']['ci_upper']:.4f}]")

    print("\n2. ESCALATION POLICY & AUTONOMY:")
    print(f"  - Escalation Recall:    {ci_results['escalation_recall']['point_estimate']:.4f}  [95% CI: {ci_results['escalation_recall']['ci_lower']:.4f} - {ci_results['escalation_recall']['ci_upper']:.4f}]")
    print(f"  - Escalation Precision: {ci_results['escalation_precision']['point_estimate']:.4f}  [95% CI: {ci_results['escalation_precision']['ci_lower']:.4f} - {ci_results['escalation_precision']['ci_upper']:.4f}]")
    print(f"  - Escalation F1:        {ci_results['escalation_f1']['point_estimate']:.4f}  [95% CI: {ci_results['escalation_f1']['ci_lower']:.4f} - {ci_results['escalation_f1']['ci_upper']:.4f}]")
    print(f"  - Autonomous Coverage:  {ci_results['autonomous_coverage']['point_estimate']*100:.2f}%  [95% CI: {ci_results['autonomous_coverage']['ci_lower']*100:.2f}% - {ci_results['autonomous_coverage']['ci_upper']*100:.2f}%]")
    print(f"  - False Auto-Handle:    {ci_results['false_auto_handle_rate']['point_estimate']*100:.2f}%   [95% CI: {ci_results['false_auto_handle_rate']['ci_lower']*100:.2f}% - {ci_results['false_auto_handle_rate']['ci_upper']*100:.2f}%]")

    print("\n3. RETRIEVAL & GROUNDING:")
    print(f"  - Intent-Match MRR:     {ci_results['intent_match_mrr']['point_estimate']:.4f}  [95% CI: {ci_results['intent_match_mrr']['ci_lower']:.4f} - {ci_results['intent_match_mrr']['ci_upper']:.4f}]")
    print(f"  - Claim Support Rate:   {ci_results['claim_support_rate']['point_estimate']*100:.2f}% [95% CI: {ci_results['claim_support_rate']['ci_lower']*100:.2f}% - {ci_results['claim_support_rate']['ci_upper']*100:.2f}%]")

    print("\n" + "-" * 70)
    print(f"Execution completed in {elapsed:.2f} seconds.")
    print("Audit & Traceability Artifacts:")
    print("  - Detailed Metrics:     eval/results/final/final_test_metrics.json")
    print("  - Bootstrap CIs:        eval/results/final/confidence_intervals.json")
    print("  - Predictions:          eval/results/final/final_test_predictions.csv")
    print("  - Failure Mode Corpus:  docs/failure_analysis.md & eval/results/final/failure_cases.jsonl")
    print("  - Headline Critiques:   docs/misleading_headlines.md")
    print("=" * 70)


if __name__ == "__main__":
    main()
