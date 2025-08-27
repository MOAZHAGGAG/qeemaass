#!/usr/bin/env python3
"""
Heavy Testing Suite for AI System and Weaviate Data Validation
Tests temporal accuracy, interest matching, and data quality
"""

import sys
import os
import json
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add current directory to path
sys.path.append('.')

try:
    from enhanced_ai_functions import (
        extract_interests_enhanced,
        query_weaviate_enhanced,
        user_asked_for_events_enhanced,
        build_search_query
    )
    from openai import OpenAI
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv("OPENAI_APIKEY"))
    
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

WEAVIATE_URL = 'http://localhost:8085'

def get_all_events_from_weaviate():
    """Get all events from Weaviate to analyze data quality"""
    try:
        gql_query = {
            'query': '''
            {
                Get {
                    Event(limit: 100) {
                        title
                        description
                        category
                        location
                        organizer
                        event_date
                        event_time
                        postgres_id
                        created_at
                        updated_at
                    }
                }
            }
            '''
        }
        
        response = requests.post(f'{WEAVIATE_URL}/v1/graphql', json=gql_query, timeout=10)
        result = response.json()
        
        if 'errors' in result:
            print(f"GraphQL errors: {result['errors']}")
            return []
            
        return result.get('data', {}).get('Get', {}).get('Event', [])
        
    except Exception as e:
        print(f"Error fetching events: {e}")
        return []

def analyze_event_dates():
    """Analyze event dates to understand temporal distribution"""
    print("\n=== EVENT DATE ANALYSIS ===")
    
    events = get_all_events_from_weaviate()
    print(f"Total events in database: {len(events)}")
    
    if not events:
        print("No events found!")
        return
    
    # Parse and analyze dates
    date_distribution = {}
    valid_dates = 0
    invalid_dates = 0
    future_events = 0
    past_events = 0
    
    current_date = datetime.now()
    
    for event in events:
        event_date_str = event.get('event_date')
        event_time_str = event.get('event_time', '00:00:00')
        
        print(f"Event: {event['title']}")
        print(f"  Date: {event_date_str}")
        print(f"  Time: {event_time_str}")
        
        if event_date_str:
            try:
                # Parse date
                event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                valid_dates += 1
                
                # Check if future or past
                if event_date > current_date:
                    future_events += 1
                    print(f"  Status: FUTURE EVENT ✓")
                else:
                    past_events += 1
                    print(f"  Status: PAST EVENT ⚠️")
                
                # Track distribution
                year_month = event_date.strftime('%Y-%m')
                date_distribution[year_month] = date_distribution.get(year_month, 0) + 1
                
            except ValueError as e:
                invalid_dates += 1
                print(f"  Status: INVALID DATE FORMAT ✗ ({e})")
        else:
            invalid_dates += 1
            print(f"  Status: NO DATE ✗")
        
        print()
    
    print(f"\n=== DATE ANALYSIS SUMMARY ===")
    print(f"Valid dates: {valid_dates}")
    print(f"Invalid dates: {invalid_dates}")
    print(f"Future events: {future_events}")
    print(f"Past events: {past_events}")
    print(f"Date distribution: {date_distribution}")

def test_temporal_filtering():
    """Test if temporal queries actually return events in the requested time period"""
    print("\n=== TEMPORAL FILTERING TEST ===")
    
    # Get current date for reference
    current_date = datetime.now()
    tomorrow = current_date + timedelta(days=1)
    next_week = current_date + timedelta(days=7)
    
    temporal_tests = [
        {
            'query': 'events today',
            'interests': {'tags': [], 'date_constraints': ['today'], 'location_constraints': []},
            'expected_date_range': (current_date.date(), current_date.date())
        },
        {
            'query': 'events tomorrow',
            'interests': {'tags': [], 'date_constraints': ['tomorrow'], 'location_constraints': []},
            'expected_date_range': (tomorrow.date(), tomorrow.date())
        },
        {
            'query': 'events this week',
            'interests': {'tags': [], 'date_constraints': ['this week'], 'location_constraints': []},
            'expected_date_range': (current_date.date(), next_week.date())
        }
    ]
    
    for test in temporal_tests:
        print(f"\nTesting: {test['query']}")
        print(f"Expected date range: {test['expected_date_range']}")
        
        # Build query
        query_text = build_search_query(test['interests'])
        print(f"Built query: '{query_text}'")
        
        # Search events
        events = query_weaviate_enhanced(query_text, limit=5)
        
        if events:
            print(f"Found {len(events)} events:")
            for i, event in enumerate(events):
                event_date_str = event.get('event_date')
                print(f"  {i+1}. {event['title']}")
                print(f"     Date: {event_date_str}")
                print(f"     Category: {event['category']}")
                
                # Validate if event is in expected date range
                if event_date_str:
                    try:
                        event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()
                        expected_start, expected_end = test['expected_date_range']
                        
                        if expected_start <= event_date <= expected_end:
                            print(f"     ✓ Date matches constraint")
                        else:
                            print(f"     ✗ Date outside constraint ({event_date} not in {expected_start} to {expected_end})")
                    except ValueError:
                        print(f"     ✗ Invalid date format")
                else:
                    print(f"     ✗ No date available")
                print()
        else:
            print("No events found")

def test_interest_accuracy():
    """Test if interest-based searches return relevant events"""
    print("\n=== INTEREST ACCURACY TEST ===")
    
    interest_tests = [
        {
            'query': 'cooking events',
            'expected_categories': ['Workshop', 'Cultural', 'Social'],
            'keywords': ['cooking', 'food', 'culinary', 'recipe', 'chef', 'kitchen']
        },
        {
            'query': 'technology programming',
            'expected_categories': ['Technology', 'Academic'],
            'keywords': ['tech', 'programming', 'code', 'software', 'developer', 'computer']
        },
        {
            'query': 'sports fitness',
            'expected_categories': ['Sports', 'Health', 'Entertainment'],
            'keywords': ['sport', 'fitness', 'exercise', 'athletic', 'physical', 'competition']
        },
        {
            'query': 'art culture',
            'expected_categories': ['Cultural', 'Entertainment', 'Workshop'],
            'keywords': ['art', 'culture', 'creative', 'gallery', 'exhibition', 'artistic']
        },
        {
            'query': 'academic conference',
            'expected_categories': ['Academic', 'Technology', 'Career'],
            'keywords': ['academic', 'research', 'conference', 'symposium', 'education', 'study']
        }
    ]
    
    for test in interest_tests:
        print(f"\nTesting interest: '{test['query']}'")
        print(f"Expected categories: {test['expected_categories']}")
        print(f"Expected keywords: {test['keywords']}")
        
        events = query_weaviate_enhanced(test['query'], limit=5)
        
        if events:
            print(f"Found {len(events)} events:")
            
            category_matches = 0
            keyword_matches = 0
            
            for i, event in enumerate(events):
                title = event.get('title', '').lower()
                description = event.get('description', '').lower()
                category = event.get('category', '')
                relevance = event.get('relevance_score', 0)
                
                print(f"  {i+1}. {event['title']} ({category}) - Relevance: {relevance:.2f}")
                print(f"     Description: {event.get('description', 'N/A')[:100]}...")
                
                # Check category match
                if category in test['expected_categories']:
                    category_matches += 1
                    print(f"     ✓ Category matches expectation")
                else:
                    print(f"     ⚠️ Category '{category}' not in expected {test['expected_categories']}")
                
                # Check keyword presence
                content = f"{title} {description}"
                found_keywords = [kw for kw in test['keywords'] if kw in content]
                
                if found_keywords:
                    keyword_matches += 1
                    print(f"     ✓ Keywords found: {found_keywords}")
                else:
                    print(f"     ⚠️ No expected keywords found in content")
                
                print()
            
            # Calculate accuracy
            category_accuracy = (category_matches / len(events)) * 100
            keyword_accuracy = (keyword_matches / len(events)) * 100
            
            print(f"Category accuracy: {category_accuracy:.1f}% ({category_matches}/{len(events)})")
            print(f"Keyword accuracy: {keyword_accuracy:.1f}% ({keyword_matches}/{len(events)})")
            
            if category_accuracy >= 60 and keyword_accuracy >= 60:
                print("✓ GOOD INTEREST MATCHING")
            else:
                print("⚠️ POOR INTEREST MATCHING - NEEDS IMPROVEMENT")
        else:
            print("No events found")

def test_location_filtering():
    """Test location-based filtering"""
    print("\n=== LOCATION FILTERING TEST ===")
    
    location_tests = [
        {
            'query': 'events in Cairo',
            'interests': {'tags': [], 'date_constraints': [], 'location_constraints': ['Cairo']},
            'expected_location': 'Cairo'
        },
        {
            'query': 'events in Alexandria',
            'interests': {'tags': [], 'date_constraints': [], 'location_constraints': ['Alexandria']},
            'expected_location': 'Alexandria'
        }
    ]
    
    for test in location_tests:
        print(f"\nTesting location: {test['query']}")
        print(f"Expected location: {test['expected_location']}")
        
        query_text = build_search_query(test['interests'])
        events = query_weaviate_enhanced(query_text, limit=5)
        
        if events:
            print(f"Found {len(events)} events:")
            location_matches = 0
            
            for i, event in enumerate(events):
                location = event.get('location', '')
                print(f"  {i+1}. {event['title']}")
                print(f"     Location: {location}")
                
                if test['expected_location'].lower() in location.lower():
                    location_matches += 1
                    print(f"     ✓ Location matches")
                else:
                    print(f"     ⚠️ Location doesn't match expected '{test['expected_location']}'")
                print()
            
            accuracy = (location_matches / len(events)) * 100
            print(f"Location accuracy: {accuracy:.1f}% ({location_matches}/{len(events)})")
        else:
            print("No events found")

def test_combined_filters():
    """Test complex queries with multiple filters"""
    print("\n=== COMBINED FILTERS TEST ===")
    
    combined_tests = [
        {
            'description': 'Technology events tomorrow in Cairo',
            'interests': {
                'tags': ['technology'],
                'date_constraints': ['tomorrow'],
                'location_constraints': ['Cairo']
            }
        },
        {
            'description': 'Sports activities this weekend',
            'interests': {
                'tags': ['sports'],
                'date_constraints': ['this weekend'],
                'location_constraints': []
            }
        },
        {
            'description': 'Academic conferences next week in Cairo',
            'interests': {
                'tags': ['academic'],
                'date_constraints': ['next week'],
                'location_constraints': ['Cairo']
            }
        }
    ]
    
    for test in combined_tests:
        print(f"\nTesting: {test['description']}")
        print(f"Interests: {test['interests']}")
        
        query_text = build_search_query(test['interests'])
        print(f"Built query: '{query_text}'")
        
        events = query_weaviate_enhanced(query_text, limit=3)
        
        if events:
            print(f"Found {len(events)} events:")
            
            for i, event in enumerate(events):
                print(f"  {i+1}. {event['title']}")
                print(f"     Category: {event.get('category', 'N/A')}")
                print(f"     Date: {event.get('event_date', 'N/A')}")
                print(f"     Location: {event.get('location', 'N/A')}")
                print(f"     Relevance: {event.get('relevance_score', 0):.2f}")
                print()
        else:
            print("No events found")

def test_edge_cases():
    """Test edge cases and error scenarios"""
    print("\n=== EDGE CASES TEST ===")
    
    edge_tests = [
        {'query': '', 'description': 'Empty query'},
        {'query': 'xyzabc123nonexistent', 'description': 'Non-existent interest'},
        {'query': 'events events events', 'description': 'Repeated generic terms'},
        {'query': '!@#$%^&*()', 'description': 'Special characters'},
        {'query': 'a' * 1000, 'description': 'Very long query'},
    ]
    
    for test in edge_tests:
        print(f"\nTesting edge case: {test['description']}")
        print(f"Query: '{test['query'][:50]}{'...' if len(test['query']) > 50 else ''}'")
        
        try:
            events = query_weaviate_enhanced(test['query'], limit=3)
            print(f"Result: Found {len(events)} events")
            
            if events:
                for i, event in enumerate(events[:2]):
                    print(f"  {i+1}. {event['title']} ({event.get('category', 'N/A')})")
        except Exception as e:
            print(f"Error: {e}")

def main():
    """Run comprehensive heavy testing"""
    print("=== COMPREHENSIVE HEAVY TESTING SUITE ===")
    print("Testing data accuracy, temporal filtering, and interest matching...")
    
    try:
        # Test 1: Analyze all event dates
        analyze_event_dates()
        
        # Test 2: Temporal filtering accuracy
        test_temporal_filtering()
        
        # Test 3: Interest matching accuracy
        test_interest_accuracy()
        
        # Test 4: Location filtering
        test_location_filtering()
        
        # Test 5: Combined filters
        test_combined_filters()
        
        # Test 6: Edge cases
        test_edge_cases()
        
        print("\n=== HEAVY TESTING COMPLETED ===")
        print("Review results above to identify areas for improvement.")
        
    except Exception as e:
        print(f"Critical error during testing: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
