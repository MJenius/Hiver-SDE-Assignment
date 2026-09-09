# Dataset Profile: Kaggle Customer Support on Twitter (`twcs.csv`)

## 1. Dataset Overview & Provenance
* **File Path**: `data\twcs\twcs.csv`
* **File Size**: 492.58 MB (516,508,641 bytes)
* **SHA-256 Digest**: `cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0`
* **Total Rows**: 2,811,774
* **Date Range**: 2008-05-08 20:MM:59 to 2017-12-03 23:14:01

## 2. Column Schema & Missingness Analysis

| Column | Type | Missing Count | Missing % | Semantic Role |
|---|---|---|---|---|
| `tweet_id` | `int64` | 0 | 0.0% | Identifier |
| `author_id` | `str` | 0 | 0.0% | User anonymized ID or Brand handle |
| `inbound` | `bool` | 0 | 0.0% | Speaker direction (True=Customer, False=Support) |
| `created_at` | `str` | 0 | 0.0% | Timestamp of publication |
| `text` | `str` | 0 | 0.0% | Raw tweet utterance |
| `response_tweet_id` | `float64` | 1,040,629 | 37.01% | Forward pointer(s) to responses |
| `in_response_to_tweet_id` | `int64` | 794,335 | 28.25% | Backward pointer to parent tweet |

### Key Structural Findings:
1. **Core Message Completeness**: `tweet_id`, `author_id`, `inbound`, `created_at`, and `text` have *:0% missing values**. Every row contains verifiable speaker role and content.
2. **Conversation Pointers**: `in_response_to_tweet_id` is missing in 28.25% of rows (representing roots or truncated parents). `response_tweet_id` is missing in 37.01% of rows (representing leaves).

## 3. Directional Distribution
* **Inbound (Customer Inquiries)**: 1,537,843 (54.69%)
* **Outbound (Brand Responses)**: 1,273,931 (45.31%)
* Overall Inbound-to-Outbound Ratio: 1.21:1

## 4. Message Character Length Distribution
* **Minimum**: 1 chars
* **25th Percentile**: 78.0 chars
* **Median**: 115.0 chars
* **Mean**: 113.9 chars
* **75th Percentile**: 139.0 chars
* **95th Percentile**: 216.0 chars
* **Maximum**: 452 chars
*(Note: Reflects Twitter's historical 140-character limit expanding to 280 characters in late 2017.)*

## 5. Top 25 Brands by Outbound Support Volume

| Rank | Brand Support Handle | Outbound Tweets |
|---|---|---|
| 1 | `CAmazonHelp` | 169,840 |
| 2 | `CAppleSupport` | 106,860 |
| 3 | `CUber_Support` | 56,270 |
| 4 | `CSpotifyCares` | 43,265 |
| 5 | `CDelta` | 42,253 |
| 6 | `CTesco` | 38,573 |
| 7 | `CAmericanAir` | 36,764 |
| 8 | `CTMobileHelp` | 34,317 |
| 9 | `Ccomcastcares` | 33,031 |
| 10 | `CBritish_Airways` | 29,361 |
| 11 | `CSouthwestAir` | 28,977 |
| 12 | `CVirginTrains` | 27,817 |
| 13 | `CAsk_Spectrum` | 25,860 |
| 14 | `CXboxSupport` | 24,557 |
| 15 | `Csprintcare` | 22,381 |
| 16 | `Chulu_support` | 21,872 |
| 17 | `Csainsburys` | 19,466 |
| 18 | `CGWRHelp` | 19,364 |
| 19 | `CAskPlayStation` | 19,098 |
| 20 | `CChipotleTweets` | 18,749 |
| 21 | `CVerizonSupport` | 17,966 |
| 22 | `CUPSHelp` | 17,817 |
| 23 | `CATVIAssist` | 17,650 |
| 24 | `CO2` | 16,212 |
| 25 | `CSafaricom_Care` | 16,077 |

## 6. Next Analytical Steps
1. Filter top candidate brands against response coverage and graph reconstructability.
2. Measure template duplication rates before finalizing candidate brand selection.