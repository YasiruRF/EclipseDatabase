"""House Points Leaderboard Page - Fixed Version"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import DatabaseManager
from config import HOUSES
from utils import (
    create_house_points_dataframe,
    create_metric_cards,
    display_warning_message
)

def show_house_points():
    """Display house points leaderboard"""
    st.header("🏆 House Points Leaderboard")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["🏆 Leaderboard", "📊 Analytics", "🎯 Detailed Breakdown"])
    
    with tab1:
        show_leaderboard(db)
    
    with tab2:
        show_analytics(db)
    
    with tab3:
        show_detailed_breakdown(db)

def show_leaderboard(db: DatabaseManager):
    """Display main house points leaderboard"""
    st.subheader("Current Standings")
    
    # Get house points
    house_points = db.get_house_points()
    
    if not house_points:
        display_warning_message("No points data available yet. Add some results first!")
        return
    
    # Auto-refresh option
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Refresh", type="primary"):
            st.rerun()
    
    # Display metric cards
    create_metric_cards(house_points)
    
    st.markdown("---")
    
    # Main leaderboard table
    df = create_house_points_dataframe(house_points)
    
    if not df.empty:
        # Style the leaderboard
        def style_leaderboard(row):
            rank = row["Rank"]
            if rank == 1:
                return ['background: linear-gradient(45deg, #FFD700, #FFA500); font-weight: bold'] * len(row)
            elif rank == 2:
                return ['background: linear-gradient(45deg, #C0C0C0, #A9A9A9); font-weight: bold'] * len(row)
            elif rank == 3:
                return ['background: linear-gradient(45deg, #CD7F32, #A0522D); font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = df.style.apply(style_leaderboard, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Victory celebration for leading house
        if house_points:
            leading_house = house_points[0]
            st.success(f"🎉 **{leading_house['house']} House** is currently leading with **{leading_house['total_points']} points**!")
        
        # Progress visualization
        st.markdown("### 📈 Points Progress")
        
        # Create bar chart
        fig = px.bar(
            df,
            x="House",
            y="Total Points",
            color="House",
            color_discrete_map={
                "Red": "#ff6b6b",
                "Blue": "#4ecdc4",
                "Green": "#95e1d3", 
                "Yellow": "#fce38a"
            },
            title="House Points Comparison"
        )
        
        fig.update_layout(
            showlegend=False,
            xaxis_title="House",
            yaxis_title="Total Points"
        )
        
        st.plotly_chart(fig, use_container_width=True)

def show_analytics(db: DatabaseManager):
    """Display detailed analytics and charts"""
    st.subheader("Points Analytics")
    
    # Get all results to analyze
    all_events = db.get_all_events()
    all_results = []
    
    for event in all_events:
        event_results = db.get_results_by_event(event["event_id"])
        all_results.extend(event_results)
    
    if not all_results:
        display_warning_message("No results data available for analysis.")
        return
    
    # Prepare data for analysis with robust error handling
    analysis_data = []
    for result in all_results:
        try:
            # Handle different possible data structures
            student_data = result.get("students", {})
            event_data = result.get("events", {})
            
            # If students/events data is a list, take first item
            if isinstance(student_data, list) and student_data:
                student_data = student_data[0]
            if isinstance(event_data, list) and event_data:
                event_data = event_data[0]
            
            # Only add if we have valid data
            if student_data and event_data:
                analysis_data.append({
                    "house": student_data.get("house", "Unknown"),
                    "event_type": event_data.get("event_type", "Unknown"),
                    "event_name": event_data.get("event_name", "Unknown"),
                    "points": result.get("points", 0) or 0,
                    "position": result.get("position", 0) or 0
                })
        except Exception as e:
            # Skip problematic records silently
            continue
    
    if not analysis_data:
        display_warning_message("No valid analysis data available.")
        return
    
    df_analysis = pd.DataFrame(analysis_data)
    
    # Points by Event Type
    st.markdown("#### 🏃‍♂️ Points by Event Type")
    
    points_by_type = df_analysis.groupby(["house", "event_type"])["points"].sum().reset_index()
    
    fig_type = px.bar(
        points_by_type,
        x="event_type",
        y="points",
        color="house",
        color_discrete_map={
            "Red": "#ff6b6b",
            "Blue": "#4ecdc4",
            "Green": "#95e1d3",
            "Yellow": "#fce38a"
        },
        title="Points Distribution by Event Type",
        barmode="group"
    )
    
    st.plotly_chart(fig_type, use_container_width=True)
    
    # Performance Analysis
    st.markdown("#### 🎯 Performance Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Average points per event
        avg_points = df_analysis.groupby("house")["points"].mean().reset_index()
        avg_points.columns = ["House", "Average Points"]
        
        fig_avg = px.pie(
            avg_points,
            values="Average Points",
            names="House",
            title="Average Points per Event by House",
            color="House",
            color_discrete_map={
                "Red": "#ff6b6b",
                "Blue": "#4ecdc4",
                "Green": "#95e1d3",
                "Yellow": "#fce38a"
            }
        )
        
        st.plotly_chart(fig_avg, use_container_width=True)
    
    with col2:
        # Podium finishes (top 3 positions)
        podium_finishes = df_analysis[df_analysis["position"] <= 3]
        podium_counts = podium_finishes.groupby("house").size().reset_index()
        podium_counts.columns = ["House", "Podium Finishes"]
        
        fig_podium = px.bar(
            podium_counts,
            x="House",
            y="Podium Finishes",
            color="House",
            color_discrete_map={
                "Red": "#ff6b6b",
                "Blue": "#4ecdc4",
                "Green": "#95e1d3",
                "Yellow": "#fce38a"
            },
            title="Total Podium Finishes (Top 3)"
        )
        
        st.plotly_chart(fig_podium, use_container_width=True)
    
    # Event participation
    st.markdown("#### 📊 Participation Analysis")
    
    participation = df_analysis.groupby("house").size().reset_index()
    participation.columns = ["House", "Total Participations"]
    
    col1, col2, col3, col4 = st.columns(4)
    
    for i, (_, row) in enumerate(participation.iterrows()):
        with [col1, col2, col3, col4][i]:
            house_avg = df_analysis[df_analysis['house'] == row['House']]['points'].mean()
            st.metric(
                f"{row['House']} House",
                f"{row['Total Participations']} events",
                delta=f"Avg: {house_avg:.1f} pts"
            )

def show_detailed_breakdown(db: DatabaseManager):
    """Show detailed points breakdown by event"""
    st.subheader("Detailed Points Breakdown")
    
    # Get all events and results
    all_events = db.get_all_events()
    
    if not all_events:
        display_warning_message("No events found.")
        return
    
    # Event selector
    selected_event = st.selectbox(
        "Select Event for Breakdown",
        options=all_events,
        format_func=lambda x: f"{x['event_name']} ({x['event_type']})",
        key="breakdown_event_selector"
    )
    
    if selected_event:
        results = db.get_results_by_event(selected_event["event_id"])
        
        if not results:
            display_warning_message(f"No results found for {selected_event['event_name']}.")
            return
        
        # Event info
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Event", selected_event["event_name"])
        with col2:
            st.metric("Type", selected_event["event_type"])
        with col3:
            st.metric("Participants", len(results))
        
        # Points breakdown by house for this event
        house_points_event = {}
        house_participants = {}
        
        for result in results:
            try:
                # Handle different possible data structures
                student_data = result.get("students", {})
                if isinstance(student_data, list) and student_data:
                    student_data = student_data[0]
                
                house = student_data.get("house", "Unknown")
                points = result.get("points", 0) or 0
                
                house_points_event[house] = house_points_event.get(house, 0) + points
                house_participants[house] = house_participants.get(house, 0) + 1
            except Exception as e:
                continue
        
        # Display breakdown
        st.markdown("### 🏆 Points Earned by House")
        
        breakdown_data = []
        for house in HOUSES:
            breakdown_data.append({
                "House": house,
                "Points Earned": house_points_event.get(house, 0),
                "Participants": house_participants.get(house, 0)
            })
        
        df_breakdown = pd.DataFrame(breakdown_data)
        
        # Style the breakdown table
        def style_breakdown(row):
            house = row["House"]
            colors = {
                "Red": "#ffebee",
                "Blue": "#e3f2fd",
                "Green": "#e8f5e8",
                "Yellow": "#fffde7"
            }
            color = colors.get(house, "#ffffff")
            return [f'background-color: {color}'] * len(row)
        
        styled_breakdown = df_breakdown.style.apply(style_breakdown, axis=1)
        st.dataframe(styled_breakdown, use_container_width=True, hide_index=True)
        
        # Detailed results for the event
        st.markdown("### 📋 Complete Results")
        
        results_data = []
        for result in results:
            try:
                student_data = result.get("students", {})
                if isinstance(student_data, list) and student_data:
                    student_data = student_data[0]
                
                results_data.append({
                    "Position": result.get("position", "N/A"),
                    "Name": f"{student_data.get('first_name', 'Unknown')} {student_data.get('last_name', '')}",
                    "House": student_data.get("house", "Unknown"),
                    "Bib ID": student_data.get("bib_id", "N/A"),
                    "Result": f"{result.get('result_value', 0):.2f}",
                    "Points": result.get("points", 0)
                })
            except Exception as e:
                continue
        
        df_results = pd.DataFrame(results_data)
        
        # Style results with position highlighting
        def highlight_positions(row):
            pos = row["Position"]
            if pos == 1:
                return ['background-color: #FFD700; font-weight: bold'] * len(row)  # Gold
            elif pos == 2:
                return ['background-color: #C0C0C0; font-weight: bold'] * len(row)  # Silver
            elif pos == 3:
                return ['background-color: #CD7F32; font-weight: bold'] * len(row)  # Bronze
            return [''] * len(row)
        
        styled_results = df_results.style.apply(highlight_positions, axis=1)
        st.dataframe(styled_results, use_container_width=True, hide_index=True)
        
        # Export option
        csv_data = df_results.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {selected_event['event_name']} Breakdown",
            data=csv_data,
            file_name=f"{selected_event['event_name'].replace(' ', '_').lower()}_breakdown.csv",
            mime="text/csv"
        )