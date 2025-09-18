"""Event Entry Page for recording results"""

import streamlit as st
from database import DatabaseManager
from config import EVENT_TYPES, EVENTS, DEFAULT_POINT_ALLOCATION
from utils import (
    validate_bib_id, 
    parse_time_input,
    display_success_message, 
    display_error_message,
    display_warning_message,
    display_info_message
)

def show_event_entry():
    """Display event entry interface"""
    st.header("🏃‍♂️ Event Entry & Results")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs
    tab1, tab2 = st.tabs(["📝 Record Results", "🎯 Manage Events"])
    
    with tab1:
        show_result_entry_form(db)
    
    with tab2:
        show_event_management(db)

def show_result_entry_form(db: DatabaseManager):
    """Display form to record event results"""
    st.subheader("Record Event Result")
    
    # Student search panel
    with st.container():
        st.markdown("### 🔍 Student Search")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            bib_id_input = st.text_input(
                "Enter Bib ID",
                placeholder="Enter student's bib number",
                key="result_entry_bib"
            )
        
        with col2:
            search_button = st.button("🔍 Search", type="primary", key="search_student_btn")
        
        # Auto-populate student details when bib ID is entered or search is clicked
        student_info = None
        if (search_button or bib_id_input) and validate_bib_id(bib_id_input):
            student_info = db.get_student_by_bib(int(bib_id_input))
        
        # Display student information
        if bib_id_input and validate_bib_id(bib_id_input):
            if student_info:
                with st.container():
                    st.success("✅ Student Found!")
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.info(f"**Name:** {student_info['first_name']} {student_info['last_name']}")
                    with col2:
                        st.info(f"**Curtin ID:** {student_info['curtin_id']}")
                    with col3:
                        st.info(f"**House:** {student_info['house']}")
            else:
                display_error_message("Student not found. Please check the Bib ID.")
                return
        elif bib_id_input and not validate_bib_id(bib_id_input):
            display_error_message("Please enter a valid Bib ID")
            return
    
    # Event selection and result entry
    if student_info:
        st.markdown("---")
        st.markdown("### 🎯 Event Selection & Result Entry")
        
        with st.form("result_entry_form"):
            # Event type selection
            col1, col2 = st.columns(2)
            
            with col1:
                event_type = st.selectbox(
                    "Select Event Type",
                    options=list(EVENT_TYPES.keys()),
                    help="Choose the type of event"
                )
            
            # Get events for selected type
            events_for_type = db.get_events_by_type(event_type)
            
            if not events_for_type:
                st.warning(f"No {event_type.lower()} events found. Please add events first.")
                return
            
            with col2:
                selected_event = st.selectbox(
                    "Select Specific Event",
                    options=events_for_type,
                    format_func=lambda x: x["event_name"],
                    help="Choose the specific event"
                )
            
            # Result input based on event type
            st.markdown("#### 📊 Enter Result")
            
            if event_type == "Running":
                col1, col2 = st.columns(2)
                with col1:
                    time_format = st.radio(
                        "Time Format",
                        options=["Seconds (SS.ss)", "Minutes:Seconds (MM:SS.ss)"],
                        key="time_format_radio"
                    )
                
                with col2:
                    if time_format.startswith("Seconds"):
                        result_input = st.number_input(
                            "Time (seconds)",
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                            help="Enter time in seconds (e.g., 12.34)"
                        )
                    else:
                        result_input = st.text_input(
                            "Time (MM:SS.ss)",
                            placeholder="e.g., 1:23.45",
                            help="Enter time in MM:SS format (e.g., 1:23.45)"
                        )
            
            else:  # Throwing or Jumping
                result_input = st.number_input(
                    f"Distance (meters)",
                    min_value=0.01,
                    step=0.01,
                    format="%.2f",
                    help=f"Enter {event_type.lower()} distance in meters"
                )
            
            # Submit button
            submitted = st.form_submit_button("🏆 Submit Result", type="primary")
            
            if submitted:
                try:
                    # Process result value
                    if event_type == "Running":
                        if time_format.startswith("Minutes"):
                            if isinstance(result_input, str):
                                result_value = parse_time_input(result_input)
                            else:
                                display_error_message("Please enter time in MM:SS format")
                                return
                        else:
                            result_value = float(result_input)
                    else:
                        result_value = float(result_input)
                    
                    # Add result to database
                    success = db.add_result(
                        curtin_id=student_info["curtin_id"],
                        event_id=selected_event["event_id"],
                        result_value=result_value
                    )
                    
                    if success:
                        display_success_message(
                            f"Result recorded for {student_info['first_name']} {student_info['last_name']} "
                            f"in {selected_event['event_name']}!"
                        )
                        st.balloons()
                        
                        # Show recent results for this event
                        show_recent_event_results(db, selected_event["event_id"])
                        
                        # Clear form
                        st.rerun()
                    
                except ValueError as e:
                    display_error_message(f"Invalid result format: {str(e)}")
                except Exception as e:
                    display_error_message(f"Error recording result: {str(e)}")

def show_event_management(db: DatabaseManager):
    """Display event management interface"""
    st.subheader("Event Management")
    
    # Add new event form
    with st.expander("➕ Add New Event", expanded=False):
        show_add_event_form(db)
    
    # Display existing events
    st.markdown("### 📋 Existing Events")
    
    all_events = db.get_all_events()
    
    if not all_events:
        display_info_message("No events created yet. Add your first event above!")
        return
    
    # Group events by type
    events_by_type = {}
    for event in all_events:
        event_type = event["event_type"]
        if event_type not in events_by_type:
            events_by_type[event_type] = []
        events_by_type[event_type].append(event)
    
    # Display events in tabs by type
    if events_by_type:
        event_tabs = st.tabs(list(events_by_type.keys()))
        
        for i, (event_type, events) in enumerate(events_by_type.items()):
            with event_tabs[i]:
                for event in events:
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.write(f"**{event['event_name']}**")
                            st.caption(f"Unit: {event['unit']}")
                        
                        with col2:
                            st.write(f"Type: {event['event_type']}")
                        
                        with col3:
                            st.write(f"ID: {event['event_id']}")
                        
                        st.markdown("---")

def show_add_event_form(db: DatabaseManager):
    """Display form to add new events"""
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_type = st.selectbox(
                "Event Type",
                options=list(EVENT_TYPES.keys())
            )
            
            # Suggest events based on type
            suggested_events = EVENTS.get(event_type, [])
            event_suggestions = [event["name"] for event in suggested_events]
            
            event_name = st.selectbox(
                "Event Name",
                options=["Custom"] + event_suggestions,
                help="Select a standard event or choose 'Custom' to create your own"
            )
            
            if event_name == "Custom":
                custom_event_name = st.text_input(
                    "Custom Event Name",
                    placeholder="Enter custom event name"
                )
                event_name = custom_event_name
        
        with col2:
            # Unit is determined by event type
            unit = EVENT_TYPES[event_type]
            if event_type == "Running":
                display_unit = "seconds/minutes"
            else:
                display_unit = "meters"
            
            st.text_input(
                "Unit",
                value=display_unit,
                disabled=True,
                help="Unit is automatically set based on event type"
            )
            
            # Point allocation (optional customization)
            use_custom_points = st.checkbox(
                "Use custom point allocation",
                help="Check to customize point allocation for this event"
            )
        
        if use_custom_points:
            st.markdown("#### Point Allocation")
            st.info("Customize points for each position (leave empty to use default)")
            
            point_cols = st.columns(4)
            custom_points = {}
            
            for i in range(1, 9):  # Positions 1-8
                col_idx = (i - 1) % 4
                with point_cols[col_idx]:
                    points = st.number_input(
                        f"{i}{'st' if i==1 else 'nd' if i==2 else 'rd' if i==3 else 'th'} place",
                        min_value=0,
                        value=DEFAULT_POINT_ALLOCATION.get(i, 0),
                        key=f"points_{i}"
                    )
                    if points > 0:
                        custom_points[str(i)] = points
        
        submitted = st.form_submit_button("Add Event", type="primary")
        
        if submitted:
            if not event_name or (event_name == "Custom" and not custom_event_name):
                display_error_message("Please enter an event name")
                return
            
            # Prepare point allocation
            points_allocation = custom_points if use_custom_points else DEFAULT_POINT_ALLOCATION
            
            success = db.add_event(
                event_name=event_name,
                event_type=event_type,
                unit=display_unit,
                point_allocation=points_allocation
            )
            
            if success:
                display_success_message(f"Event '{event_name}' added successfully!")
                st.rerun()

def show_recent_event_results(db: DatabaseManager, event_id: int):
    """Show recent results for the event"""
    st.markdown("#### 🏆 Current Rankings")
    
    results = db.get_results_by_event(event_id)
    
    if results:
        for i, result in enumerate(results[:5]):  # Show top 5
            student = result["students"]
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            
            st.write(
                f"{medal} {student['first_name']} {student['last_name']} "
                f"({student['house']}) - {result['result_value']:.2f} - {result['points']} pts"
            )