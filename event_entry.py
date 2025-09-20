import streamlit as st
from database import DatabaseManager
import json
from utils import (
    validate_bib_id, 
    parse_time_input,
    validate_time_input,
    display_success_message, 
    display_error_message,
    get_time_input_placeholder
)

def load_events_from_json():
    with open('points.json', 'r') as f:
        return json.load(f)

EVENTS = load_events_from_json()

def show_event_entry():
    """Display enhanced event entry interface"""
    st.header("🏃‍♂️ Event Entry & Results")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    show_result_entry_form(db)

def show_result_entry_form(db: DatabaseManager):
    """Display enhanced form to record event results"""
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
            if 'student_info' not in st.session_state or st.session_state.student_info['bib_id'] != int(bib_id_input):
                student_info = db.get_student_by_bib(int(bib_id_input))
                if student_info:
                    st.session_state.student_info = student_info
                else:
                    st.session_state.student_info = None

    if 'student_info' in st.session_state and st.session_state.student_info:
        student_info = st.session_state.student_info
        st.success("✅ Student Found!")
        st.info(f"**Name:** {student_info.get('first_name', '')} {student_info.get('last_name', '')}")
        if st.button("Clear Student"):
            del st.session_state.student_info
            st.rerun()

        st.markdown("---")
        st.markdown("### 🎯 Event Selection & Result Entry")

        event_options = [event['name'] for event_type in EVENTS.values() for event in event_type]
        selected_event_name = st.selectbox("Select Event", event_options)

        if st.button("Enter", key="enter_event_btn"):
            st.session_state.selected_event_name = selected_event_name

        if 'selected_event_name' in st.session_state and st.session_state.selected_event_name:
            event_name = st.session_state.selected_event_name
            event_details = None
            for event_type in EVENTS.values():
                for event in event_type:
                    if event['name'] == event_name:
                        event_details = event
                        break
                if event_details:
                    break

            if event_details:
                st.write(f"**Event:** {event_details['name']}")
                st.write(f"**Unit:** {event_details['unit']}")

                with st.form("result_entry_form"):
                    if event_details['unit'] == 'time':
                        time_input = st.text_input(
                            "Time",
                            placeholder=get_time_input_placeholder(event_details['name']),
                            help="Formats: MM:SS.ms, SS.ms, or seconds"
                        )
                        result_value = time_input
                    else:
                        distance_input = st.number_input(
                            "Distance (meters)",
                            min_value=0.0,
                            format="%.2f",
                            step=0.01
                        )
                        result_value = distance_input

                    submitted = st.form_submit_button("🏆 Submit Result")
                    if st.form_submit_button("🗑️ Delete Last Result"):
                        success = db.delete_last_result(student_info["curtin_id"])
                        if success:
                            display_success_message("Last result deleted successfully!")

                    if submitted:
                        if event_details['unit'] == 'time':
                            if not result_value or not validate_time_input(result_value):
                                display_error_message("Invalid time format.")
                                return
                            processed_result = parse_time_input(result_value)
                        else:
                            if result_value <= 0:
                                display_error_message("Invalid distance.")
                                return
                            processed_result = float(result_value)

                        event_from_db = db.get_event_by_name(event_name)
                        if not event_from_db:
                            display_error_message("Event not found in database.")
                            return

                        success = db.add_result(
                            curtin_id=student_info["curtin_id"],
                            event_id=event_from_db['event_id'],
                            result_value=processed_result,
                            house=student_info['house']
                        )

                        if success:
                            display_success_message("Result recorded successfully!")
                            if 'selected_event_name' in st.session_state:
                                del st.session_state.selected_event_name
                            st.rerun()