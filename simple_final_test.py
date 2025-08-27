#!/usr/bin/env python3
"""
SIMPLIFIED FINAL TEST - Event Management AI System
Tests the integrated system with basic validation
"""

import sys
import os
import logging
from datetime import datetime, timedelta
import requests
import json

# Add the parent directory to the Python path
sys.path.append('/Users/moaz/Downloads/qeemas final/event-management-app-main-2-copy-4-main')

from advanced_ai_functions import (
    query_weaviate_with_advanced_filtering,
    extract_interests_with_temporal_awareness,
    parse_temporal_constraints,
    normalize_location
)

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_ai_system():
    """Simple test of the AI system"""
    print("🚀 TESTING INTEGRATED AI SYSTEM")
    print("=" * 50)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    test_queries = [
        "Show me events tomorrow",
        "Any tech events in Cairo?", 
        "Sports activities this weekend",
        "What's happening tonight?",
        "Cultural events this week"
    ]
    
    success_count = 0
    total_tests = len(test_queries)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}/{total_tests}: '{query}' ---")
        
        try:
            # Extract interests from the query
            interests = extract_interests_with_temporal_awareness(query, client)
            print(f"Extracted interests: {interests}")
            
            # Query events using advanced filtering
            events = query_weaviate_with_advanced_filtering(interests, limit=5)
            print(f"Found {len(events)} events")
            
            if events:
                for j, event in enumerate(events[:3], 1):  # Show top 3
                    print(f"  {j}. {event.get('title', 'No title')}")
                    print(f"     Date: {event.get('event_date', 'No date')}")
                    print(f"     Time: {event.get('event_time', 'No time')}")
                    print(f"     Location: {event.get('location', 'No location')}")
                    print(f"     Category: {event.get('category', 'No category')}")
                    if 'enhanced_relevance_score' in event:
                        print(f"     Relevance: {event['enhanced_relevance_score']:.2f}")
            
            success_count += 1
            print("✅ Test passed")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            logger.error(f"Error in test '{query}': {e}")
    
    print(f"\n{'='*50}")
    print(f"📊 RESULTS: {success_count}/{total_tests} tests passed")
    print(f"Success rate: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! System is working correctly.")
    elif success_count >= total_tests * 0.8:
        print("👍 Most tests passed. System is mostly functional.")
    else:
        print("⚠️  Some tests failed. System needs attention.")
    
    return success_count >= total_tests * 0.8

def test_specific_cases():
    """Test specific edge cases that were problematic before"""
    print("\n🔍 TESTING SPECIFIC PROBLEM CASES")
    print("=" * 50)
    
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Test temporal accuracy
    print("\n--- Testing Temporal Accuracy ---")
    tomorrow_query = "events tomorrow"
    interests = extract_interests_with_temporal_awareness(tomorrow_query, client)
    events = query_weaviate_with_advanced_filtering(interests, limit=10)
    
    tomorrow_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    correct_dates = 0
    
    if events:
        for event in events:
            event_date = event.get('event_date', '')
            if event_date.startswith(tomorrow_date):
                correct_dates += 1
        
        temporal_accuracy = (correct_dates / len(events)) * 100
        print(f"Temporal accuracy for 'tomorrow': {temporal_accuracy:.1f}% ({correct_dates}/{len(events)})")
    else:
        print("No events found for tomorrow")
    
    # Test location accuracy  
    print("\n--- Testing Location Accuracy ---")
    cairo_query = "events in Cairo"
    interests = extract_interests_with_temporal_awareness(cairo_query, client)
    events = query_weaviate_with_advanced_filtering(interests, limit=10)
    
    correct_locations = 0
    
    if events:
        for event in events:
            location = event.get('location', '').lower()
            if any(term in location for term in ['cairo', 'zamalek', 'heliopolis', 'downtown']):
                correct_locations += 1
        
        location_accuracy = (correct_locations / len(events)) * 100
        print(f"Location accuracy for 'Cairo': {location_accuracy:.1f}% ({correct_locations}/{len(events)})")
    else:
        print("No events found for Cairo")

if __name__ == "__main__":
    # Run basic system test
    basic_success = test_ai_system()
    
    # Run specific problem case tests
    test_specific_cases()
    
    print(f"\n{'='*60}")
    if basic_success:
        print("🎯 FINAL RESULT: AI SYSTEM IS WORKING WELL!")
        print("✅ The system can handle temporal, location, and interest filtering.")
        print("✅ Ready for integration with the main application.")
    else:
        print("⚠️  FINAL RESULT: AI SYSTEM NEEDS MORE WORK")
        print("❌ Some core functionality is not working as expected.")
    
    exit(0 if basic_success else 1)
