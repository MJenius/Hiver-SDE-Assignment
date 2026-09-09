"""
scripts/reconstruct_conversations.py
Executes conversation graph reconstruction on AppleSupport tweets from data/twcs/twcs.csv.
Preserves both the full graph DAG and derived root-to-leaf paths, saves inspectable samples,
and outputs docs/conversation_graph_analysis.md.
"""

import os
import sys
import json
from collections import Counter
from dataclasses import asdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import pandas as pd
from src.reconstruction import (
    Turn, Case, Conversation,
    build_conversation_graph,
    reconstruct_conversation_paths,
    extract_cases_from_conversation
)

DATA_PATH = os.path.join("data", "twcs", "twcs.csv")
BRAND = "AppleSupport"
CHUNK_SIZE = 150_000

def run_reconstruction():
    print(f"Step 1: Extracting all tweets involving @{BRAND}...")
    brand_handle_lower = f"@{BRAND.lower()}"
    tweets_by_id = {}
    
    chunk_idx = 0
    total_processed = 0
    
    for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype=str):
        total_processed += len(chunk)
        chunk_idx += 1
        if chunk_idx % 5 == 0:
            print(f"  Processed {total_processed:,} rows...")
            
        out_mask = (chunk["inbound"] == "False") & (chunk["author_id"] == BRAND)
        in_mask = (chunk["inbound"] == "True") & chunk["text"].str.lower().str.contains(brand_handle_lower, na=False)
        
        rel_chunk = chunk[out_mask | in_mask]
        for _, row in rel_chunk.iterrows():
            tid = str(row["tweet_id"])
            tweets_by_id[tid] = row.to_dict()

    print(f"Total candidate tweets collected for {BRAND}: {len(tweets_by_id):,}")

    print("Step 2: Building directed graph and identifying thread roots...")
    tweet_list = list(tweets_by_id.values())
    children_map = build_conversation_graph(tweet_list)

    roots = []
    orphan_replies = 0
    branching_count = 0

    for tw in tweet_list:
        tid = str(tw["tweet_id"])
        inbound = str(tw.get("inbound")).lower() == "true"
        parent = tw.get("in_response_to_tweet_id")

        if len(children_map.get(tid, [])) > 1:
            branching_count += 1

        if not parent or str(parent) in ("nan", "none", "", "<na>"):
            if inbound:
                roots.append(tid)
        else:
            p_str = str(parent)
            if p_str not in tweets_by_id:
                orphan_replies += 1
                if inbound:
                    roots.append(tid)

    print(f"Identified {len(roots):,} potential conversation roots.")
    print(f"Graph properties: {branching_count:,} branching nodes, {orphan_replies:,} orphan turns (missing parent).")

    print("Step 3: Traversing DAG and deriving linear dialogue paths...")
    conversations = []
    total_cases = []
    turn_length_counts = Counter()
    path_count_distribution = Counter()

    for root_id in roots:
        conv = reconstruct_conversation_paths(root_id, tweets_by_id, children_map, BRAND)
        if conv and conv.turn_count >= 2:
            has_customer = any(t.speaker_role == "customer" for t in conv.turns)
            has_support = any(t.speaker_role == "support" for t in conv.turns)
            if has_customer and has_support:
                conversations.append(conv)
                turn_length_counts[conv.turn_count] += 1
                path_count_distribution[len(conv.derived_paths)] += 1
                cases = extract_cases_from_conversation(conv)
                total_cases.extend(cases)

    print(f"Successfully reconstructed {len(conversations):,} two-sided conversations!")
    print(f"Total actionable cases extracted along derived paths: {len(total_cases):,}")

    os.makedirs("docs", exist_ok=True)
    sample_convs = [asdict(c) for c in conversations[:10]]
    with open("docs/reconstructed_conversations_sample.json", "w", encoding="utf-8") as f:
        json.dump(sample_convs, f, indent=2)

    md = f"""# Conversation Graph Analysis: `@{BRAND}`

## 1. Graph Reconstruction Summary
* **Raw Extracted Brand Tweets**: {len(tweets_by_id):,}
* **Initiating Dialogue Roots**: {len(roots):,}
* **Reconstructed Two-Sided Conversations (>= 2 turns)**: {len(conversations):,}
* **Total Actionable Cases Extracted**: {len(total_cases):,}
* **Branching Nodes (1-to-many responses)**: {branching_count:,}
* **Orphan Turns (parent tweet deleted or unobserved)**: {orphan_replies:,}
* **Multi-Path Conversations (Branched DAGs)**: {sum(cnt for paths, cnt in path_count_distribution.items() if paths > 1):,}

## 2. Conversation Length Distribution (Turns per Conversation)

| Turn Count | Number of Conversations | % of Two-Sided Conversations |
|---|---|---|
"""
    for length, cnt in sorted(turn_length_counts.items())[:8]:
        pct = round(cnt / len(conversations) * 100, 2)
        md += f"| {length} turns | {cnt:,} | {pct}% |\n"

    md += """
## 3. Structural Graph & Path Preservation
1. **Node and Edge Adjacency**: Each conversation preserves its local DAG graph (`graph: parent_id -> [child_ids]`).
2. **Derived Path Extraction**: Rather than flattening branched trees chronologically, the pipeline derives all distinct root-to-leaf paths (`derived_paths`).
3. **Context Isolation**: For any customer turn requiring response, context is formed strictly from ancestors along its specific dialogue path, preventing sibling branches from leaking unobserved context.
4. **Self-Loops & Cycles**: Self-referencing tweet IDs are explicitly filtered during graph construction.
"""
    with open("docs/conversation_graph_analysis.md", "w", encoding="utf-8") as f:
        f.write(md)

    print("docs/conversation_graph_analysis.md and docs/reconstructed_conversations_sample.json generated.")

if __name__ == "__main__":
    run_reconstruction()
