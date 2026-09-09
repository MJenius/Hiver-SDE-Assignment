"""
scripts/select_brand.py
Comprehensive empirical evaluation of candidate brands across all dimensions:
- Inbound & outbound volume
- Unique customer reach
- Response coverage ratio
- Inbound & outbound template / duplication rates
- Direct Message (DM) mention rate
- Self-service / external link rate
- Linguistic composition (% English vs non-English/multilingual)
Produces docs/candidate_brands_profile.json and updates docs/brand_selection.md.
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

def normalize_tweet_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    t = text.lower()
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"@\w+", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t

def is_english_ascii(text: str) -> bool:
    if not isinstance(text, str):
        return True
    return not bool(re.search(r"[^\x00-\x7F]", text))

def evaluate_candidates():
    print(f"Executing comprehensive empirical brand evaluation across {len(CANDIDATE_BRANDS)} candidate brands:")
    print(CANDIDATE_BRANDS)

    brand_data = {b: {
        "outbound_count": 0,
        "inbound_count": 0,
        "unique_customers": set(),
        "outbound_texts_sample": [],
        "inbound_texts_sample": [],
        "outbound_dm_count": 0,
        "outbound_link_count": 0,
        "outbound_non_ascii_count": 0,
        "outbound_total_scanned": 0
    } for b in CANDIDATE_BRANDS}

    cand_mentions = {f"@{b.lower()}": b for b in CANDIDATE_BRANDS}

    print("\nStreaming twcs.csv in chunks of 150,000...")
    chunk_idx = 0
    total_processed = 0

    for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype={"tweet_id": str, "in_response_to_tweet_id": str, "response_tweet_id": str, "author_id": str}):
        total_processed += len(chunk)
        chunk_idx += 1
        if chunk_idx % 5 == 0:
            print(f"  Processed {total_processed:,} rows...")

        inbound_mask = (chunk["inbound"] == True)

        # 1. Process Outbound
        outbound_chunk = chunk[~inbound_mask]
        for brand in CANDIDATE_BRANDS:
            b_out = outbound_chunk[outbound_chunk["author_id"] == brand]
            if not b_out.empty:
                bdict = brand_data[brand]
                bdict["outbound_count"] += len(b_out)
                bdict["outbound_total_scanned"] += len(b_out)
                
                # Link and DM presence
                dm_matches = b_out["text"].str.contains(r"\bDM\b", regex=True, na=False)
                link_matches = b_out["text"].str.contains(r"https?://", regex=True, na=False)
                non_ascii_matches = b_out["text"].str.contains(r"[^\x00-\x7F]", regex=True, na=False)
                
                bdict["outbound_dm_count"] += int(dm_matches.sum())
                bdict["outbound_link_count"] += int(link_matches.sum())
                bdict["outbound_non_ascii_count"] += int(non_ascii_matches.sum())

                # Collect sample for template analysis
                if len(bdict["outbound_texts_sample"]) < 5000:
                    needed = 5000 - len(bdict["outbound_texts_sample"])
                    bdict["outbound_texts_sample"].extend(b_out["text"].dropna().tolist()[:needed])

        # 2. Process Inbound
        inbound_chunk = chunk[inbound_mask]
        for text, author_id in zip(inbound_chunk["text"], inbound_chunk["author_id"]):
            low_text = str(text).lower()
            for mention, brand in cand_mentions.items():
                if mention in low_text:
                    bdict = brand_data[brand]
                    bdict["inbound_count"] += 1
                    bdict["unique_customers"].add(author_id)
                    if len(bdict["inbound_texts_sample"]) < 5000:
                        bdict["inbound_texts_sample"].append(str(text))
                    break

    print("\nComputing empirical metrics across all dimensions...")
    results = []
    
    for b in CANDIDATE_BRANDS:
        d = brand_data[b]
        out_cnt = d["outbound_count"]
        in_cnt = d["inbound_count"]
        cust_cnt = len(d["unique_customers"])

        # Template duplication rates on samples
        norm_out = [normalize_tweet_text(t) for t in d["outbound_texts_sample"]]
        norm_out_nonempty = [t for t in norm_out if len(t) > 10]
        out_unique_ratio = len(set(norm_out_nonempty)) / len(norm_out_nonempty) if norm_out_nonempty else 0.0
        out_template_rate = round((1.0 - out_unique_ratio) * 100, 2)

        norm_in = [normalize_tweet_text(t) for t in d["inbound_texts_sample"]]
        norm_in_nonempty = [t for t in norm_in if len(t) > 10]
        in_unique_ratio = len(set(norm_in_nonempty)) / len(norm_in_nonempty) if norm_in_nonempty else 0.0
        in_template_rate = round((1.0 - in_unique_ratio) * 100, 2)

        # DM %, Link %, and English %
        dm_rate = round((d["outbound_dm_count"] / out_cnt) * 100, 2) if out_cnt > 0 else 0.0
        link_rate = round((d["outbound_link_count"] / out_cnt) * 100, 2) if out_cnt > 0 else 0.0
        non_en_rate = round((d["outbound_non_ascii_count"] / out_cnt) * 100, 2) if out_cnt > 0 else 0.0
        en_rate = round(100.0 - non_en_rate, 2)
        resp_ratio = round(out_cnt / in_cnt, 3) if in_cnt > 0 else 0.0

        results.append({
            "brand": b,
            "outbound_count": out_cnt,
            "inbound_count": in_cnt,
            "unique_customers": cust_cnt,
            "resp_coverage_ratio": resp_ratio,
            "outbound_template_rate": out_template_rate,
            "inbound_template_rate": in_template_rate,
            "dm_mention_rate": dm_rate,
            "link_rate": link_rate,
            "english_rate": en_rate,
            "non_english_rate": non_en_rate
        })

    df_res = pd.DataFrame(results)
    print("\nEmpirical Candidate Comparison Table (Fully Derived):")
    print(df_res.to_string())

    os.makedirs("docs", exist_ok=True)
    with open("docs/candidate_brands_profile.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results

if __name__ == "__main__":
    evaluate_candidates()
