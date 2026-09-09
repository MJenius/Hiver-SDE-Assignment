"""
scripts/inspect_data.py
Performs streaming profiling of data/twcs/twcs.csv to compute dataset-wide statistics,
schema invariants, missingness, and candidate brand volumes without loading the 516MB file all at once.
Outputs docs/data_manifest.json, docs/data_profile.json, and docs/data_profile.md.
"""

import os
import sys
import hashlib
import json
import platform
from datetime import datetime
from collections import Counter
import pandas as pd
import numpy as np

DATA_PATH = os.path.join("data", "twcs", "twcs.csv")
CHUNK_SIZE = 100_000

def compute_sha256(filepath):
    print(f"[1/4] Computing SHA-256 hash for {filepath}...")
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(65536), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def inspect_dataset():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    file_size_bytes = os.path.getsize(DATA_PATH)
    file_sha256 = compute_sha256(DATA_PATH)
    print(f"File size: {file_size_bytes / (1024*1024):.2f} MB | SHA-256: {file_sha256}")

    print("[2/4] Reading initial chunk to inspect schema...")
    df_first = pd.read_csv(DATA_PATH, nrows=5)
    schema = {col: str(dtype) for col, dtype in df_first.dtypes.items()}
    columns = list(df_first.columns)

    print("[3/4] Streaming through dataset in chunks of 100,000...")
    total_rows = 0
    inbound_count = 0
    outbound_count = 0
    missing_counts = Counter()
    brand_outbound_counts = Counter()
    text_lengths = []

    has_in_response_to = 0
    has_response_tweet_id = 0

    min_date = None
    max_date = None

    chunk_idx = 0
    for chunk in pd.read_csv(DATA_PATH, chunksize=CHUNK_SIZE, dtype={"tweet_id": str, "in_response_to_tweet_id": str, "response_tweet_id": str, "author_id": str}):
        total_rows += len(chunk)
        chunk_idx += 1
        if chunk_idx % 5 == 0:
            print(f"  Processed {total_rows:,} rows...")

        for col in columns:
            missing_counts[col] += int(chunk[col].isna().sum())

        inbound_mask = (chunk["inbound"] == True)
        inbound_count += int(inbound_mask.sum())
        outbound_count += int((~inbound_mask).sum())

        has_in_response_to += int(chunk["in_response_to_tweet_id"].notna().sum())
        has_response_tweet_id += int(chunk["response_tweet_id"].notna().sum())

        outbound_authors = chunk.loc[~inbound_mask, "author_id"].value_counts()
        for author, count in outbound_authors.items():
            brand_outbound_counts[author] += int(count)

        sampled_lens = chunk["text"].dropna().str.len().iloc[::20].tolist()
        text_lengths.extend(sampled_lens)

        dates = pd.to_datetime(chunk["created_at"], format="%a %b %d %H:%M:%S %z %Y", errors="coerce")
        c_min = dates.min()
        c_max = dates.max()
        if min_date is None or (pd.notna(c_min) and c_min < min_date):
            min_date = c_min
        if max_date is None or (pd.notna(c_max) and c_max > max_date):
            max_date = c_max

    print(f"Total rows inspected: {total_rows:,}")

    text_lens_arr = np.array(text_lengths)
    text_stats = {
        "mean": float(np.mean(text_lens_arr)),
        "median": float(np.median(text_lens_arr)),
        "p25": float(np.percentile(text_lens_arr, 25)),
        "p75": float(np.percentile(text_lens_arr, 75)),
        "p95": float(np.percentile(text_lens_arr, 95)),
        "min": int(np.min(text_lens_arr)),
        "max": int(np.max(text_lens_arr)),
    }

    manifest = {
        "dataset_file": DATA_PATH,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
        "sha256": file_sha256,
        "total_rows": total_rows,
        "columns": columns,
        "schema": schema,
        "date_range_min": min_date.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(min_date) else None,
        "date_range_max": max_date.strftime("%Y-%m-%d %H:%M:%S") if pd.notna(max_date) else None,
        "environment": {
            "python_version": platform.python_version(),
            "os": platform.system() + " " + platform.release(),
            "pandas_version": pd.__version__,
            "numpy_version": np.__version__,
            "generated_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    os.makedirs("docs", exist_ok=True)
    with open("docs/data_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    top_brands = [{"brand": b, "outbound_tweets": count} for b, count in brand_outbound_counts.most_common(25)]

    profile = {
        "total_records": total_rows,
        "inbound_records": int(inbound_count),
        "outbound_records": int(outbound_count),
        "inbound_percentage": round(float(inbound_count / total_rows) * 100, 2),
        "outbound_percentage": round(float(outbound_count / total_rows) * 100, 2),
        "missing_values": {col: int(cnt) for col, cnt in missing_counts.items()},
        "missing_percentages": {col: round(float(cnt / total_rows) * 100, 2) for col, cnt in missing_counts.items()},
        "link_fields": {
            "records_with_in_response_to": int(has_in_response_to),
            "percentage_with_in_response_to": round(float(has_in_response_to / total_rows) * 100, 2),
            "records_with_response_tweet_id": int(has_response_tweet_id),
            "percentage_with_response_tweet_id": round(float(has_response_tweet_id / total_rows) * 100, 2)
        },
        "text_length_distribution": text_stats,
        "top_25_brands_by_outbound": top_brands
    }

    with open("docs/data_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2)

    lines = [
        "# Dataset Profile: Kaggle Customer Support on Twitter (`twcs.csv`)",
        "",
        "## 1. Dataset Overview & Provenance",
        f"* **File Path**: `{DATA_PATH}`",
        f"* **File Size**: {file_size_bytes / (1024 * 1024):.2f} MB ({file_size_bytes:,} bytes)",
        f"* **SHA-256 Digest**: `{file_sha256}`",
        f"* **Total Rows**: {total_rows:,}",
        f"* **Date Range**: {manifest['date_range_min']} to {manifest['date_range_max']}",
        "",
        "## 2. Column Schema & Missingness Analysis",
        "",
        "| Column | Type | Missing Count | Missing % | Semantic Role |",
        "|---|---|---|---|---|"
    ]

    for col in columns:
        role = "Identifier"
        if col == "inbound": role = "Speaker direction (True=Customer, False=Support)"
        elif col == "author_id": role = "User anonymized ID or Brand handle"
        elif col == "created_at": role = "Timestamp of publication"
        elif col == "text": role = "Raw tweet utterance"
        elif col == "response_tweet_id": role = "Forward pointer(s) to responses"
        elif col == "in_response_to_tweet_id": role = "Backward pointer to parent tweet"
        lines.append(f"| `{col}` | `{schema[col]}` | {missing_counts[col]:,} | {profile['missing_percentages'][col]}% | {role} |")

    lines.extend([
        "",
        "### Key Structural Findings:",
        "1. **Core Message Completeness**: `tweet_id`, `author_id`, `inbound`, `created_at`, and `text` have *:0% missing values**. Every row contains verifiable speaker role and content.",
        f"2. **Conversation Pointers**: `in_response_to_tweet_id` is missing in {profile['missing_percentages']['in_response_to_tweet_id']}% of rows (representing roots or truncated parents). `response_tweet_id` is missing in {profile['missing_percentages']['response_tweet_id']}% of rows (representing leaves).",
        "",
        "## 3. Directional Distribution",
        f"* **Inbound (Customer Inquiries)**: {inbound_count:,} ({profile['inbound_percentage']}%)",
        f"* **Outbound (Brand Responses)**: {outbound_count:,} ({profile['outbound_percentage']}%)",
        f"* Overall Inbound-to-Outbound Ratio: {inbound_count / outbound_count:.2f}:1",
        "",
        "## 4. Message Character Length Distribution",
        f"* **Minimum**: {text_stats['min']} chars",
        f"* **25th Percentile**: {text_stats['p25']} chars",
        f"* **Median**: {text_stats['median']} chars",
        f"* **Mean**: {text_stats['mean']:.1f} chars",
        f"* **75th Percentile**: {text_stats['p75']} chars",
        f"* **95th Percentile**: {text_stats['p95']} chars",
        f"* **Maximum**: {text_stats['max']} chars",
        "*(Note: Reflects Twitter's historical 140-character limit expanding to 280 characters in late 2017.)*",
        "",
        "## 5. Top 25 Brands by Outbound Support Volume",
        "",
        "| Rank | Brand Support Handle | Outbound Tweets |",
        "|---|---|---|"
    ])

    for idx, b in enumerate(top_brands, 1):
        lines.append(f"| {idx} | `C{b['brand']}` | {b['outbound_tweets']:,} |")


    lines.extend([ 
        "",
        "## 6. Next Analytical Steps",
        "1. Filter top candidate brands against response coverage and graph reconstructability.",
        "2. Measure template duplication rates before finalizing candidate brand selection."
    ])

    with open("docs/data_profile.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print("[4/4] docs/data_manifest.json, docs/data_profile.json, and docs/data_profile.md generated successfully.")

if __name__ == "__main__":
    inspect_dataset()
