"""Simplified Event Entry with Better Error Handling for Migration Issues"""

import streamlit as st
from database import DatabaseManager
from utils import (
    validate_bib_id, 
    parse_time_input,
    validate_time_input,
    display_success_message, 
    display_error_message,
    display_warning_message
)

def show_event_entry():
    """Simplified event entry interface with better error handling"""
    st.header("🏃‍♂️ Event Entry & Results")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        try:
            st.session_state.db_manager = DatabaseManager()
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            st.info("Please check your database connection and try refreshing the page.")
            return
    
    db = st.session_state.db_manager
    
    # Check if system is properly set up
    if not verify_system_setup(db):
        return
    
    show_result_entry_form(db)

def verify_system_setup(db: DatabaseManager):
    """Verify that the system is properly set up"""
    try:
        # Check if we have students
        students = db.get_all_students()
        if not students:
            st.warning("⚠️ No students found in database. Please add students first.")
            return False
        
        # Check if we have events
        events = db.get_all_events()
        if not events:
            st.warning("⚠️ No events found in database. Please add events first.")
            if st.button("Initialize Basic Events"):
                initialize_basic_events(db)
                st.rerun()
            return False
        
        return True
        
    except Exception as e:
        st.error(f"System setup verification failed: {str(e)}")
        return False

def initialize_basic_events(db: DatabaseManager):
    """Initialize basic events for testing"""
    basic_events = [
        {"name": "100m Sprint", "type": "Track", "unit": "time", "is_relay": False},
        {"name": "Long Jump", "type": "Field", "unit": "meters", "is_relay": False},
        {"name": "4x100m Relay", "type": "Track", "unit": "time", "is_relay": True},
    ]
    
    for event_info in basic_events:
        try:
            is_relay = event_info["is_relay"]
            male_points = {"1": 15, "2": 9, "3": 5, "4": 3} if is_relay else {"1": 10, "2": 6, "3": 3, "4": 1}
            female_points = {"1": 15, "2": 9, "3": 5, "4": 3} if is_relay else {"1": 10, "2": 6, "3": 3, "4": 1}
            
            db.add_event(
                event_name=event_info["name"],
                event_type=event_info["type"],
                unit=event_info["unit"],
                is_relay=is_relay,
                male_points=male_points,
                female_points=female_points
            )
        except Exception as e:
            st.error(f"Failed to add {event_info['name']}: {str(e)}")

def show_result_entry_form(db: DatabaseManager):
    """Display simplified form to record event results"""
    st.subheader("Record Event Result")

    # Student search panel
    with st.container():
        st.markdown("### 🔍 Student Search")

        bib_id_input = st.text_input(
            "Enter Bib ID",
            placeholder="Enter student's bib number",
            key="result_entry_bib"
        )

        if bib_id_input and validate_bib_id(bib_id_input):
            try:
                student_info = db.get_student_by_bib(int(bib_id_input))
                if student_info:
                    st.session_state.student_info = student_info
                else:
                    st.session_state.student_info = None
                    display_error_message(f"No student found with Bib ID {bib_id_input}")
            except Exception as e:
                display_error_message(f"Error searching for student: {str(e)}")
                st.session_state.student_info = None

    if 'student_info' in st.session_state and st.session_state.student_info:
        student_info = st.session_state.student_info
        st.success("✅ Student Found!")
        
        # Display student info with gender
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Name:** {student_info.get('first_name', '')} {student_info.get('last_name', '')}")
        with col2:
            st.info(f"**House:** {student_info.get('house', 'Unknown')}")
        with col3:
            gender = student_info.get('gender', 'Not specified')
            gender_emoji = {"Male": "👨", "Female": "👩", "Other": "🧑"}
            gender_icon = gender_emoji.get(gender, "🧑")
            st.info(f"**Gender:** {gender_icon} {gender}")
            
        if st.button("Clear Student"):
            del st.session_state.student_info
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Event Selection & Result Entry")

        # Gender competition info
        if gender in ["Male", "Female"]:
            st.info(f"**Competition:** This {gender.lower()} athlete will compete in the {gender} category for individual events.")
        
        # Event selection
        try:
            events = db.get_all_events()
            if not events:
                display_warning_message("No events available.")
                return
            
            event_options = [(event['event_name'], event) for event in events]
            selected_event_name, selected_event = st.selectbox(
                "Select Event",
                options=event_options,
                format_func=lambda x: x[0]
            )
            
            if selected_event:
                display_event_form(db, student_info, selected_event)
                
        except Exception as e:
            display_error_message(f"Error loading events: {str(e)}")

def display_event_form(db: DatabaseManager, student_info: dict, event: dict):
    """Display the form for entering event results"""
    st.write(f"**Event:** {event['event_name']}")
    st.write(f"**Type:** {event['event_type']} ({event['unit']})")
    
    # Show gender-specific competition info
    if not event.get('is_relay', False):
        gender = student_info.get('gender', 'Unknown')
        st.info(f"**Competition Category:** {gender} - This athlete will compete against other {gender.lower()} athletes")

    with st.form("result_entry_form", clear_on_submit=True):
        # Input based on event type
        if event['unit'] == 'time':
            result_input = st.text_input(
                "Time",
                placeholder="e.g., 12.34 or 1:23.45",
                help="Enter time in seconds (12.34) or minutes:seconds (1:23.45)"
            )
        else:
            result_input = st.number_input(
                "Distance (meters)",
                min_value=0.0,
                format="%.2f",
                step=0.01,
                help="Enter distance in meters"
            )

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("🏆 Submit Result", type="primary")
        with col2:
            delete_last = st.form_submit_button("🗑️ Delete Last Result")

        if delete_last:
            try:
                success = db.delete_last_result(student_info["bib_id"])
                if success:
                    display_success_message("Last result deleted successfully!")
                    st.rerun()
                else:
                    display_error_message("No results found to delete for this student.")
            except Exception as e:
                display_error_message(f"Error deleting result: {str(e)}")

        if submitted:
            try:
                # Validate and process input
                if event['unit'] == 'time':
                    if not result_input or not validate_time_input(result_input):
                        display_error_message("Please enter a valid time format (e.g., 12.34 or 1:23.45)")
                        return
                    processed_result = parse_time_input(result_input)
                else:
                    if result_input is None or result_input <= 0:
                        display_error_message("Please enter a valid distance greater than 0")
                        return
                    processed_result = float(result_input)

                # Add result to database
                success = db.add_result(
                    bib_id=student_info["bib_id"],
                    event_id=event['event_id'],
                    result_value=processed_result
                )

                if success:
                    gender = student_info.get('gender', 'Unknown')
                    display_success_message(f"Result recorded successfully for {student_info.get('first_name', '')} {student_info.get('last_name', '')} ({gender} competition)!")
                    
                    # Show what happened
                    if event.get('is_relay', False):
                        st.info("Note: This is a relay event. Individual times are recorded but teams compete together.")
                    else:
                        st.info(f"Result recorded in {gender} competition category.")
                    
                    st.rerun()
                else:
                    display_error_message("Failed to record result. Please try again.")
                    
            except Exception as e:
                display_error_message(f"Error recording result: {str(e)}")
                st.error("This might be due to database constraints. Common issues:")
                st.write("- Student may already have a result for this event")
                st.write("- Database connection issues")
                st.write("- Missing required fields")

def show_recent_results(db: DatabaseManager):
    """Show recent results for verification"""
    try:
        st.markdown("### 📊 Recent Results")
        results = db.get_all_results()
        
        if not results:
            st.info("No results recorded yet.")
            return
        
        # Show last 10 results
        recent_results = results[-10:] if len(results) > 10 else results
        
        for result in reversed(recent_results):
            try:
                student_data = result.get('students', {})
                event_data = result.get('events', {})
                
                # Handle list format from Supabase joins
                if isinstance(student_data, list):
                    student_data = student_data[0] if student_data else {}
                if isinstance(event_data, list):
                    event_data = event_data[0] if event_data else {}
                
                student_name = f"{student_data.get('first_name', 'Unknown')} {student_data.get('last_name', '')}"
                event_name = event_data.get('event_name', 'Unknown Event')
                result_value = result.get('result_value', 0)
                position = result.get('position', 'N/A')
                points = result.get('points', 0)
                
                # Format result value
                if event_data.get('unit') == 'time':
                    if result_value < 60:
                        formatted_result = f"{result_value:.2f}s"
                    else:
                        minutes = int(result_value // 60)
                        seconds = result_value % 60
                        formatted_result = f"{minutes}:{seconds:05.2f}"
                else:
                    formatted_result = f"{result_value:.2f}m"
                
                st.write(f"**{student_name}** - {event_name}: {formatted_result} (Position: {position}, Points: {points})")
                
            except Exception as e:
                st.write(f"Error displaying result: {str(e)}")
                
    except Exception as e:
        st.error(f"Error loading recent results: {str(e)}")

# Add this to the main show_event_entry function
def show_event_entry_enhanced():
    """Enhanced event entry with recent results"""
    show_event_entry()
    
    # Add recent results section
    if "db_manager" in st.session_state:
        st.markdown("---")
        show_recent_results(st.session_state.db_manager)

# For backward compatibility, keep the original function name
show_event_entry = show_event_entry_enhanced