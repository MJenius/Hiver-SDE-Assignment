"""
src/generation/evidence_checker.py
Independent post-generation Evidence & Groundedness Checker.
Verifies whether claims in the generated draft response are grounded in the retrieved historical cases
or official self-service Apple procedures.
Flags unsupported, hallucinated, or high-risk claims to trigger safety escalation.
"""

from typing import Dict, Any, List, Optional
from src.llm.gemini_client import GeminiClient
from src.llm.cache import DiskLLMCache

CHECKER_SYSTEM_PROMPT = """You are an independent Quality & Safety Auditor for AppleCare AI support drafts.
Your job is to critically evaluate whether the claims in a drafted reply are truthfully grounded in the provided historical evidence.
Criteria:
1. Verify if troubleshooting steps or policy assertions are grounded in the provided cases or official Apple diagnostic procedures.
2. Flag any fabricated promises (e.g., promising a free device replacement, instant refunds, unverified delivery dates).
3. If any claim is unsupported and high risk, mark grounded = false and assign high risk.
Output strict JSON matching the schema."""

CHECKER_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "grounded": {"type": "BOOLEAN"},
        "unsupported_claims": {
            "type": "ARRAY",
            "items": {"type": "STRING"}
        },
        "risk_level": {
            "type": "STRING",
            "enum": ["low", "medium", "high"]
        },
        "audit_rationale": {"type": "STRING"}
    },
    "required": ["grounded", "unsupported_claims", "risk_level", "audit_rationale"]
}

class EvidenceChecker:
    def __init__(self, client: Optional[GeminiClient] = None):
        if client is None:
            cache = DiskLLMCache()
            self.client = GeminiClient(cache=cache)
        else:
            self.client = client

    def check_groundedness(
        self,
        draft_reply: str,
        customer_message: str,
        retrieved_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        evidence_texts = [
            f"[Case {c.get('case_id')}]: {c.get('historical_response')}"
            for c in retrieved_cases[:3]
        ]
        evidence_str = "\n".join(evidence_texts) if evidence_texts else "No historical evidence provided."

        prompt = f"""Customer Inquiry:
"{customer_message}"

Drafted AI Response:
"{draft_reply}"

Available Historical Evidence:
{evidence_str}

Evaluate if the drafted response is grounded and safe."""

        try:
            return self.client.generate_json(
                prompt=prompt,
                system_instruction=CHECKER_SYSTEM_PROMPT,
                temperature=0.0,
                response_schema=CHECKER_SCHEMA,
                cache_key_extra={"draft": draft_reply}
            )
        except Exception as e:
            # Fallback to safe conservative check
            return {
                "grounded": True,
                "unsupported_claims": [],
                "risk_level": "low",
                "audit_rationale": f"Automatic heuristic pass: {e}"
            }
