"""
tests/test_reconstruction.py
Unit tests for conversation reconstruction, DAG graph preservation,
derived path extraction, branching isolation, and case extraction.
"""

import pytest
from src.reconstruction import (
    Turn, Case, Conversation,
    build_conversation_graph,
    find_root_to_leaf_paths,
    reconstruct_conversation_paths,
    extract_cases_from_conversation
)

def test_direction_role_assignment():
    tweets = {
        "101": {
            "tweet_id": "101",
            "author_id": "cust_1",
            "inbound": True,
            "created_at": "Tue Nov 07 16:53:24 +0000 2017",
            "text": "My iPhone battery drains in 2 hours",
            "in_response_to_tweet_id": None
        },
        "102": {
            "tweet_id": "102",
            "author_id": "AppleSupport",
            "inbound": False,
            "created_at": "Tue Nov 07 16:55:00 +0000 2017",
            "text": "We can help. What iOS version are you running?",
            "in_response_to_tweet_id": "101"
        }
    }
    graph = build_conversation_graph(list(tweets.values()))
    conv = reconstruct_conversation_paths("101", tweets, graph, "AppleSupport")
    
    assert conv is not None
    assert conv.turn_count == 2
    assert conv.turns[0].speaker_role == "customer"
    assert conv.turns[0].author_id == "cust_1"
    assert conv.turns[1].speaker_role == "support"
    assert conv.turns[1].author_id == "AppleSupport"
    assert conv.derived_paths == [["101", "102"]]
    assert "101" in conv.graph
    assert conv.graph["101"] == ["102"]

def test_extract_cases_and_linear_path():
    tweets = {
        "101": {"tweet_id": "101", "author_id": "cust_1", "inbound": True, "created_at": "Tue Nov 07 16:50:00 +0000 2017", "text": "App crashes", "in_response_to_tweet_id": None},
        "102": {"tweet_id": "102", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 16:52:00 +0000 2017", "text": "Have you updated to iOS 11?", "in_response_to_tweet_id": "101"},
        "103": {"tweet_id": "103", "author_id": "cust_1", "inbound": True, "created_at": "Tue Nov 07 16:54:00 +0000 2017", "text": "Yes, on 11.1 now", "in_response_to_tweet_id": "102"},
        "104": {"tweet_id": "104", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 16:56:00 +0000 2017", "text": "Please try resetting all settings.", "in_response_to_tweet_id": "103"}
    }
    graph = build_conversation_graph(list(tweets.values()))
    conv = reconstruct_conversation_paths("101", tweets, graph, "AppleSupport")
    cases = extract_cases_from_conversation(conv)

    assert len(cases) == 2
    # Case 1
    assert cases[0].customer_turn.tweet_id == "101"
    assert len(cases[0].context_turns) == 0
    assert len(cases[0].reference_support_turns) == 1
    assert cases[0].reference_support_turns[0].tweet_id == "102"
    assert cases[0].has_reference_response is True

    # Case 2
    assert cases[1].customer_turn.tweet_id == "103"
    assert len(cases[1].context_turns) == 2
    assert cases[1].context_turns[0].tweet_id == "101"
    assert cases[1].context_turns[1].tweet_id == "102"
    assert len(cases[1].reference_support_turns) == 1
    assert cases[1].reference_support_turns[0].tweet_id == "104"

def test_branched_graph_paths_and_context_isolation():
    # Customer turn 301 is replied by two different agents (302 and 303).
    # Then customer replies to 302 with 304.
    # Turn 304's path context must include 301 and 302, but NOT 303!
    tweets = {
        "301": {"tweet_id": "301", "author_id": "cust_3", "inbound": True, "created_at": "Tue Nov 07 17:00:00 +0000 2017", "text": "Help me with iOS", "in_response_to_tweet_id": None},
        "302": {"tweet_id": "302", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 17:01:00 +0000 2017", "text": "Agent A here, reboot device", "in_response_to_tweet_id": "301"},
        "303": {"tweet_id": "303", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 17:02:00 +0000 2017", "text": "Agent B here, send DM", "in_response_to_tweet_id": "301"},
        "304": {"tweet_id": "304", "author_id": "cust_3", "inbound": True, "created_at": "Tue Nov 07 17:03:00 +0000 2017", "text": "Rebooted, still broken", "in_response_to_tweet_id": "302"},
        "305": {"tweet_id": "305", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 17:04:00 +0000 2017", "text": "Ok try resetting network", "in_response_to_tweet_id": "304"}
    }
    graph = build_conversation_graph(list(tweets.values()))
    conv = reconstruct_conversation_paths("301", tweets, graph, "AppleSupport")
    
    assert conv.is_branched is True
    assert len(conv.derived_paths) == 2
    # Path 1: 301 -> 302 -> 304 -> 305
    # Path 2: 301 -> 303
    path_1 = ["301", "302", "304", "305"]
    path_2 = ["301", "303"]
    assert path_1 in conv.derived_paths
    assert path_2 in conv.derived_paths
    
    cases = extract_cases_from_conversation(conv)
    case_304 = [c for c in cases if c.customer_turn.tweet_id == "304"][0]
    
    # Context for 304 must contain only turns along its branch: 301 and 302, NOT 303!
    context_tids = [t.tweet_id for t in case_304.context_turns]
    assert context_tids == ["301", "302"]
    assert "303" not in context_tids
