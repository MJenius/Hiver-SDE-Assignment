# Data Assumptions & Epistemic Boundaries

This document records the foundational assumptions, limitations, and operational boundaries governing the Twitter Customer Support dataset (	wcs.csv) in this project.

---

## 1. Identity & Directional Semantics
1. **Customer Authorship**: Tweets marked inbound = True represent inquiries authored by external end-users directed toward a company support handle.
2. **Support Authorship**: Tweets marked inbound = False represent messages published by company customer care accounts.
3. **Handle Consistency**: A brand is uniquely identified by its primary support handle (e.g., @AmazonHelp, @AppleSupport, @Uber_Support).

---

## 2. Epistemic Status of Historical Responses: Reference Behavior ≠ Ground Truth
1. **Reference Behavior**: Outbound support tweets are treated as **historical behavioral evidence** of how human agents handled tweets at that point in time.
2. **Not Axiomatic Policy**: Historical tweets do NOT constitute current, infallible, or comprehensive brand policy. Historical agents made mistakes, gave outdated instructions, or suffered from inconsistent phrasing.
3. **Evaluation Standard**: Evaluation cannot be: *Did the AI match the exact historical tweet?* Evaluation must be: *Was the AI response grounded in historical precedents, factually consistent, relevant to the customer intent, and safe under brand policy?*

---

## 3. Response Coverage vs. True Resolution
1. **Response Coverage**: Defined strictly as the proportion of customer turns that elicited an outbound support tweet.
2. **Unobserved Post-DM Resolution**: Twitter support is frequently an intake portal for private channels (Please DM us your order ID). The final business resolution (refund, ticket closure, package redelivery) occurs out-of-band in private DMs or CRM systems.
3. **Resolution Evidence Heuristic**: In Phase 1, any metric relating to resolution is strictly an observable textual heuristic (e.g., presence of self-service links, explicit troubleshooting steps, customer acknowledgment). We explicitly DO NOT claim unverified resolution.

---

## 4. Graph Completeness & Missing Context
1. **API Truncation & Deleted Tweets**: Missing parent tweet IDs (in_response_to_tweet_id referencing IDs not present in 	wcs.csv) represent deleted, private, or rate-limited tweets.
2. **No Hallucinated Ancestry**: The reconstruction pipeline treats missing parents as unobserved boundary nodes; it never hallucinates or synthesizes missing parent turns.

---

## 5. Splitting Unit & Data Leakage
1. **Conversation Independence**: Because multiple turns in a single thread share context, customer IDs, and specific order details, **splitting at the tweet level causes massive data leakage**.
2. **Atomic Unit of Splitting**: The entire **Conversation** (and all associated Cases) is the minimal permissible unit of partitioning between Train, Dev, Golden, and Hard evaluation sets.
