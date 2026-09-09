"""
src/reconstruction.py
Core algorithms for reconstructing multi-turn customer support conversations
from Twitter directed graph relationship pointers (in_response_to_tweet_id, response_tweet_id).
"""

from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Turn:
    tweet_id: str
    author_id: str
    speaker_role: str  # "customer" or "support"
    created_at: str
    text: str
    in_response_to_tweet_id: Optional[str] = None
    response_tweet_id: Optional[str] = None

@dataclass
class Case:
    case_id: str
    conversation_id: str
    customer_turn: Turn
    context_turns: List[Turn]
    reference_support_turns: List[Turn]
    has_reference_response: bool

@dataclass
class Conversation:
    conversation_id: str
    brand: str
    customer_id: str
    turns: List[Turn]
    is_branched: bool
    turn_count: int

def parse_twitter_date(dt_str: str) -> Optional[datetime]:
    try:
        return datetime.strptime(dt_str, "%a %b %d %H:%M:%S %z %Y")
    except Exception:
        return None

def build_conversation_graph(tweets: List[Dict]) -> Dict[str, List[str]]:
    """
    Constructs an adjacency list mapping parent_tweet_id -> list of child_tweet_ids.
    Handles multiple child branches, cycles, and self-references safely.
    """
    graph = {}
    for tw in tweets:
        t_id = str(tw["tweet_id"])
        parent_id = tw.get("in_response_to_tweet_id")
        if parent_id and str(parent_id) != "nan" and str(parent_id) != t_id:
            parent_id = str(parent_id)
            if parent_id not in graph:
                graph[parent_id] = []
            graph[parent_id].append(t_id)
    return graph

def reconstruct_conversation_paths(
    root_id: str,
    tweets_by_id: Dict[str, Dict],
    children_map: Dict[str, List[str]],
    brand: str
) -> Optional[Conversation]:
    """
    Reconstructs a Conversation starting from an initiating root tweet.
    Uses BFS/DFS to traverse the DAG, ordering turns chronologically.
    """
    if root_id not in tweets_by_id:
        return None

    visited = set()
    turns_list = []
    queue = [root_id]
    is_branched = False
    customer_id = None

    while queue:
        curr_id = queue.pop(0)
        if curr_id in visited:
            continue
        visited.add(curr_id)

        tw = tweets_by_id.get(curr_id)
        if not tw:
            continue

        inbound = str(tw.get("inbound")).lower() == "true"
        speaker_role = "customer" if inbound else "support"
        if speaker_role == "customer" and customer_id is None:
            customer_id = str(tw.get("author_id"))

        turn = Turn(
            tweet_id=curr_id,
            author_id=str(tw.get("author_id")),
            speaker_role=speaker_role,
            created_at=str(tw.get("created_at")),
            text=str(tw.get("text", "")),
            in_response_to_tweet_id=str(tw.get("in_response_to_tweet_id")) if pd_not_na(tw.get("in_response_to_tweet_id")) else None,
            response_tweet_id=str(tw.get("response_tweet_id")) if pd_not_na(tw.get("response_tweet_id")) else None
        )
        turns_list.append(turn)

        children = children_map.get(curr_id, [])
        if len(children) > 1:
            is_branched = True
        for ch in children:
            if ch not in visited:
                queue.append(ch)

    if not turns_list:
        return None

    # Sort turns chronologically
    turns_list.sort(key=lambda t: parse_twitter_date(t.created_at) or datetime.min)

    return Conversation(
        conversation_id=root_id,
        brand=brand,
        customer_id=customer_id or "unknown",
        turns=turns_list,
        is_branched=is_branched,
        turn_count=len(turns_list)
    )

def extract_cases_from_conversation(conv: Conversation) -> List[Case]:
    """
    Extracts atomic Cases from a Conversation.
    Each customer turn requiring response forms a Case with preceding context and subsequent reference support turn(s).
    """
    cases = []
    turns = conv.turns

    for i, turn in enumerate(turns):
        if turn.speaker_role == "customer":
            context = turns[:i]
            # Find subsequent support turns immediately responding to this customer turn
            support_responses = []
            for next_turn in turns[i+1:]:
                if next_turn.speaker_role == "support":
                    support_responses.append(next_turn)
                else:
                    # Next customer turn begins subsequent case
                    break

            case_id = f"conv_{conv.conversation_id}_turn_{turn.tweet_id}"
            cases.append(Case(
                case_id=case_id,
                conversation_id=conv.conversation_id,
                customer_turn=turn,
                context_turns=context,
                reference_support_turns=support_responses,
                has_reference_response=len(support_responses) > 0
            ))

    return cases

def pd_not_na(val) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s not in ("", "nan", "none", "<na>")
