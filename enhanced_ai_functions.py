"""
Enhanced AI Functions for Event Management App
Implements comprehensive fixes for search relevance, error handling, and query building
"""

import json
import requests
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Activity mapping for better search relevance
ACTIVITY_MAPPING = {
    # Cooking and Food
    'cooking': ['culinary', 'food', 'recipes', 'cuisine', 'gastronomy', 'chef'],
    'food': ['culinary', 'cooking', 'cuisine', 'gastronomy', 'tasting'],
    'cuisine': ['cooking', 'food', 'culinary', 'gastronomy'],
    
    # Technology
    'technology': ['tech', 'programming', 'coding', 'software', 'digital', 'innovation'],
    'programming': ['coding', 'software', 'development', 'tech', 'computer'],
    'coding': ['programming', 'software', 'development', 'tech'],
    'tech': ['technology', 'programming', 'coding', 'digital', 'innovation'],
    
    # Sports and Fitness
    'sports': ['athletics', 'fitness', 'exercise', 'physical', 'competition'],
    'fitness': ['exercise', 'workout', 'health', 'wellness', 'physical'],
    'exercise': ['fitness', 'workout', 'health', 'physical', 'sports'],
    
    # Social and Networking
    'social': ['networking', 'community', 'meetup', 'gathering', 'interaction'],
    'networking': ['social', 'professional', 'community', 'connections'],
    'party': ['social', 'celebration', 'entertainment', 'gathering'],
    
    # Academic and Professional
    'academic': ['educational', 'learning', 'conference', 'seminar', 'research'],
    'professional': ['career', 'business', 'networking', 'development'],
    'career': ['professional', 'job', 'development', 'business'],
    
    # Arts and Culture
    'art': ['creative', 'cultural', 'artistic', 'exhibition', 'gallery'],
    'culture': ['cultural', 'art', 'heritage', 'traditional', 'festival'],
    'music': ['musical', 'concert', 'performance', 'entertainment'],
    
    # Health and Wellness
    'health': ['wellness', 'medical', 'fitness', 'mental', 'wellbeing'],
    'wellness': ['health', 'fitness', 'mindfulness', 'wellbeing'],
}

# Category mapping for better relevance checking
CATEGORY_KEYWORDS = {
    'Academic': ['academic', 'educational', 'learning', 'conference', 'seminar', 'research', 'study'],
    'Technology': ['technology', 'tech', 'programming', 'coding', 'software', 'digital', 'innovation'],
    'Social': ['social', 'networking', 'community', 'meetup', 'gathering', 'party'],
    'Sports': ['sports', 'athletics', 'fitness', 'exercise', 'physical', 'competition'],
    'Workshop': ['workshop', 'training', 'hands-on', 'practical', 'skill', 'learning'],
    'Entertainment': ['entertainment', 'fun', 'music', 'gaming', 'performance', 'show'],
    'Cultural': ['cultural', 'art', 'heritage', 'traditional', 'festival', 'exhibition'],
    'Career': ['career', 'professional', 'job', 'business', 'development'],
    'Health': ['health', 'wellness', 'medical', 'fitness', 'mental', 'wellbeing'],
}

def extract_interests_enhanced(user_message: str, client) -> Dict:
    """
    Enhanced interest extraction with better error handling and more comprehensive prompts
    """
    try:
        system_prompt = """You are an expert event recommendation assistant for a campus event management system.

Your task is to extract user interests from their message and return them in a structured format.

Extract the following information:
1. Activity interests (what they want to do)
2. Date/time constraints (when they want it)
3. Location preferences (where they want it)

Guidelines:
- Focus on ACTIVITIES and INTERESTS, not generic words like "events"
- Extract specific activities like "cooking", "programming", "sports", "music"
- For dates, extract relative terms like "today", "tomorrow", "this weekend", "next week"
- For locations, extract specific places mentioned
- If no specific interests are mentioned, return empty arrays
- Be conservative - only extract clear, specific interests

Return ONLY a JSON object with this exact structure:
{
    "tags": ["interest1", "interest2"],
    "date_constraints": ["date1", "date2"],
    "location_constraints": ["location1"]
}

Examples:
- "I want cooking classes" → {"tags": ["cooking"], "date_constraints": [], "location_constraints": []}
- "Show me tech events tomorrow" → {"tags": ["technology"], "date_constraints": ["tomorrow"], "location_constraints": []}
- "Any sports activities this weekend in Cairo?" → {"tags": ["sports"], "date_constraints": ["this weekend"], "location_constraints": ["Cairo"]}
"""

        user_prompt = f"Extract interests from this message: \"{user_message}\""

        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )

        result = response.choices[0].message.content.strip()
        
        # Clean the response - remove markdown code blocks if present
        if result.startswith("```"):
            result = result.split("\n", 1)[1].rsplit("\n", 1)[0]
        
        # Parse JSON
        interests = json.loads(result)
        
        # Validate structure
        required_keys = ["tags", "date_constraints", "location_constraints"]
        for key in required_keys:
            if key not in interests:
                interests[key] = []
                
        # Ensure all values are lists
        for key in required_keys:
            if not isinstance(interests[key], list):
                interests[key] = []
                
        logger.info(f"Extracted interests: {interests}")
        return interests

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in extract_interests: {e}")
        return {"tags": [], "date_constraints": [], "location_constraints": []}
    except Exception as e:
        logger.error(f"Error in extract_interests: {e}")
        return {"tags": [], "date_constraints": [], "location_constraints": []}

def expand_search_terms(tags: List[str]) -> List[str]:
    """
    Expand search terms using activity mapping for better search relevance
    """
    expanded_terms = set(tags)  # Start with original tags
    
    for tag in tags:
        tag_lower = tag.lower()
        if tag_lower in ACTIVITY_MAPPING:
            # Add related terms
            expanded_terms.update(ACTIVITY_MAPPING[tag_lower][:3])  # Limit to top 3 related terms
            
    return list(expanded_terms)

def build_search_query(interests: Dict) -> str:
    """
    Build an optimized search query from user interests
    """
    try:
        tags = interests.get("tags", [])
        date_constraints = interests.get("date_constraints", [])
        location_constraints = interests.get("location_constraints", [])
        
        if not tags and not date_constraints and not location_constraints:
            return ""
            
        # Expand search terms
        expanded_tags = expand_search_terms(tags)
        
        # Build query components
        query_parts = []
        
        # Add activity terms (most important)
        if expanded_tags:
            # Prioritize original tags, then expanded terms
            primary_terms = [tag for tag in tags if tag.lower() != 'events']  # Exclude generic "events"
            secondary_terms = [term for term in expanded_tags if term not in primary_terms]
            
            # Use top terms to avoid too broad queries
            all_terms = (primary_terms + secondary_terms)[:5]
            query_parts.extend(all_terms)
        
        # Add temporal context if specified
        if date_constraints:
            for constraint in date_constraints[:2]:  # Limit to 2 constraints
                if constraint.lower() not in ['today', 'tomorrow', 'this week', 'next week']:
                    query_parts.append(constraint)
        
        # Add location context if specified
        if location_constraints:
            query_parts.extend(location_constraints[:1])  # Limit to 1 location
            
        query = " ".join(query_parts)
        logger.info(f"Built search query: '{query}' from interests: {interests}")
        return query
        
    except Exception as e:
        logger.error(f"Error building search query: {e}")
        return " ".join(interests.get("tags", [])[:3])  # Fallback

def query_weaviate_enhanced(query: str, limit: int = 2, weaviate_url: str = "http://localhost:8085") -> List[Dict]:
    """
    Enhanced Weaviate querying with error handling and query optimization
    """
    try:
        if not query or not query.strip():
            logger.warning("Empty query provided to query_weaviate_enhanced")
            return []
            
        # Clean and prepare the query
        clean_query = query.strip()
        
        # Build GraphQL query
        gql = {
            "query": f'''{{
                Get {{
                    Event(
                        nearText: {{concepts: ["{clean_query}"]}}
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
        }
        
        # Make request with timeout
        response = requests.post(
            f"{weaviate_url}/v1/graphql",
            json=gql,
            timeout=10,
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
        
        # Filter and rank results
        ranked_events = rank_events_by_relevance(events, query)
        
        logger.info(f"Query '{query}' returned {len(ranked_events)} events")
        return ranked_events
        
    except requests.exceptions.Timeout:
        logger.error("Weaviate request timeout")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Weaviate request error: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error in query_weaviate_enhanced: {e}")
        return []

def rank_events_by_relevance(events: List[Dict], query: str) -> List[Dict]:
    """
    Rank events by relevance to the query using multiple criteria
    """
    try:
        query_terms = set(word.lower() for word in query.split())
        
        for event in events:
            relevance_score = 0
            
            # Score based on category match
            category = event.get("category", "").lower()
            for term in query_terms:
                if term in CATEGORY_KEYWORDS:
                    if category in [cat.lower() for cat in CATEGORY_KEYWORDS if term in CATEGORY_KEYWORDS[cat]]:
                        relevance_score += 3
                        
            # Score based on title match
            title = event.get("title", "").lower()
            for term in query_terms:
                if term in title:
                    relevance_score += 2
                    
            # Score based on description match
            description = event.get("description", "").lower()
            for term in query_terms:
                if term in description:
                    relevance_score += 1
                    
            # Add Weaviate's similarity score
            weaviate_score = float(event.get("_additional", {}).get("score", 0))
            relevance_score += weaviate_score * 10  # Scale up the similarity score
            
            event["relevance_score"] = relevance_score
            
        # Sort by relevance score (descending)
        return sorted(events, key=lambda x: x.get("relevance_score", 0), reverse=True)
        
    except Exception as e:
        logger.error(f"Error ranking events: {e}")
        return events

def user_asked_for_events_enhanced(user_input: str, interests: Dict) -> bool:
    """
    Enhanced event detection with better keyword coverage and context awareness
    """
    try:
        # Check if user has specific interests
        if interests.get("tags") or interests.get("date_constraints") or interests.get("location_constraints"):
            return True
            
        # Comprehensive event keywords
        event_keywords = [
            "event", "events", "activity", "activities", 
            "show", "shows", "meeting", "meetings",
            "workshop", "workshops", "seminar", "seminars",
            "conference", "conferences", "session", "sessions",
            "class", "classes", "course", "courses",
            "festival", "festivals", "celebration", "celebrations",
            "party", "parties", "gathering", "gatherings",
            "meetup", "meetups", "networking",
            "competition", "competitions", "contest", "contests",
            "performance", "performances", "concert", "concerts",
            "exhibition", "exhibitions", "expo", "fair",
            "tournament", "tournaments", "match", "matches",
            "training", "trainings", "bootcamp", "bootcamps"
        ]
        
        # Action keywords that imply event search
        action_keywords = [
            "find", "search", "look", "looking", "show", "get",
            "recommend", "suggest", "want", "need", "interested",
            "attend", "join", "participate", "sign up", "register",
            "what's", "whats", "any", "are there", "tell me about"
        ]
        
        user_lower = user_input.lower()
        
        # Check for direct event keywords
        for keyword in event_keywords:
            if keyword in user_lower:
                return True
                
        # Check for action + context combinations
        has_action = any(action in user_lower for action in action_keywords)
        has_activity_context = any(activity in user_lower for activity in ACTIVITY_MAPPING.keys())
        
        if has_action and has_activity_context:
            return True
            
        # Check for question patterns
        question_patterns = [
            r'\bwhat.*(?:happening|going on|available)\b',
            r'\bany.*(?:events|activities|shows)\b',
            r'\btell me about\b',
            r'\bshow me\b',
            r'\bfind.*(?:events|activities)\b'
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, user_lower):
                return True
                
        return False
        
    except Exception as e:
        logger.error(f"Error in user_asked_for_events_enhanced: {e}")
        return False

def merge_interests_enhanced(existing: Dict, new: Dict) -> Dict:
    """
    Enhanced interest merging with conflict resolution and decay
    """
    try:
        # Instead of accumulating, prioritize current interests
        # This fixes the contamination problem
        result = {
            "tags": [],
            "date_constraints": [],
            "location_constraints": []
        }
        
        # Prioritize new interests over existing ones
        for key in ["tags", "date_constraints", "location_constraints"]:
            new_values = new.get(key, [])
            existing_values = existing.get(key, [])
            
            if new_values:
                # If new interests exist, use them primarily
                result[key] = new_values[:]
                
                # Only add existing values if they're compatible
                if key == "location_constraints":
                    # For locations, keep existing if new doesn't specify
                    for val in existing_values:
                        if val not in result[key]:
                            result[key].append(val)
                elif key == "date_constraints":
                    # For dates, prioritize new constraints
                    pass  # Use only new date constraints
                else:
                    # For tags, limit accumulation to avoid contamination
                    for val in existing_values[:2]:  # Limit to 2 existing tags
                        if val not in result[key] and len(result[key]) < 5:
                            result[key].append(val)
            else:
                # If no new interests, use existing but limit them
                result[key] = existing_values[:3] if key == "tags" else existing_values[:]
                
        logger.info(f"Merged interests - Existing: {existing}, New: {new}, Result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error in merge_interests_enhanced: {e}")
        return new if new else existing

def generate_reply_enhanced(user_input: str, events: List[Dict], interests: Dict, history: List, client) -> str:
    """
    Enhanced reply generation with better context and error handling
    """
    try:
        current_date = datetime.now().strftime("%A, %B %d, %Y")
        
        if user_asked_for_events_enhanced(user_input, interests):
            if events:
                event_count = len(events)
                interest_summary = ", ".join(interests.get("tags", [])[:3]) if interests.get("tags") else "your interests"
                
                context_parts = []
                if interests.get("date_constraints"):
                    context_parts.append(f"for {', '.join(interests['date_constraints'][:2])}")
                if interests.get("location_constraints"):
                    context_parts.append(f"in {', '.join(interests['location_constraints'][:1])}")
                
                context = " " + " ".join(context_parts) if context_parts else ""
                
                reply = f"I found {event_count} great event{'s' if event_count != 1 else ''} related to {interest_summary}{context}! Here are the details:"
            else:
                search_terms = interests.get("tags", [])
                if search_terms:
                    reply = f"I couldn't find any events matching {', '.join(search_terms[:2])} right now. Try browsing all events or searching with different keywords!"
                else:
                    reply = "I couldn't find any events matching your request. Would you like to see what's available or try a different search?"
        else:
            # Generate conversational response
            system_prompt = f"""You are a helpful campus event assistant. Today is {current_date}.
            
The user said: "{user_input}"

Respond naturally and helpfully. If they're asking about events, encourage them to be more specific about their interests. Keep responses concise and friendly.

If they're asking general questions, provide helpful information while gently steering towards event discovery."""

            response = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7,
                max_tokens=150
            )
            
            reply = response.choices[0].message.content.strip()
            
        return reply
        
    except Exception as e:
        logger.error(f"Error in generate_reply_enhanced: {e}")
        return "I'm here to help you find great campus events! What kind of activities are you interested in?"
