# Ambiguity & Hard-Case Analysis: `@AppleSupport`

## 1. Overview & Purpose
In real-world customer support, a substantial proportion of incoming messages do not present clean, unambiguous technical specifications. Evaluating an AI agent solely on sanitized, easy examples produces misleadingly optimistic performance metrics.
This document formalizes the **Taxonomy of Ambiguity** grounded directly in AppleSupport Twitter interactions, defining the criteria for the Hard Evaluation Set (`eval/hard/candidates/`).

---

## 2. Taxonomy of Ambiguity Types

### 2.1 Multi-Intent Overlap
* **Definition**: A single customer turn describing two or more distinct technical failures.
* **Real Dataset Example**:
  > *"My battery dies in 2 hours and my screen is also unresponsive to touch at the top."*
  > (Symptom overlap: `battery_performance` + `hardware_screen_physical`)
* **Challenge for Agent**: Classification must select the primary actionable triage path or recognize multi-intent; retrieval must retrieve diagnostic guidance without conflicting advice.

### 2.2 Low-Information & Ultra-Short Messages
* **Definition**: Messages with fewer than 8 words or missing essential diagnostic details (device model, iOS version, error code).
* **Real Dataset Example**:
  > *"It doesn't work."* or *"Need help with my iPhone ASAP."*
* **Challenge for Agent**: The agent cannot solve or give concrete steps; it must formulate a clarifying diagnostic probe rather than hallucinating an answer, and recognize that evidence is insufficient (`evidence_sufficient = "no"`).

### 2.3 Context-Dependent Inquiries
* **Definition**: Turns that are completely unintelligible without reading the preceding turns in the conversation thread.
* **Real Dataset Example**:
  > *"Tried that, still not working. What else?"*
* **Challenge for Agent**: Zero-shot single-tweet models fail completely; requires multi-turn dialogue state awareness.

### 2.4 Typo-Heavy & Informal Slang
* **Definition**: Messages containing distorted phonetic spelling, emojis, lack of punctuation, or colloquial slang.
* **Real Dataset Example**:
  > *"bruhhh y my fon keep freezn up on da lockscreen afte dat update smh fix dis"*
* **Challenge for Agent**: TF-IDF and keyword matching fail; requires robust semantic embedding representations.

### 2.5 Conflicting or Inconsistent Historical Resolution
* **Definition**: Cases where historical support agents provided contradictory responses or where past instructions are now deprecated.
* **Real Dataset Example**:
  > In some threads, agents ask users to reset all network settings; in others for the same symptom, they immediately route to private DM due to known iOS 11 bugs.
* **Challenge for Agent**: Requires resolution consensus and confidence gating before deciding to auto-handle.

---

## 3. Ambiguity vs. Escalation Boundary
Ambiguity does not automatically necessitate human escalation:
* **Ambiguous, but Auto-Handlable**: An ultra-short query (*"iPhone won't turn on"*) can be auto-handled with a standard diagnostic clarification question (*"What model of iPhone do you have, and does it respond when connected to a charger?"*).
* **Ambiguous, and Must Escalate**: A customer in acute distress (*"I think someone hacked my bank through my phone, lock everything right now!"*) requires immediate, zero-latency human escalation regardless of ambiguity.
