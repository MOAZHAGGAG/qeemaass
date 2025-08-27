#!/usr/bin/env python3
"""
Direct PostgreSQL Event Search - bypasses Weaviate for more accurate results
"""

import psycopg2
from typing import List, Dict
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host="localhost",   
        dbname="event_management",
        user="eventuser",
        password="eventpass123",
        port="5445"
    )

def search_events_by_category(interests: List[str], limit: int = 3) -> List[Dict]:
    """
    Direct PostgreSQL search for more accurate category matching
    """
    try:
        conn = get_connection()
        cur = conn.cursor()
        
        # Map user interests to exact database categories
        category_mapping = {
            "sports": ["Sports", "Athletics", "Fitness"],
            "technology": ["Technology", "Tech"],
            "cultural": ["Cultural", "Culture", "Art"],
            "academic": ["Academic", "Education", "Workshop"],
            "career": ["Career", "Professional", "Business"]
        }
        
        # Build category search terms
        search_categories = []
        search_titles = []
        
        for interest in interests:
            interest_lower = interest.lower()
            if interest_lower in category_mapping:
                search_categories.extend(category_mapping[interest_lower])
            search_titles.append(interest)
        
        # Build SQL query with category and title matching
        conditions = []
        params = []
        
        if search_categories:
            category_placeholders = ','.join(['%s'] * len(search_categories))
            conditions.append(f"category IN ({category_placeholders})")
            params.extend(search_categories)
        
        if search_titles:
            for title_term in search_titles:
                conditions.append("(title ILIKE %s OR description ILIKE %s)")
                params.extend([f"%{title_term}%", f"%{title_term}%"])
        
        if not conditions:
            return []
        
        # Execute query
        query = f"""
            SELECT id, title, description, category, location, event_date, event_time, organizer
            FROM events 
            WHERE {' OR '.join(conditions)}
            AND event_date >= CURRENT_DATE
            ORDER BY event_date ASC
            LIMIT %s
        """
        params.append(limit)
        
        print(f"DEBUG: Executing SQL: {query}")
        print(f"DEBUG: With params: {params}")
        
        cur.execute(query, params)
        rows = cur.fetchall()
        
        # Convert to dictionaries
        events = []
        for row in rows:
            event = {
                'postgres_id': row[0],
                'title': row[1],
                'description': row[2],
                'category': row[3],
                'location': row[4],
                'event_date': row[5].strftime('%Y-%m-%d') if row[5] else None,
                'event_time': row[6].strftime('%H:%M:%S') if row[6] else None,
                'organizer': row[7]
            }
            events.append(event)
        
        cur.close()
        conn.close()
        
        print(f"DEBUG: Found {len(events)} events directly from PostgreSQL")
        for event in events:
            print(f"  - {event['title']} ({event['category']})")
        
        return events
        
    except Exception as e:
        print(f"Error in direct PostgreSQL search: {e}")
        return []
