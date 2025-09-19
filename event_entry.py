"""Enhanced Event Entry Page with improved time handling and point systems"""

import streamlit as st
from database import DatabaseManager
from config import (
    EVENT_TYPES, EVENTS, POINT_SYSTEM_TEMPLATES, 
    DEFAULT_INDIVIDUAL_POINTS, DEFAULT_RELAY_POINTS
)
from utils import (
    validate_bib_id, 
    parse_time_input,
    validate_time_input,
    validate_distance_input,
    display_success_message, 
    display_error_message,
    display_warning_message,
    display_info_message,
    get_time_input_placeholder,
    is_relay_event
)

def show_event_entry():
    """Display enhanced event entry interface"""
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
    """Display enhanced form to record event results"""
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
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.info(f"**Name:** {student_info['first_name']} {student_info['last_name']}")
                    with col2:
                        st.info(f"**Curtin ID:** {student_info['curtin_id']}")
                    with col3:
                        st.info(f"**House:** {student_info['house']}")
                    with col4:
                        st.info(f"**Gender:** {student_info.get('gender', 'Not specified')}")
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
                    help="Track events use time, Field events use distance"
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
                    format_func=lambda x: f"{x['event_name']} ({'Relay' if x.get('is_relay') else 'Individual'})",
                    help="Choose the specific event"
                )
            
            # Result input based on event type
            st.markdown("#### 📊 Enter Result")
            
            if event_type == "Track":
                # Track events - time input
                col1, col2 = st.columns(2)
                
                with col1:
                    # Show appropriate input method based on event
                    event_name = selected_event['event_name']
                    is_sprint = any(distance in event_name for distance in ['100m', '200m', '400m'])
                    
                    if is_sprint:
                        st.info("Sprint Event: Enter time in seconds")
                        result_input = st.number_input(
                            "Time (seconds)",
                            min_value=0.01,
                            step=0.01,
                            format="%.2f",
                            help="Enter time in seconds (e.g., 12.34)"
                        )
                        result_value = result_input
                    else:
                        st.info("Distance Event: Enter time in MM:SS.ms format")
                        time_input = st.text_input(
                            "Time (MM:SS.ms)",
                            placeholder=get_time_input_placeholder(event_name),
                            help="Enter time in MM:SS.ms format (e.g., 1:23.45)"
                        )
                        
                        if time_input and not validate_time_input(time_input):
                            st.error("Invalid time format. Use MM:SS.ms (e.g., 1:23.45)")
                        
                        result_value = time_input
                
                with col2:
                    # Display event info
                    st.metric("Event Type", event_type)
                    st.metric("Measurement", "Time")
                    if selected_event.get('is_relay'):
                        st.success("🔗 Relay Event")
                    
            else:  # Field events - distance input
                col1, col2 = st.columns(2)
                
                with col1:
                    result_input = st.number_input(
                        "Distance/Height (meters)",
                        min_value=0.01,
                        step=0.01,
                        format="%.2f",
                        help="Enter distance or height in meters"
                    )
                    result_value = result_input
                
                with col2:
                    st.metric("Event Type", event_type)
                    st.metric("Measurement", "Meters")
                    
            # Display point system info
            st.markdown("#### 🏆 Point System Information")
            point_system = selected_event.get('point_system_name', 'Individual Events')
            point_allocation = selected_event.get('point_allocation', DEFAULT_INDIVIDUAL_POINTS)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Point System:** {point_system}")
            with col2:
                # Show top 3 point values
                sorted_points = sorted([(int(k), v) for k, v in point_allocation.items()])
                if len(sorted_points) >= 3:
                    st.info(f"**Points:** 1st:{sorted_points[0][1]}, 2nd:{sorted_points[1][1]}, 3rd:{sorted_points[2][1]}")
            
            # Submit button
            submitted = st.form_submit_button("🏆 Submit Result", type="primary")
            
            if submitted:
                try:
                    # Process result value based on event type
                    if event_type == "Track":
                        if isinstance(result_value, str):  # MM:SS format
                            if not result_value:
                                display_error_message("Please enter a time")
                                return
                            processed_result = parse_time_input(result_value)
                        else:  # Seconds format
                            processed_result = float(result_value)
                    else:  # Field events
                        if result_value <= 0:
                            display_error_message("Please enter a valid distance/height")
                            return
                        processed_result = float(result_value)
                    
                    # Add result to database
                    success = db.add_result(
                        curtin_id=student_info["curtin_id"],
                        event_id=selected_event["event_id"],
                        result_value=processed_result
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
    """Display enhanced event management interface"""
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
                        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
                        
                        with col1:
                            relay_badge = " 🔗" if event.get('is_relay') else ""
                            st.write(f"**{event['event_name']}{relay_badge}**")
                            st.caption(f"Unit: {event['unit']}")
                        
                        with col2:
                            st.write(f"Type: {event['event_type']}")
                            if event.get('is_relay'):
                                st.caption("Relay")
                        
                        with col3:
                            point_system = event.get('point_system_name', 'Individual')
                            st.write(f"Points: {point_system}")
                        
                        with col4:
                            st.write(f"ID: {event['event_id']}")
                        
                        st.markdown("---")

def show_add_event_form(db: DatabaseManager):
    """Display enhanced form to add new events with point systems"""
    with st.form("add_event_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            event_type = st.selectbox(
                "Event Type",
                options=list(EVENT_TYPES.keys()),
                help="Track events use time, Field events use distance/height"
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
            
            # Check if it's a relay event
            is_relay = is_relay_event(event_name) if event_name != "Custom" else False
            is_relay = st.checkbox(
                "Relay Event",
                value=is_relay,
                help="Relay events typically have higher point allocations"
            )
        
        with col2:
            # Unit is determined by event type
            unit = EVENT_TYPES[event_type]
            display_unit = "time" if event_type == "Track" else "meters"
            
            st.text_input(
                "Unit",
                value=display_unit,
                disabled=True,
                help="Unit is automatically set based on event type"
            )
            
            # Point system selection
            default_system = "Relay Events" if is_relay else "Individual Events"
            point_system_name = st.selectbox(
                "Point System",
                options=list(POINT_SYSTEM_TEMPLATES.keys()),
                index=list(POINT_SYSTEM_TEMPLATES.keys()).index(default_system),
                help="Choose a point allocation system"
            )
        
        # Show and allow customization of point allocation
        st.markdown("#### 🏆 Point Allocation")
        
        selected_template = POINT_SYSTEM_TEMPLATES[point_system_name]
        
        if point_system_name == "Custom":
            st.info("Create your own point allocation system")
            custom_points = {}
            
            point_cols = st.columns(4)
            for i in range(1, 9):  # Positions 1-8
                col_idx = (i - 1) % 4
                with point_cols[col_idx]:
                    points = st.number_input(
                        f"{i}{'st' if i==1 else 'nd' if i==2 else 'rd' if i==3 else 'th'} place",
                        min_value=0,
                        value=0,
                        key=f"custom_points_{i}"
                    )
                    if points > 0:
                        custom_points[i] = points
            
            point_allocation = custom_points
        else:
            # Show current template and allow modifications
            st.info(f"Using {point_system_name} template. Modify if needed:")
            
            point_allocation = {}
            point_cols = st.columns(4)
            
            for i in range(1, 9):  # Positions 1-8
                col_idx = (i - 1) % 4
                default_value = selected_template.get(i, 0)
                
                with point_cols[col_idx]:
                    points = st.number_input(
                        f"{i}{'st' if i==1 else 'nd' if i==2 else 'rd' if i==3 else 'th'} place",
                        min_value=0,
                        value=default_value,
                        key=f"template_points_{i}"
                    )
                    if points > 0:
                        point_allocation[i] = points
        
        submitted = st.form_submit_button("Add Event", type="primary")
        
        if submitted:
            if not event_name or (event_name == "Custom" and not custom_event_name):
                display_error_message("Please enter an event name")
                return
            
            if not point_allocation:
                display_error_message("Please set at least one position's points")
                return
            
            success = db.add_event(
                event_name=event_name,
                event_type=event_type,
                unit=display_unit,
                is_relay=is_relay,
                point_allocation=point_allocation,
                point_system_name=point_system_name
            )
            
            if success:
                display_success_message(f"Event '{event_name}' added successfully with {point_system_name} point system!")
                st.rerun()

def show_recent_event_results(db: DatabaseManager, event_id: int):
    """Show recent results for the event with enhanced formatting"""
    st.markdown("#### 🏆 Current Rankings")
    
    results = db.get_results_by_event(event_id)
    
    if results:
        for i, result in enumerate(results[:5]):  # Show top 5
            student = result["students"]
            event = result["events"]
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"{i+1}."
            
            # Format result value
            from utils import format_result_value
            formatted_result = format_result_value(result['result_value'], event['event_type'])
            
            st.write(
                f"{medal} {student['first_name']} {student['last_name']} "
                f"({student['house']}) - {formatted_result} - {result['points']} pts"
            )