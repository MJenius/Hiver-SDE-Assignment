# Context-Awareness Experiment: Preceding Turn Impact

## 1. Experimental Setup
* **Objective**: Measure whether feeding conversation context improves intent classification and retrieval groundedness.
* **Evaluation Set**: 3,000 cases from `validation`.
* **Configurations Tested**:
  * **C1: Query Only**: Customer message evaluated in isolation.
  * **C2: Bounded Context**: Customer message concatenated with the immediate last 2 preceding turns along the dialogue path.
  * **C3: Full Path Context**: Customer message concatenated with all ancestral turns along the dialogue path.

## 2. Quantitative Results

| Configuration | Accuracy | Macro-F1 | Delta F1 vs C1 |
|---|---|---|---|
| **C1: Query Only** | 0.9567 | 0.8800 | baseline |
| **C2: Bounded Context (Last 2 turns)** | 0.7943 | 0.6975 | -0.1825 |
| **C3: Full Path Context** | 0.7603 | 0.6654 | -0.2146 |

## 3. Analysis & Production Recommendation
1. **Query-Only (C1) Dominates Intent Classification (0.8800 vs 0.6975)**: Preceding turns often contain broad support greetings or previous symptoms that dilute the discriminative signal of the immediate customer query. For intent classification, evaluating the customer message directly (C1) yields superior accuracy and macro-F1.
2. **Context Role in Generation vs. Classification**: While intent classification is highest on raw query text (C1), generative response drafting requires bounded context (C2) to understand antecedent pronouns and troubleshooting history (*"I tried that, still failing"*).
3. **Production Design**: The pipeline uses **C1 (Query Only) for intent classification** to maximize classification precision, and passes **C2 (Bounded Context, last 2 turns) to the retrieval engine and response generator** for grounded dialogue comprehension.
