# Experiment Registry & Headline Traceability Ledger

This ledger records every empirical experiment, benchmark evaluation, and headline figure across Phase 1, Phase 2, and Phase 3 of the project. Every reported metric is formally mapped to its unique Experiment ID, source partition, configuration, model, git commit, and data hash.

---

## 1. Traceability Summary Table

| Experiment ID | Purpose / Component | Git Commit | Dataset SHA-256 | Split | N | Primary Metric | Reported Point Estimate | 95% Confidence Interval | Execution Command |
|---|---|---|---|---|---|---|---|---|---|
| **EXP-DATA-01** | Raw Corpus Ingestion & Profiling | `64368df` | `cd297fcfa1bf...` | Full (`twcs.csv`) | 2,811,774 | Total Apple Cases | 84,608 cases | — | `python scripts/inspect_data.py` |
| **EXP-SPLIT-01** | Zero-Leakage 4-Way Splitting | `45d0b51` | `cd297fcfa1bf...` | All partitions | 81,767 | Overlap Check | 0 conversation overlap | — | `python src/evaluation/split_guard.py` |
| **EXP-BASE-00** | Baseline 0: Majority Class | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.0722 | [0.0680, 0.0765] | `python eval/run_baselines.py` |
| **EXP-BASE-01** | Baseline 1: TF-IDF LogReg | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.8546 | [0.8410, 0.8682] | `python eval/run_baselines.py` |
| **EXP-BASE-02** | Baseline 2: Semantic 1-NN | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.3838 | [0.3650, 0.4025] | `python eval/run_baselines.py` |
| **EXP-CLF-C1** | C1 Query-Only Context Intent Clf | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.8800 | [0.8675, 0.8924] | `python eval/run_classifier_eval.py` |
| **EXP-CLF-C2** | C2 Bounded-Context Turn Ablation | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.6975 | [0.6812, 0.7138] | `python eval/run_classifier_eval.py` |
| **EXP-CLF-C3** | C3 Full-Path Dialogue Ablation | `45d0b51` | `cd297fcfa1bf...` | `validation` | 3,000 | Intent Macro-F1 | 0.6654 | [0.6480, 0.6828] | `python eval/run_classifier_eval.py` |
| **EXP-RETR-R1** | R1 Lexical Search (BM25) | `45d0b51` | `cd297fcfa1bf...` | Index: `train` ($30k$) | 200 | MRR / Recall@5 | 0.2700 / 0.3550 | [0.2410, 0.2990] | `python eval/run_retrieval_experiments.py` |
| **EXP-RETR-R2** | R2 Dense Semantic Search | `45d0b51` | `cd297fcfa1bf...` | Index: `train` ($30k$) | 200 | MRR / Recall@5 | 0.2236 / 0.3200 | [0.1960, 0.2512] | `python eval/run_retrieval_experiments.py` |
| **EXP-RETR-R3** | R3 Hybrid Fusion (RRF $k=60$) | `45d0b51` | `cd297fcfa1bf...` | Index: `train` ($30k$) | 200 | MRR / Recall@5 | 0.2523 / 0.3600 | [0.2240, 0.2806] | `python eval/run_retrieval_experiments.py` |
| **EXP-RETR-R4** | R4 Hybrid + Cross-Encoder Rerank | `45d0b51` | `cd297fcfa1bf...` | Index: `train` ($30k$) | 200 | MRR / Recall@5 | 0.2694 / 0.3600 | [0.2405, 0.2983] | `python eval/run_retrieval_experiments.py` |
| **EXP-ESC-SWEEP** | Threshold Sweep ($\tau = 0.55$) | `45d0b51` | `cd297fcfa1bf...` | `validation` | 1,500 | Recall / Coverage | 99.12% / 27.93% | [98.6%, 99.6%] | `python eval/run_threshold_sweep.py` |
| **EXP-AGENT-01** | LLM-Only vs RAG Generation | `1dfb39f` | `cd297fcfa1bf...` | `validation` | 15 | Groundedness (1-5) | 3.40 (RAG) vs 3.53 | [3.10, 3.70] | `python eval/run_agent_eval.py` |
| **EXP-ANN-01** | Dual-Annotator Agreement Protocol | `78f2619` | `cd297fcfa1bf...` | `test` | 50 | Intent Kappa / Agreement | 0.8742 / 92.0% | [0.76, 0.98] | `eval/golden/annotations/` |
| **EXP-TEST-FINAL** | Quarantined Policy Benchmark Eval | `3a6baec` | `cd297fcfa1bf...` | Quarantined `test` | 200 | Policy-Adjudicated Benchmark | Macro-F1: 0.8668, Recall: 0.9355 | Bootstrap CIs ($B=1000$) | `python scripts/run_final_evaluation.py` |


---

## 2. Configuration & Parameter Reproducibility
* **Random Seed**: Fixed globally to `42` across NumPy, Scikit-Learn, and Python random modules.
* **LLM Temperature**: Generation at `0.2` (grounded responses); Judge evaluation at `0.0` (deterministic scoring).
* **Disk Cache**: Pluggable hash cache located at `data/llm_cache/` prevents repeated API expenditure.
