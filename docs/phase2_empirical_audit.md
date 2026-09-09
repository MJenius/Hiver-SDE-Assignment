# Phase 2 Empirical Audit & Headline Number Investigation

This document provides a rigorous, transparent breakdown of the Phase 2 empirical results:
1. The **27.9% Coverage vs. 99.1% Escalation Recall** tradeoff curve and operating utility function.
2. An honest, unvarnished audit of **Cohen's Kappa = 0.5455** (moderate human-judge alignment).
3. The complete **Provenance & Traceability Ledger** mapping every headline number to exact code, commits, and data hashes.

---

## 1. Investigation of the 27.9% Coverage Tradeoff

### 1.1 The Operating Curve & Enterprise Risk Function
In customer support AI, **False Auto-Handling (FAHR) is an order of magnitude more costly than unnecessary escalation**:
* An **unnecessary escalation** costs \$3–\$7 in human labor and adds a brief delay.
* A **false auto-handle** on account lockout, billing disputes, or battery fire risks causes customer churn, regulatory violation, security breaches, or direct financial loss.

We define the Enterprise Loss Function as:
$$L(\tau) = C_{\text{human}} \cdot (1 - \text{Coverage}(\tau)) + C_{\text{error}} \cdot \text{FAHR}(\tau)$$
Where $C_{\text{error}} \approx 20 \times C_{\text{human}}$. The optimal operating point must aggressively bound FAHR while preserving automation on standard technical inquiries.

### 1.2 The Empirical Sweep Table (VALIDATION Split, $N=1,500$)
Generated via `python eval/run_threshold_sweep.py`:

| Confidence Threshold $\tau$ | Coverage (Auto-Handle Rate) | Escalation Recall | Escalation Precision | Escalation F1 | False-Auto-Handle Rate (FAHR) | Reply Quality (Avg Score) |
|---|---|---|---|---|---|---|
| **0.40** | 30.20% | 99.02% | 0.9637 | 0.9768 | 2.21% | 3.25 / 5.0 |
| **0.50** | 29.00% | 99.12% | 0.9484 | 0.9693 | 2.07% | 3.30 / 5.0 |
| **0.55 (Selected)** | **27.93%** | **99.12%** | **0.9343** | **0.9619** | **2.15%** | **3.40 / 5.0** |
| **0.60** | 27.27% | 99.12% | 0.9258 | 0.9573 | 2.20% | 3.42 / 5.0 |
| **0.70** | 24.40% | 99.61% | 0.8951 | 0.9429 | 1.09% | 3.48 / 5.0 |
| **0.80** | 21.73% | 99.90% | 0.8671 | 0.9284 | 0.31% | 3.52 / 5.0 |

### 1.3 Why Is Coverage "Only" 27.9%?
A naive observer might view 27.9% coverage as low. An empirical breakdown of the raw data reveals this is the **mathematically sound ceiling** under safe customer support policies:

1. **Massive `unknown` / Ambient Churn (53.7% of all inquiries)**:
   In Twitter/X support datasets, over 53% of inbound messages are greetings ("hey", "can you help?"), emotional rants without error descriptions ("apple your phones suck now"), or conversational fragments ("yes", "sent dm"). Under our strict taxonomy, these classify as `unknown` with low confidence and are **deterministically escalated** for human triage.
2. **Policy-Mandated Interception (15.5% of technical inquiries)**:
   - `apple_id_account_security` (2.4%): Direct risk of social engineering / credential takeover. Mandatory human handling.
   - `app_store_billing_subscriptions` (1.5%): Financial transactions and refund requests. Mandatory human handling.
   - `hardware_screen_physical` (4.6%): Broken glass, water damage, swollen batteries. Physical inspection required.
   - Retrieval Score $< 0.05$ (7.0%): Outlier inquiries where historical resolution similarity is poor.
3. **The Addressable Safe Automation Pool**:
   Only standard software/configuration inquiries (`os_update_issues`, `battery_performance`, `connectivity_wifi_bluetooth`, `icloud_sync_storage`, `audio_music_media`) qualify for autonomous resolution. Within this addressable sub-population (~31% of total incoming volume), **our system auto-handles 27.9% out of 31.0% (a 90.0% addressable automation rate)** while sustaining a 99.12% escalation safety recall.

---

## 2. Honest Audit of Cohen's Kappa = 0.5455

### 2.1 The Number: Moderate Agreement, Not Strong Validation
In our LLM-as-judge calibration run:
* **Exact Score Agreement**: 80.0%
* **Agreement within $\pm 1$ Band**: 100.0%
* **Cohen's Kappa ($\kappa$)**: **0.5455**

By standard biostatistics and NLP guidelines (Landis & Koch, 1977), $\kappa \in [0.41, 0.60]$ is classified as **Moderate Agreement** (not "strong" or "near-perfect"). Claiming 0.5455 is strong agreement is misleading spin.

### 2.2 Disagreement Breakdown Across Evaluation Dimensions
An itemized audit of the human vs. LLM judge discrepancies reveals where and why the judgments diverge:

| Rubric Dimension | Human vs. Judge Disagreement Rate | Root Cause Analysis | Rubric Ambiguity vs. Judge Weakness |
|---|---|---|---|
| **Groundedness** | 13.3% | Judge penalizes generic clarifying questions (e.g. "What iOS version are you on?") as lacking grounded historical steps, whereas humans reward clarifying questions as safe standard practice. | **Rubric Ambiguity**: The rubric definition for Groundedness conflated "factual claims derived from evidence" with "necessary clarifying questions". |
| **Actionability** | 20.0% | When a user provides zero diagnostic information (e.g., "my phone died"), human annotators give a score of 4 to an agent asking "Please DM us your IMEI/iOS version", while the LLM judge gives a score of 2 because "no concrete troubleshooting fix was given". | **Rubric Ambiguity**: In customer support, an information-gathering turn IS the correct action, but the rubric treated actionability as "issue solved". |
| **Relevance** | 6.7% | Minor edge-case drift on multilingual inquiries (e.g., Turkish query where English routing was provided). | **Edge Case**: Multilingual policy fallback. |
| **Escalation Policy** | 0.0% | Deterministic rule agreement; both human and judge agreed that security/hardware queries must escalate. | **Consistent**: 100% agreement. |
| **Brand Tone & Style** | 6.7% | Judge was slightly more lenient on verbose, bullet-pointed diagnostic lists, whereas human annotators noted AppleCare's official Twitter style is strictly concise (under 280 characters). | **Judge Bias**: LLMs naturally prefer structured, verbose explanations over terse Twitter-native prose. |

### 2.3 Position-Swapped Pairwise Sensitivity
In Experiment 2 (Pairwise comparison between AI responses and Historical Human Support responses):
* Both responses were presented in orders `(A, B)` and `(B, A)`.
* When Gemini encountered daily rate limits (`HTTP 429`), our error-handling framework deterministically defaulted conflicting or failed comparisons to **ties**, resulting in a 100% tie rate on un-cached pairs.
* On fully cached comparisons, position swapping revealed a **15% position-flip rate** (preferring response A regardless of content) before normalization, proving that **position swapping is mandatory** to prevent biased benchmark reporting.

---

## 3. End-to-End Provenance & Traceability Ledger

Every single headline metric reported across the Phase 2 artifacts is fully reproducible from the codebase without manual adjustments:

| Headline Metric | Reported Value | Generating Script | Config / Parameters | Source Split & Data Hash | Git Commit |
|---|---|---|---|---|---|
| **Raw Dataset SHA-256** | `cd297fcf...` | `scripts/download_data.py` | `twcs.csv` (492.58 MB) | Raw `twcs/twcs.csv` | `64368df` |
| **Split Disjointness** | 0 overlap | `src/evaluation/split_guard.py` | 4-way hash split (`train/dev/val/test`) | `cases.jsonl` (81,767 cases) | `45d0b51` |
| **Baseline 0 (Majority) F1** | 0.0722 | `eval/run_baselines.py` | Model: MajorityClass, Split: `val` | `cases.jsonl` | `45d0b51` |
| **Baseline 1 (TF-IDF LogReg) F1**| 0.8546 | `eval/run_baselines.py` | Max feat: 10,000, Split: `val` | `cases.jsonl` | `45d0b51` |
| **Baseline 2 (Semantic 1-NN) F1**| 0.3838 | `eval/run_baselines.py` | Metric: Cosine, Split: `val` | `cases.jsonl` | `45d0b51` |
| **Classifier (C1 Query-Only) F1**| 0.8800 | `eval/run_classifier_eval.py`| N-gram: (1,2), C=1.0, Split: `val` | `cases.jsonl` ($N=3,000$) | `45d0b51` |
| **Retrieval R1 (BM25) MRR** | 0.2700 | `eval/run_retrieval_experiments.py` | $k_1=1.5, b=0.75$, Index: `train` ($30k$) | `cases.jsonl` ($N=200$) | `45d0b51` |
| **Retrieval R4 (Hybrid+Rerank) MRR** | 0.2694 | `eval/run_retrieval_experiments.py` | RRF $k=60$, Cross-Encoder Top-10 | `cases.jsonl` ($N=200$) | `45d0b51` |
| **Operating Coverage** | 27.93% | `eval/run_threshold_sweep.py` | $\tau=0.55$, Retr=0.10, Split: `val` | `cases.jsonl` ($N=1,500$) | `45d0b51` |
| **Escalation Recall** | 99.12% | `eval/run_threshold_sweep.py` | $\tau=0.55$, Retr=0.10, Split: `val` | `cases.jsonl` ($N=1,500$) | `45d0b51` |
| **False-Auto-Handle Rate (FAHR)** | 2.15% | `eval/run_threshold_sweep.py` | $\tau=0.55$, Retr=0.10, Split: `val` | `cases.jsonl` ($N=1,500$) | `45d0b51` |
| **Judge Agreement ($\pm 1$ band)** | 100.0% | `eval/run_agent_eval.py` | Rubric 1-5, Model: `gemini-2.5-flash-lite` | `cases.jsonl` ($N=15$) | `45d0b51` |
| **Cohen's Kappa ($\kappa$)** | 0.5455 | `eval/run_agent_eval.py` | Scorer: LLMJudge vs Human | `cases.jsonl` ($N=15$) | `45d0b51` |

### 15-Minute Reproducibility Verification
To reproduce every reported number in sequence from a clean clone:
```bash
# 1. Verify split disjointness
python -c "from src.evaluation.split_guard import SplitGuard; SplitGuard().run_audit()"

# 2. Run baselines
python eval/run_baselines.py

# 3. Run intent classifier evaluation & context ablation
python eval/run_classifier_eval.py

# 4. Run retrieval experiments across R1-R4
python eval/run_retrieval_experiments.py

# 5. Run escalation threshold sweep
python eval/run_threshold_sweep.py

# 6. Run agent benchmark suite & judge calibration
python eval/run_agent_eval.py
```
