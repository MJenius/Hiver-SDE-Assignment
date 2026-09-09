"""
scripts/select_brand.py
Evaluates candidate brands on empirical supportability, response coverage,
conversation reconstructability, customer diversity, and preliminary template/duplicate leakage.
Produces docs/brand_selection.md.
"""

import os
import re
import json
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

DATA_PATH = os.path.join("data", "twcs", "twcs.csv")
CHUNK_SIZE = 150_000

CANDIDATE_BRANDS = [
    "AmazonHelp",
    "AppleSupport",
    "Uber_Support",
    "SpotifyCares",
    "Delta",
    "Tesco",
    "AmericanAir",
    "comcastcares"
]

def normalize_tweet_text(text):
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"@\w+", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def evaluate_candidates():
    print(f"Evaluating {len(CANDIDATE_BRANDS)} candidate brands: {CANDIDATE_BRANDS}")
    
    brand_data = {b: {
        "outbound_count": 0,
        "inbound_count": 0,
        "unique_customers": set(),
        "outbound_texts": [],
        "inbound_texts": [],
        "outbound_tweet_ids": set(),
        "inbound_tweet_ids": set(),
        "in_response_to_map": {},
    } for b in CANDIDATE_BRANDS}

    cand_mentions = {f"@{b.lower()}": b for b in CANDIDATE_BRANDS}

    print("Pass 1: Streaming dataset to extract candidate tweets and inbound mappings...")
    chunk_idx = 0
    total_processed = 0

    for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype={"tweet_id": str, "in_response_to_tweet_id": str, "response_tweet_id": str, "author_id": str}):
        total_processed += len(chunk)
        chunk_idx += 1
        if chunk_idx % 5 == 0:
            print(f"  Processed {total_processed:,} rows...")

        inbound_mask = chunk["inbound"] == True

        # 1. Collect outbound for candidate brands
        outbound_chunk = chunk[~inbound_mask]
        for brand in CANDIDATE_BRANDS:
            brand_out = outbound_chunk[outbound_chunk["author_id"] == brand]
            if not brand_out.empty:
                brand_data[brand]["outbound_count"] += len(brand_out)
                brand_data[brand]["outbound_tweet_ids"].update(brand_out["tweet_id"].tolist())
                if len(brand_data[brand]["outbound_texts"]) < 5000:
                    brand_data[brand]["outbound_texts"].extend(brand_out["text"].tolist()[:5000 - len(brand_data[brand]["outbound_texts"])])

        # 2. Collect inbound directed to candidate brands
        inbound_chunk = chunk[inbound_mask]
        for text, author_id, tweet_id, in_resp in zip(inbound_chunk["text"], inbound_chunk["author_id"], inbound_chunk["tweet_id"], inbound_chunk["in_response_to_tweet_id"]):
            low_text = str(text).lower()
            for mention, brand in cand_mentions.items():
                if mention in low_text:
                    bdict = brand_data[brand]
                    bdict["inbound_count"] += 1
                    bdict["unique_customers"].add(author_id)
                    bdict["inbound_tweet_ids"].add(tweet_id)
                    if pd.notna(in_resp):
                        bdict["in_response_to_map"][tweet_id] = str(in_resp)
                    if len(bdict["inbound_texts"]) < 5000:
                        bdict["inbound_texts"].append(str(text))
                    break

    print("\nComputing metrics and preliminary leakage scores...")

    results = []
    for b in CANDIDATE_BRANDS:
        d = brand_data[b]
        out_cnt = d["outbound_count"]
        in_cnt = d["inbound_count"]
        cust_cnt = len(d["unique_customers"])

        norm_out = [normalize_tweet_text(t) for t in d["outbound_texts"]]
        norm_out_nonempty = [t for t in norm_out if len(t) > 10]
        out_unique_ratio = len(set(norm_out_nonempty)) / len(norm_out_nonempty) if norm_out_nonempty else 0.0
        out_template_rate = 1.0 - out_unique_ratio

        norm_in = [normalize_tweet_text(t) for t in d["inbound_texts"]]
        norm_in_nonempty = [t for t in norm_in if len(t) > 10]
        in_unique_ratio = len(set(norm_in_nonempty)) / len(norm_in_nonempty) if norm_in_nonempty else 0.0
        in_template_rate = 1.0 - in_unique_ratio

        resp_ratio = round(out_cnt / in_cnt, 3) if in_cnt > 0 else 0.0

        results.append({
            "brand": b,
            "outbound_count": out_cnt,
            "inbound_count": in_cnt,
            "unique_customers": cust_cnt,
            "outbound_sample_size": len(norm_out_nonempty),
            "outbound_template_rate": round(out_template_rate * 100, 2),
            "inbound_template_rate": round(in_template_rate * 100, 2),
            "resp_coverage_ratio": resp_ratio
        })

    df_res = pd.DataFrame(results)
    print("\nCandidate Comparison Table:")
    print(df_res.to_string())

    os.makedirs("docs", exist_ok=True)
    with open("docs/candidate_brands_profile.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    evaluate_candidates()

