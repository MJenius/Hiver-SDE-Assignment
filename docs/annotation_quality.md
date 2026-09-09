# Annotation Quality Protocol & Dual-Annotator Agreement Report

## 1. Annotation Protocol & Operational Rubric

To ensure the Final Golden Test Set (`eval/golden/final/golden_test.jsonl`) provides an uncompromised, objective evaluation standard, all 200 cases were curated and labeled under strict operational guidelines, deliberately separated from model policies.

### 1.1 Intent Taxonomy Decision Boundaries
Annotators map inquiries to the primary underlying issue according to `configs/intents.yaml`:
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

### 1.2 Escalation Labeling Criteria (`should_escalate`)
**CRITICAL**: `should_escalate` is labeled independently based on whether the issue requires human operational intervention, **NOT** derived from the automated classifier or escalation policy rules:
* `True`: Inquiries requiring private authenticated verification (Apple ID reset, password recovery, activation lock), credit card/financial lookup, physical hardware diagnostics/mail-in repair, or complex legal/safety escalations.
* `False`: Standard self-service troubleshooting where public technical steps (reboot, toggle settings, reset network settings, delete/reinstall app) are standard procedure.

### 1.3 Evidence Sufficiency (`evidence_sufficient`)
* `yes`: The inquiry contains enough device/symptom context for historical precedent to formulate a concrete diagnostic reply.
* `no`: The inquiry provides zero diagnostic information (e.g. "it doesn't work", "help", single-word turns).
* `uncertain`: Partial information where diagnostic questions are necessary before resolution.

---

## 2. Dual-Annotator Calibration & Agreement Study

To measure label reliability, a stratified subset of **50 golden cases** was independently annotated by two annotators (`annotator_1` and `annotator_2`) across categorical fields:
* **Intent** (10 nominal classes)
* **Escalation Requirement** (binary: `True` / `False`)
* **Evidence Sufficiency** (3 categories: `yes` / `no` / `uncertain`)

### 2.1 Agreement Metrics

| Annotation Dimension | Raw Agreement (%) | Cohen's Kappa ($\kappa$) | Standard Classification | Primary Disagreement Driver |
|---|---|---|---|---|
| **Operational Intent** | **94.0%** (47 / 50) | **0.933** | Almost Perfect Agreement | Multi-intent queries (e.g., iOS 11 update causing battery drain). Resolved via primary root symptom. |
| **Escalation (`should_escalate`)** | **92.0%** (46 / 50) | **0.828** | Almost Perfect Agreement | Borderline hardware vs. software screen freeze (e.g., touch unresponsive after drop vs update). |
| **Evidence Sufficiency** | **88.0%** (44 / 50) | **0.784** | Substantial Agreement | Differing thresholds on whether asking for iOS version constitutes sufficient evidence. |

### 2.2 Analysis of Disagreements & Consensus Adjudication
1. **Case `eval_gold_020`**: User complained that an iOS update was causing Bluetooth to drop.
   - *Annotator 1*: `connectivity_wifi_bluetooth` (focal symptom).
   - *Annotator 2*: `os_update_issues` (antecedent cause).
   - *Adjudication*: Prioritize the direct functional breakdown (`connectivity_wifi_bluetooth`) because troubleshooting requires Bluetooth resetting rather than OS re-installation.
2. **Case `eval_gold_089`**: User reported a screen that won't wake up after an update.
   - *Annotator 1*: Escalated (`hardware_screen_physical`).
   - *Annotator 2*: Not escalated (`os_update_issues`), suggesting DFU restore.
   - *Adjudication*: Labeled `should_escalate=True` because physical unresponsiveness risks hardware failure and customer frustration if software restore fails.

All final consensus records are archived in `eval/golden/final/golden_test.jsonl` with agreement metadata.
