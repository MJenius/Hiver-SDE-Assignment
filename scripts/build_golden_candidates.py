"""
scripts/build_golden_candidates.py
Generates stratified golden evaluation set candidate pools and hard evaluation candidate pools
from the strictly held-out test partition of reconstructed AppleSupport conversations.
Outputs:
  eval/golden/candidates/golden_candidates.jsonl
  eval/golden/annotations_template.csv
  eval/hard/candidates/hard_candidates.jsonl
"""

import os
import sys
import json
import csv
import re
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.splitting import partition_conversations
from src.reconstruction import (
    Turn, Case, Conversation,
    build_conversation_graph,
    reconstruct_conversation_paths,
    extract_cases_from_conversation
)
import pandas as pd

DATA_PATH = os.path.join("data", "twcs", "twcs.csv")
BRAND = "AppleSupport"
CHUNK_SIZE = 150_000
RANDOM_SEED = 42

INTENT_KEYWORDS = {
    "os_update_issues": [r"\bupdate\b", r"\bios 11\b", r"\bglitch\b", r"\binstall", r"\bverifying\b", r"\bkeyboard\b", r"\bautocorrect\b"],
    "battery_performance": [r"\bbattery\b", r"\bdrain\b", r"\bcharge\b", r"\bcharging\b", r"\boverheating\b", r"\bhot\b", r"\bpower\b"],
    "apple_id_account_security": [r"\bapple id\b", r"\bpassword\b", r"\bicmp\b", r"\blogin\b", r"\blocked\b", r"\bverification code\b", r"\b2fa\b", r"\bactivation lock\b"],
    "app_store_billing_subscriptions": [r"\bbill\b", r"\bbilling\b", r"\brefund\b", r"\bcharge\b", r"\bsubscription\b", r"\bpurchase\b", r"\bcard\b", r"\bapp store\b"],
    "hardware_screen_physical": [r"\bscreen\b", r"\bcracked\b", r"\bdisplay\b", r"\btouch\b", r"\bcamera\b", r"\bspeaker\b", r"\bwater\b", r"\bbroken\b"],
    "connectivity_wifi_bluetooth": [r"\bwi-?fi\b", r"\bbluetooth\b", r"\bairpods\b", r"\bdisconnect\b", r"\bpair\b", r"\bpairing\b", r"\bcellular\b"],
    "icloud_sync_storage": [r"\bicloud\b", r"\bsync\b", r"\bbackup\b", r"\bphotos\b", r"\bstorage full\b", r"\brestore\b"],
    "audio_music_media": [r"\bapple music\b", r"\bplaylist\b", r"\bpodcast\b", r"\bsong\b", r"\balbum\b", r"\bvolume\b"],
    "store_orders_shipping": [r"\border\b", r"\btracking\b", r"\bship\b", r"\bshipping\b", r"\bdeliv\b", r"\bgenius bar\b", r"\bstore\b"]
}

def matches_keywords(text: str, patterns: List[str]) -> bool:
    t = text.lower()
    return any(re.search(p, t) for p in patterns)

def build_candidates():
    print("Step 1: Streaming AppleSupport tweets...")
    tweets_by_id = {}
    brand_handle_lower = f"@{BRAND.lower()}"

    for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype=str):
        out_mask = (chunk["inbound"] == "False") & (chunk["author_id"] == BRAND)
        in_mask = (chunk["inbound"] == "True") & chunk["text"].str.lower().str.contains(brand_handle_lower, na=False)
        for _, row in chunk[out_mask | in_mask].iterrows():
            tweets_by_id[str(row["tweet_id"])] = row.to_dict()

    print(f"Loaded {len(tweets_by_id):,} candidate tweets.")
    children_map = build_conversation_graph(list(tweets_by_id.values()))

    roots = []
    for tw in tweets_by_id.values():
        tid = str(tw["tweet_id"])
        inbound = str(tw.get("inbound")).lower() == "true"
        parent = tw.get("in_response_to_tweet_id")
        if (not parent or str(parent) in ("nan", "none", "", "<na>")) and inbound:
            roots.append(tid)

    print(f"Found {len(roots):,} root initiating tweets. Partitioning conversations (seed={RANDOM_SEED})...")
    splits = partition_conversations(roots, train_ratio=0.8, dev_ratio=0.1, test_ratio=0.1, seed=RANDOM_SEED)
    test_roots = set(splits["test"])
    print(f"Test split contains {len(test_roots):,} conversations.")

    test_cases = []
    for r_id in test_roots:
        conv = reconstruct_conversation_paths(r_id, tweets_by_id, children_map, BRAND)
        if conv and conv.turn_count >= 2:
            cases = extract_cases_from_conversation(conv)
            for c in cases:
                if c.has_reference_response:
                    test_cases.append(c)

    print(f"Total candidate cases in test split: {len(test_cases):,}")

    golden_candidates = []
    hard_candidates = []

    intent_buckets = {k: [] for k in INTENT_KEYWORDS.keys()}
    intent_buckets["unknown"] = []

    for c in test_cases:
        txt = c.customer_turn.text
        matched_intents = [intent for intent, pats in INTENT_KEYWORDS.items() if matches_keywords(txt, pats)]
        
        is_hard = False
        ambiguity_type = "none"
        if len(matched_intents) > 1:
            is_hard = True
            ambiguity_type = "multi_intent"
        elif len(txt.split()) < 6:
            is_hard = True
            ambiguity_type = "short"
        elif len(c.context_turns) >= 2:
            is_hard = True
            ambiguity_type = "context_dependent"

        if is_hard:
            hard_candidates.append({
                "case": c,
                "ambiguity_type": ambiguity_type,
                "candidate_intents": matched_intents
            })

        if len(matched_intents) == 1:
            intent_buckets[matched_intents[0]].append(c)
        elif len(matched_intents) == 0:
            intent_buckets["unknown"].append(c)

    selected_golden = []
    example_idx = 1

    for intent, bucket in intent_buckets.items():
        bucket_sorted = sorted(bucket, key=lambda c: len(c.customer_turn.text))
        step = max(1, len(bucket_sorted) // 20) if bucket_sorted else 1
        sampled = bucket_sorted[::step][:20]
        
        for case in sampled:
            context_str = " | ".join([f"{t.speaker_role}: {t.text}" for t in case.context_turns]) if case.context_turns else ""
            record = {
                "example_id": f"eval_gold_{example_idx:03d}",
                "case_id": case.case_id,
                "conversation_id": case.conversation_id,
                "customer_message": case.customer_turn.text,
                "preceding_context": context_str,
                "candidate_intent": intent,
                "reference_historical_response": " | ".join([t.text for t in case.reference_support_turns]),
                "intent": "",
                "should_escalate": "",
                "escalation_reason": "",
                "evidence_sufficient": "",
                "ambiguity_type": "none" if not context_str else "context_dependent",
                "notes": ""
            }
            selected_golden.append(record)
            example_idx += 1

    print(f"Sampled {len(selected_golden)} golden candidates across {len(intent_buckets)} buckets.")

    os.makedirs("eval/golden/candidates", exist_ok=True)
    with open("eval/golden/candidates/golden_candidates.jsonl", "w", encoding="utf-8") as f:
        for item in selected_golden:
            f.write(json.dumps(item) + "\n")

    fieldnames = [
        "example_id", "case_id", "conversation_id", "customer_message",
        "preceding_context", "candidate_intent", "reference_historical_response",
        "intent", "should_escalate", "escalation_reason", "evidence_sufficient",
        "ambiguity_type", "notes"
    ]
    with open("eval/golden/annotations_template.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in selected_golden:
            writer.writerow(item)

    os.makedirs("eval/hard/candidates", exist_ok=True)
    sampled_hard = hard_candidates[:100]
    with open("eval/hard/candidates/hard_candidates.jsonl", "w", encoding="utf-8") as f:
        for idx, h in enumerate(sampled_hard, 1):
            c = h["case"]
            ctx_str = " | ".join([f"{t.speaker_role}: {t.text}" for t in c.context_turns]) if c.context_turns else ""
            rec = {
                "example_id": f"eval_hard_{idx:03d}",
                "case_id": c.case_id,
                "conversation_id": c.conversation_id,
                "customer_message": c.customer_turn.text,
                "preceding_context": ctx_str,
                "reference_historical_response": " | ".join([t.text for t in c.reference_support_turns]),
                "ambiguity_type": h["ambiguity_type"],
                "candidate_intents": h["candidate_intents"]
            }
            f.write(json.dumps(rec) + "\n")

    print("Candidate generation complete:")
    print("  -> eval/golden/candidates/golden_candidates.jsonl (200 items)")
    print("  -> eval/golden/annotations_template.csv")
    print("  -> eval/hard/candidates/hard_candidates.jsonl (100 items - Hard / Stress Set)")

if __name__ == "__main__":
    build_candidates()
