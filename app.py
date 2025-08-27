import streamlit as st
import psycopg2
import pandas as pd
import os
from datetime import datetime, date, time
from typing import Optional, List, Tuple

# Database connection configuration
def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 5432)),
        "database": os.getenv("DB_NAME", "event_management"),
        "user": os.getenv("DB_USER", "eventuser"),
        "password": os.getenv("DB_PASSWORD", "eventpass123")
    }

@st.cache_resource
def get_connection():
    """Create and cache database connection"""
    try:
        config = get_db_config()
        conn = psycopg2.connect(**config)
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

def add_event(title: str, description: str, category: str, location: str, event_date: date, event_time: time, organizer: str) -> bool:
    """Add a new event to the database"""
    config = get_db_config()
    conn = None
    try:
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        query = """
            INSERT INTO events (title, description, category, location, event_date, event_time, organizer)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query, (title, description, category, location, event_date, event_time, organizer))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Error adding event: {e}")
        if conn and not conn.closed:
            conn.rollback()
            conn.close()
        return False

def get_all_events() -> Optional[pd.DataFrame]:
    """Retrieve all events from the database"""
    conn = get_connection()
    if conn:
        try:
            query = """
                SELECT id, title, description, category, location, event_date, event_time, organizer, created_at
                FROM events
                ORDER BY event_date, event_time
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error retrieving events: {e}")
            return None
    return None

def update_event(event_id: int, title: str, description: str, category: str, location: str, event_date: date, event_time: time, organizer: str) -> bool:
    """Update an existing event"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            query = """
                UPDATE events 
                SET title = %s, description = %s, category = %s, location = %s, 
                    event_date = %s, event_time = %s, organizer = %s
                WHERE id = %s
            """
            cursor.execute(query, (title, description, category, location, event_date, event_time, organizer, event_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error updating event: {e}")
            conn.rollback()
            return False
    return False

def delete_event(event_id: int) -> bool:
    """Delete an event from the database"""
    conn = get_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error deleting event: {e}")
            conn.rollback()
            return False
    return False

def main():
    st.set_page_config(page_title="Event Management System", page_icon="📅", layout="wide")
    
    st.title("📅 Event Management System")
    st.markdown("---")
    
    # Sidebar menu
    st.sidebar.title("Menu")
    menu_option = st.sidebar.radio(
        "Select an option:",
        ["Add Event", "View Events", "Update Event", "Delete Event"]
    )
    
    if menu_option == "Add Event":
        st.header("Add New Event")
        
        with st.form("add_event_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                title = st.text_input("Title*", placeholder="Enter event title")
                category = st.text_input("Category", placeholder="e.g., Conference, Workshop, Meeting")
                event_date = st.date_input("Date*", value=datetime.now().date())
                organizer = st.text_input("Organizer", placeholder="Event organizer name")
            
            with col2:
                location = st.text_input("Location", placeholder="Event location")
                event_time = st.time_input("Time*", value=time(9, 0))
            
            description = st.text_area("Description", placeholder="Event description (optional)")
            
            submitted = st.form_submit_button("Add Event", type="primary")
            
            if submitted:
                if title and event_date and event_time:
                    if add_event(title, description, category, location, event_date, event_time, organizer):
                        st.success("✅ Event added successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to add event. Please try again.")
                else:
                    st.error("❌ Please fill in all required fields (marked with *)")
    
    elif menu_option == "View Events":
        st.header("All Events")
        
        events_df = get_all_events()
        if events_df is not None and not events_df.empty:
            # Add filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                categories = ['All'] + list(events_df['category'].dropna().unique())
                selected_category = st.selectbox("Filter by Category", categories)
            
            with col2:
                date_filter = st.date_input("Filter by Date (optional)")
            
            with col3:
                search_term = st.text_input("Search in Title/Description")
            
            # Apply filters
            filtered_df = events_df.copy()
            
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['category'] == selected_category]
            
            if search_term:
                mask = (
                    filtered_df['title'].str.contains(search_term, case=False, na=False) |
                    filtered_df['description'].str.contains(search_term, case=False, na=False)
                )
                filtered_df = filtered_df[mask]
            
            st.markdown(f"**Total Events:** {len(filtered_df)}")
            
            # Display events
            for _, event in filtered_df.iterrows():
                with st.expander(f"📅 {event['title']} - {event['event_date']} at {event['event_time']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**Category:** {event['category'] or 'N/A'}")
                        st.write(f"**Location:** {event['location'] or 'N/A'}")
                        st.write(f"**Organizer:** {event['organizer'] or 'N/A'}")
                    
                    with col2:
                        st.write(f"**Date:** {event['event_date']}")
                        st.write(f"**Time:** {event['event_time']}")
                        st.write(f"**Created:** {event['created_at'].strftime('%Y-%m-%d %H:%M')}")
                    
                    if event['description']:
                        st.write(f"**Description:** {event['description']}")
        else:
            st.info("No events found. Add some events to get started!")
    
    elif menu_option == "Update Event":
        st.header("Update Event")
        
        events_df = get_all_events()
        if events_df is not None and not events_df.empty:
            # Select event to update
            event_options = [f"{row['title']} - {row['event_date']}" for _, row in events_df.iterrows()]
            selected_event = st.selectbox("Select Event to Update", event_options)
            
            if selected_event:
                event_index = event_options.index(selected_event)
                event = events_df.iloc[event_index]
                
                with st.form("update_event_form"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        title = st.text_input("Title*", value=event['title'])
                        category = st.text_input("Category", value=event['category'] or '')
                        event_date = st.date_input("Date*", value=pd.to_datetime(event['event_date']).date())
                        organizer = st.text_input("Organizer", value=event['organizer'] or '')
                    
                    with col2:
                        location = st.text_input("Location", value=event['location'] or '')
                        event_time = st.time_input("Time*", value=pd.to_datetime(event['event_time'], format='%H:%M:%S').time())
                    
                    description = st.text_area("Description", value=event['description'] or '')
                    
                    updated = st.form_submit_button("Update Event", type="primary")
                    
                    if updated:
                        if title and event_date and event_time:
                            if update_event(event['id'], title, description, category, location, event_date, event_time, organizer):
                                st.success("✅ Event updated successfully!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to update event. Please try again.")
                        else:
                            st.error("❌ Please fill in all required fields (marked with *)")
        else:
            st.info("No events available to update.")
    
    elif menu_option == "Delete Event":
        st.header("Delete Event")
        
        events_df = get_all_events()
        if events_df is not None and not events_df.empty:
            # Select event to delete
            event_options = [f"{row['title']} - {row['event_date']}" for _, row in events_df.iterrows()]
            selected_event = st.selectbox("Select Event to Delete", event_options)
            
            if selected_event:
                event_index = event_options.index(selected_event)
                event = events_df.iloc[event_index]
                
                st.warning(f"Are you sure you want to delete: **{event['title']}**?")
                st.write(f"Date: {event['event_date']}")
                st.write(f"Time: {event['event_time']}")
                
                if st.button("🗑️ Delete Event", type="secondary"):
                    if delete_event(event['id']):
                        st.success("✅ Event deleted successfully!")
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete event. Please try again.")
        else:
            st.info("No events available to delete.")

if __name__ == "__main__":
    main()