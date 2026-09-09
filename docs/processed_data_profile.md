# Processed Data Profile: AppleSupport Case Corpus

## 1. Corpus Summary
* **Initiating Roots**: 51,517
* **Two-Sided Conversations (>= 2 turns)**: 51,211
* **Total Actionable Cases**: 81,767
* **Cases with Historical Support Responses**: 68,862 (84.22%)
* **Branched Conversation DAGs**: 3,259 (6.36%)

## 2. Partition Distribution (Zero-Leakage Whole-Conversation Hash)

| Split | Conversations | % of Convs | Cases | % of Cases | Primary Role |
|---|---|---|---|---|---|
| `train` | 35,873 | 70.05% | 57,421 | 70.23% | Historical Case Index, BM25 Index, TF-IDF fitting |
| `dev` | 5,127 | 10.01% | 8,037 | 9.83% | Retrieval ablations, prompt iteration, context experiments |
| `val` | 5,175 | 10.11% | 8,344 | 10.2% | Escalation threshold sweep, judge calibration |
| `test` | 5,036 | 9.83% | 7,965 | 9.74% | Quarantined source of Golden and Hard sets |

## 3. Conversation Length Distribution

| Length (Turns) | Count | % of Total |
|---|---|---|
| 2 turns | 33,442 | 65.3% |
| 3 turns | 4,328 | 8.45% |
| 4 turns | 7,125 | 13.91% |
| 5 turns | 1,853 | 3.62% |
| 6 turns | 2,145 | 4.19% |
| 7 turns | 801 | 1.56% |
| 8 turns | 705 | 1.38% |
| 9 turns | 276 | 0.54% |

## 4. Context Depth Breakdown
* **Initiating Queries (Turn index = 0, no prior context)**: 62.6% of cases.
* **Follow-up Queries (Turn index >= 2, requiring preceding context)**: 37.4% of cases.
