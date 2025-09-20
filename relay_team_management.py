"""
Updated Relay Team Management Interface - Using Bib ID as Primary Key
"""

import streamlit as st
from database import DatabaseManager
from config import HOUSES
from utils import (
    validate_time_input, 
    parse_time_input,
    validate_bib_id,
    display_success_message, 
    display_error_message,
    display_warning_message
)
import pandas as pd

def show_relay_team_management():
    """Display relay team management interface using bib IDs"""
    st.header("🏃‍♂️🏃‍♀️ Relay Team Management")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Gender-mixed relay info
    st.info("**Relay Team Rules:** Teams can be mixed-gender and compete together in a single category. All relay events use the same point system (1st=15pts, 2nd=9pts, 3rd=5pts, 4th=3pts)")
    
    # Create tabs for different relay operations
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Register Team", "🎯 Record Results", "📊 Team Results", "🏆 Relay Standings"])
    
    with tab1:
        show_relay_team_registration(db)
    
    with tab2:
        show_relay_result_entry(db)
    
    with tab3:
        show_relay_team_results(db)
    
    with tab4:
        show_relay_standings(db)

def show_relay_team_registration(db: DatabaseManager):
    """Display form to register relay teams using bib IDs"""
    st.subheader("Register Relay Team")
    
    # Get relay events
    relay_events = [event for event in db.get_all_events() if event.get('is_relay', False)]
    
    if not relay_events:
        display_warning_message("No relay events found. Please add relay events first.")
        return
    
    with st.form("relay_team_registration"):
        col1, col2 = st.columns(2)
        
        with col1:
            team_name = st.text_input(
                "Team Name",
                placeholder="e.g., Ignis Lightning",
                help="Enter a name for your relay team"
            )
            
            house = st.selectbox(
                "House",
                options=HOUSES,
                help="Select the house this team represents"
            )
            
            event = st.selectbox(
                "Relay Event",
                options=relay_events,
                format_func=lambda x: x['event_name'],
                help="Select which relay event this team will compete in"
            )
        
        with col2:
            st.markdown("#### Team Members")
            st.markdown("*Enter Bib IDs for each team member*")
            
            member1_bib = st.text_input("Member 1 Bib ID", placeholder="101")
            member2_bib = st.text_input("Member 2 Bib ID", placeholder="102")
            member3_bib = st.text_input("Member 3 Bib ID", placeholder="103")
            member4_bib = st.text_input("Member 4 Bib ID", placeholder="104")
        
        # Member validation area
        if member1_bib or member2_bib or member3_bib or member4_bib:
            st.markdown("#### Member Validation")
            member_bibs = [member1_bib, member2_bib, member3_bib, member4_bib]
            valid_members = []
            
            for i, bib in enumerate(member_bibs, 1):
                if bib and validate_bib_id(bib):
                    student = db.get_student_by_bib(int(bib))
                    if student:
                        gender_icon = {"Male": "👨", "Female": "👩", "Other": "🧑"}.get(student.get('gender'), "🧑")
                        st.success(f"Member {i}: {student['first_name']} {student['last_name']} ({gender_icon} {student.get('gender', 'Unknown')}) - {student['house']} House")
                        valid_members.append(student)
                    else:
                        st.error(f"Member {i}: No student found with Bib ID {bib}")
                elif bib:
                    st.error(f"Member {i}: Invalid Bib ID format")
            
            # Check house consistency
            if len(valid_members) > 1:
                houses = set(member['house'] for member in valid_members)
                if len(houses) > 1:
                    st.error("⚠️ All team members must be from the same house!")
                elif len(houses) == 1 and list(houses)[0] != house:
                    st.warning(f"Team house ({house}) doesn't match member houses ({list(houses)[0]})")
        
        submitted = st.form_submit_button("🏃‍♂️ Register Relay Team", type="primary")
        
        if submitted:
            # Validate inputs
            errors = []
            
            if not team_name.strip():
                errors.append("Please enter a team name")
            
            member_bibs = [member1_bib, member2_bib, member3_bib, member4_bib]
            
            # Validate all member Bib IDs
            valid_bib_ids = []
            for i, bib in enumerate(member_bibs, 1):
                if not bib.strip():
                    errors.append(f"Please enter Bib ID for Member {i}")
                elif not validate_bib_id(bib):
                    errors.append(f"Invalid Bib ID format for Member {i}")
                else:
                    # Check if student exists
                    student = db.get_student_by_bib(int(bib))
                    if not student:
                        errors.append(f"No student found with Bib ID {bib}")
                    elif student['house'] != house:
                        errors.append(f"Member {i} ({student['first_name']} {student['last_name']}) is not in {house} House")
                    else:
                        valid_bib_ids.append(int(bib))
            
            # Check for duplicate members
            if len(set(valid_bib_ids)) != 4:
                errors.append("All team members must be different students")
            
            if errors:
                for error in errors:
                    display_error_message(error)
            else:
                # Register the team with bib IDs
                success = db.add_relay_team(
                    team_name=team_name.strip(),
                    house=house,
                    event_id=event['event_id'],
                    member1_bib=int(member1_bib),
                    member2_bib=int(member2_bib),
                    member3_bib=int(member3_bib),
                    member4_bib=int(member4_bib)
                )
                
                if success:
                    display_success_message(f"Relay team '{team_name}' registered successfully!")
                    st.balloons()
                    st.rerun()

def show_relay_result_entry(db: DatabaseManager):
    """Display form to record relay team results"""
    st.subheader("Record Relay Team Result")
    
    # Get all relay events
    relay_events = [event for event in db.get_all_events() if event.get('is_relay', False)]
    
    if not relay_events:
        display_warning_message("No relay events found.")
        return
    
    # Event selector
    selected_event = st.selectbox(
        "Select Relay Event",
        options=relay_events,
        format_func=lambda x: x['event_name']
    )
    
    if selected_event:
        # Get teams for this event
        teams = db.get_relay_teams_by_event(selected_event['event_id'])
        
        if not teams:
            display_warning_message("No teams registered for this event.")
            return
        
        # Team selector
        selected_team = st.selectbox(
            "Select Team",
            options=teams,
            format_func=lambda x: f"{x.get('team_name', 'Unknown')} ({x.get('house', 'Unknown')} House)"
        )
        
        if selected_team:
            with st.form("relay_result_entry"):
                st.markdown(f"### Recording result for: **{selected_team.get('team_name', 'Unknown')}**")
                
                # Show team members with their details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Team Members:**")
                    # Try to get member details by bib ID
                    for i in range(1, 5):
                        bib_key = f'member{i}_bib_id'
                        name_key = f'member{i}_name'
                        
                        if bib_key in selected_team and selected_team[bib_key]:
                            member_bib = selected_team[bib_key]
                            member_name = selected_team.get(name_key, 'Loading...')
                            
                            # Get additional member info
                            member_info = db.get_student_by_bib(member_bib)
                            if member_info:
                                gender_icon = {"Male": "👨", "Female": "👩", "Other": "🧑"}.get(member_info.get('gender'), "🧑")
                                st.write(f"{i}. {member_name} (Bib #{member_bib}) {gender_icon}")
                        else:
                            st.write(f"{i}. Member info loading...")
                
                with col2:
                    st.markdown("**House & Event:**")
                    st.write(f"House: {selected_team.get('house', 'Unknown')}")
                    st.write(f"Event: {selected_event['event_name']}")
                
                # Time input
                time_input = st.text_input(
                    "Team Time",
                    placeholder="e.g., 45.23 or 1:45.23",
                    help="Enter the relay team's finish time"
                )
                
                submitted = st.form_submit_button("🏆 Submit Relay Result", type="primary")
                
                if submitted:
                    if not time_input or not validate_time_input(time_input):
                        display_error_message("Please enter a valid time format")
                    else:
                        try:
                            result_value = parse_time_input(time_input)
                            success = db.add_relay_team_result(
                                team_id=selected_team['team_id'],
                                result_value=result_value
                            )
                            
                            if success:
                                display_success_message("Relay result recorded successfully!")
                                st.rerun()
                        except ValueError as e:
                            display_error_message(f"Invalid time format: {str(e)}")

def show_relay_team_results(db: DatabaseManager):
    """Display relay team results by event"""
    st.subheader("Relay Team Results")
    
    # Get all relay events
    relay_events = [event for event in db.get_all_events() if event.get('is_relay', False)]
    
    if not relay_events:
        display_warning_message("No relay events found.")
        return
    
    # Event selector
    selected_event = st.selectbox(
        "Select Event to View Results",
        options=relay_events,
        format_func=lambda x: x['event_name']
    )
    
    if selected_event:
        # Get results for this event
        teams = db.get_relay_teams_by_event(selected_event['event_id'])
        
        if not teams:
            display_warning_message("No results available for this event.")
            return
        
        # Display results in a table
        results_data = []
        for team in teams:
            if team.get('result_value'):  # Only show teams with results
                # Build member list
                member_names = []
                for i in range(1, 5):
                    name_key = f'member{i}_name'
                    bib_key = f'member{i}_bib_id'
                    
                    if name_key in team:
                        member_name = team[name_key]
                    elif bib_key in team and team[bib_key]:
                        # Fallback: get name from bib ID
                        member_info = db.get_student_by_bib(team[bib_key])
                        member_name = f"{member_info['first_name']} {member_info['last_name']}" if member_info else f"Bib #{team[bib_key]}"
                    else:
                        member_name = "Unknown"
                    
                    member_names.append(member_name)
                
                results_data.append({
                    "Position": team.get('position', 'N/A'),
                    "Team Name": team.get('team_name', 'Unknown'),
                    "House": team.get('house', 'Unknown'),
                    "Time": f"{team.get('result_value', 0):.2f}s",
                    "Points": team.get('points', 0),
                    "Members": " | ".join(member_names)
                })
        
        if results_data:
            df = pd.DataFrame(results_data)
            
            # Style the dataframe
            def highlight_positions(row):
                pos = row["Position"]
                if pos == 1:
                    return ['background-color: #FFD700; font-weight: bold'] * len(row)  # Gold
                elif pos == 2:
                    return ['background-color: #C0C0C0; font-weight: bold'] * len(row)  # Silver
                elif pos == 3:
                    return ['background-color: #CD7F32; font-weight: bold'] * len(row)  # Bronze
                else:
                    return [''] * len(row)
            
            styled_df = df.style.apply(highlight_positions, axis=1)
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Export option
            csv_data = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results",
                data=csv_data,
                file_name=f"{selected_event['event_name']}_relay_results.csv",
                mime="text/csv"
            )
        else:
            display_warning_message("No results recorded yet for this event.")

def show_relay_standings(db: DatabaseManager):
    """Display overall relay standings by house"""
    st.subheader("Relay Standings by House")
    
    # Get all relay events
    relay_events = [event for event in db.get_all_events() if event.get('is_relay', False)]
    
    if not relay_events:
        display_warning_message("No relay events found.")
        return
    
    # Calculate relay points by house
    house_relay_points = {}
    
    for event in relay_events:
        teams = db.get_relay_teams_by_event(event['event_id'])
        for team in teams:
            if team.get('points', 0) > 0:
                house = team.get('house', 'Unknown')
                house_relay_points[house] = house_relay_points.get(house, 0) + team.get('points', 0)
    
    if house_relay_points:
        # Create standings dataframe
        standings_data = []
        for house, points in house_relay_points.items():
            standings_data.append({
                "House": house,
                "Relay Points": points
            })
        
        # Sort by points
        standings_data.sort(key=lambda x: x["Relay Points"], reverse=True)
        
        # Add rankings
        for i, standing in enumerate(standings_data):
            standing["Rank"] = i + 1
        
        df = pd.DataFrame(standings_data)
        
        # Display with house colors
        from config import HOUSE_COLORS
        house_style_colors = {
            "Ignis": "#ffebee",
            "Nereus": "#e3f2fd", 
            "Ventus": "#fffde7",
            "Terra": "#e8f5e8"
        }
        
        def style_houses(row):
            house = row["House"]
            color = house_style_colors.get(house, "#ffffff")
            return [f'background-color: {color}'] * len(row)
        
        styled_df = df.style.apply(style_houses, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Show leading house
        leader = standings_data[0]
        st.success(f"🏆 {leader['House']} House leads relay events with {leader['Relay Points']} points!")
        
        # Show event breakdown
        st.subheader("Event Breakdown")
        for event in relay_events:
            with st.expander(f"📊 {event['event_name']} Results"):
                teams = db.get_relay_teams_by_event(event['event_id'])
                if teams and any(t.get('result_value') for t in teams):
                    event_results = []
                    for team in teams:
                        if team.get('result_value'):
                            event_results.append({
                                "Position": team.get('position', 'N/A'),
                                "Team": team.get('team_name', 'Unknown'),
                                "House": team.get('house', 'Unknown'),
                                "Time": f"{team.get('result_value', 0):.2f}s",
                                "Points": team.get('points', 0)
                            })
                    
                    if event_results:
                        event_df = pd.DataFrame(event_results)
                        st.dataframe(event_df, hide_index=True, use_container_width=True)
                else:
                    st.info("No results recorded for this event yet.")
    
    else:
        display_warning_message("No relay results recorded yet.")