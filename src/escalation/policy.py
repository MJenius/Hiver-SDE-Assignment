"""
src/escalation/policy.py
Deterministic, transparent policy layer governing human escalation vs auto-handling.
Decides whether an inquiry can be safely resolved by an automated agent or requires human handoff,
with structured reason codes and actionable explanations.
"""

from typing import Dict, Any, Optional, List

# Controlled vocabulary for escalation reasons
REASON_UNKNOWN_INTENT = "unknown_intent"
REASON_LOW_INTENT_CONFIDENCE = "low_intent_confidence"
REASON_INSUFFICIENT_EVIDENCE = "insufficient_historical_evidence"
REASON_HARDWARE_REPAIR = "hardware_repair_or_service"
REASON_SECURITY_OR_ACCOUNT = "security_or_account_compromise"
REASON_BILLING_DISPUTE = "financial_or_billing_dispute"
REASON_HIGH_RISK_CLAIM = "unsupported_or_high_risk_claim"

class EscalationPolicy:
    def __init__(
        self,
        intent_confidence_threshold: float = 0.55,
        retrieval_score_threshold: float = 0.05,
        auto_escalate_intents: Optional[List[str]] = None
    ):
        self.intent_confidence_threshold = intent_confidence_threshold
        self.retrieval_score_threshold = retrieval_score_threshold
        # High-risk categories requiring human advisory by default
        self.auto_escalate_intents = auto_escalate_intents or [
            "apple_id_account_security",
            "app_store_billing_subscriptions"
        ]

    def evaluate(
        self,
        intent: str,
        intent_confidence: float,
        retrieved_cases: List[Any],
        evidence_grounded: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluates signals and outputs structured escalation decision.
        Returns:
          {
            "decision": "auto_handle" | "escalate",
            "should_escalate": bool,
            "escalation_reason": str | None,
            "explanation": str
          }
        """
        # Rule 1: Unknown intent fallback
        if intent == "unknown":
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_UNKNOWN_INTENT,
                "explanation": "Inquiry could not be mapped to supported technical taxonomy with sufficient certainty."
            }

        # Rule 2: Low intent confidence
        if intent_confidence < self.intent_confidence_threshold:
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_LOW_INTENT_CONFIDENCE,
                "explanation": f"Intent confidence ({intent_confidence:.2f}) is below safe operational threshold ({self.intent_confidence_threshold:.2f})."
            }

        # Rule 3: Mandatory policy escalation for high-risk categories
        if intent == "apple_id_account_security":
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_SECURITY_OR_ACCOUNT,
                "explanation": "Account lockouts, 2FA credentials, and security keys require authenticated human verification."
            }
        elif intent == "app_store_billing_subscriptions":
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_BILLING_DISPUTE,
                "explanation": "Credit card transactions, charge reversals, and refunds require financial account access."
            }

        # Rule 4: Hardware damage detection
        if intent == "hardware_screen_physical":
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_HARDWARE_REPAIR,
                "explanation": "Physical display damage, camera hardware failure, or liquid ingress require AppleCare physical service."
            }

        # Rule 5: Insufficient retrieval evidence
        if not retrieved_cases or retrieved_cases[0].score < self.retrieval_score_threshold:
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_INSUFFICIENT_EVIDENCE,
                "explanation": "No relevant historical precedents found in knowledge base with sufficient similarity."
            }

        # Rule 6: Response evidence check failure (unsupported claim)
        if not evidence_grounded:
            return {
                "decision": "escalate",
                "should_escalate": True,
                "escalation_reason": REASON_HIGH_RISK_CLAIM,
                "explanation": "Generated draft contains claims not verified by retrieved evidence."
            }

        # Default: Safe for automated resolution
        return {
            "decision": "auto_handle",
            "should_escalate": False,
            "escalation_reason": None,
            "explanation": "Standard self-service technical query with high classification confidence and strong retrieval evidence."
        }
