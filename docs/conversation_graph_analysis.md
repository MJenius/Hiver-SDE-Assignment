# Conversation Graph Analysis: `@AppleSupport`

## 1. Graph Reconstruction Summary
* **Raw Extracted Brand Tweets**: 204,756
* **Initiating Dialogue Roots**: 53,427
* **Reconstructed Two-Sided Conversations (>= 2 turns)**: 53,010
* **Total Actionable Cases Extracted**: 84,600
* **Branching Nodes (1-to-many responses)**: 5,118
* **Orphan Turns (parent tweet deleted or unobserved)**: 30,201
* **Multi-Path Conversations (Branched DAGs)**: 3,354

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

## 3. Structural Graph & Path Preservation
1. **Node and Edge Adjacency**: Each conversation preserves its local DAG graph (`graph: parent_id -> [child_ids]`).
2. **Derived Path Extraction**: Rather than flattening branched trees chronologically, the pipeline derives all distinct root-to-leaf paths (`derived_paths`).
3. **Context Isolation**: For any customer turn requiring response, context is formed strictly from ancestors along its specific dialogue path, preventing sibling branches from leaking unobserved context.
4. **Self-Loops & Cycles**: Self-referencing tweet IDs are explicitly filtered during graph construction.
