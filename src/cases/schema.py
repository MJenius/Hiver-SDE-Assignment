"""
src/cases/schema.py
Explicit Data Contract for Conversations and Cases in Phase 2.
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class CaseTurn:
    tweet_id: str
    author_id: str
    speaker_role: str  # "customer" or "support"
    created_at: str
    text: str

@dataclass
class ProcessedCase:
    case_id: str
    conversation_id: str
    split: str  # "train", "dev", "val", "test"
    customer_tweet_id: str
    customer_message: str
    preceding_context_turns: List[Dict[str, Any]]
    preceding_context_text: str
    historical_support_turns: List[Dict[str, Any]]
    historical_support_response: str
    has_reference_response: bool
    path_turn_ids: List[str]
    is_branched: bool
    turn_index_in_path: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessedCase":
        return cls(**d)

@dataclass
class ProcessedConversation:
    conversation_id: str
    brand: str
    customer_id: str
    split: str
    turn_count: int
    is_branched: bool
    graph: Dict[str, List[str]]
    derived_paths: List[List[str]]
    turns: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ProcessedConversation":
        return cls(**d)
