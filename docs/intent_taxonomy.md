# Operational Intent Taxonomy: `@AppleSupport`

## 1. Grounding & Discovery Methodology
The intent taxonomy was derived through a combination of empirical unsupervised discovery and human domain synthesis:
1. **Unsupervised Exploratory Clustering**: Evaluated 10,000 initiating customer messages using MiniBatch K-Means over TF-IDF n-grams (1-2 words). Discovered organic semantic clusters centered on iOS updates, battery drainage, account/passwords, App Store billing, iCloud sync, hardware/screens, connectivity, and media.
2. **Operational Boundaries**: Rather than adopting an artificial off-the-shelf taxonomy (e.g. Banking77), the taxonomy reflects actual operational triage units handled by AppleCare frontline advisors.
3. **Number of Intents**: 9 well-defined operational categories plus 1 formal fallback category (`unknown`), striking the optimal balance between granularity and mutual exclusivity.

---

## 2. Intent Taxonomy Specification

### Summary Table

| Intent ID | Intent Name | Common Symptoms & Key Entities | Precedence |
|---|---|---|---|
| `os_update_issues` | OS Update Issues & Glitches | iOS 11 update bugs, stuck on Apple logo, keyboard "I" glitch, verification errors | 1 |
| `battery_performance` | Battery & Power Drainage | Rapid percentage drop, unexpected shutdown, overheating, charging failure | 2 |
| `apple_id_account_security` | Apple ID & Account Security | Locked account, 2FA code missing, password recovery, Activation Lock | 1 |
| `app_store_billing_subscriptions` | App Store, Purchases & Billing | Unexpected charges, refund requests, subscription cancellation, card declined | 2 |
| `hardware_screen_physical` | Hardware, Screen & Physical Damage | Cracked display, touch unresponsiveness, camera failure, water damage | 2 |
| `connectivity_wifi_bluetooth` | Connectivity, Wi-Fi & Bluetooth | Wi-Fi greyed out, AirPods dropping, cellular data lost, Bluetooth pairing | 3 |
| `icloud_sync_storage` | iCloud, Backup & Data Sync | Photos not syncing, backup failing, storage quota full, restore failure | 3 |
| `audio_music_media` | Apple Music, Podcasts & Audio | Playlist missing, Apple Music crashing, podcast download, playback pause | 3 |
| `store_orders_shipping` | Apple Store Orders & Delivery | Pre-order delivery tracking, trade-in kit, Genius Bar appointment | 2 |
| `unknown` | Unknown / Out-of-Distribution / Vague | Unintelligible text, pure rant without actionable bug, zero-context greetings | 99 |

---

## 3. Precedence Rules for Multi-Intent & Overlapping Cases
When a customer message touches upon multiple issues simultaneously, annotators and models must apply deterministic precedence rules:
1. **Security & Identity Takes Top Precedence**: If an Apple ID lockout or compromised account is mentioned alongside a sync or app issue, classify as `apple_id_account_security`.
2. **Update Context vs. Root Symptom**:
   * If a symptom is explicitly introduced by an OS update within the message (e.g. *"iOS 11 broke my Bluetooth"*), classify as `os_update_issues` if the query focuses on the update bug, or `connectivity_wifi_bluetooth` if asking for Bluetooth troubleshooting steps.
   * If battery drains specifically after an update (e.g., *"updated to 11.1 and now battery dies in 1 hr"*), classify as `battery_performance` because the actionable remediation is battery diagnostic triage.
3. **Billing over App Crash**: If a customer complains that an app crashed AND demands a refund, classify as `app_store_billing_subscriptions`.
4. **Fallback to `unknown`**: Only assign `unknown` if the message cannot be grounded in any technical category even with generous interpretation.
