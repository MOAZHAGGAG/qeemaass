#!/usr/bin/env python3
"""
Enhanced Event Recommendation Chatbot
Focused on recommending single events based on user interests, date preferences, and location preferences
"""

import openai
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional

def extract_user_preferences(user_message: str, client) -> Dict:
    """Extract user interests and date preferences from their message"""
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    system_prompt = f"""You are an event recommendation assistant. Today's date is {today_str}. Extract user preferences from their message.

Your task:
1. Extract user interests/activities they mentioned
2. Extract any date preferences (specific dates, date ranges, time periods)
3. Extract any location preferences (cities, venues, areas they mentioned)
4. Determine if they want event recommendations

IMPORTANT: Map interests to these specific categories:
- "sports" for: sports, athletics, fitness, exercise, running, football, basketball, etc.
- "technology" for: tech, programming, coding, software, AI, computers, innovation, etc.
- "cultural" for: culture, art, music, heritage, festival, exhibition, fashion, cultural night, etc.
- "academic" for: education, learning, workshop, seminar, conference, research, science, debate, language, environmental, etc.
- "career" for: career, professional, job, networking, business, career fair, etc.
- "entertainment" for: entertainment, music concert, gaming, film festival, winter concert, etc.
- "social" for: social, party, celebration, food festival, volunteer, new year, halloween, etc.
- "workshop" for: workshop, photography, entrepreneurship, etc.
- "health" for: health, wellness, medical, fitness (non-sports), etc.

Return JSON format:
{{
    "interests": ["technology", "sports", "entertainment"],
    "date_preferences": {{
        "has_date_preference": true/false,
        "preferred_dates": "description of dates they mentioned",
        "date_range": "specific range if mentioned"
    }},
    "location_preferences": {{
        "has_location_preference": true/false,
        "preferred_locations": ["New York", "Central Park"],
        "location_description": "description of locations they mentioned"
    }},
    "wants_recommendation": true/false,
    "conversation_type": "event_seeking" or "general_chat"
}}

Examples:
- "I like sports events next week in New York" → interests: ["sports"], location: ["New York"], wants_recommendation: true
- "Any tech events this weekend in San Francisco?" → interests: ["technology"], location: ["San Francisco"], wants_recommendation: true
- "Show me cultural events in Chicago" → interests: ["cultural"], location: ["Chicago"], wants_recommendation: true
- "Events near Central Park" → location: ["Central Park"], wants_recommendation: true
- "I want to see entertainment events" → interests: ["entertainment"], wants_recommendation: true
- "Social events in Maadi" → interests: ["social"], location: ["Maadi"], wants_recommendation: true
- "Hello" → interests: [], wants_recommendation: false
"""

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Extract preferences from: {user_message}"}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        result = json.loads(response.choices[0].message.content.strip())
        return result
    except Exception as e:
        print(f"Error extracting preferences: {e}")
        return {
            "interests": [],
            "date_preferences": {"has_date_preference": False, "preferred_dates": "", "date_range": ""},
            "location_preferences": {"has_location_preference": False, "preferred_locations": [], "location_description": ""},
            "wants_recommendation": False,
            "conversation_type": "general_chat"
        }

def generate_conversational_response(user_message: str, preferences: Dict, events: List, history: List, client) -> str:
    """Generate focused conversational response for event recommendations"""
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Limit history to prevent hallucination
    recent_history = history[-6:] if len(history) > 6 else history
    history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in recent_history[-4:]])
    
    # Determine conversation stage
    wants_recommendation = preferences.get("wants_recommendation", False)
    has_date_preference = preferences.get("date_preferences", {}).get("has_date_preference", False)
    has_location_preference = preferences.get("location_preferences", {}).get("has_location_preference", False)
    interests = preferences.get("interests", [])
    
    if wants_recommendation and events:
        # User wants events and we found some - recommend the best one
        event = events[0]  # Always recommend just one event
        system_prompt = f"""You are a helpful event recommendation assistant. Today's date is {today_str}.

The user is looking for events and you found a perfect match. Present this ONE event in an engaging, conversational way.

Event Details:
- Title: {event.get('title', 'N/A')}
- Description: {event.get('description', 'N/A')}
- Category: {event.get('category', 'N/A')}
- Location: {event.get('location', 'N/A')}
- Date: {event.get('event_date', 'N/A')}
- Time: {event.get('event_time', 'N/A')}

Rules:
1. Present ONLY this one event enthusiastically
2. Explain why it matches their interests, date preferences, and location preferences
3. Mention the key details (date, location, category)
4. Keep it conversational and friendly
5. Don't mention other events
6. End with encouragement to register

Be natural and enthusiastic, not robotic."""

    elif wants_recommendation and not events:
        # User wants events but we didn't find any - provide intelligent suggestions based on actual data
        system_prompt = f"""You are a helpful event recommendation assistant. Today's date is {today_str}.

The user is looking for events but no matching events were found in the database for their specific criteria.

Based on the current date (August 27, 2025), here's what you should know:
- There ARE events happening today (Welcome Week Orientation and test 45)
- The next upcoming events are:
  * Tech Innovation Summit on September 5, 2025
  * Cultural Heritage Festival on September 12, 2025
  * Career Fair on September 18, 2025
  * Sports Day Championship on September 25, 2025

Respond helpfully by:
1. Acknowledging their specific request
2. If they asked for today/tomorrow/this week, mention that there ARE events today but maybe not matching their specific interests
3. Suggest specific upcoming events with actual dates and names
4. Offer to show them popular categories with real examples
5. Be encouraging and provide actionable alternatives

Be conversational, specific, and helpful. Use actual event names and dates when possible."""

    elif not wants_recommendation and not has_date_preference and not interests:
        # General greeting or chat
        system_prompt = f'''You are a friendly event recommendation assistant. Today's date is {today_str}.

The user seems to be starting a conversation or chatting generally.

Respond by:
1. Greeting them warmly
2. Explaining that you help find events based on their interests
3. Ask what kind of events they're interested in
4. Ask if they have any specific dates in mind
5. Be helpful and encouraging

Keep it brief, friendly, and focused on getting their event preferences.'''

    else:
        # User mentioned interests but not clearly asking for events, or needs date clarification
        system_prompt = f'''You are a helpful event recommendation assistant. Today's date is {today_str}.

The user mentioned some interests but either:
- Didn't clearly ask for event recommendations yet
- Mentioned interests but no date preferences
- Needs clarification

Respond by:
1. Acknowledging their interests
2. Asking if they want event recommendations
3. If they didn't mention dates, ask about their preferred time period
4. Be helpful and conversational
5. Guide them toward getting a recommendation

Keep it natural and encouraging.'''

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Recent conversation:\n{history_text}\n\nUser just said: {user_message}\n\nUser interests detected: {interests}\nDate preferences: {preferences.get('date_preferences', {})}\nLocation preferences: {preferences.get('location_preferences', {})}"}
            ],
            temperature=0.7,
            max_tokens=200
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating response: {e}")
        return "I'd love to help you find events! What kind of activities are you interested in?"

def should_clear_history(history: List) -> bool:
    """Determine if history should be cleared to prevent hallucination"""
    return False  # Never auto-clear - user can manually clear if needed

def query_events_with_preferences(preferences: Dict, client, query_function) -> List:
    """Query events based on user preferences using Weaviate search with interests as primary filter"""

    interests = preferences.get("interests", [])
    location_prefs = preferences.get("location_preferences", {})
    date_prefs = preferences.get("date_preferences", {})
    wants_recommendation = preferences.get("wants_recommendation", False)

    if not wants_recommendation:
        return []

    try:
        from simple_weaviate_search import simple_weaviate_search

        # If no interests specified, search broadly for all events
        if not interests:
            print("DEBUG: No interests specified - searching for all events")
            # Use a broad search term that should match all events
            broad_search_terms = ["Academic", "Technology", "Cultural", "Sports", "Career", "Entertainment", "Social", "Workshop", "Health"]
            all_events = []
            for term in broad_search_terms:
                events = simple_weaviate_search(term, limit=5)
                all_events.extend(events)
        else:
            # Enhanced category mapping for better Weaviate search
            category_mapping = {
                "sports": "Sports",
                "technology": "Technology",
                "cultural": "Cultural",
                "academic": "Academic",
                "career": "Career",
                "entertainment": "Entertainment",
                "social": "Social",
                "workshop": "Workshop",
                "health": "Health"
            }

            print(f"DEBUG: User preferences - Interests: {interests}, Location: {location_prefs}, Date: {date_prefs}")

            # Search primarily by interests (main criteria)
            all_events = []
            for interest in interests:
                interest_lower = interest.lower()

                # Direct category search first
                if interest_lower in category_mapping:
                    search_term = category_mapping[interest_lower]
                    print(f"DEBUG: Using Weaviate search for interest: {search_term}")

                    # Get more events initially to allow for filtering
                    events = simple_weaviate_search(search_term, limit=10)
                    print(f"DEBUG: Found {len(events)} events for '{search_term}'")

                    all_events.extend(events)
                else:
                    # Fallback: search by interest term directly
                    print(f"DEBUG: Direct search for interest term: {interest}")
                    events = simple_weaviate_search(interest, limit=5)
                    all_events.extend(events)

        # Remove duplicates
        unique_events = []
        seen_ids = set()
        for event in all_events:
            event_id = event.get('postgres_id') or event.get('id')
            if event_id not in seen_ids:
                unique_events.append(event)
                seen_ids.add(event_id)

        print(f"DEBUG: After deduplication: {len(unique_events)} unique events")

        # Apply location filtering if specified
        if location_prefs.get("has_location_preference", False):
            preferred_locations = location_prefs.get("preferred_locations", [])
            if preferred_locations:
                print(f"DEBUG: Filtering by locations: {preferred_locations}")
                filtered_events = []
                for event in unique_events:
                    event_location = event.get('location', '').lower()
                    # Check if any preferred location matches the event location
                    for pref_loc in preferred_locations:
                        pref_loc_lower = pref_loc.lower()
                        # More flexible location matching
                        should_include = False

                        # Exact match in either direction
                        if pref_loc_lower in event_location or event_location in pref_loc_lower:
                            should_include = True

                        # Handle common location patterns for Cairo
                        elif pref_loc_lower == "cairo" and ("cairo" in event_location or "giza" in event_location or "cairo university" in event_location):
                            should_include = True
                        elif pref_loc_lower == "giza" and ("giza" in event_location or "cairo university" in event_location):
                            should_include = True
                        elif pref_loc_lower == "dokki" and ("dokki" in event_location or "national research" in event_location):
                            should_include = True
                        elif pref_loc_lower == "maadi" and "maadi" in event_location:
                            should_include = True
                        elif pref_loc_lower == "zamalek" and "zamalek" in event_location:
                            should_include = True
                        elif pref_loc_lower == "new cairo" and ("new cairo" in event_location or "american university" in event_location):
                            should_include = True
                        elif pref_loc_lower == "nasr city" and ("nasr city" in event_location or "cairo international" in event_location):
                            should_include = True
                        elif pref_loc_lower == "downtown cairo" and ("downtown cairo" in event_location or "greek campus" in event_location):
                            should_include = True
                        elif pref_loc_lower == "garden city" and "garden city" in event_location:
                            should_include = True
                        elif pref_loc_lower == "old cairo" and ("old cairo" in event_location or "citadel" in event_location or "al-azhar" in event_location):
                            should_include = True
                        elif pref_loc_lower == "heliopolis" and "heliopolis" in event_location:
                            should_include = True
                        elif pref_loc_lower == "agouza" and ("agouza" in event_location or "british council" in event_location):
                            should_include = True
                        elif pref_loc_lower == "ain shams" and ("ain shams" in event_location or "medical city" in event_location):
                            should_include = True
                        elif pref_loc_lower == "smart village" and "smart village" in event_location:
                            should_include = True
                        elif pref_loc_lower == "islamic cairo" and ("islamic cairo" in event_location or "al-azhar park" in event_location):
                            should_include = True

                        if should_include:
                            filtered_events.append(event)
                            break
                unique_events = filtered_events
                print(f"DEBUG: After location filtering: {len(unique_events)} events")

        # Apply date filtering if specified
        print(f"DEBUG: Checking date filtering - date_prefs: {date_prefs}")
        if date_prefs.get("has_date_preference", False):
            preferred_dates = date_prefs.get("preferred_dates", "")
            date_range = date_prefs.get("date_range", "")

            if preferred_dates or date_range:
                print(f"DEBUG: Filtering by dates: '{preferred_dates}' or range: '{date_range}'")
                filtered_events = []

                # Parse today's date for comparison
                today = datetime.now().date()

                for event in unique_events:
                    event_date_str = event.get('event_date', '')
                    if event_date_str:
                        try:
                            # Try to parse the event date
                            event_date = datetime.strptime(event_date_str, '%Y-%m-%d').date()

                            # Check if this event matches the user's date preference
                            should_include = False

                            # Handle past dates - always exclude
                            if any(keyword in (preferred_dates + date_range).lower() for keyword in ["yesterday", "2024", "past", "last week", "last month"]):
                                should_include = False
                            elif "today" in (preferred_dates + date_range).lower():
                                should_include = (event_date == today)
                            elif "tomorrow" in (preferred_dates + date_range).lower():
                                tomorrow = today + timedelta(days=1)
                                should_include = (event_date == tomorrow)
                            elif "weekend" in (preferred_dates + date_range).lower():
                                # Check if event is on Saturday or Sunday
                                should_include = (event_date.weekday() >= 5)  # 5=Saturday, 6=Sunday
                            elif "next week" in (preferred_dates + date_range).lower():
                                next_week_start = today + timedelta(days=(7 - today.weekday()))
                                next_week_end = next_week_start + timedelta(days=6)
                                should_include = (next_week_start <= event_date <= next_week_end)
                            elif "this month" in (preferred_dates + date_range).lower():
                                should_include = (event_date.year == today.year and event_date.month == today.month)
                            elif "next month" in (preferred_dates + date_range).lower():
                                next_month = today.month + 1 if today.month < 12 else 1
                                next_month_year = today.year if today.month < 12 else today.year + 1
                                should_include = (event_date.year == next_month_year and event_date.month == next_month)
                            elif "september" in (preferred_dates + date_range).lower() or "in september" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 9 and event_date.year == 2025)
                            elif "october" in (preferred_dates + date_range).lower() or "in october" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 10 and event_date.year == 2025)
                            elif "november" in (preferred_dates + date_range).lower() or "in november" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 11 and event_date.year == 2025)
                            elif "december" in (preferred_dates + date_range).lower() or "in december" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 12 and event_date.year == 2025)
                            elif "january" in (preferred_dates + date_range).lower() or "in january" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 1 and event_date.year == 2026)
                            elif "february" in (preferred_dates + date_range).lower() or "in february" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 2 and event_date.year == 2026)
                            elif "march" in (preferred_dates + date_range).lower() or "in march" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month == 3 and event_date.year == 2026)
                            elif "fall" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month in [9, 10, 11] and event_date.year == 2025)
                            elif "winter" in (preferred_dates + date_range).lower():
                                should_include = ((event_date.month in [12] and event_date.year == 2025) or (event_date.month in [1, 2] and event_date.year == 2026))
                            elif "spring" in (preferred_dates + date_range).lower():
                                should_include = (event_date.month in [3, 4, 5] and event_date.year == 2026)
                            else:
                                # For any other date preference, include upcoming events only
                                should_include = (event_date >= today)

                            if should_include:
                                filtered_events.append(event)

                        except ValueError:
                            # If date parsing fails, include the event only if no specific date was requested
                            if "today" not in (preferred_dates + date_range).lower():
                                filtered_events.append(event)
                    else:
                        # If no date on event, include only if no specific date was requested
                        if "today" not in (preferred_dates + date_range).lower():
                            filtered_events.append(event)

                unique_events = filtered_events
                print(f"DEBUG: After date filtering: {len(unique_events)} events")

        # Sort by relevance (prioritize events that match both interests and filters)
        # For now, just take the first one since we want to return only ONE event
        if unique_events:
            # Return only the first (best) matching event
            result_events = [unique_events[0]]
            print(f"DEBUG: Returning 1 event: {result_events[0].get('title', 'N/A')}")
            return result_events

        print("DEBUG: No events found matching criteria")
        return []

    except Exception as e:
        print(f"Error querying events: {e}")
        return []
