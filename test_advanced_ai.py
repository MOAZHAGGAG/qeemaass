#!/usr/bin/env python3
"""
Test Advanced AI Functions with Temporal and Location Filtering
"""

import sys
import os
from dotenv import load_dotenv

load_dotenv()
sys.path.append('.')

try:
    from advanced_ai_functions import (
        parse_temporal_constraints,
        normalize_location,
        build_enhanced_weaviate_query,
        query_weaviate_with_advanced_filtering,
        extract_interests_with_temporal_awareness
    )
    from openai import OpenAI
    
    client = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_temporal_parsing():
    """Test temporal constraint parsing"""
    print("\n=== TEMPORAL PARSING TEST ===")
    
    test_cases = [
        "today",
        "tomorrow", 
        "this week",
        "next week",
        "this weekend",
        "this month"
    ]
    
    for constraint in test_cases:
        result = parse_temporal_constraints([constraint])
        print(f"{constraint} → {result}")

def test_location_normalization():
    """Test location normalization"""
    print("\n=== LOCATION NORMALIZATION TEST ===")
    
    test_locations = [
        "Cairo",
        "downtown cairo",
        "Cairo University",
        "Alexandria",
        "alex",
        "Zamalek",
        "Heliopolis", 
        "Giza"
    ]
    
    for location in test_locations:
        normalized = normalize_location(location)
        print(f"'{location}' → '{normalized}'")

def test_advanced_temporal_queries():
    """Test advanced temporal queries"""
    print("\n=== ADVANCED TEMPORAL QUERIES TEST ===")
    
    temporal_tests = [
        {
            'description': 'Events today',
            'interests': {'tags': [], 'date_constraints': ['today'], 'location_constraints': []}
        },
        {
            'description': 'Events tomorrow',
            'interests': {'tags': [], 'date_constraints': ['tomorrow'], 'location_constraints': []}
        },
        {
            'description': 'Tech events this week',
            'interests': {'tags': ['technology'], 'date_constraints': ['this week'], 'location_constraints': []}
        },
        {
            'description': 'Sports this weekend',
            'interests': {'tags': ['sports'], 'date_constraints': ['this weekend'], 'location_constraints': []}
        }
    ]
    
    for test in temporal_tests:
        print(f"\nTesting: {test['description']}")
        print(f"Interests: {test['interests']}")
        
        events = query_weaviate_with_advanced_filtering(test['interests'], limit=3)
        
        if events:
            print(f"Found {len(events)} events:")
            for i, event in enumerate(events):
                relevance = event.get('enhanced_relevance_score', 0)
                print(f"  {i+1}. {event['title']}")
                print(f"     Date: {event.get('event_date', 'N/A')}")
                print(f"     Category: {event.get('category', 'N/A')}")
                print(f"     Relevance: {relevance:.2f}")
        else:
            print("No events found")

def test_advanced_location_queries():
    """Test advanced location queries"""
    print("\n=== ADVANCED LOCATION QUERIES TEST ===")
    
    location_tests = [
        {
            'description': 'Events in Cairo',
            'interests': {'tags': [], 'date_constraints': [], 'location_constraints': ['Cairo']}
        },
        {
            'description': 'Events in Alexandria', 
            'interests': {'tags': [], 'date_constraints': [], 'location_constraints': ['Alexandria']}
        },
        {
            'description': 'Tech events in Cairo',
            'interests': {'tags': ['technology'], 'date_constraints': [], 'location_constraints': ['Cairo']}
        }
    ]
    
    for test in location_tests:
        print(f"\nTesting: {test['description']}")
        print(f"Interests: {test['interests']}")
        
        events = query_weaviate_with_advanced_filtering(test['interests'], limit=3)
        
        if events:
            print(f"Found {len(events)} events:")
            for i, event in enumerate(events):
                relevance = event.get('enhanced_relevance_score', 0)
                location = event.get('location', 'N/A')
                print(f"  {i+1}. {event['title']}")
                print(f"     Location: {location}")
                print(f"     Category: {event.get('category', 'N/A')}")
                print(f"     Relevance: {relevance:.2f}")
                
                # Check if location matches
                expected_location = test['interests']['location_constraints'][0] if test['interests']['location_constraints'] else None
                if expected_location:
                    normalized_expected = normalize_location(expected_location)
                    if normalized_expected.lower() in location.lower():
                        print(f"     ✓ Location matches")
                    else:
                        print(f"     ⚠️ Location mismatch")
        else:
            print("No events found")

def test_enhanced_interest_extraction():
    """Test enhanced interest extraction with temporal awareness"""
    print("\n=== ENHANCED INTEREST EXTRACTION TEST ===")
    
    test_messages = [
        "I want cooking classes tomorrow",
        "Any tech events this weekend?",
        "Show me sports activities in Cairo",
        "What's happening tonight?",
        "Looking for academic conferences next week",
        "Any parties this weekend in Alexandria?",
        "Find me art exhibitions this month"
    ]
    
    for message in test_messages:
        print(f"\nMessage: \"{message}\"")
        interests = extract_interests_with_temporal_awareness(message, client)
        print(f"Extracted: {interests}")
        
        # Test the full pipeline
        events = query_weaviate_with_advanced_filtering(interests, limit=2)
        print(f"Found {len(events)} events")

def main():
    """Run all advanced AI function tests"""
    print("=== ADVANCED AI FUNCTIONS TESTING ===")
    
    try:
        test_temporal_parsing()
        test_location_normalization()
        test_advanced_temporal_queries()
        test_advanced_location_queries()
        test_enhanced_interest_extraction()
        
        print("\n=== ADVANCED TESTING COMPLETED ===")
        
    except Exception as e:
        print(f"Critical error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
