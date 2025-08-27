#!/usr/bin/env python3
"""
Comprehensive Testing Script for Enhanced AI System
Tests all fixes and validates the improvements
"""

import sys
import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

try:
    from enhanced_ai_functions import (
        extract_interests_enhanced,
        merge_interests_enhanced,
        user_asked_for_events_enhanced,
        query_weaviate_enhanced,
        generate_reply_enhanced,
        build_search_query,
        expand_search_terms,
        rank_events_by_relevance
    )
    from openai import OpenAI
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

WEAVIATE_URL = 'http://localhost:8085'

def test_enhanced_interest_extraction():
    """Test enhanced interest extraction"""
    print("\n=== ENHANCED INTEREST EXTRACTION TEST ===")
    
    test_cases = [
        "I want cooking classes",
        "Show me tech events tomorrow",
        "Any sports activities this weekend?",
        "Looking for parties tonight",
        "Find me academic conferences next week",
        "I'm interested in art and culture",
        "What events are happening?",
        "Tell me about campus activities"
    ]
    
    for test_input in test_cases:
        print(f"\nInput: \"{test_input}\"")
        try:
            interests = extract_interests_enhanced(test_input, client)
            print(f"Extracted: {interests}")
            
            # Validate structure
            assert isinstance(interests, dict), "Should return dict"
            assert "tags" in interests, "Should have tags"
            assert "date_constraints" in interests, "Should have date_constraints"
            assert "location_constraints" in interests, "Should have location_constraints"
            print("✓ Structure valid")
            
        except Exception as e:
            print(f"✗ Error: {e}")

def test_enhanced_query_building():
    """Test enhanced query building with activity mapping"""
    print("\n=== ENHANCED QUERY BUILDING TEST ===")
    
    test_cases = [
        {"tags": ["cooking"], "date_constraints": [], "location_constraints": []},
        {"tags": ["technology", "programming"], "date_constraints": ["tomorrow"], "location_constraints": []},
        {"tags": ["sports"], "date_constraints": ["this weekend"], "location_constraints": ["Cairo"]},
        {"tags": ["events"], "date_constraints": [], "location_constraints": []},  # Should exclude "events"
        {"tags": [], "date_constraints": [], "location_constraints": []},  # Empty case
    ]
    
    for interests in test_cases:
        print(f"\nInterests: {interests}")
        try:
            query = build_search_query(interests)
            print(f"Built query: \"{query}\"")
            
            # Test search term expansion
            if interests.get("tags"):
                expanded = expand_search_terms(interests["tags"])
                print(f"Expanded terms: {expanded}")
                
        except Exception as e:
            print(f"✗ Error: {e}")

def test_enhanced_event_detection():
    """Test enhanced event detection"""
    print("\n=== ENHANCED EVENT DETECTION TEST ===")
    
    test_cases = [
        ("I want cooking events", {"tags": ["cooking"]}, True),
        ("Any parties tonight?", {}, True),
        ("Show me workshops", {}, True),
        ("Hello how are you?", {}, False),
        ("What's your name?", {}, False),
        ("Find me tech meetups", {}, True),
        ("Looking for conferences", {}, True),
        ("Tell me about bootcamps", {}, True),
    ]
    
    for user_input, interests, expected in test_cases:
        print(f"\nInput: \"{user_input}\" | Interests: {interests}")
        try:
            result = user_asked_for_events_enhanced(user_input, interests)
            print(f"Detected: {result} (expected: {expected})")
            if result == expected:
                print("✓ Correct")
            else:
                print("✗ Incorrect")
                
        except Exception as e:
            print(f"✗ Error: {e}")

def test_enhanced_search_relevance():
    """Test enhanced search relevance and ranking"""
    print("\n=== ENHANCED SEARCH RELEVANCE TEST ===")
    
    test_queries = [
        {'query': 'cooking culinary food', 'expected_categories': ['Workshop', 'Cultural']},
        {'query': 'technology programming coding', 'expected_categories': ['Technology', 'Academic']},
        {'query': 'sports athletics fitness', 'expected_categories': ['Sports', 'Entertainment']},
        {'query': 'social networking community', 'expected_categories': ['Social', 'Entertainment']},
    ]

    total_tests = 0
    high_relevance_tests = 0

    for test in test_queries:
        query = test['query']
        expected = test['expected_categories']
        
        print(f"\nTesting: \"{query}\"")
        print(f"Expected categories: {expected}")
        
        try:
            events = query_weaviate_enhanced(query, limit=3)
            
            if events:
                print("Enhanced results:")
                found_categories = []
                for i, event in enumerate(events[:3]):
                    score = event.get('relevance_score', 0)
                    weaviate_score = event.get('_additional', {}).get('score', 0)
                    category = event['category']
                    found_categories.append(category)
                    print(f"  {i+1}. {event['title']} ({category})")
                    print(f"     Relevance: {score:.2f} | Weaviate: {weaviate_score}")
                    
                # Check relevance
                relevant_count = sum(1 for cat in found_categories if cat in expected)
                relevance_score = relevant_count / len(events) * 100
                print(f"  Overall relevance: {relevance_score:.1f}% ({relevant_count}/{len(events)} relevant)")
                
                total_tests += 1
                if relevance_score >= 50:
                    print("  ✓ GOOD RELEVANCE!")
                    high_relevance_tests += 1
                else:
                    print("  ⚠️  LOW RELEVANCE!")
            else:
                print("  No results found")
                
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\n=== ENHANCED SEARCH SUMMARY ===")
    print(f"Total tests: {total_tests}")
    print(f"High relevance tests: {high_relevance_tests}")
    if total_tests > 0:
        success_rate = high_relevance_tests / total_tests * 100
        print(f"Success rate: {success_rate:.1f}%")

def test_interest_contamination_fix():
    """Test that interest contamination is fixed"""
    print("\n=== INTEREST CONTAMINATION FIX TEST ===")
    
    # Simulate conversation flow
    print("Simulating conversation:")
    
    # First query: tech interests
    existing_interests = {"tags": [], "date_constraints": [], "location_constraints": []}
    new_interests1 = {"tags": ["technology", "programming"], "date_constraints": [], "location_constraints": []}
    
    merged1 = merge_interests_enhanced(existing_interests, new_interests1)
    print(f"1. User asks for tech events: {merged1}")
    
    # Second query: cooking interests (should not be contaminated)
    new_interests2 = {"tags": ["cooking", "culinary"], "date_constraints": [], "location_constraints": []}
    
    merged2 = merge_interests_enhanced(merged1, new_interests2)
    print(f"2. User asks for cooking events: {merged2}")
    
    # Check if cooking dominates (fix for contamination)
    cooking_tags = [tag for tag in merged2.get("tags", []) if tag in ["cooking", "culinary"]]
    tech_tags = [tag for tag in merged2.get("tags", []) if tag in ["technology", "programming"]]
    
    print(f"Cooking tags: {cooking_tags}")
    print(f"Tech tags: {tech_tags}")
    
    if len(cooking_tags) >= len(tech_tags):
        print("✓ Contamination fixed - new interests prioritized")
    else:
        print("✗ Contamination still present")

def test_full_conversation_flow():
    """Test complete conversation flow with enhanced functions"""
    print("\n=== FULL CONVERSATION FLOW TEST ===")
    
    conversation_tests = [
        {
            'user_input': 'I want cooking classes',
            'description': 'Cooking event request'
        },
        {
            'user_input': 'Show me tech events',
            'description': 'Technology event request'
        },
        {
            'user_input': 'Any parties tonight?',
            'description': 'Social event request with time constraint'
        }
    ]
    
    for i, test in enumerate(conversation_tests):
        user_input = test['user_input']
        description = test['description']
        
        print(f"\n--- Test {i+1}: {description} ---")
        print(f"User: \"{user_input}\"")
        
        try:
            # Extract interests
            interests = extract_interests_enhanced(user_input, client)
            print(f"Interests: {interests}")
            
            # Check event detection
            asking_for_events = user_asked_for_events_enhanced(user_input, interests)
            print(f"Asking for events: {asking_for_events}")
            
            if asking_for_events:
                # Build query
                query = build_search_query(interests)
                print(f"Search query: \"{query}\"")
                
                # Search for events
                events = query_weaviate_enhanced(query, limit=2)
                print(f"Found {len(events)} events")
                
                for j, event in enumerate(events):
                    relevance = event.get('relevance_score', 0)
                    print(f"  {j+1}. {event['title']} ({event['category']}) - Relevance: {relevance:.2f}")
                
                # Generate reply
                reply = generate_reply_enhanced(user_input, events, interests, [], client)
                print(f"Reply: {reply}")
            
        except Exception as e:
            print(f"✗ Error in conversation flow: {e}")

def main():
    """Run all enhanced AI system tests"""
    print("=== COMPREHENSIVE ENHANCED AI SYSTEM TESTING ===")
    print("Testing all fixes and improvements...")
    
    try:
        # Test 1: Enhanced interest extraction
        test_enhanced_interest_extraction()
        
        # Test 2: Enhanced query building
        test_enhanced_query_building()
        
        # Test 3: Enhanced event detection
        test_enhanced_event_detection()
        
        # Test 4: Enhanced search relevance
        test_enhanced_search_relevance()
        
        # Test 5: Interest contamination fix
        test_interest_contamination_fix()
        
        # Test 6: Full conversation flow
        test_full_conversation_flow()
        
        print("\n=== TESTING COMPLETED ===")
        print("All enhanced AI functions have been tested.")
        print("Check the results above for any issues that need attention.")
        
    except Exception as e:
        print(f"Critical error during testing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
