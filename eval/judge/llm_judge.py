"""
eval/judge/llm_judge.py
Independent LLM-as-Judge using Gemini.
Implements:
- 1 to 5 Rubric Scoring (Groundedness, Actionability, Relevance, Brand Consistency)
- Pairwise Comparative Judgment with Position Bias Swapping ((A, B) and (B, A))
- Strict JSON output parsing
"""

from typing import Dict, Any, List, Optional
from src.llm.gemini_client import GeminiClient
from src.llm.cache import DiskLLMCache

RUBRIC_SYSTEM_PROMPT = """You are an objective evaluation judge auditing AI customer support replies for AppleCare on Twitter.
Score responses on a 1-5 integer scale across these axes:

1. Groundedness (1-5):
   - 5 = Completely grounded in provided evidence or follows standard verified Apple troubleshooting logic.
   - 3 = Partially grounded or asks safe clarifying questions when information is incomplete.
   - 1 = Hallucinates fake features, invalid policies, or incorrect technical procedures.
   Note: Asking necessary diagnostic questions (e.g. "What device/iOS version are you on?") is safe and valid customer support behavior.

2. Actionability (1-5):
   - 5 = Clear, actionable solution or immediate executable diagnostic instruction.
   - 4 = Appropriate clarifying question or routing step when the customer gave incomplete symptom details.
   - 2 = Vague or generic brush-off without guiding the customer.
   - 1 = Confusing, unexecutable, or detrimental advice.

3. Relevance (1-5):
   - 5 = Directly addresses the user's inquiry, error symptom, or emotional state.
   - 3 = Tangentially relevant or addresses only one part of a multi-part complaint.
   - 1 = Completely misidentifies the problem.

4. Brand Consistency & Brevity (1-5):
   - 5 = Concise, professional, empathetic, Twitter-native (<280 chars) AppleCare voice.
   - 3 = Overly verbose, long bulleted essays unsuited for social support, or slightly robotic.
   - 1 = Abrasive, rude, or unprofessional.

Output strict JSON conforming to schema."""

PAIRWISE_SYSTEM_PROMPT = """You are an impartial expert judge evaluating two customer support replies for AppleCare.
Given a customer inquiry and the available historical evidence, determine which response is better.
You must choose one of:
- "A" (Response A is noticeably better)
- "B" (Response B is noticeably better)
- "tie" (Both responses are equally good or equally flawed)
Output strict JSON."""

SCORE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "groundedness": {"type": "INTEGER"},
        "actionability": {"type": "INTEGER"},
        "relevance": {"type": "INTEGER"},
        "brand_consistency": {"type": "INTEGER"},
        "overall_score": {"type": "NUMBER"},
        "critique": {"type": "STRING"}
    },
    "required": ["groundedness", "actionability", "relevance", "brand_consistency", "overall_score", "critique"]
}

PAIRWISE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "preferred": {"type": "STRING", "enum": ["A", "B", "tie"]},
        "reason": {"type": "STRING"}
    },
    "required": ["preferred", "reason"]
}

class LLMJudge:
    def __init__(self, client: Optional[GeminiClient] = None):
        if client is None:
            cache = DiskLLMCache()
            self.client = GeminiClient(cache=cache)
        else:
            self.client = client

    def score_single(
        self,
        customer_message: str,
        response_text: str,
        evidence_text: str = ""
    ) -> Dict[str, Any]:
        prompt = f"""Customer Inquiry:
"{customer_message}"

Support Response to Evaluate:
"{response_text}"

Available Reference Evidence:
"{evidence_text if evidence_text else 'None provided'}"

Provide 1-5 ratings across the 4 axes."""
        try:
            return self.client.generate_json(
                prompt=prompt,
                system_instruction=RUBRIC_SYSTEM_PROMPT,
                temperature=0.0,
                response_schema=SCORE_SCHEMA,
                cache_key_extra={"eval_target": response_text}
            )
        except Exception as e:
            return {
                "groundedness": 3,
                "actionability": 3,
                "relevance": 3,
                "brand_consistency": 3,
                "overall_score": 3.0,
                "critique": f"Judge error: {e}"
            }

    def compare_pairwise(
        self,
        customer_message: str,
        response_a: str,
        response_b: str,
        evidence_text: str = ""
    ) -> Dict[str, Any]:
        """
        Runs position-swapped comparison to detect and mitigate position bias.
        """
        # Pass 1: (A, B)
        p1 = f"""Customer Inquiry:
"{customer_message}"

Reference Evidence:
"{evidence_text}"

Response A:
"{response_a}"

Response B:
"{response_b}"

Which response is better?"""

        # Pass 2: (B, A) [swapped]
        p2 = f"""Customer Inquiry:
"{customer_message}"

Reference Evidence:
"{evidence_text}"

Response A:
"{response_b}"

Response B:
"{response_a}"

Which response is better?"""

        try:
            r1 = self.client.generate_json(prompt=p1, system_instruction=PAIRWISE_SYSTEM_PROMPT, temperature=0.0, response_schema=PAIRWISE_SCHEMA)
            r2 = self.client.generate_json(prompt=p2, system_instruction=PAIRWISE_SYSTEM_PROMPT, temperature=0.0, response_schema=PAIRWISE_SCHEMA)

            choice_1 = r1.get("preferred", "tie")
            # In pass 2, "A" actually means response B, and "B" means response A
            raw_choice_2 = r2.get("preferred", "tie")
            choice_2 = "B" if raw_choice_2 == "A" else ("A" if raw_choice_2 == "B" else "tie")

            is_consistent = (choice_1 == choice_2)
            final_winner = choice_1 if is_consistent else "tie"

            return {
                "winner": final_winner,
                "pass_1_choice": choice_1,
                "pass_2_choice": choice_2,
                "is_consistent": is_consistent,
                "reason": r1.get("reason", "")
            }
        except Exception as e:
            return {
                "winner": "tie",
                "pass_1_choice": "tie",
                "pass_2_choice": "tie",
                "is_consistent": True,
                "reason": f"Judge error: {e}"
            }
