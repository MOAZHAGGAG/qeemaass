#!/usr/bin/env python3
"""
Test script for enhanced chatbot with location and date filtering
This test follows the EXACT same pattern as the real app uses
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from enhanced_chatbot import (
    extract_user_preferences,
    generate_conversational_response,
    query_events_with_preferences
)
from simple_weaviate_search import simple_weaviate_search
from openai import OpenAI

def test_enhanced_chatbot_flow():
    """Test the enhanced chatbot following the exact same flow as the real app"""

    # Initialize OpenAI client (you'll need to set your API key)
    client = OpenAI(api_key=os.getenv("OPENAI_APIKEY", ""))

    if not client.api_key:
        print("⚠️  Please set OPENAI_APIKEY environment variable to test AI features")
        return

    # Test queries that include location and date preferences
    test_queries = [
        "I want sports events in New York next week",
        "Show me technology events in San Francisco this weekend",
        "Any cultural events in Chicago tomorrow",
        "Find academic workshops near Central Park",
        "Sports events today",
        "Technology meetups in Boston"
    ]

    print("🧪 Testing Enhanced Chatbot Flow (Real App Pattern)")
    print("=" * 70)

    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: '{query}'")
        print("-" * 50)

        try:
            # Step 1: Extract user preferences (same as real app)
            preferences = extract_user_preferences(query, client)

            print(f"📊 Extracted Preferences:")
            print(f"   Interests: {preferences.get('interests', [])}")
            print(f"   Date Prefs: {preferences.get('date_preferences', {})}")
            print(f"   Location Prefs: {preferences.get('location_preferences', {})}")
            print(f"   Wants Recommendation: {preferences.get('wants_recommendation', False)}")

            # Step 2: Query events if user wants recommendations (same as real app)
            events = []
            if preferences.get("wants_recommendation", False):
                # Use the same lambda pattern as the real app, but with simple_weaviate_search
                events = query_events_with_preferences(
                    preferences,
                    client,
                    lambda query_term, limit=5: simple_weaviate_search(query_term, limit=limit)
                )

            print(f"🎯 Found {len(events)} events")

            # Step 3: Generate conversational response (same as real app)
            # Mock history for testing
            mock_history = [
                {"role": "system", "content": "You are a friendly campus events assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you find events?"}
            ]

            reply = generate_conversational_response(
                query, preferences, events, mock_history, client
            )

            print(f"💬 AI Response: {reply[:200]}...")

            # Show the recommended event details
            if events:
                event = events[0]  # Only show the first (and only) event
                print(f"🏆 Recommended Event:")
                print(f"   Title: {event.get('title', 'N/A')}")
                print(f"   Category: {event.get('category', 'N/A')}")
                print(f"   Location: {event.get('location', 'N/A')}")
                print(f"   Date: {event.get('event_date', 'N/A')}")
                print(f"   Matches Interests: {preferences.get('interests', [])}")
                print(f"   Matches Location: {preferences.get('location_preferences', {}).get('preferred_locations', [])}")
                print(f"   Matches Date: {preferences.get('date_preferences', {}).get('preferred_dates', '')}")

        except Exception as e:
            print(f"❌ Error in test {i}: {e}")
            import traceback
            traceback.print_exc()

def test_location_date_filtering():
    """Test specific location and date filtering scenarios"""

    client = OpenAI(api_key=os.getenv("OPENAI_APIKEY", ""))

    if not client.api_key:
        print("⚠️  Please set OPENAI_APIKEY environment variable to test filtering")
        return

    print("\n🎯 Testing Location & Date Filtering")
    print("=" * 50)

    # Test cases with different combinations
    test_cases = [
        {
            "query": "sports events in New York",
            "expected_interests": ["sports"],
            "expected_location": ["New York"]
        },
        {
            "query": "technology events this weekend in San Francisco",
            "expected_interests": ["technology"],
            "expected_location": ["San Francisco"],
            "expected_date": "weekend"
        },
        {
            "query": "cultural events tomorrow",
            "expected_interests": ["cultural"],
            "expected_date": "tomorrow"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['query']}")

        preferences = extract_user_preferences(test_case['query'], client)

        interests = preferences.get('interests', [])
        location_prefs = preferences.get('location_preferences', {})
        date_prefs = preferences.get('date_preferences', {})

        print(f"   ✅ Interests: {interests}")
        print(f"   📍 Location: {location_prefs.get('preferred_locations', [])}")
        print(f"   📅 Date: {date_prefs.get('preferred_dates', '')}")

        # Verify expectations
        if test_case['expected_interests'][0] in interests:
            print("   ✅ Interest extraction: PASS")
        else:
            print(f"   ❌ Interest extraction: FAIL (expected {test_case['expected_interests']})")

        if test_case.get('expected_location') and location_prefs.get('has_location_preference'):
            if test_case['expected_location'][0] in location_prefs.get('preferred_locations', []):
                print("   ✅ Location extraction: PASS")
            else:
                print(f"   ❌ Location extraction: FAIL (expected {test_case['expected_location']})")
        elif not test_case.get('expected_location'):
            print("   ✅ Location extraction: PASS (no location expected)")
        else:
            print("   ❌ Location extraction: FAIL (location expected but not found)")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Chatbot Tests")
    print("This test follows the EXACT same flow as the real Streamlit app")
    print()

    test_enhanced_chatbot_flow()
    test_location_date_filtering()

    print("\n✨ Test completed!")
