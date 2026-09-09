# Data Cleaning & Evaluation Leakage Analysis

## 1. Overview of Evaluation Leakage Risks
Evaluation leakage occurs when information from test/golden sets contaminates the retrieval corpus, prompt context, or training features, leading to artificially inflated benchmark numbers.
In Twitter Customer Support datasets, standard random sampling produces catastrophic evaluation leakage if performed carelessly.

---

## 2. Identified Leakage Mechanisms & Real Dataset Evidence

### 2.1 Multi-Turn Conversation Entanglement (Thread Leakage)
* **Mechanism**: In a multi-turn conversation (e.g., Turn 1: *"My battery drains fast"*, Turn 2: *"What iOS version?"*, Turn 3: *"iOS 11.1 on iPhone 7"*), splitting by individual tweet puts Turn 1 in Train and Turn 3 in Golden.
* **Why It Corrupts Evaluation**: The retrieval retriever or model would have access to the exact customer ID, device specs, and prior problem description from Train when answering the test turn.
* **Mitigation**: **Whole-Conversation Partitioning**. The atomic unit of data splitting is the entire Conversation DAG (`conversation_id`). All turns and derived cases from a thread are guaranteed to reside in the exact same split.

### 2.2 Template Memorization & Boilerplate Response Inflation
* **Mechanism**: Brands often employ canned responses for specific workflows (e.g. *"Please send us a DM with your Apple ID email"*). If thousands of near-identical queries appear in both splits, a 1-NN retriever trivially memorizes the exact canned text without understanding the problem.
* **Empirical Finding**: `@AppleSupport` has an outbound template duplication rate of **8.30%** (substantially cleaner than Uber at 49.66%), but requires deduplication for retrieval index construction.
* **Mitigation**: Normalization and fuzzy MinHash deduplication of reference responses in the retrieval bank.

### 2.3 Exact & Near-Duplicate Customer Queries
* **Mechanism**: Viral software issues (e.g., the iOS 11.1 "I" autocorrect bug, battery drain complaints after an update) cause hundreds of distinct users to tweet verbatim phrases like *"why is my I changing to an A [?] symbol"*.
* **Mitigation**: Stratified sampling for the Golden Set filters out identical verbatim customer strings, capping duplicate query clusters to ensure diversity.

### 2.4 User-Level Leakage (Cross-Thread Customer Recurrence)
* **Mechanism**: High-frequency Twitter users submit multiple distinct support inquiries across months.
* **Measurement**: For AppleSupport, 58,567 unique customers generate 53,010 two-sided conversations, indicating an average of ~1.1 conversations per customer. Customer-level overlap across distinct conversations is less than 5%.

---

## 3. Concrete Splitting & Deduplication Strategy
1. **Splitting Hierarchy**: `Conversation` -> all child `Cases` -> assigned exclusively via SHA-256 hash modulo.
2. **Physical Directory Isolation**:
   * `data/twcs/twcs.csv` (Raw - Git ignored)
   * `eval/golden/candidates/` (Gated candidate pool)
   * `eval/golden/annotations/` (Human annotation records)
   * `eval/golden/final/` (Immutable test set)
   * `eval/hard/candidates/` (Hard / adversarial cases)
3. **Retrieval Corpus Sanitization**: All conversations assigned to `eval/` are strictly excluded from the historical retrieval index and baseline training sets.
