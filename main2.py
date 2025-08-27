# Helper to get Postgres event_id from title and date
def get_postgres_event_id(title, event_date):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM events WHERE title=%s AND event_date=%s", (title, event_date))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

import logging
import datetime
import streamlit as st
import psycopg2
import json
import requests
import os
from openai import OpenAI
from dotenv import load_dotenv
# Get current date for context
CURRENT_DATE = datetime.date.today().isoformat()
logging.debug(f"Current date for context: {CURRENT_DATE}")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.FileHandler("main2_debug.log"), logging.StreamHandler()]
)
import psycopg2

# --- Event Registration Logic (from main.py) ---
def is_user_registered(user_id, event_id):
    logging.debug(f"Checking if user {user_id} is registered for event {event_id}")
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

def register_for_event(user_id, event_id, notes=None):
    logging.debug(f"Registering user {user_id} for event {event_id} (notes={notes})")
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

def cancel_registration(user_id, event_id):
    logging.debug(f"Cancelling registration for user {user_id} and event {event_id}")
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

def display_event_card(event, user_id, key_suffix=""):
    logging.debug(f"Displaying event card for event: {event.get('title')} (id={event.get('postgres_id') or event.get('id')}) for user {user_id}")
    title = event.get('title', 'Unknown Event')
    description = event.get('description', 'No description available')
    category = event.get('category', 'General')
    location = event.get('location', 'Location TBD')
    event_date = event.get('event_date', 'Date TBD')
    event_time = event.get('event_time', 'Time TBD')
    organizer = event.get('organizer', 'Unknown Organizer')
    # Map Weaviate event to Postgres event_id
    event_id = get_postgres_event_id(title, event_date)
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
                already_registered = is_user_registered(user_id, event_id)
                if already_registered:
                    st.success("✅ Registered")
                    if st.button("Cancel Registration", key=f"cancel_{event_id}{key_suffix}", type="secondary", use_container_width=True):
                        if cancel_registration(user_id, event_id):
                            st.success("❌ Registration cancelled")
                            st.rerun()
                        else:
                            st.error("Failed to cancel registration")
                else:
                    if st.button("📝 Register", key=f"register_{event_id}{key_suffix}", type="primary", use_container_width=True):
                        if register_for_event(user_id, event_id):
                            st.success("🎉 Registration successful! You'll receive a confirmation email.")
                            st.rerun()
                        else:
                            st.error("Registration failed. You may already be registered.")
            elif user_id and not event_id:
                st.warning("Registration not available: Event not found in database.")
            else:
                st.info("Login to register")
        st.markdown("---")


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
def create_user(username, password):
    logging.debug(f"Creating user: {username}")
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (username, password)
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
    logging.debug(f"Authenticating user: {username}")
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM users WHERE username=%s AND password=%s",
        (username, password)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user is not None

# -------------------- Chatbot Config --------------------
OPENAI_API_KEY = os.getenv("OPENAI_APIKEY")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8085")

client = OpenAI(api_key=OPENAI_API_KEY)

# -------------------- Chatbot Functions --------------------
def extract_interests(user_message):
    logging.debug(f"Extracting interests from user message: {user_message}")
    system_prompt = """
    Extract up to 5 interests, date/time constraints, and optional locations from the text.
    Output valid JSON only with keys: tags, date_constraints, location_constraints.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        temperature=0
    )
    content = resp.choices[0].message.content
    try:
        return json.loads(content)
    except:
        return {"tags": [], "date_constraints": [], "location_constraints": []}
    
def merge_interests(existing, new):
    logging.debug(f"Merging interests: existing={existing}, new={new}")
    for key in ["tags", "date_constraints", "location_constraints"]:
        for val in new.get(key, []):
            if val not in existing[key]:
                existing[key].append(val)
    return existing

def user_asked_for_events(user_input, interests):
    logging.debug(f"Checking if user asked for events: input={user_input}, interests={interests}")
    # Only check for explicit event requests in user input
    event_keywords = ["event", "party", "session", "conference", "seminar", "concert", "meeting", "match", "workshop", "show me", "find", "recommend", "looking for"]
    user_asked_explicitly = any(word in user_input.lower() for word in event_keywords)
    
    # Check if user has specified interests/constraints that indicate they want events
    has_specific_interests = bool(interests.get("tags") or interests.get("date_constraints") or interests.get("location_constraints"))
    
    result = user_asked_explicitly or has_specific_interests
    logging.debug(f"User asked for events: {result} (explicit={user_asked_explicitly}, has_interests={has_specific_interests})")
    return result

def query_weaviate(query: str, limit: int = 5, weaviate_url: str = WEAVIATE_URL):
    logging.debug(f"Querying Weaviate with query='{query}', limit={limit}, url={weaviate_url}")
    if query.strip():
        gql = {"query": f"""{{ Get {{ Event(nearText: {{concepts: ["{query}"]}}, limit: {limit}) {{ title description category location organizer event_date event_time _additional {{ id }} }} }} }}"""}
    else:
        gql = {"query": f"""{{ Get {{ Event(limit: {limit}) {{ title description category location organizer event_date event_time _additional {{ id }} }} }} }}"""}

    try:
        r = requests.post(f"{weaviate_url}/v1/graphql", json=gql, timeout=10)
        r.raise_for_status()
        events = r.json().get("data", {}).get("Get", {}).get("Event", [])
        
        # Add the Weaviate ID as postgres_id for registration compatibility
        for event in events:
            if "_additional" in event and "id" in event["_additional"]:
                event["postgres_id"] = event["_additional"]["id"]
        
        logging.debug(f"Processed events with IDs: {[e.get('postgres_id') for e in events]}")
        return events
    except Exception as e:
        st.error(f"Weaviate error: {e}")
        return []

def generate_reply(user_input, events, interests, history):
    logging.debug(f"Generating reply for user_input={user_input}, events={len(events)} events, interests={interests}")
    user_wants_events = user_asked_for_events(user_input, interests)
    # Add current date to the prompt context
    date_context = f"Today's date is {CURRENT_DATE}."
    if user_wants_events:
        if events:
            prompt = f"""
            You are a helpful campus events chatbot. 
            {date_context}
            The user asked for events and we found {len(events)} matching events.
            - Keep conversations natural and friendly. 
            - Mention that you found events and they're displayed below.
            - Don't list all event details in text since they're shown as cards.
            - Keep replies under 80 words.

            User query: {user_input}
            Found {len(events)} events: {[e.get('title') for e in events]}
            """
        else:
            prompt = f"""
            You are a helpful campus events chatbot. 
            {date_context}
            The user asked for events but we found no matching events.
            - Keep conversations natural and friendly. 
            - Suggest asking about other categories, dates, or locations.
            - Keep replies under 80 words.

            User query: {user_input}
            User interests: {interests}
            """
    else:
        prompt = f"""
        {date_context}
        The user said: "{user_input}".
        Respond naturally in a friendly chatbot style.
        Do not recommend or mention any events unless the user asked for them.
        Keep the reply short (1-2 sentences).
        """

    history_plus_prompt = history + [{"role": "user", "content": prompt}]
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=history_plus_prompt,
        temperature=0.7
    )
    return resp.choices[0].message.content

# -------------------- Authentication Page --------------------
def show_auth_page():
    logging.debug("Rendering authentication page")
    st.title("🔑 Sign Up / Log In")
    
    mode = st.radio("Select mode:", ["Log In", "Sign Up"])

    if mode == "Sign Up":
        st.subheader("Create a new account")
        with st.form("signup_form"):
            new_user = st.text_input("Username")
            new_pass = st.text_input("Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")
            signup_btn = st.form_submit_button("Sign Up")

            if signup_btn:
                if new_pass != confirm_pass:
                    st.error("⚠️ Passwords do not match")
                elif new_user.strip() == "" or new_pass.strip() == "":
                    st.error("⚠️ Please fill all fields")
                else:
                    success = create_user(new_user, new_pass)
                    if success:
                        st.success("✅ Account created successfully! Please log in.")
                    else:
                        st.error("⚠️ Username already exists")

    elif mode == "Log In":
        st.subheader("Log in to your account")
        with st.form("login_form"):
            user = st.text_input("Username")
            passwd = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Log In")

            if login_btn:
                if authenticate_user(user, passwd):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user
                    st.success(f"✅ Welcome back, {user}!")
                    st.rerun()  # This will refresh and show the chatbot
                else:
                    st.error("❌ Invalid username or password")

# -------------------- Chatbot Page --------------------
def show_chatbot_page():
    logging.debug("Rendering chatbot page")
    st.title("🎓 Campus Events Chatbot")
    
    # Show user info and logout button in sidebar
    logging.debug(f"Session state at chatbot page: {st.session_state}")
    with st.sidebar:
        st.write(f"👤 Logged in as: **{st.session_state['username']}**")
        if st.button("🚪 Log Out"):
            # Clear all session state related to authentication and chatbot
            for key in ["authenticated", "username", "history", "collected_interests", "messages"]:
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
        st.session_state.messages = []

    # Display previous messages and event cards if any
    for i, msg in enumerate(st.session_state.messages):
        logging.debug(f"Displaying chat message {i}: {msg}")
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            # If this is an assistant message and we have events for it, show event cards
            if msg["role"] == "assistant" and "events" in msg:
                user_id = None
                if st.session_state.get("username"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE username=%s", (st.session_state["username"],))
                    user = cur.fetchone()
                    cur.close()
                    conn.close()
                    user_id = user[0] if user else None
                for j, event in enumerate(msg["events"]):
                    logging.debug(f"Displaying event card for chat message {i}, event {j}: {event}")
                    display_event_card(event, user_id, key_suffix=f"_msg_{i}_{j}")

    # Handle new user input
    if user_input := st.chat_input("Ask about events..."):
        logging.info(f"User input: {user_input}")
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.session_state.history.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.markdown(user_input)

        # Extract new interests
        new_interests = extract_interests(user_input)
        st.session_state.collected_interests = merge_interests(st.session_state.collected_interests, new_interests)
        logging.debug(f"Updated collected_interests: {st.session_state.collected_interests}")

        # Only query events if user explicitly asked for them
        events = []
        user_wants_events = user_asked_for_events(user_input, new_interests)
        logging.debug(f"User wants events: {user_wants_events}")
        
        if user_wants_events:
            # Query Weaviate
            query_text = ", ".join(st.session_state.collected_interests.get("tags", []))
            logging.info(f"Querying events with: {query_text}")
            events = query_weaviate(query_text)
            logging.info(f"Events found: {len(events)} events")
        else:
            logging.info("User didn't ask for events, skipping event query")

        # Generate reply
        reply = generate_reply(user_input, events, st.session_state.collected_interests, st.session_state.history)
        logging.info(f"AI reply: {reply}")

        # Save and show assistant reply, and attach events if found
        msg = {"role": "assistant", "content": reply}
        if events:
            msg["events"] = events
        st.session_state.messages.append(msg)
        st.session_state.history.append({"role": "assistant", "content": reply})
        with st.chat_message("assistant"):
            st.markdown(reply)
            if events and user_wants_events:
                user_id = None
                if st.session_state.get("username"):
                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM users WHERE username=%s", (st.session_state["username"],))
                    user = cur.fetchone()
                    cur.close()
                    conn.close()
                    user_id = user[0] if user else None
                for j, event in enumerate(events):
                    logging.debug(f"Displaying event card for user input, event {j}: {event}")
                    display_event_card(event, user_id, key_suffix=f"_input_{j}")

# -------------------- Main App Logic --------------------
def main():
    logging.debug("Starting main app logic")
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
    
    # Route to appropriate page
    if st.session_state["authenticated"]:
        show_chatbot_page()
    else:
        show_auth_page()

if __name__ == "__main__":
    main()