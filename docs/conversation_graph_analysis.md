# Conversation Graph Analysis: `@AppleSupport`

## 1. Graph Reconstruction Summary
* **Raw Extracted Brand Tweets**: 204,756
* **Initiating Dialogue Roots**: 53,427
* **Reconstructed Two-Sided Conversations (>= 2 turns)**: 53,010
* **Total Actionable Cases Extracted**: 84,608
* **Branching Nodes (1-to-many responses)**: 5,118
* **Orphan Turns (parent tweet deleted or unobserved)**: 30,201

## 2. Conversation Length Distribution (Turns per Conversation)

| Turn Count | Number of Conversations | % of Two-Sided Conversations |
|---|---|---|
| 2 turns | 34,674 | 65.41% |
| 3 turns | 4,525 | 8.54% |
| 4 turns | 7,303 | 13.78% |
| 5 turns | 1,921 | 3.62% |
| 6 turns | 2,191 | 4.13% |
| 7 turns | 826 | 1.56% |
| 8 turns | 731 | 1.38% |
| 9 turns | 286 | 0.54% |

## 3. Structural Anomalies Handled
1. **Branching Threads**: When multiple support agents reply to the same customer turn, both responses are preserved in chronological turn order and flagged as `is_branched = True`.
2. **Missing Parents / Orphans**: Twitter users frequently reply to tweets outside the 2017 scrape window or deleted tweets. Such customer turns are treated as sub-tree roots rather than dropping the conversation.
3. **Self-Loops**: Self-referencing tweet IDs are explicitly filtered during graph construction to prevent infinite cycles.
