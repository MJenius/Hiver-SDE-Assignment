"""
tests/test_reconstruction.py
Unit tests for conversation reconstruction, directionality invariants,
branching, cycle handling, and case extraction.
"""

import pytest
from src.reconstruction import (
    Turn, Case, Conversation,
    build_conversation_graph,
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

def test_extract_cases():
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

def test_cycle_and_self_reference_resilience():
    # Self-referencing tweet or circular thread
    tweets = {
        "201": {"tweet_id": "201", "author_id": "cust_2", "inbound": True, "created_at": "Tue Nov 07 17:00:00 +0000 2017", "text": "Self loop", "in_response_to_tweet_id": "201"}
    }
    graph = build_conversation_graph(list(tweets.values()))
    assert "201" not in graph  # Self-loops must be discarded

def test_branching_detection():
    # Single customer tweet replied by two separate agents
    tweets = {
        "301": {"tweet_id": "301", "author_id": "cust_3", "inbound": True, "created_at": "Tue Nov 07 17:00:00 +0000 2017", "text": "Help me", "in_response_to_tweet_id": None},
        "302": {"tweet_id": "302", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 17:01:00 +0000 2017", "text": "Agent A here", "in_response_to_tweet_id": "301"},
        "303": {"tweet_id": "303", "author_id": "AppleSupport", "inbound": False, "created_at": "Tue Nov 07 17:02:00 +0000 2017", "text": "Agent B here", "in_response_to_tweet_id": "301"}
    }
    graph = build_conversation_graph(list(tweets.values()))
    conv = reconstruct_conversation_paths("301", tweets, graph, "AppleSupport")
    assert conv.is_branched is True
    assert conv.turn_count == 3
