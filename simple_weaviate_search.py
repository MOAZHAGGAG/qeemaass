#!/usr/bin/env python3
"""
Simple Direct Weaviate Search
A clean, working implementation for event search
"""

import requests
import json
from typing import List, Dict

def simple_weaviate_search(query: str, limit: int = 5, weaviate_url: str = "http://localhost:8085") -> List[Dict]:
    """
    Simple, direct Weaviate search that actually works
    """
    try:
        # Build simple GraphQL query
        graphql_query = {
            "query": f"""
            {{
                Get {{
                    Event(bm25: {{query: "{query}"}}, limit: {limit}) {{
                        title
                        description
                        category
                        location
                        event_date
                        event_time
                        organizer
                        postgres_id
                    }}
                }}
            }}
            """
        }
        
        print(f"DEBUG: Sending Weaviate query: {query}")
        
        # Send request to Weaviate
        response = requests.post(
            f"{weaviate_url}/v1/graphql",
            json=graphql_query,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Check for errors
        if "errors" in result:
            print(f"ERROR: Weaviate GraphQL errors: {result['errors']}")
            return []
        
        # Extract events
        events = result.get("data", {}).get("Get", {}).get("Event", [])
        print(f"DEBUG: Weaviate returned {len(events)} events for query '{query}'")
        
        for event in events:
            print(f"DEBUG: - {event.get('title', 'N/A')} ({event.get('category', 'N/A')})")
        
        return events
        
    except Exception as e:
        print(f"ERROR: Simple Weaviate search failed: {e}")
        return []

if __name__ == "__main__":
    # Test the simple search
    test_queries = ["Sports", "Technology", "Cultural", "Academic", "Career"]
    
    for query in test_queries:
        print(f"\n🔍 Testing: {query}")
        print("=" * 40)
        events = simple_weaviate_search(query, limit=3)
        if not events:
            print("No events found")
