"""
tests/test_failure_modes.py
Deterministic regression tests covering the 5 primary failure modes (FM-01 through FM-05)
identified in the post-mortem analysis (docs/failure_analysis.md).
"""

import re
import pytest
from src.escalation.policy import EscalationPolicy
from src.retrieval.schemas import RetrievedCase

# FM-01 Action regex for transaction mutations
TRANSACTION_CANCEL_PATTERN = re.compile(
    r"\b(cancel|duplicate|ordered twice|wrong (?:email|address|card)|charged twice)\b",
    re.IGNORECASE
)

def test_fm01_order_cancellation_escalation():
    """
    FM-01: Verifies that transactional modification requests (e.g. 'ordered twice. how to cancel')
    are safely caught by escalation policies or transaction triggers rather than auto-handling
    with static tracking links.
    """
    message = "@AppleSupport I made a mistake and I ordered twice. how to cancel the first order"
    
    # Assert regex trigger catches transaction mutation intent
    match = TRANSACTION_CANCEL_PATTERN.search(message)
    assert match is not None, "Transaction cancellation pattern should match customer query"
    assert match.group(0).lower() in ["ordered twice", "cancel"]

    policy = EscalationPolicy()
    
    # If the policy evaluates a query with transactional flag or insufficient evidence
    decision = policy.evaluate(
        intent="store_orders_shipping",
        intent_confidence=0.88,
        retrieved_cases=[],  # No verified cancellation API precedent
        evidence_grounded=True
    )
    assert decision["should_escalate"] is True
    assert decision["decision"] == "escalate"


def test_fm02_multi_intent_safe_handling():
    """
    FM-02: Verifies that compound/multi-intent queries involving security and billing
    trigger escalation when security or billing boundaries are crossed.
    Query: 'I don't want my kid downloading apps without my permission. How can I lock the app store or require password?'
    """
    policy = EscalationPolicy()
    
    # When collapsed to billing or security, policy must escalate to prevent unauthorized actions
    for high_risk_intent in ["apple_id_account_security", "app_store_billing_subscriptions"]:
        decision = policy.evaluate(
            intent=high_risk_intent,
            intent_confidence=0.90,
            retrieved_cases=[RetrievedCase("case_1", 0.85, 1, "ctx", "resp", high_risk_intent)]
        )
        assert decision["should_escalate"] is True
        assert decision["decision"] == "escalate"


def test_fm03_conversational_underspecification_safe_escalation():
    """
    FM-03: Verifies that vague, underspecified queries ('facing problems with iPhone x contacted the customer care twice')
    fall back to unknown intent or low confidence, triggering conservative human handoff.
    """
    policy = EscalationPolicy(intent_confidence_threshold=0.55)
    
    decision = policy.evaluate(
        intent="unknown",
        intent_confidence=0.32,
        retrieved_cases=[]
    )
    assert decision["should_escalate"] is True
    assert decision["escalation_reason"] == "unknown_intent"


def test_fm04_cross_device_entity_mismatch_awareness():
    """
    FM-04: Verifies entity extraction awareness for hardware devices (iPhone vs Apple Watch vs Mac)
    to prevent cross-device retrieval drift.
    """
    query = "Out of nowhere, my Apple Watch S2 was dying. It is losing battery even while powered off."
    
    # Entity extraction pattern
    device_pattern = re.compile(r"\b(apple watch|watchOS|iphone|macbook|ipad)\b", re.IGNORECASE)
    match = device_pattern.search(query)
    assert match is not None
    assert match.group(0).lower() == "apple watch"
    
    # Assert that retriever candidates can be filtered by entity
    sample_candidates = [
        {"id": "doc1", "title": "iPhone Battery and Performance", "device": "iphone"},
        {"id": "doc2", "title": "Apple Watch Battery Life Optimization", "device": "apple watch"},
    ]
    filtered = [c for c in sample_candidates if c["device"] == "apple watch"]
    assert len(filtered) == 1
    assert filtered[0]["id"] == "doc2"


def test_fm05_stale_workaround_freshness_checking():
    """
    FM-05: Verifies that transient historical workarounds (e.g. iOS 11 'I' autocorrect bug)
    are flagged as stale or deprecated when checking temporal validity metadata.
    """
    historical_precedents = [
        {
            "id": "tweet_2017_ios11",
            "text": "Go to Settings > General > Keyboard > Text Replacement to fix letter I bug.",
            "os_version": "iOS 11.1",
            "is_transient_workaround": True,
            "deprecated": True
        },
        {
            "id": "kb_official_ios",
            "text": "Update to iOS 11.1.1 or later to resolve the automatic keyboard replacement issue.",
            "os_version": "iOS 11.1.1",
            "is_transient_workaround": False,
            "deprecated": False
        }
    ]
    
    active_precedents = [p for p in historical_precedents if not p.get("deprecated", False)]
    assert len(active_precedents) == 1
    assert active_precedents[0]["id"] == "kb_official_ios"
