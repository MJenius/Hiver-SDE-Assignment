# AI Customer Support Agent Benchmark — Phase 1: Empirical Foundation

[![Tests](https://img.shields.io/badge/pytest-10%20passed-brightgreen.svg)]()
[![Dataset SHA-256](https://img.shields.io/badge/SHA--256-cd297fcf...-blue.svg)](docs/data_manifest.json)
[![Selected Brand](https://img.shields.io/badge/Brand-%40AppleSupport-black.svg)](docs/brand_selection.md)

This repository contains the completed **Phase 1: Empirical Foundation & Evaluation Design** of the SDE internship take-home assignment for Hiver.

Phase 1 establishes an unshakeable, evidence-based benchmark foundation for an AI Customer Support Agent on the Kaggle "Customer Support on Twitter" dataset (`data/twcs/twcs.csv`).

In accordance with strict empirical principles, **Phase 1 introduces zero premature models, zero fabricated benchmark numbers, and zero data leakage**.

---

## 1. Executive Summary

1. **Selected Brand**: `@AppleSupport` (Score: **4.61 / 5.0** on transparent supportability rubric).
2. **Why Selected**: 58,567 unique customers (highest in dataset), rich technical troubleshooting dialogues, low customer duplication (0.58%), clean English corpus (87.5%), and clear operational boundaries for auto-handling vs. escalation. Top alternatives (`@AmazonHelp` and `@Uber_Support`) were rejected due to 23% multilingual fragmentation and 49.66% template duplication, respectively.
3. **Reconstructed Scale**: **53,010** two-sided conversations ($\ge 2$ turns) and **84,608** actionable support cases reconstructed via DAG traversal.
4. **Leakage Controls**: **Whole-conversation hashing** ensures zero overlap between Train, Dev, Golden, and Hard splits.
5. **Intent Taxonomy**: 10 operational classes (9 device support intents + `unknown` fallback) grounded in data clustering and AppleCare triage workflows (`configs/intents.yaml`).
6. **Evaluation Sets**:
   - `eval/golden/candidates/golden_candidates.jsonl`: Exactly 200 stratified evaluation candidates.
   - `eval/golden/annotations_template.csv`: Standardized annotation sheet with `evidence_sufficient` and `should_escalate` fields.
   - `eval/hard/candidates/hard_candidates.jsonl`: 100 hard cases (multi-intent, ultra-short, context-dependent).
7. **Baselines & Metrics Formally Specified**: Baseline 0 (Majority), Baseline 1 (TF-IDF + Logistic Regression), Baseline 2 (Dense Nearest Neighbor).

---

## 2. Repository Structure

```
├── .gitignore                      # Strictly excludes raw data/ and large datasets
├── pyproject.toml                  # Python package configuration
├── .env.example                    # Environment variable templates
├── README.md                       # Reproducibility guide & documentation index
├── src/
│   ├── reconstruction.py           # Directed graph conversation & case reconstruction
│   └── splitting.py                # Zero-leakage whole-conversation hashing & splitting
├── scripts/
│   ├── inspect_data.py             # Memory-safe streaming profiler & SHA-256 calculator
│   ├── select_brand.py             # Quantitative candidate brand analysis & template scoring
│   ├── reconstruct_conversations.py# Full reconstruction of AppleSupport dialogues
│   └── build_golden_candidates.py  # Stratified sampling of golden & hard evaluation sets
├── eval/
│   ├── golden/
│   │   ├── candidates/             # eval/golden/candidates/golden_candidates.jsonl (200 items)
│   │   ├── annotations/            # Human annotation protocol & records
│   │   ├── final/                  # Final quarantined golden test benchmark (Phase 2)
│   │   └── annotations_template.csv# Annotation sheet
│   └── hard/
│       └── candidates/             # eval/hard/candidates/hard_candidates.jsonl (100 items)
├── configs/
│   └── intents.yaml                # Formal 10-class intent schema with precedence rules
├── tests/
│   ├── test_invariants.py          # Manifest, schema, and sampling invariant tests
│   ├── test_reconstruction.py      # Graph traversal, branching, and cycle tests
│   └── test_splitting.py           # Deterministic whole-conversation split tests
└── docs/
    ├── data_model.md               # 5-tier entity specification (Tweet -> Case -> Example)
    ├── data_assumptions.md         # Reference behavior != ground truth; response coverage limits
    ├── data_manifest.json          # Dataset provenance, SHA-256, row count, environment
    ├── data_profile.json           # Raw JSON data profiling statistics
    ├── data_profile.md             # Human-readable dataset quality report
    ├── brand_selection.md          # Multi-criteria scoring rubric & candidate rejection rationale
    ├── conversation_graph_analysis.md # Branching, orphan turns, and thread distributions
    ├── leakage_analysis.md         # Entanglement mechanisms, template risks, & mitigations
    ├── intent_taxonomy.md          # Full taxonomy definitions, inclusion/exclusion criteria
    ├── ambiguity_analysis.md       # Taxonomy of ambiguity (multi-intent, low info, context)
    ├── golden_set_protocol.md      # Sampling strategy & annotation agreement protocol
    ├── evaluation_plan.md          # Exact formulas for Intent, Retrieval, Escalation & Judge
    ├── baselines.md                # Specifications for Baselines 0, 1, and 2
    ├── failure_taxonomy.md         # Top data-grounded failure modes
    ├── decision_log.md             # 12 substantive engineering & methodological decisions
    └── phase1_summary.json         # Complete machine-readable Phase 1 summary
```

---

## 3. Reproducibility in Under 15 Minutes

### Step 1: Environment Setup
Ensure Python 3.10+ is installed:
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
```

### Step 2: Run Automated Unit & Invariant Tests
```powershell
python -m pytest tests/
```
*(All 10 unit and invariant tests will pass in < 1 second).*

### Step 3: Reproduce Pipeline Scripts
Each script runs independently and deterministically (`seed=42`):
```powershell
# 1. Profile dataset & compute SHA-256 digest (~2 min)
python scripts/inspect_data.py

# 2. Evaluate candidate brands & template duplication (~2 min)
python scripts/select_brand.py

# 3. Reconstruct conversations and analyze graph DAG (~2 min)
python scripts/reconstruct_conversations.py

# 4. Generate 200 stratified golden candidates and 100 hard cases (~1.5 min)
python scripts/build_golden_candidates.py
```

---

## 4. Key Epistemic Principles Governing this Benchmark
* **Response Coverage $\ne$ Solve Rate**: Outbound agent presence reflects response coverage. True resolution requires post-interaction verification.
* **Historical Behavior $\ne$ Ground Truth**: Past support tweets reflect reference behavior, not infallible policy. We evaluate whether drafts are grounded in evidence, not whether they memorize 2017 tweets.
* **Whole-Conversation Partitioning**: Zero tweet-level splitting. All turns belonging to a conversation DAG remain together.
* **Separation of Intent from Escalation**: An intent can be completely clear while still requiring mandatory human escalation (e.g. account takeover, unauthorized charges).
