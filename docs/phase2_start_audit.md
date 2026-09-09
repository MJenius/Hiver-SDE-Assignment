# Phase 2 Start Audit: Foundation Verification, Constraints & Plan of Record

## 1. Verified Phase 1 Artifacts
All Phase 1 code, data manifests, schemas, and tests were audited at commit `64368df` (tagged and pushed as `phase-1-foundation`):
* **`data/twcs/twcs.csv`**: Provenance locked with SHA-256 `cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0` (2,811,774 records, 492.58 MB).
* **Selected Brand**: `@AppleSupport` validated with 204,756 extracted tweets and 58,567 unique customers.
* **Conversation Graph Model**: Preserves local DAG structure (`graph: parent_id -> [child_ids]`) and derived distinct linear root-to-leaf paths (`derived_paths`), guaranteeing path-isolated Case contexts without parallel sibling branch pollution.
* **Intent Taxonomy**: 10-class schema (9 device support intents + `unknown` fallback) validated in `configs/intents.yaml`.
* **Golden & Hard Evaluation Pools**:
  * `eval/golden/candidates/golden_candidates.jsonl`: 200 stratified candidates quarantined from model tuning.
  * `eval/hard/candidates/hard_candidates.jsonl`: 100 naturally occurring Hard / Stress candidates (multi-intent, ultra-short, context-dependent).
* **Test Suite**: 9/9 unit and invariant tests passing (`pytest tests/`).

---

## 2. Identified Discrepancies & Required Fixes
1. **Split Granularity in `src/splitting.py`**:
   * *Observation*: Phase 1 `partition_conversations` defaulted to 3 splits: `train` (80%), `dev` (10%), and `test` (10%).
   * *Phase 2 Requirement*: Phase 2 mandates explicit separation among:
     - `train` (70%): Primary training corpus and retrieval index.
     - `dev` (10%): Exploration, feature iteration, and context ablation.
     - `validation` (10%): Metric threshold tuning, confidence sweep, and judge calibration.
     - `test` (10%): Held-out partition from which the 200 Golden Candidates and 100 Hard/Stress Candidates were sampled.
   * *Action*: Update `src/splitting.py` to support explicit 4-way partition (`train`: 0.70, `dev`: 0.10, `val`: 0.10, `test`: 0.10) while preserving existing `test` partition memberships deterministically.
2. **LLM Provider Isolation**:
   * *Requirement*: Gemini is the **exclusive LLM provider** for Phase 2. No OpenAI or LangChain/LangGraph dependencies.
   * *Action*: Build a dedicated zero-dependency REST client in `src/llm/gemini_client.py` using standard `urllib.request` with exponential backoff, strict JSON schema parsing, and disk-backed SHA-256 caching in `src/llm/cache.py`.

---

## 3. Inherited Assumptions & Invariants
1. **Historical Behavior != Ground Truth**: Reference support turns provide historical behavioral evidence, not infallible policy.
2. **Whole-Conversation Gating**: All turns and derived cases of a conversation must strictly belong to the same partition.
3. **Quarantine Contract**: No case from `test` (including Golden or Hard candidates) may be indexed into the training retrieval corpus or used for model parameter/threshold tuning.

---

## 4. Exact Data Splits for Phase 2
Partitions mapped via deterministic hashing (`seed=42`) over all 51,517 initiating root conversation IDs:
* **`train`** (70%): ~36,061 conversations (~59,000 cases). Sole source for TF-IDF training, semantic embeddings index, and BM25 store.
* **`dev`** (10%): ~5,152 conversations (~8,500 cases). Used for prompt iteration, retrieval ablations, and error analysis.
* **`validation`** (10%): ~5,152 conversations (~8,500 cases). Used for escalation threshold tuning, confidence sweeps, and judge calibration.
* **`test`** (10%): ~5,152 conversations (~8,500 cases). Quarantined source of the 200 Golden Candidates and 100 Hard/Stress Candidates.
