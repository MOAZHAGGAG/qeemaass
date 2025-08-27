#!/usr/bin/env python3
"""
Test the event recommendation system
"""

import os
import sys
sys.path.append('.')

from enhanced_chatbot import extract_user_preferences, query_events_with_preferences
from advanced_ai_functions import query_weaviate_with_advanced_filtering
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Setup
OPENAI_API_KEY = os.getenv("OPENAI_APIKEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8085")
client = OpenAI(api_key=OPENAI_API_KEY)

def test_recommendation(user_message):
    print(f"\n🧪 Testing: '{user_message}'")
    print("=" * 50)
    
    # Extract preferences
    preferences = extract_user_preferences(user_message, client)
    print(f"📊 Extracted preferences: {preferences}")
    
    # Query events
    events = query_events_with_preferences(
        preferences, 
        client, 
        lambda query, limit: query_weaviate_with_advanced_filtering(
            [query], limit=limit, weaviate_url=WEAVIATE_URL
        )
    )
    
    print(f"\n🎯 Found {len(events)} events:")
    for i, event in enumerate(events[:3]):
        print(f"{i+1}. {event.get('title', 'N/A')} ({event.get('category', 'N/A')})")
        print(f"   Date: {event.get('event_date', 'N/A')}")
        print(f"   Description: {event.get('description', 'N/A')[:100]}...")
        print()

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "I want sports events",
        "Show me technology events", 
        "Any cultural events?",
        "I'm interested in academic workshops",
        "Career events please"
    ]
    
    for test_case in test_cases:
        test_recommendation(test_case)
