"""
src/retrieval/schemas.py
Standardized interfaces and data schemas for all retrieval models.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

@dataclass
class RetrievedCase:
    case_id: str
    score: float
    rank: int
    customer_message: str
    historical_response: str
    intent: str
    preceding_context: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
