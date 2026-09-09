# Annotation Protocol & Simulation / Calibration Study

## 1. Provenance & Implementation Disclosure

To maintain strict epistemic integrity, this document explicitly delineates between what is **currently implemented in code/artifacts** versus the **proposed human-annotation protocol** designed for future human-in-the-loop scaling.

### 1.1 Implemented Evidence (Current Repository State)
* **Quarantined Benchmark Targets**: Exactly 200 evaluation targets in `eval/golden/final/golden_test.jsonl` sampled from the held-out `test` partition (`split == "test"`).
* **Programmatic Policy Adjudication**: Targets (`intent`, `should_escalate`, `evidence_sufficient`) were programmatically derived from candidate intent heuristics and domain risk policy rules over customer inquiries, rather than produced by biological human annotators.
* **Benchmark Purpose**: Measures internal consistency, conservative escalation recall, and retrieval grounding under fixed operational assumptions.

### 1.2 Proposed Human-Annotation Protocol (Production Roadmap)
* **Dual-Annotator Coverage**: Stratified 50-case overlap with independent blind labeling.
* **Agreement Scoring**: Formalized Cohen’s Kappa ($\kappa \ge 0.80$) thresholding to validate inter-rater reliability.
* **Consensus Adjudication**: Two-tier adjudication resolving taxonomy boundary disputes before deploying models.

---

## 2. Operational Rubric Specification

The benchmark targets are structured around the following operational boundaries:

### 2.1 Intent Taxonomy Decision Boundaries
Inquiries map to the primary underlying issue according to `configs/intents.yaml`:
1. `os_update_issues`: OS installation failures, verification hangs, post-update glitches (e.g. keyboard autocorrect bugs, UI overlap).
2. `battery_performance`: Unusually rapid drainage, device overheating, sudden shutdowns at percentage > 10%, slow charging.
3. `apple_id_account_security`: Forgotten credentials, account locked, 2FA codes not received, Activation Lock on secondhand devices, phishing verification.
4. `app_store_billing_subscriptions`: In-app purchase disputes, refund requests, unverified card charges, subscription renewals/cancellations.
5. `hardware_screen_physical`: Cracked displays, touch screen unresponsiveness, water immersion, battery swelling/bulging, camera hardware distortion.
6. `connectivity_wifi_bluetooth`: Wi-Fi disconnects, Bluetooth audio stuttering, AirPods latency/pairing failures, cellular data/LTE drops.
7. `icloud_sync_storage`: iCloud storage full alerts, photo stream sync drops, corrupted backup restoration, contacts/calendar sync across devices.
8. `audio_music_media`: Apple Music catalog availability, playlist playback stops, podcast download issues, system sound volume balance.
9. `store_orders_shipping`: Apple Online Store order status, shipping carrier delivery delays, trade-in kit delivery, physical retail Genius Bar appointments.
10. `unknown`: Greetings ("hey"), unstructured complaints ("apple sucks"), ambient noise, multi-sentence fragments, non-English text without technical specifics.

### 2.2 Escalation Criteria (`should_escalate`)
Defines escalation necessity based on whether the issue requires human operational intervention, decoupled from classifier prediction confidence:
* `True`: Inquiries requiring private authenticated verification (Apple ID reset, password recovery, activation lock), credit card/financial lookup, physical hardware diagnostics/mail-in repair, or complex legal/safety escalations.
* `False`: Standard self-service troubleshooting where public technical steps (reboot, toggle settings, reset network settings, delete/reinstall app) are standard procedure.

### 2.3 Evidence Sufficiency (`evidence_sufficient`)
* `yes`: The inquiry contains enough device/symptom context for historical precedent to formulate a concrete diagnostic reply.
* `no`: The inquiry provides zero diagnostic information (e.g. "it doesn't work", "help", single-word turns).
* `uncertain`: Partial information where diagnostic questions are necessary before resolution.

---

## 3. Protocol Calibration & Target Agreement Benchmarks

To guide real annotator onboarding in production, we established target consistency thresholds across categorical dimensions:

| Annotation Dimension | Target Raw Agreement (%) | Target Cohen's Kappa ($\kappa$) | Target Agreement Class | Anticipated Boundary Driver |
|---|---|---|---|---|
| **Operational Intent** | **$\ge$ 90.0%** | **$\kappa \ge 0.80$** | Substantial / Near-Perfect | Multi-intent compound inquiries (e.g., iOS 11 update causing battery drain). Prioritize direct functional breakdown. |
| **Escalation (`should_escalate`)** | **$\ge$ 88.0%** | **$\kappa \ge 0.75$** | Substantial Agreement | Borderline hardware vs. software screen freeze (e.g., touch unresponsive after drop vs update). |
| **Evidence Sufficiency** | **$\ge$ 85.0%** | **$\kappa \ge 0.70$** | Substantial Agreement | Differing thresholds on whether asking for iOS version constitutes sufficient evidence. |

### 3.1 Simulated Adjudication Walkthrough (Reference Cases)
To illustrate how the protocol resolves ambiguous cases:
1. **Compound Inquiry (e.g., Case `eval_gold_020`)**: User complains that an iOS update caused Bluetooth audio to drop.
   * *Option A*: `connectivity_wifi_bluetooth` (focal functional symptom).
   * *Option B*: `os_update_issues` (antecedent trigger).
   * *Adjudication Rule*: Prioritize the direct functional breakdown (`connectivity_wifi_bluetooth`) because initial troubleshooting requires Bluetooth resetting rather than OS reinstallation.
2. **Screen Unresponsiveness (e.g., Case `eval_gold_089`)**: User reports a screen that won't wake up after an update.
   * *Option A*: Escalated (`hardware_screen_physical`).
   * *Option B*: Not escalated (`os_update_issues`), suggesting DFU restore.
   * *Adjudication Rule*: Adjudicate as `should_escalate=True` because physical unresponsiveness risks underlying hardware failure and customer churn if self-service software restore fails.

All 50 reference calibration examples are recorded in `eval/golden/annotations/simulated_annotation_examples_50.jsonl` as reference calibration data.
