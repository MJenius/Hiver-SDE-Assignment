# Phase 1 Decision Log

This log records the 12 key engineering and methodological decisions made during Phase 1. Each entry documents the rationale, empirical evidence, alternatives considered, and explicit reasons for rejection.

---

### Decision 1: Terminology — "Response Coverage" vs. "Solve Rate"
* **Decision**: Rename outbound presence metrics to **Response Coverage** and treat resolution evidence strictly as a textual heuristic.
* **Why**: An outbound tweet does not establish business resolution; many tweets merely request an account number or direct the user to DM. Claiming a "solve rate" introduces an unverified epistemic assumption.
* **Evidence**: Over 51.5% of Apple outbound tweets direct users to private DMs.
* **Alternative Considered**: Defining solve rate as any conversation with an outbound tweet.
* **Why Rejected**: Methodologically dishonest and easily dismantled in review.

---

### Decision 2: Empirical Selection of `@AppleSupport` over `@AmazonHelp`
* **Decision**: Select `@AppleSupport` despite `@AmazonHelp` having higher raw outbound volume.
* **Why**: AppleSupport features deep technical troubleshooting dialogue, the highest unique customer reach (58,567), and clean English text (87.5%). AmazonHelp has 23.0% multilingual fragmentation (39,019 non-English tweets) and shallow delivery-lookup turns.
* **Evidence**: Quantified in `docs/brand_selection.md` and `docs/candidate_brands_profile.json`.
* **Alternative Considered**: Selecting AmazonHelp or SpotifyCares.
* **Why Rejected**: AmazonHelp introduced linguistic confounding; SpotifyCares had less than half the customer volume.

---

### Decision 3: Rejection of `@Uber_Support` due to Extreme Template Duplication
* **Decision**: Eliminate Uber Support from consideration despite its large volume (56,270 outbound tweets).
* **Why**: Uber exhibited a 49.66% outbound template rate (identical boilerplate canned responses).
* **Evidence**: Empirical template analysis on 5,000 sampled outbound tweets.
* **Alternative Considered**: Deduplicating Uber and using the remainder.
* **Why Rejected**: The underlying support variety is too narrow and would make benchmark retrieval trivially easy.

---

### Decision 4: Explicit 5-Tier Data Model (`docs/data_model.md`)
* **Decision**: Formally distinguish Tweet, Turn, Conversation, Case, and Evaluation Example.
* **Why**: Prevents conflating atomic tweets with retrieval units or evaluation examples.
* **Evidence**: The retrieval and evaluation tasks require paired customer query + preceding context + historical response ("Case").
* **Alternative Considered**: Operating directly on raw tweet rows with joins.
* **Why Rejected**: Leads to fragmented multi-turn context and accidental evaluation leakage.

---

### Decision 5: Epistemic Boundary — Historical Behavior ≠ Ground Truth
* **Decision**: Codify in `docs/data_assumptions.md` that past support tweets represent historical behavior, not infallible policy truth.
* **Why**: Support agents in 2017 made typos, gave temporary workarounds (e.g. iOS 11 text replacement), or used legacy URLs.
* **Evidence**: Inspection of raw 2017 tweets.
* **Alternative Considered**: Treating historical agent tweets as ground-truth target text for BLEU/ROUGE string matching.
* **Why Rejected**: String matching against historical tweets rewards memorizing outdated agent idiosyncrasies rather than sound grounded reasoning.

---

### Decision 6: Atomic Splitting Unit — Whole Conversation DAG
* **Decision**: Restrict all train/dev/test partitioning strictly to the entire Conversation DAG (`conversation_id`).
* **Why**: Splitting by individual tweet causes severe leakage of customer ID, device context, and resolution state.
* **Evidence**: 34.6% of reconstructed conversations have 3 or more turns.
* **Alternative Considered**: Random tweet-level sampling or temporal split by month.
* **Why Rejected**: Tweet-level sampling causes catastrophic leakage; temporal split introduces severe distribution shift due to the release of iOS 11 and iPhone X in late 2017.

---

### Decision 7: Graph-Theoretic Reconstruction Handling Orphans & Self-Loops
* **Decision**: Model thread reconstruction as a directed graph traversal filtering self-loops and treating missing parents as sub-tree roots.
* **Why**: 30,201 turns in the Apple subset reference parent tweet IDs that are deleted or outside the scrape window.
* **Evidence**: Verified by unit test suite and `docs/conversation_graph_analysis.md`.
* **Alternative Considered**: Discarding any thread with missing parent references.
* **Why Rejected**: Would discard over 50% of valid customer interactions.

---

### Decision 8: Human-in-the-Loop Operational Intent Taxonomy (10 Classes)
* **Decision**: Define a 10-class taxonomy (9 operational intents + `unknown`) grounded in data clustering and AppleCare triage workflows.
* **Why**: Off-the-shelf taxonomies (Banking77) do not reflect technical device support. Clustering proposes candidate themes, but humans must establish operational boundaries.
* **Evidence**: MiniBatch K-Means over 10,000 customer queries identified clear clusters for battery, updates, screen/hardware, and billing.
* **Alternative Considered**: Relying on 25 raw unsupervised cluster labels.
* **Why Rejected**: Unsupervised clusters lack clean mutual exclusivity and contain meaningless lexical artifacts (e.g. greeting clusters).

---

### Decision 9: Separation of Intent Classification from Human Escalation
* **Decision**: Model `intent` and `should_escalate` as independent, orthogonal labels in the golden schema.
* **Why**: A query can have a perfectly clear intent (e.g. `app_store_billing_subscriptions`) while still requiring mandatory human escalation due to sensitive financial data.
* **Evidence**: Real AppleCare cases requiring credit card dispute escalation.
* **Alternative Considered**: Defining escalation as a sub-intent or simply triggering escalation on low intent confidence.
* **Why Rejected**: Conflates problem classification with action risk policy.

---

### Decision 10: Mandatory "Evidence Sufficiency" Field
* **Decision**: Add `evidence_sufficient` (`yes` / `no` / `uncertain`) to all golden evaluation examples.
* **Why**: Distinguishes between what a customer is asking and whether the system has adequate historical evidence to formulate a grounded response.
* **Evidence**: Ultra-short queries (*"iPhone broken"*) have clear domain context but zero actionable evidence.
* **Alternative Considered**: Relying solely on character length as a proxy for sufficiency.
* **Why Rejected**: Long angry rants can still lack actionable diagnostic evidence.

---

### Decision 11: Dedicated Hard / Stress Evaluation Set
* **Decision**: Programmatically sample 100 naturally occurring hard cases (`eval/hard/candidates/`) covering multi-intent, ultra-short, and context-dependent cases.
* **Why**: AI agents often perform well on clean benchmark sets but degrade catastrophically on ambiguous real-world inputs. The term "Hard / Stress Set" accurately reflects naturally occurring difficult cases, avoiding the misnomer "adversarial" which implies synthetic perturbation attacks.
* **Evidence**: Reconstructed dataset contains 5,118 branching threads and thousands of ultra-short queries.
* **Alternative Considered**: Calling them an "adversarial" set, or relying exclusively on standard golden set evaluation.
* **Why Rejected**: Calling natural data "adversarial" is terminologically inaccurate; omitting a hard evaluation slice hides real failure modes behind aggregate headline numbers.

---

### Decision 12: Reproducibility via Dataset Manifest & Hash Locking
* **Decision**: Generate `docs/data_manifest.json` capturing file size, SHA-256 digest (`cd297fcfa1bf6f99938be242e8e578980bc6d1b96adc8691abec9a39175b03c0`), Python environment, and fixed seeds (`42`).
* **Why**: Ensures that any reviewer can verify that experiments run against the exact same data bytes and logic.
* **Evidence**: Manifest generated and verified by `scripts/inspect_data.py`.
* **Alternative Considered**: Plain text notes in README.
* **Why Rejected**: Non-machine-readable and unverified.

---

### Decision 13: Separate Query Representation for Intent vs. Context for Grounding
* **Decision**: Use single-turn customer query text (C1) for intent classification, while reserving preceding dialogue context (C2) for historical case retrieval and grounded response generation.
* **Why**: Controlled context ablation demonstrated that concatenating preceding turns degraded classifier Macro-F1 from 0.8800 down to 0.6975 (C2) and 0.6654 (C3) due to greeting/filler token dilution.
* **Evidence**: Empirical ablation on 3,000 validation cases documented in `docs/context_experiment.md`.
* **Alternative Considered**: Feeding full multi-turn linear dialogue into the intent classifier.
* **Why Rejected**: Introduced severe noise and degraded discriminative intent classification.

---

### Decision 14: Multi-Stage Hybrid Retrieval with Reciprocal Rank Fusion (RRF)
* **Decision**: Implement hybrid retrieval combining BM25 lexical search with sublinear TF-IDF dense embeddings via RRF ($k=60$), followed by cross-encoder re-ranking.
* **Why**: Pure lexical search suffers on vocabulary mismatch (e.g. "battery drain" vs. "discharging fast"), while dense search alone misses exact model/error terms ("iOS 11.0.3"). Hybrid RRF achieves strong Recall@5 (0.360) and MRR (0.2694) without external API dependencies.
* **Evidence**: Documented across experiments R1–R4 in `docs/retrieval_experiments.md`.
* **Alternative Considered**: Dense-only semantic retrieval via third-party embedding APIs.
* **Why Rejected**: API latency, quota volatility, and poor exact-match precision on technical version identifiers.

---

### Decision 15: Conservative Operating Point Selection ($\tau = 0.55$)
* **Decision**: Set the operational intent confidence threshold at $\tau = 0.55$, accepting 27.9% auto-handle coverage in order to secure 99.12% escalation recall.
* **Why**: In safety-critical support, false auto-handling on security, billing, or physical hardware issues presents acute operational risk. Operating at $\tau = 0.55$ ensures high recall on sensitive inquiries while safely automating common troubleshooting.
* **Evidence**: Quantitative sweep across 6 threshold points ($N=1,500$) in `eval/results/escalation/threshold_sweep.csv`.
* **Alternative Considered**: Lowering the threshold to $\tau = 0.40$ to increase nominal coverage to 30.2%.
* **Why Rejected**: Increased false auto-handling risk on borderline ambiguous inquiries.
