"""
src/reconstruction.py
Core algorithms for reconstructing multi-turn customer support conversations
from Twitter directed graph relationship pointers (in_response_to_tweet_id, response_tweet_id).
Preserves the full graph DAG (nodes and edges) as well as derived linear dialogue paths.
"""

from typing import Dict, List, Set, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
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
    turns: List[Turn]  # Chronologically sorted unique turns
    is_branched: bool
    turn_count: int
    graph: Dict[str, List[str]] = field(default_factory=dict)  # parent_id -> list of child_ids
    derived_paths: List[List[str]] = field(default_factory=list)  # distinct root-to-leaf turn_id paths

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
            if t_id not in graph[parent_id]:
                graph[parent_id].append(t_id)
    return graph

def find_root_to_leaf_paths(root_id: str, graph: Dict[str, List[str]], max_depth: int = 20) -> List[List[str]]:
    """
    Finds all distinct linear root-to-leaf paths through the dialogue DAG.
    """
    paths = []
    
    def dfs(curr_id: str, current_path: List[str], visited: Set[str]):
        if len(current_path) > max_depth:
            paths.append(list(current_path))
            return
            
        children = [ch for ch in graph.get(curr_id, []) if ch not in visited]
        if not children:
            paths.append(list(current_path))
            return
            
        for ch in children:
            visited.add(ch)
            current_path.append(ch)
            dfs(ch, current_path, visited)
            current_path.pop()
            visited.remove(ch)

    dfs(root_id, [root_id], {root_id})
    return paths

def reconstruct_conversation_paths(
    root_id: str,
    tweets_by_id: Dict[str, Dict],
    children_map: Dict[str, List[str]],
    brand: str
) -> Optional[Conversation]:
    """
    Reconstructs a Conversation starting from an initiating root tweet.
    Traverses the sub-DAG, extracts nodes, preserves local graph edges, and computes derived paths.
    """
    if root_id not in tweets_by_id:
        return None

    visited = set()
    turns_dict = {}
    queue = [root_id]
    local_graph = {}
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
        turns_dict[curr_id] = turn

        children = [ch for ch in children_map.get(curr_id, []) if ch in tweets_by_id and ch not in visited]
        if len(children) > 1:
            is_branched = True
        local_graph[curr_id] = children
        for ch in children:
            queue.append(ch)

    if not turns_dict:
        return None

    # Derive all distinct linear paths in this dialogue graph
    derived_paths = find_root_to_leaf_paths(root_id, local_graph)

    # Sort turns chronologically for global conversation overview
    turns_list = list(turns_dict.values())
    turns_list.sort(key=lambda t: parse_twitter_date(t.created_at) or datetime.min)

    return Conversation(
        conversation_id=root_id,
        brand=brand,
        customer_id=customer_id or "unknown",
        turns=turns_list,
        is_branched=is_branched,
        turn_count=len(turns_list),
        graph=local_graph,
        derived_paths=derived_paths
    )

def extract_cases_from_conversation(conv: Conversation) -> List[Case]:
    """
    Extracts atomic Cases from a Conversation along its derived paths.
    For each customer turn along a dialogue path, preceding turns along THAT path
    constitute context, and direct subsequent support turns along THAT path constitute reference responses.
    This guarantees branching paths never mix context from parallel sibling branches.
    """
    cases_dict = {}
    turns_by_id = {t.tweet_id: t for t in conv.turns}

    for path in conv.derived_paths:
        path_turns = [turns_by_id[tid] for tid in path if tid in turns_by_id]
        for i, turn in enumerate(path_turns):
            if turn.speaker_role == "customer":
                context = path_turns[:i]
                support_responses = []
                for next_turn in path_turns[i+1:]:
                    if next_turn.speaker_role == "support":
                        support_responses.append(next_turn)
                    else:
                        break

                case_id = f"conv_{conv.conversation_id}_turn_{turn.tweet_id}"
                # If a customer turn appears in multiple branches, merge distinct responses
                if case_id not in cases_dict:
                    cases_dict[case_id] = Case(
                        case_id=case_id,
                        conversation_id=conv.conversation_id,
                        customer_turn=turn,
                        context_turns=context,
                        reference_support_turns=support_responses,
                        has_reference_response=len(support_responses) > 0
                    )
                else:
                    # Append any newly discovered responses from alternative branches
                    existing = cases_dict[case_id]
                    seen_tids = {t.tweet_id for t in existing.reference_support_turns}
                    for resp in support_responses:
                        if resp.tweet_id not in seen_tids:
                            existing.reference_support_turns.append(resp)
                    existing.has_reference_response = len(existing.reference_support_turns) > 0

    return list(cases_dict.values())

def pd_not_na(val) -> bool:
    if val is None:
        return False
    s = str(val).strip().lower()
    return s not in ("", "nan", "none", "<na>")
