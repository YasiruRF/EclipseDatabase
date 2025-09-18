"""Results View Page for displaying event results"""

import streamlit as st
import pandas as pd
from database import DatabaseManager
from config import EVENT_TYPES, HOUSES
from utils import (
    create_results_dataframe,
    format_result_value,
    search_and_filter_results,
    display_warning_message,
    export_results_to_csv
)

def show_results_view():
    """Display results viewing interface"""
    st.header("🏆 Event Results")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📊 By Event Type", "🎯 Individual Events", "🔍 Search Results"])
    
    with tab1:
        show_results_by_type(db)
    
    with tab2:
        show_individual_event_results(db)
    
    with tab3:
        show_search_results(db)

def show_results_by_type(db: DatabaseManager):
    """Display results grouped by event type"""
    st.subheader("Results by Event Type")
    
    # Event type selector
    event_type = st.selectbox(
        "Select Event Type",
        options=list(EVENT_TYPES.keys()),
        key="results_event_type"
    )
    
    # Get results for selected event type
    results = db.get_results_by_event_type(event_type)
    
    if not results:
        display_warning_message(f"No results found for {event_type.lower()} events.")
        return
    
    # Display filters
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "Search participants",
            placeholder="Search by name or ID",
            key=f"search_{event_type}"
        )
    
    with col2:
        house_filter = st.selectbox(
            "Filter by House",
            options=["All"] + HOUSES,
            key=f"house_filter_{event_type}"
        )
    
    with col3:
        # Get unique events for this type
        unique_events = list(set(result["events"]["event_name"] for result in results))
        event_filter = st.selectbox(
            "Filter by Event",
            options=["All"] + unique_events,
            key=f"event_filter_{event_type}"
        )
    
    # Apply filters
    filtered_results = search_and_filter_results(
        results, search_term, house_filter, event_filter
    )
    
    if not filtered_results:
        display_warning_message("No results match the current filters.")
        return
    
    # Group results by event
    events_dict = {}
    for result in filtered_results:
        event_name = result["events"]["event_name"]
        if event_name not in events_dict:
            events_dict[event_name] = []
        events_dict[event_name].append(result)
    
    # Display results for each event
    for event_name, event_results in events_dict.items():
        with st.expander(f"🏃‍♂️ {event_name} ({len(event_results)} participants)", expanded=True):
            df = create_results_dataframe(event_results)
            
            if not df.empty:
                # Style the dataframe
                styled_df = style_results_dataframe(df)
                st.dataframe(styled_df, use_container_width=True)
                
                # Export option
                csv = export_results_to_csv(event_results, f"{event_name}_results.csv")
                if csv:
                    st.download_button(
                        label=f"📥 Download {event_name} Results",
                        data=csv,
                        file_name=f"{event_name.replace(' ', '_').lower()}_results.csv",
                        mime="text/csv"
                    )

def show_individual_event_results(db: DatabaseManager):
    """Display results for individual events"""
    st.subheader("Individual Event Results")
    
    # Get all events
    all_events = db.get_all_events()
    
    if not all_events:
        display_warning_message("No events found. Please add events first.")
        return
    
    # Event selector
    selected_event = st.selectbox(
        "Select Event",
        options=all_events,
        format_func=lambda x: f"{x['event_name']} ({x['event_type']})",
        key="individual_event_selector"
    )
    
    if selected_event:
        # Get results for selected event
        results = db.get_results_by_event(selected_event["event_id"])
        
        if not results:
            display_warning_message(f"No results found for {selected_event['event_name']}.")
            return
        
        # Display event info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Event", selected_event["event_name"])
        with col2:
            st.metric("Type", selected_event["event_type"])
        with col3:
            st.metric("Participants", len(results))
        
        # Display podium (top 3)
        if len(results) >= 3:
            st.markdown("### 🏆 Podium")
            
            pod_col1, pod_col2, pod_col3 = st.columns(3)
            
            # 1st place
            with pod_col2:  # Center column for 1st place
                winner = results[0]["students"]
                st.markdown(f"""
                <div style="text-align: center; padding: 20px; background: linear-gradient(45deg, #FFD700, #FFA500); border-radius: 10px; margin: 10px 0;">
                    <h2>🥇</h2>
                    <h3>{winner['first_name']} {winner['last_name']}</h3>
                    <p><strong>{winner['house']} House</strong></p>
                    <p>Result: {format_result_value(results[0]['result_value'], selected_event['event_type'])}</p>
                    <p>Points: {results[0]['points']}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 2nd place
            if len(results) >= 2:
                with pod_col1:
                    second = results[1]["students"]
                    st.markdown(f"""
                    <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #C0C0C0, #A9A9A9); border-radius: 10px; margin: 10px 0;">
                        <h3>🥈</h3>
                        <h4>{second['first_name']} {second['last_name']}</h4>
                        <p>{second['house']} House</p>
                        <p>{format_result_value(results[1]['result_value'], selected_event['event_type'])}</p>
                        <p>{results[1]['points']} pts</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 3rd place
            if len(results) >= 3:
                with pod_col3:
                    third = results[2]["students"]
                    st.markdown(f"""
                    <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #CD7F32, #A0522D); border-radius: 10px; margin: 10px 0;">
                        <h3>🥉</h3>
                        <h4>{third['first_name']} {third['last_name']}</h4>
                        <p>{third['house']} House</p>
                        <p>{format_result_value(results[2]['result_value'], selected_event['event_type'])}</p>
                        <p>{results[2]['points']} pts</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Full results table
        st.markdown("### 📋 Complete Results")
        
        df = create_results_dataframe(results)
        if not df.empty:
            styled_df = style_results_dataframe(df)
            st.dataframe(styled_df, use_container_width=True)
            
            # Export option
            csv = export_results_to_csv(results, f"{selected_event['event_name']}_results.csv")
            if csv:
                st.download_button(
                    label="📥 Download Results",
                    data=csv,
                    file_name=f"{selected_event['event_name'].replace(' ', '_').lower()}_results.csv",
                    mime="text/csv"
                )

def show_search_results(db: DatabaseManager):
    """Display searchable results across all events"""
    st.subheader("Search All Results")
    
    # Get all results using the improved method
    all_results = db.get_all_results()
    
    if not all_results:
        display_warning_message("No results found in the database.")
        return
    
    # Search and filter controls
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        search_term = st.text_input(
            "Search",
            placeholder="Name, ID, etc.",
            key="global_search"
        )
    
    with col2:
        house_filter = st.selectbox(
            "House",
            options=["All"] + HOUSES,
            key="global_house_filter"
        )
    
    with col3:
        event_type_filter = st.selectbox(
            "Event Type",
            options=["All"] + list(EVENT_TYPES.keys()),
            key="global_event_type_filter"
        )
    
    with col4:
        # Get unique events
        unique_events = list(set(result["events"]["event_name"] for result in all_results))
        event_filter = st.selectbox(
            "Specific Event",
            options=["All"] + unique_events,
            key="global_event_filter"
        )
    
    # Apply filters
    filtered_results = all_results
    
    # Search term filter
    if search_term:
        search_term = search_term.lower()
        filtered_results = [
            result for result in filtered_results
            if (search_term in result["students"]["first_name"].lower() or
                search_term in result["students"]["last_name"].lower() or
                search_term in result["students"]["curtin_id"].lower() or
                search_term in str(result["students"]["bib_id"]))
        ]
    
    # House filter
    if house_filter != "All":
        filtered_results = [
            result for result in filtered_results
            if result["students"]["house"] == house_filter
        ]
    
    # Event type filter
    if event_type_filter != "All":
        filtered_results = [
            result for result in filtered_results
            if result["events"]["event_type"] == event_type_filter
        ]
    
    # Specific event filter
    if event_filter != "All":
        filtered_results = [
            result for result in filtered_results
            if result["events"]["event_name"] == event_filter
        ]
    
    # Display results count
    st.info(f"Found {len(filtered_results)} results out of {len(all_results)} total results")
    
    if not filtered_results:
        display_warning_message("No results match the current filters.")
        return
    
    # Display results
    df = create_results_dataframe(filtered_results)
    if not df.empty:
        styled_df = style_results_dataframe(df)
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Export filtered results
        csv = export_results_to_csv(filtered_results, "filtered_results.csv")
        if csv:
            st.download_button(
                label="📥 Download Filtered Results",
                data=csv,
                file_name="filtered_results.csv",
                mime="text/csv"
            )

def style_results_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Apply styling to results dataframe"""
    if df.empty:
        return df
    
    house_colors = {
        "Red": "#ffebee",
        "Blue": "#e3f2fd", 
        "Green": "#e8f5e8",
        "Yellow": "#fffde7"
    }
    
    def highlight_row(row):
        if "House" in row.index:
            house = row["House"]
            color = house_colors.get(house, "#ffffff")
            return [f'background-color: {color}'] * len(row)
        return [''] * len(row)
    
    def highlight_position(row):
        if "Position" in row.index:
            position = row["Position"]
            if position == 1:
                return ['font-weight: bold; color: #FFD700'] * len(row)  # Gold
            elif position == 2:
                return ['font-weight: bold; color: #C0C0C0'] * len(row)  # Silver
            elif position == 3:
                return ['font-weight: bold; color: #CD7F32'] * len(row)  # Bronze
        return [''] * len(row)
    
    # Apply styling
    styled = df.style.apply(highlight_row, axis=1)
    return styled