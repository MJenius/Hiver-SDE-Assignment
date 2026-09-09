# LLM-as-Judge Protocol & Calibration Simulation Walkthrough

## 1. Provenance & Purpose Disclosure

This document describes the calibration walkthrough and operational rubric designed for evaluating the Gemini LLM Judge. 

> [!IMPORTANT]
> **Simulation Disclosure**: In the exploratory Phase 2 run (`eval/run_agent_eval.py`), calibration scores were generated via a programmatic perturbation simulation over automated judge outputs to test the scoring pipeline, agreement math, and tie-breaking mechanics. **No empirical human agreement statistic was measured.** The metrics below represent a protocol calibration walkthrough and design template, not an observed biological human evaluation.

---

## 2. Judge Calibration Walkthrough Metrics (Simulation Run)

* **Exact Agreement Target**: 80.0%
* **Agreement within +/- 1 Band Target**: 100.0%
* **Simulation Cohen's Kappa**: 0.5455 (Moderate agreement benchmark)
* **Position Bias Control**: Evaluated via two-pass position swapping ($(A, B)$ and $(B, A)$), with contradictory pairs deterministically resolved to ties.

---

## 3. Disagreement Boundary Analysis (Design Rubric)

Inspecting discrepancies in automated scoring revealed key operational areas requiring rubric refinement:
1. **Clarifying Questions**: Terse support tweets asking the user for their iOS version or hardware model were initially penalized as "unactionable" by standard LLM prompts. The rubric in `eval/judge/llm_judge.py` was refined to explicitly recognize diagnostic information-gathering as actionable support behavior.
2. **Platform Brevity**: Evaluators must account for Twitter's 280-character limit, avoiding penalization of concise, link-directed responses in favor of long explanatory prose.

---

## 4. Production Human Validation Protocol (Roadmap)

Before deploying the LLM judge as an automated production gate:
1. **Sampling**: Draw 50 representative candidate replies across all 10 intent categories.
2. **Independent Scoring**: Two human support leads score Groundedness (1-5), Actionability (1-5), and Tone (1-5) blindly without seeing LLM ratings.
3. **Statistical Validation**: Calculate Cohen's Kappa ($\kappa$) and Pearson correlation ($r$). Model passes only if $\kappa \ge 0.70$ on Groundedness and Actionability.
