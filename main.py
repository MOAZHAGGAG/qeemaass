import streamlit as st
import psycopg2
import json
import requests
import os
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from enhanced_chatbot import (
    extract_user_preferences, 
    generate_conversational_response, 
    should_clear_history, 
    query_events_with_preferences
)

load_dotenv()

# -------------------- Database Connection --------------------
def get_connection():
    return psycopg2.connect(
        host="localhost",   
        dbname="event_management",
        user="eventuser",
        password="eventpass123",
        port="5445"
    )

# -------------------- Authentication Functions --------------------
def create_user(username, password, email=None, full_name=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password, email, full_name) VALUES (%s, %s, %s, %s)",
            (username, password, email, full_name)
        )
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, full_name FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, email, full_name FROM users WHERE username=%s",
        (username,)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

# -------------------- Event Registration Functions --------------------
def register_for_event(user_id, event_id, notes=None):
    """Register a user for an event"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO event_registrations (user_id, event_id, notes) 
            VALUES (%s, %s, %s)
        """, (user_id, event_id, notes))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False  # Already registered
    except Exception as e:
        conn.rollback()
        st.error(f"Registration failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

def is_user_registered(user_id, event_id):
    """Check if user is already registered for an event"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id FROM event_registrations 
        WHERE user_id = %s AND event_id = %s AND status = 'registered'
    """, (user_id, event_id))
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def get_user_registrations(user_id):
    """Get all events a user is registered for"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT er.id, er.registration_date, er.status,
               e.id as event_id, e.title, e.description, e.category,
               e.location, e.event_date, e.event_time, e.organizer
        FROM event_registrations er
        JOIN events e ON er.event_id = e.id
        WHERE er.user_id = %s
        ORDER BY er.registration_date DESC
    """, (user_id,))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results

def cancel_registration(user_id, event_id):
    """Cancel a user's registration for an event"""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE event_registrations 
            SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP
            WHERE user_id = %s AND event_id = %s
        """, (user_id, event_id))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Cancellation failed: {e}")
        return False
    finally:
        cur.close()
        conn.close()

# -------------------- Event Registration Functions --------------------
def get_user_id(username):
    """Get user ID from username"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user[0] if user else None

def register_for_event(user_id, event_id):
    """Register user for an event"""
    print(f"DEBUG: register_for_event called with user_id={user_id}, event_id={event_id}")
    
    if not user_id or not event_id:
        print(f"DEBUG: Missing required data - user_id={user_id}, event_id={event_id}")
        return False
        
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        cur.execute(
            """INSERT INTO event_registrations 
               (user_id, event_id, registration_date, status, email_sent, created_at, updated_at) 
               VALUES (%s, %s, CURRENT_TIMESTAMP, 'registered', false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
            (user_id, event_id)
        )
        conn.commit()
        print(f"DEBUG: Registration successful for user {user_id}, event {event_id}")
        return True
    except psycopg2.IntegrityError as e:
        print(f"DEBUG: IntegrityError: {e}")
        conn.rollback()
        return False
    except Exception as e:
        print(f"DEBUG: Registration error: {e}")
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def unregister_from_event(user_id, event_id):
    """Unregister user from an event"""
    if not user_id or not event_id:
        return False
        
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE event_registrations SET status = 'cancelled', updated_at = CURRENT_TIMESTAMP WHERE user_id=%s AND event_id=%s AND status='registered'",
            (user_id, event_id)
        )
        affected = cur.rowcount
        conn.commit()
        return affected > 0
    except Exception as e:
        print(f"Unregistration error: {e}")  # Debug print
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def is_user_registered(user_id, event_id):
    """Check if user is registered for an event"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT 1 FROM event_registrations WHERE user_id=%s AND event_id=%s AND status='registered'",
        (user_id, event_id)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result is not None

def get_registration_count(event_id):
    """Get total number of registrations for an event"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) FROM event_registrations WHERE event_id=%s AND status='registered'",
        (event_id,)
    )
    count = cur.fetchone()[0]
    cur.close()
    conn.close()
    return count

def get_event_id_by_details(title, event_date):
    """Get PostgreSQL event ID by matching title and date"""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id FROM events WHERE title=%s AND event_date=%s",
        (title, event_date)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    return result[0] if result else None

# -------------------- Chatbot Config --------------------
OPENAI_API_KEY = os.getenv("OPENAI_APIKEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8085")

client = OpenAI(api_key=OPENAI_API_KEY)

# Import advanced AI functions
from advanced_ai_functions import (
    extract_interests_enhanced,
    merge_interests_enhanced,
    user_asked_for_events_enhanced,
    query_weaviate_with_advanced_filtering,
    generate_reply_enhanced,
    build_enhanced_weaviate_query
)

# -------------------- Enhanced Chatbot Functions --------------------
def extract_interests(user_message):
    """Extract user interests using enhanced AI functions"""
    return extract_interests_enhanced(user_message, client)
    
def merge_interests(existing, new):
    """Merge interests using enhanced logic to prevent contamination"""
    return merge_interests_enhanced(existing, new)

def user_asked_for_events(user_input, interests):
    """Detect if user is asking for events using enhanced detection"""
    return user_asked_for_events_enhanced(user_input, interests)

def query_weaviate(query: str, limit: int = 2, weaviate_url: str = WEAVIATE_URL):
    """Query Weaviate using advanced search with temporal and location filtering"""
    # Extract interests from the query string
    interests = extract_interests(query)
    return query_weaviate_with_advanced_filtering(interests, limit, weaviate_url)

def generate_reply(user_input, events, interests, history):
    """Generate reply using enhanced AI with better context handling"""
    return generate_reply_enhanced(user_input, events, interests, history, client)

# -------------------- Helper Functions --------------------
def get_user_id(username):
    """Get user ID from username"""
    user_data = get_user_by_username(username)
    return user_data[0] if user_data else None

def display_event_card(event, user_id, key_suffix=""):
    """Display an event card with registration functionality"""
    event_id = event.get('postgres_id')
    title = event.get('title', 'Unknown Event')
    description = event.get('description', 'No description available')
    category = event.get('category', 'General')
    location = event.get('location', 'Location TBD')
    event_date = event.get('event_date', 'Date TBD')
    event_time = event.get('event_time', 'Time TBD')
    organizer = event.get('organizer', 'Unknown Organizer')
    
    # Create a nice event card
    with st.container():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.markdown(f"**🎯 {title}**")
            st.markdown(f"📅 **Date:** {event_date} | ⏰ **Time:** {event_time}")
            st.markdown(f"📍 **Location:** {location}")
            st.markdown(f"🏷️ **Category:** {category}")
            st.markdown(f"👤 **Organizer:** {organizer}")
            if description and description != 'No description available':
                with st.expander("📝 Description"):
                    st.markdown(description)
        
        with col2:
            if user_id and event_id:
                # Check if user is already registered
                already_registered = is_user_registered(user_id, event_id)
                
                if already_registered:
                    st.success("✅ Registered")
                    if st.button("Cancel Registration", key=f"cancel_{event_id}{key_suffix}", 
                               type="secondary", use_container_width=True):
                        if cancel_registration(user_id, event_id):
                            st.success("❌ Registration cancelled")
                            st.rerun()
                        else:
                            st.error("Failed to cancel registration")
                else:
                    if st.button("📝 Register", key=f"register_{event_id}{key_suffix}", 
                               type="primary", use_container_width=True):
                        if register_for_event(user_id, event_id):
                            st.success("🎉 Registration successful! You'll receive a confirmation email.")
                            st.rerun()
                        else:
                            st.error("Registration failed. You may already be registered.")
            else:
                st.info("Login to register")
        
        st.markdown("---")

def show_user_registrations():
    """Show user's event registrations"""
    st.title("🗓️ My Event Registrations")
    
    user_id = get_user_id(st.session_state['username'])
    if not user_id:
        st.error("❌ Could not find user information")
        return
    
    registrations = get_user_registrations(user_id)
    
    if not registrations:
        st.info("📭 You haven't registered for any events yet.")
        st.markdown("💡 Use the AI chat to find and register for events!")
        return
    
    st.success(f"🎉 You are registered for {len(registrations)} event(s)")
    
    # Group registrations by status
    active_registrations = [r for r in registrations if r[2] == 'registered']  # status column
    cancelled_registrations = [r for r in registrations if r[2] == 'cancelled']
    
    # Show active registrations
    if active_registrations:
        st.subheader("✅ Active Registrations")
        for reg in active_registrations:
            with st.expander(f"🎯 {reg[4]} - {reg[9]}", expanded=True):  # title and event_date
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**📅 Date:** {reg[9]} | **⏰ Time:** {reg[10]}")
                    st.markdown(f"**📍 Location:** {reg[8]}")
                    st.markdown(f"**🏷️ Category:** {reg[6]}")
                    st.markdown(f"**👤 Organizer:** {reg[11]}")
                    st.markdown(f"**📝 Registered:** {reg[1].strftime('%Y-%m-%d %H:%M')}")
                    if reg[5]:  # description
                        st.markdown(f"**Description:** {reg[5]}")
                
                with col2:
                    if st.button("❌ Cancel Registration", key=f"cancel_reg_{reg[0]}", 
                               type="secondary", use_container_width=True):
                        if cancel_registration(user_id, reg[3]):  # event_id
                            st.success("Registration cancelled")
                            st.rerun()
                        else:
                            st.error("Failed to cancel registration")
    
    # Show cancelled registrations
    if cancelled_registrations:
        st.subheader("❌ Cancelled Registrations")
        for reg in cancelled_registrations:
            with st.expander(f"🚫 {reg[4]} - {reg[9]}"):
                st.markdown(f"**📅 Date:** {reg[9]} | **⏰ Time:** {reg[10]}")
                st.markdown(f"**📍 Location:** {reg[8]}")
                st.markdown(f"**📝 Originally Registered:** {reg[1].strftime('%Y-%m-%d %H:%M')}")
                st.markdown("*Registration was cancelled*")

# -------------------- Enhanced Chatbot Functions --------------------
def extract_interests(user_message):
    """Extract user interests using enhanced AI functions"""
    return extract_interests_enhanced(user_message, client)
    
def merge_interests(existing, new):
    """Merge interests using enhanced logic to prevent contamination"""
    return merge_interests_enhanced(existing, new)

def user_asked_for_events(user_input, interests):
    """Detect if user is asking for events using enhanced detection"""
    return user_asked_for_events_enhanced(user_input, interests)

def query_weaviate(query: str, limit: int = 2, weaviate_url: str = WEAVIATE_URL):
    """Query Weaviate using advanced search with temporal and location filtering"""
    # Extract interests from the query string
    interests = extract_interests(query)
    return query_weaviate_with_advanced_filtering(interests, limit, weaviate_url)

def generate_reply(user_input, events, interests, history):
    """Generate reply using enhanced AI with better context handling"""
    return generate_reply_enhanced(user_input, events, interests, history, client)

# -------------------- Authentication Page --------------------
def show_auth_page():
    st.title("🔑 Sign Up / Log In")
    
    mode = st.radio("Select mode:", ["Log In", "Sign Up"])

    if mode == "Sign Up":
        st.subheader("Create a new account")
        with st.form("signup_form"):
            new_user = st.text_input("Username")
            new_email = st.text_input("Email Address")
            full_name = st.text_input("Full Name")
            new_pass = st.text_input("Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Sign Up")

            if signup_btn:
                if new_pass != confirm_pass:
                    st.error("⚠️ Passwords do not match")
                elif new_user.strip() == "" or new_pass.strip() == "" or new_email.strip() == "":
                    st.error("⚠️ Please fill all required fields (Username, Email, Password)")
                else:
                    success = create_user(new_user, new_pass, new_email, full_name)
                    if success:
                        st.success("✅ Account created successfully! Please log in.")
                    else:
                        st.error("⚠️ Username or email already exists")

    elif mode == "Log In":
        st.subheader("Log in to your account")
        with st.form("login_form"):
            user = st.text_input("Username")
            passwd = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Log In")

            if login_btn:
                user_data = authenticate_user(user, passwd)
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user
                    st.session_state["user_id"] = user_data[0]
                    st.session_state["user_email"] = user_data[2]
                    st.session_state["user_full_name"] = user_data[3]
                    st.success(f"✅ Welcome back, {user}!")
                    st.rerun()  # This will refresh and show the chatbot
                else:
                    st.error("❌ Invalid username or password")

# -------------------- Event Card Display Functions --------------------
def display_event_card(event, user_id, key_suffix=""):
    """Display a beautiful event card with registration functionality"""
    
    # Use the postgres_id from Weaviate
    event_id = event.get('postgres_id')
    
    with st.container():
        # Event card styling
        st.markdown("""
        <style>
        .event-card {
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .event-title {
            font-size: 1.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .event-info {
            margin: 5px 0;
            font-size: 0.9em;
        }
        </style>
        """, unsafe_allow_html=True)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            <div class="event-card">
                <div class="event-title">🎉 {event.get('title', 'Unknown Event')}</div>
                <div class="event-info">📅 <strong>Date:</strong> {event.get('event_date', 'TBD')}</div>
                <div class="event-info">⏰ <strong>Time:</strong> {event.get('event_time', 'TBD')}</div>
                <div class="event-info">📍 <strong>Location:</strong> {event.get('location', 'TBD')}</div>
                <div class="event-info">👥 <strong>Organizer:</strong> {event.get('organizer', 'TBD')}</div>
                <div class="event-info">📝 <strong>Description:</strong> {event.get('description', 'No description available')}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            if event_id:
                registration_count = get_registration_count(event_id)
                is_registered = is_user_registered(user_id, event_id)
                
                st.metric("👥 Registered", registration_count)
                
                # Create unique keys using event data + suffix to avoid duplicates
                unique_key = f"{event_id}_{user_id}_{hash(str(event.get('title', ''))) % 1000}{key_suffix}"
                
                if is_registered:
                    if st.button(f"❌ Unregister", key=f"unreg_{unique_key}", type="secondary"):
                        if unregister_from_event(user_id, event_id):
                            st.success("✅ Successfully unregistered!")
                            st.rerun()
                        else:
                            st.error("❌ Failed to unregister")
                else:
                    if st.button(f"✅ Register", key=f"reg_{unique_key}", type="primary"):
                        if register_for_event(user_id, event_id):
                            st.success("🎉 Successfully registered!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Registration failed - you might already be registered")
            else:
                st.warning("⚠️ Event ID not available")

# -------------------- Events Page --------------------
def show_events_page():
    st.title("🎭 Campus Events")
    
    # Show user info and logout button in sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state['username']}**")
        
        # Navigation menu
        st.markdown("---")
        page = st.radio("📍 Navigation", ["🤖 AI Chat", "🗓️ My Registrations"], key="nav_menu")
        
        st.markdown("---")
        if st.button("🚪 Log Out"):
            # Clear all session state related to authentication
            for key in ["authenticated", "username", "user_id", "user_email", "user_full_name"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Handle navigation
    if page == "🗓️ My Registrations":
        show_user_registrations()
        return
    
    # Default page is AI Chat
    st.title("🎭 Campus Events - AI Assistant")
    
    # Get user ID for registration functionality
    user_id = get_user_id(st.session_state['username'])
    st.write("🔍 Loading events...")
    all_events = query_weaviate("", limit=20)  # Get all events, no filter
    
    if not all_events:
        st.warning("🔍 No events found in the database.")
        st.info("💡 **To get started:** Use the AI Chatbot to search for events!")
        
        st.markdown("### 🎯 **Try these example queries:**")
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**By Category:**")
            st.markdown("- 'academic events'")
            st.markdown("- 'technology events in September'")
            st.markdown("- 'cultural events in Zamalek'")
            
        with col2:
            st.markdown("**By Date/Location:**")
            st.markdown("- 'events this month'")
            st.markdown("- 'events in Cairo'")
            st.markdown("- 'upcoming entertainment events'")
        
        st.markdown("### 🚀 **Quick Start:**")
        if st.button("🎭 Go to AI Chatbot", type="primary"):
            st.session_state["current_page"] = "chatbot"
            st.rerun()
            
        return
    
    st.success(f"Found {len(all_events)} events")
    
    # Display all events in a grid
    cols = st.columns(2)
    for i, event in enumerate(all_events):
        with cols[i % 2]:
            display_event_card(event, user_id, key_suffix=f"_events_page_{i}")
            st.markdown("---")

# -------------------- Chatbot Page --------------------
def show_chatbot_page():
    st.title("🎓 Campus Events Chatbot")
    
    # Show user info and logout button in sidebar
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state['username']}**")
        
        # Clear Chat button
        if st.button("🧹 Clear Chat History"):
            st.session_state.history = []
            st.session_state.messages = []
            st.session_state.collected_interests = []
            st.session_state.events_by_message = {}
            st.success("Chat history cleared!")
            st.rerun()
        
        if st.button("🚪 Log Out"):
            # Clear all session state related to authentication and chatbot
            for key in ["authenticated", "username", "history", "collected_interests", "messages", "current_events", "events_by_message"]:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
    
    # Initialize chatbot session state
    if "history" not in st.session_state:
        st.session_state.history = [
            {"role": "system", "content": "You are a friendly campus events assistant. You remember user preferences during the conversation and use them to recommend events."}
        ]

    if "collected_interests" not in st.session_state:
        st.session_state.collected_interests = {"tags": [], "date_constraints": [], "location_constraints": []}

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant", 
                "content": "👋 Hi! I'm your event recommendation assistant. I help you find the perfect events based on your interests and schedule.\n\nTell me:\n- What kind of events interest you? (sports, tech, cultural, academic, etc.)\n- When would you prefer to attend? (this week, next month, specific dates, etc.)\n\nI'll recommend the best event just for you! 🎯"
            }
        ]
    
    if "current_events" not in st.session_state:
        st.session_state.current_events = []
    
    if "events_by_message" not in st.session_state:
        st.session_state.events_by_message = {}

    # Display previous messages and persistent events
    for i, msg in enumerate(st.session_state.messages):
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
            # Only show stored events if this was an assistant response to an event request
            if (msg["role"] == "assistant" and 
                i in st.session_state.events_by_message and
                len(st.session_state.events_by_message[i]) > 0):
                
                events_for_this_message = st.session_state.events_by_message[i]
                
                st.markdown("---")
                st.markdown("### 🎯 **Events:**")
                
                # Get user ID for registration functionality
                user_id = get_user_id(st.session_state['username'])
                
                for j, event in enumerate(events_for_this_message[:1]):
                    display_event_card(event, user_id, key_suffix=f"_persistent_{i}_{j}")

    # Handle new user input
    if user_input := st.chat_input("Ask about events..."):
        # Clear history if it gets too long to prevent hallucination
        if should_clear_history(st.session_state.history):
            st.session_state.history = []
            st.session_state.messages = []
            st.session_state.collected_interests = []
            st.session_state.events_by_message = {}
        
        # Save user message
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "user", "content": user_input})

        # Show user message
        with st.chat_message("user"):
            st.markdown(user_input)

        # Extract user preferences using enhanced chatbot
        preferences = extract_user_preferences(user_input, client)
        
        # Query events if user wants recommendations
        events = []
        if preferences.get("wants_recommendation", False):
            # Use enhanced query with direct category matching
            events = query_events_with_preferences(
                preferences, 
                client, 
                lambda query, limit: query_weaviate_with_advanced_filtering(
                    [query], limit=limit, weaviate_url=WEAVIATE_URL
                )
            )
            
            # Store events for display if found
            if events:
                message_index = len(st.session_state.messages)  # Index of assistant message we're about to add
                st.session_state.events_by_message[message_index] = events.copy()

        # Generate conversational response
        reply = generate_conversational_response(
            user_input, preferences, events, st.session_state.history, client
        )

        # Save and show assistant reply
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.session_state.history.append({"role": "assistant", "content": reply})
        
        with st.chat_message("assistant"):
            st.markdown(reply)
            
            # Show event card ONLY if user asked for recommendations AND we found events
            if events and preferences.get("wants_recommendation", False):
                st.markdown("---")
                st.markdown("### 🎯 **Perfect Event for You:**")
                
                # Get user ID for registration functionality
                user_id = get_user_id(st.session_state['username'])
                
                # Show only the first (best) event
                display_event_card(events[0], user_id, key_suffix=f"_rec_{len(st.session_state.messages)}")
            
            # Show helpful suggestions when no events are found
            elif preferences.get("wants_recommendation", False) and not events:
                st.markdown("---")
                st.markdown("### 💡 **Suggestions to Find Events:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🎯 Try Different Categories:**")
                    st.markdown("- Academic, Technology, Cultural")
                    st.markdown("- Entertainment, Social, Sports")
                    st.markdown("- Workshop, Health, Career")
                    
                    st.markdown("**📅 Try Different Dates:**")
                    st.markdown("- This month, Next month")
                    st.markdown("- September, October, November")
                    st.markdown("- Fall season, Winter season")
                
                with col2:
                    st.markdown("**📍 Popular Locations:**")
                    st.markdown("- Cairo University, Giza")
                    st.markdown("- American University, New Cairo")
                    st.markdown("- Opera House, Zamalek")
                    st.markdown("- Maadi Community Center")
                    
                    st.markdown("**💬 Or just tell me:**")
                    st.markdown('"Show me upcoming technology events"')
                    st.markdown('"What academic events are in October?"')
                    st.markdown('"Find cultural events in Zamalek"')

        # Refresh to show new messages
        st.rerun()

# -------------------- Main App Logic --------------------
def main():
    st.set_page_config(
        page_title="Campus Events App", 
        page_icon="🎓", 
        layout="wide"
    )
    
    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = None
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "chatbot"
    
    # Route to appropriate page
    if st.session_state["authenticated"]:
        # Add navigation sidebar
        with st.sidebar:
            st.markdown("## 🧭 Navigation")
            if st.button("💬 Chatbot", use_container_width=True):
                st.session_state["current_page"] = "chatbot"
                st.rerun()
            if st.button("🎭 Events", use_container_width=True):
                st.session_state["current_page"] = "events"
                st.rerun()
        
        # Show selected page
        if st.session_state["current_page"] == "events":
            show_events_page()
        else:
            show_chatbot_page()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()