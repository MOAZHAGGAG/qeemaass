"""
Critical Fixes for AI System Based on Heavy Testing Results
Addresses temporal filtering, semantic search quality, and location accuracy
"""

import json
import requests
import re
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced activity mapping with more comprehensive terms
ENHANCED_ACTIVITY_MAPPING = {
    # Cooking and Food - Enhanced
    'cooking': ['culinary', 'food', 'recipes', 'cuisine', 'gastronomy', 'chef', 'kitchen', 'baking', 'meal'],
    'food': ['culinary', 'cooking', 'cuisine', 'gastronomy', 'tasting', 'dining', 'restaurant', 'meal'],
    'cuisine': ['cooking', 'food', 'culinary', 'gastronomy', 'recipe', 'chef'],
    'culinary': ['cooking', 'food', 'cuisine', 'chef', 'kitchen', 'recipe'],
    
    # Technology - Enhanced
    'technology': ['tech', 'programming', 'coding', 'software', 'digital', 'innovation', 'computer', 'IT'],
    'programming': ['coding', 'software', 'development', 'tech', 'computer', 'developer', 'code'],
    'coding': ['programming', 'software', 'development', 'tech', 'code', 'developer'],
    'tech': ['technology', 'programming', 'coding', 'digital', 'innovation', 'software'],
    'software': ['programming', 'coding', 'development', 'tech', 'computer'],
    
    # Sports and Fitness - Enhanced
    'sports': ['athletics', 'fitness', 'exercise', 'physical', 'competition', 'athletic', 'sport'],
    'fitness': ['exercise', 'workout', 'health', 'wellness', 'physical', 'training', 'gym'],
    'exercise': ['fitness', 'workout', 'health', 'physical', 'sports', 'training'],
    'athletics': ['sports', 'athletic', 'competition', 'physical', 'exercise'],
    
    # Academic - Enhanced
    'academic': ['educational', 'learning', 'conference', 'seminar', 'research', 'education', 'study'],
    'education': ['academic', 'learning', 'educational', 'study', 'school', 'university'],
    'research': ['academic', 'study', 'investigation', 'analysis', 'science'],
    
    # Arts and Culture - Enhanced
    'art': ['creative', 'cultural', 'artistic', 'exhibition', 'gallery', 'arts', 'creativity'],
    'culture': ['cultural', 'art', 'heritage', 'traditional', 'festival', 'arts'],
    'music': ['musical', 'concert', 'performance', 'entertainment', 'band', 'song'],
    
    # Social and Entertainment - Enhanced
    'social': ['networking', 'community', 'meetup', 'gathering', 'interaction', 'party'],
    'party': ['social', 'celebration', 'entertainment', 'gathering', 'fun', 'parties'],
    'entertainment': ['fun', 'show', 'performance', 'party', 'social', 'leisure'],
}

def parse_temporal_constraints(date_constraints: List[str]) -> Optional[Tuple[str, str]]:
    """
    Parse temporal constraints and return date range for Weaviate filtering
    Returns (start_date, end_date) in YYYY-MM-DD format
    """
    try:
        current_date = datetime.now()
        
        for constraint in date_constraints:
            constraint_lower = constraint.lower()
            
            if constraint_lower == 'today':
                date_str = current_date.strftime('%Y-%m-%d')
                return (date_str, date_str)
                
            elif constraint_lower == 'tomorrow':
                tomorrow = current_date + timedelta(days=1)
                date_str = tomorrow.strftime('%Y-%m-%d')
                return (date_str, date_str)
                
            elif constraint_lower in ['this week', 'week']:
                # From today to end of week (Sunday)
                days_until_sunday = 6 - current_date.weekday()
                end_of_week = current_date + timedelta(days=days_until_sunday)
                return (current_date.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d'))
                
            elif constraint_lower in ['next week']:
                # Next Monday to next Sunday
                days_to_next_monday = 7 - current_date.weekday()
                next_monday = current_date + timedelta(days=days_to_next_monday)
                next_sunday = next_monday + timedelta(days=6)
                return (next_monday.strftime('%Y-%m-%d'), next_sunday.strftime('%Y-%m-%d'))
                
            elif constraint_lower in ['this weekend', 'weekend']:
                # This Friday to Sunday
                days_to_friday = 4 - current_date.weekday()
                if days_to_friday < 0:  # Already past Friday
                    days_to_friday += 7
                this_friday = current_date + timedelta(days=days_to_friday)
                this_sunday = this_friday + timedelta(days=2)
                return (this_friday.strftime('%Y-%m-%d'), this_sunday.strftime('%Y-%m-%d'))
                
            elif constraint_lower in ['this month', 'month']:
                # Rest of this month
                end_of_month = current_date.replace(day=1) + timedelta(days=32)
                end_of_month = end_of_month.replace(day=1) - timedelta(days=1)
                return (current_date.strftime('%Y-%m-%d'), end_of_month.strftime('%Y-%m-%d'))
                
            # Try to parse specific dates
            try:
                parsed_date = datetime.strptime(constraint, '%Y-%m-%d')
                date_str = parsed_date.strftime('%Y-%m-%d')
                return (date_str, date_str)
            except ValueError:
                pass
                
        return None
        
    except Exception as e:
        logger.error(f"Error parsing temporal constraints: {e}")
        return None

def normalize_location(location: str) -> str:
    """Normalize location for better matching"""
    if not location:
        return ""
        
    location_lower = location.lower()
    
    # Location mappings
    if 'cairo' in location_lower:
        return 'Cairo'
    elif 'alexandria' in location_lower or 'alex' in location_lower:
        return 'Alexandria'
    elif 'giza' in location_lower:
        return 'Giza'
    elif 'zamalek' in location_lower:
        return 'Cairo'  # Zamalek is part of Cairo
    elif 'heliopolis' in location_lower:
        return 'Cairo'  # Heliopolis is part of Cairo
    
    return location.title()

def build_enhanced_weaviate_query(interests: Dict, limit: int = 2) -> Dict:
    """
    Build enhanced Weaviate GraphQL query with proper filtering
    """
    try:
        tags = interests.get("tags", [])
        date_constraints = interests.get("date_constraints", [])
        location_constraints = interests.get("location_constraints", [])
        
        # Build concepts for semantic search
        concepts = []
        if tags:
            # Add original tags
            concepts.extend(tags)
            
            # Add enhanced terms
            for tag in tags:
                tag_lower = tag.lower()
                if tag_lower in ENHANCED_ACTIVITY_MAPPING:
                    enhanced_terms = ENHANCED_ACTIVITY_MAPPING[tag_lower][:3]  # Top 3
                    concepts.extend(enhanced_terms)
        
        # If no concepts, use broad search
        if not concepts:
            concepts = ["event", "activity"]
            
        # Build WHERE clause for filtering using proper Weaviate syntax
        where_conditions = []
        
        # Add date filtering
        date_range = parse_temporal_constraints(date_constraints)
        if date_range:
            start_date, end_date = date_range
            
            if start_date == end_date:
                # Single date filter
                where_conditions.append(f'''{{
                    path: ["event_date"]
                    operator: Equal
                    valueString: "{start_date}"
                }}''')
                logger.info(f"Added exact date filter: {start_date}")
            else:
                # Date range filter
                where_conditions.append(f'''{{
                    path: ["event_date"]
                    operator: GreaterThanEqual
                    valueString: "{start_date}"
                }}''')
                where_conditions.append(f'''{{
                    path: ["event_date"]
                    operator: LessThanEqual
                    valueString: "{end_date}"
                }}''')
                logger.info(f"Added date range filter: {start_date} to {end_date}")
        
        # Add location filtering
        if location_constraints:
            for location in location_constraints:
                normalized_location = normalize_location(location)
                where_conditions.append(f'''{{
                    path: ["location"]
                    operator: Like
                    valueString: "*{normalized_location}*"
                }}''')
                logger.info(f"Added location filter: {normalized_location}")
        
        # Build the complete query
        concepts_str = '", "'.join(concepts[:5])  # Limit concepts
        
        if where_conditions:
            # Build WHERE clause with proper GraphQL syntax
            if len(where_conditions) == 1:
                where_clause = where_conditions[0]
            else:
                operands_str = ', '.join(where_conditions)
                where_clause = f'''{{
                    operator: And
                    operands: [{operands_str}]
                }}'''
            
            query = f'''{{
                Get {{
                    Event(
                        nearText: {{concepts: ["{concepts_str}"]}}
                        where: {where_clause}
                        limit: {limit}
                    ) {{
                        title
                        description
                        category
                        location
                        organizer
                        event_date
                        event_time
                        postgres_id
                        _additional {{ score }}
                    }}
                }}
            }}'''
        else:
            # No filtering, just semantic search
            query = f'''{{
                Get {{
                    Event(
                        nearText: {{concepts: ["{concepts_str}"]}}
                        limit: {limit}
                    ) {{
                        title
                        description
                        category
                        location
                        organizer
                        event_date
                        event_time
                        postgres_id
                        _additional {{ score }}
                    }}
                }}
            }}'''
        
        return {"query": query}
        
    except Exception as e:
        logger.error(f"Error building enhanced query: {e}")
        # Fallback to simple query
        return {
            "query": f'''{{
                Get {{
                    Event(limit: {limit}) {{
                        title
                        description
                        category
                        location
                        organizer
                        event_date
                        event_time
                        postgres_id
                        _additional {{ score }}
                    }}
                }}
            }}'''
        }

def enhanced_relevance_scoring(events: List[Dict], interests: Dict) -> List[Dict]:
    """
    Enhanced relevance scoring with temporal and semantic factors
    """
    try:
        current_date = datetime.now()
        tags = interests.get("tags", [])
        date_constraints = interests.get("date_constraints", [])
        location_constraints = interests.get("location_constraints", [])
        
        # Expand search terms for matching
        all_terms = set()
        for tag in tags:
            tag_lower = tag.lower()
            all_terms.add(tag_lower)
            if tag_lower in ENHANCED_ACTIVITY_MAPPING:
                all_terms.update([term.lower() for term in ENHANCED_ACTIVITY_MAPPING[tag_lower][:5]])
        
        for event in events:
            relevance_score = 0.0
            
            # 1. Semantic similarity from Weaviate (if available)
            weaviate_score = float(event.get("_additional", {}).get("score", 0))
            if weaviate_score > 0:
                relevance_score += weaviate_score * 10
            
            # 2. Title matching (highest weight)
            title = event.get("title", "").lower()
            title_matches = sum(1 for term in all_terms if term in title)
            relevance_score += title_matches * 5
            
            # 3. Description matching
            description = event.get("description", "").lower()
            desc_matches = sum(1 for term in all_terms if term in description)
            relevance_score += desc_matches * 2
            
            # 4. Category matching
            category = event.get("category", "").lower()
            if any(term in category for term in all_terms):
                relevance_score += 3
            
            # 5. Location matching
            event_location = event.get("location", "").lower()
            for constraint in location_constraints:
                if normalize_location(constraint).lower() in event_location:
                    relevance_score += 4
            
            # 6. Temporal relevance (boost upcoming events)
            event_date_str = event.get("event_date")
            if event_date_str:
                try:
                    event_date = datetime.strptime(event_date_str, '%Y-%m-%d')
                    days_diff = (event_date - current_date).days
                    
                    # Boost events happening soon
                    if 0 <= days_diff <= 7:  # This week
                        relevance_score += 2
                    elif 0 <= days_diff <= 30:  # This month
                        relevance_score += 1
                    elif days_diff < 0:  # Past events
                        relevance_score -= 5
                        
                except ValueError:
                    pass
            
            # 7. Penalize poor matches
            if relevance_score == 0 and tags:
                relevance_score = -1  # Poor match indicator
                
            event["enhanced_relevance_score"] = relevance_score
            logger.debug(f"Event '{event['title']}' scored {relevance_score:.2f}")
        
        # Sort by relevance score
        return sorted(events, key=lambda x: x.get("enhanced_relevance_score", 0), reverse=True)
        
    except Exception as e:
        logger.error(f"Error in enhanced relevance scoring: {e}")
        return events

def query_weaviate_with_advanced_filtering(interests: Dict, limit: int = 2, weaviate_url: str = "http://localhost:8085") -> List[Dict]:
    """
    Advanced Weaviate querying with proper temporal and location filtering
    """
    try:
        # Build enhanced query
        gql_query = build_enhanced_weaviate_query(interests, limit)
        logger.info(f"Enhanced query built for interests: {interests}")
        
        # Execute query
        response = requests.post(
            f"{weaviate_url}/v1/graphql",
            json=gql_query,
            timeout=15,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            logger.error(f"Weaviate request failed with status {response.status_code}")
            return []
            
        result = response.json()
        
        # Check for GraphQL errors
        if "errors" in result:
            logger.error(f"GraphQL errors: {result['errors']}")
            return []
            
        events = result.get("data", {}).get("Get", {}).get("Event", [])
        
        if not events:
            logger.warning("No events found with filtering, trying broader search")
            # Fallback: try without filtering
            simple_query = {
                "query": f'''{{
                    Get {{
                        Event(limit: {limit}) {{
                            title
                            description
                            category
                            location
                            organizer
                            event_date
                            event_time
                            postgres_id
                            _additional {{ score }}
                        }}
                    }}
                }}'''
            }
            
            response = requests.post(f"{weaviate_url}/v1/graphql", json=simple_query, timeout=10)
            if response.status_code == 200:
                result = response.json()
                events = result.get("data", {}).get("Get", {}).get("Event", [])
        
        # Apply enhanced relevance scoring
        ranked_events = enhanced_relevance_scoring(events, interests)
        
        logger.info(f"Query returned {len(ranked_events)} events with enhanced filtering")
        return ranked_events
        
    except requests.exceptions.Timeout:
        logger.error("Weaviate request timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Weaviate request error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in query_weaviate_with_advanced_filtering: {e}")
        return []

def extract_interests_with_temporal_awareness(user_message: str, client) -> Dict:
    """
    Enhanced interest extraction with better temporal understanding
    """
    try:
        system_prompt = """You are an expert event recommendation assistant with strong temporal awareness.

Extract user interests and return a structured JSON response. Pay special attention to temporal expressions.

Guidelines:
1. ACTIVITIES: Extract specific activities, hobbies, or interests (NOT generic words like "events")
2. TEMPORAL: Recognize and extract time-related expressions:
   - "today", "tomorrow", "tonight"
   - "this week", "next week", "this weekend"
   - "this month", "next month"
   - Specific dates if mentioned
3. LOCATION: Extract any mentioned places, cities, or venues
4. Be conservative - only extract clear, specific interests

Return ONLY this JSON structure:
{
    "tags": ["specific_activity1", "specific_activity2"],
    "date_constraints": ["temporal_expression1"],
    "location_constraints": ["location1"]
}

Examples:
- "I want cooking classes tomorrow" → {"tags": ["cooking"], "date_constraints": ["tomorrow"], "location_constraints": []}
- "Any tech events this weekend in Cairo?" → {"tags": ["technology"], "date_constraints": ["this weekend"], "location_constraints": ["Cairo"]}
- "Show me sports activities" → {"tags": ["sports"], "date_constraints": [], "location_constraints": []}
- "What's happening tonight?" → {"tags": [], "date_constraints": ["tonight"], "location_constraints": []}
"""

        user_prompt = f"Extract interests from: \"{user_message}\""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()
        
        # Clean the response
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("\n", 1)[0]
        
        # Parse JSON
        interests = json.loads(result)
        
        # Validate and clean
        required_keys = ["tags", "date_constraints", "location_constraints"]
        for key in required_keys:
            if key not in interests:
                interests[key] = []
            elif not isinstance(interests[key], list):
                interests[key] = []
        
        # Filter out generic terms from tags
        generic_terms = ["event", "events", "activity", "activities", "things", "stuff"]
        interests["tags"] = [tag for tag in interests["tags"] if tag.lower() not in generic_terms]
        
        logger.info(f"Enhanced extraction: {interests}")
        return interests

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {"tags": [], "date_constraints": [], "location_constraints": []}
    except Exception as e:
        logger.error(f"Error in enhanced extraction: {e}")
        return {"tags": [], "date_constraints": [], "location_constraints": []}


# -------------------- Compatibility Functions for Main App --------------------

def extract_interests_enhanced(user_message: str, client):
    """Wrapper for main app compatibility"""
    return extract_interests_with_temporal_awareness(user_message, client)

def merge_interests_enhanced(existing: Dict, new: Dict) -> Dict:
    """Merge interests with conflict resolution"""
    merged = {"tags": [], "date_constraints": [], "location_constraints": []}
    
    # Merge tags (avoid duplicates)
    all_tags = set(existing.get("tags", []) + new.get("tags", []))
    merged["tags"] = list(all_tags)
    
    # For date constraints, prefer new ones (more recent intent)
    merged["date_constraints"] = new.get("date_constraints", []) or existing.get("date_constraints", [])
    
    # For location, prefer new ones (more recent intent)
    merged["location_constraints"] = new.get("location_constraints", []) or existing.get("location_constraints", [])
    
    return merged

def user_asked_for_events_enhanced(user_input: str, interests: Dict) -> bool:
    """Detect if user is asking for events"""
    user_lower = user_input.lower()
    
    # Event-related keywords
    event_keywords = [
        "event", "events", "happening", "activities", "show me", "find", "what's on",
        "things to do", "going on", "available", "schedule", "calendar", "meetup",
        "conference", "workshop", "class", "party", "gathering", "festival"
    ]
    
    # Check for event keywords
    if any(keyword in user_lower for keyword in event_keywords):
        return True
    
    # Check if user mentioned specific constraints (implies event search)
    if interests.get("date_constraints") or interests.get("location_constraints"):
        return True
    
    # Check for implicit event requests
    activity_phrases = ["looking for", "interested in", "want to", "need to find"]
    if any(phrase in user_lower for phrase in activity_phrases):
        return True
    
    return False

def generate_reply_enhanced(user_input: str, events: List[Dict], interests: Dict, history: List[Dict], client):
    """Generate contextual reply"""
    if events:
        # Format events for display
        event_text = "I found these events for you:\n\n"
        for i, event in enumerate(events[:3], 1):
            title = event.get("title", "Unknown Event")
            date = event.get("event_date", "TBD")
            time = event.get("event_time", "")
            location = event.get("location", "TBD")
            
            event_text += f"{i}. **{title}**\n"
            if date != "TBD":
                event_text += f"   📅 {date}"
                if time:
                    event_text += f" at {time}"
                event_text += "\n"
            event_text += f"   📍 {location}\n\n"
        
        return event_text
    else:
        return "I couldn't find any events matching your criteria. Try being more specific or check back later!"
