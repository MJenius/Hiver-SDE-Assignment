"""
src/agent.py
The Complete Phase 2 AppleSupport Customer Support Agent Pipeline.
Coordinates:
1. Discriminative Intent Classification (IntentClassifier)
2. Bounded Context Retrieval (Hybrid BM25 + Dense + Reranking)
3. Transparent Escalation Policy (EscalationPolicy)
4. Grounded Response Generation via Gemini (GroundedResponseGenerator)
5. Post-Generation Evidence Verification (EvidenceChecker)
"""

import os
import sys
import pickle
from typing import Dict, Any, Optional, List

from src.intent_classifier import IntentClassifier
from src.retrieval.hybrid import HybridRetriever
from src.retrieval.reranker import SimpleReranker
from src.escalation.policy import EscalationPolicy
from src.generation.generator import GroundedResponseGenerator
from src.generation.evidence_checker import EvidenceChecker

class AppleSupportAgent:
    def __init__(
        self,
        classifier: Optional[IntentClassifier] = None,
        retriever: Optional[HybridRetriever] = None,
        escalation_policy: Optional[EscalationPolicy] = None,
        generator: Optional[GroundedResponseGenerator] = None,
        checker: Optional[EvidenceChecker] = None,
        retriever_path: str = "data/retrieval_index.pkl",
        classifier_path: str = "data/intent_classifier.pkl"
    ):
        if classifier is not None:
            self.classifier = classifier
        elif os.path.exists(classifier_path):
            self.classifier = IntentClassifier.load(classifier_path)
        else:
            self.classifier = IntentClassifier()

        if retriever is not None:
            self.retriever = retriever
        elif os.path.exists(retriever_path):
            with open(retriever_path, "rb") as f:
                self.retriever = pickle.load(f)
        else:
            self.retriever = HybridRetriever()

        self.reranker = SimpleReranker()
        self.escalation_policy = escalation_policy or EscalationPolicy(intent_confidence_threshold=0.55)
        self.generator = generator or GroundedResponseGenerator()
        self.checker = checker or EvidenceChecker()

    def handle(self, message: str, context: str = "") -> Dict[str, Any]:
        """
        End-to-end processing of a customer inquiry.
        """
        # Step 1: Intent Classification (using raw query for maximum discriminative power)
        intent_res = self.classifier.predict(message)
        predicted_intent = intent_res["intent"]
        intent_conf = intent_res["confidence"]

        # Step 2: Retrieval (using query + bounded context)
        raw_candidates = self.retriever.retrieve(message, context=context, k=10)
        retrieved_cases = self.reranker.rerank(message, context, raw_candidates, top_k=3)

        retrieval_payload = [
            {
                "case_id": c.case_id,
                "score": c.score,
                "rank": c.rank,
                "customer_message": c.customer_message,
                "historical_response": c.historical_response,
                "intent": c.intent
            }
            for c in retrieved_cases
        ]

        # Step 3: Preliminary Policy Evaluation
        esc_decision = self.escalation_policy.evaluate(
            intent=predicted_intent,
            intent_confidence=intent_conf,
            retrieved_cases=retrieved_cases,
            evidence_grounded=True
        )

        # If preliminary escalation triggered, abort draft generation
        if esc_decision["should_escalate"]:
            return {
                "decision": "escalate",
                "intent": predicted_intent,
                "intent_confidence": intent_conf,
                "escalation_reason": esc_decision["escalation_reason"],
                "escalation_explanation": esc_decision["explanation"],
                "retrieval": retrieval_payload,
                "reply": None,
                "claims": [],
                "evidence_check": None
            }

        # Step 4: Grounded Response Generation
        gen_result = self.generator.generate_reply(
            customer_message=message,
            context=context,
            intent=predicted_intent,
            retrieved_cases=retrieval_payload
        )
        draft_reply = gen_result.get("reply", "")

        # Step 5: Independent Post-Generation Evidence Verification
        audit = self.checker.check_groundedness(
            draft_reply=draft_reply,
            customer_message=message,
            retrieved_cases=retrieval_payload
        )

        # If evidence checker flags unsupported or high-risk claims, trigger safety escalation
        if not audit.get("grounded", True) or audit.get("risk_level") == "high":
            esc_override = self.escalation_policy.evaluate(
                intent=predicted_intent,
                intent_confidence=intent_conf,
                retrieved_cases=retrieved_cases,
                evidence_grounded=False
            )
            return {
                "decision": "escalate",
                "intent": predicted_intent,
                "intent_confidence": intent_conf,
                "escalation_reason": esc_override["escalation_reason"],
                "escalation_explanation": f"Post-generation audit failure: {audit.get('audit_rationale')}",
                "retrieval": retrieval_payload,
                "reply": None,
                "claims": gen_result.get("claims", []),
                "evidence_check": audit
            }

        # Step 6: Return Safe Auto-Handled Result
        return {
            "decision": "auto_handle",
            "intent": predicted_intent,
            "intent_confidence": intent_conf,
            "escalation_reason": None,
            "escalation_explanation": esc_decision["explanation"],
            "retrieval": retrieval_payload,
            "reply": draft_reply,
            "claims": gen_result.get("claims", []),
            "evidence_check": audit
        }
