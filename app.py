"""
Sports Meet Event Summary - Audience View
Independent display app for showing event results and house standings
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Configure page
st.set_page_config(
    page_title="Sports Meet Results",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Handle imports
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    st.error("Database connection not available")
    st.stop()

# Database connection
@st.cache_resource
def init_supabase():
    """Initialize Supabase client"""
    try:
        # Get credentials from environment or secrets
        url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
        
        if not url or not key:
            st.error("Database credentials not configured")
            st.stop()
        
        return create_client(url, key)
    except Exception as e:
        st.error(f"Database connection failed: {str(e)}")
        st.stop()

supabase = init_supabase()

# House colors for consistent theming
HOUSE_COLORS = {
    "Ignis": "#ff6b6b",    # Red
    "Nereus": "#4ecdc4",   # Blue  
    "Ventus": "#fce38a",   # Yellow
    "Terra": "#95e1d3"     # Green
}

# Data fetching functions
@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_house_standings():
    """Get current house point standings"""
    try:
        result = supabase.table("corrected_house_points").select("*").order("total_points", desc=True).execute()
        return result.data or []
    except Exception as e:
        st.error(f"Error fetching house standings: {str(e)}")
        return []

@st.cache_data(ttl=60)  # Cache for 1 minute
def get_all_events():
    """Get all events"""
    try:
        result = supabase.table("events").select("*").order("event_name").execute()
        return result.data or []
    except Exception as e:
        st.error(f"Error fetching events: {str(e)}")
        return []

@st.cache_data(ttl=60)
def get_event_results(event_id):
    """Get results for a specific event"""
    try:
        result = supabase.table("results").select("""
            *, 
            students!inner(curtin_id, bib_id, first_name, last_name, house, gender),
            events!inner(event_name, event_type, unit, is_relay)
        """).eq("event_id", event_id).order("position").execute()
        
        return result.data or []
    except Exception as e:
        st.error(f"Error fetching event results: {str(e)}")
        return []

@st.cache_data(ttl=60)
def get_relay_results(event_id):
    """Get relay team results for a specific event"""
    try:
        result = supabase.table("relay_team_results").select("*").eq("event_id", event_id).order("position").execute()
        return result.data or []
    except Exception as e:
        return []

def format_result_display(result_value, event_type):
    """Format result value for display"""
    if event_type == "Track":
        if result_value < 60:
            return f"{result_value:.2f}s"
        else:
            minutes = int(result_value // 60)
            seconds = result_value % 60
            return f"{minutes}:{seconds:05.2f}"
    else:
        return f"{result_value:.2f}m"

# Main app layout
def main():
    # Header
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(90deg, #ff6b6b, #4ecdc4, #fce38a, #95e1d3); color: white; margin-bottom: 2rem; border-radius: 10px;">
        <h1 style="margin: 0; font-size: 3rem; font-weight: bold;">🏆 Sports Meet Results</h1>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.2rem;">Live Event Summary & House Standings</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Disclaimer
    st.warning("⚠️ **Disclaimer:** Results displayed here might contain errors or be incomplete. This is a live summary that updates automatically. For official results, please check with event organizers.")
    
    # Auto-refresh info
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"📊 Last updated: {current_time} | Page refreshes every 30 seconds")
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        show_house_leaderboard()
    
    with col2:
        show_event_summaries()

def show_house_leaderboard():
    """Display current house point standings"""
    st.subheader("🏠 House Point Standings")
    
    house_data = get_house_standings()
    
    if not house_data:
        st.warning("No house point data available")
        return
    
    # Create leaderboard
    for i, house in enumerate(house_data):
        rank = i + 1
        house_name = house["house"]
        total_points = house["total_points"]
        individual_points = house.get("individual_points", 0)
        relay_points = house.get("relay_team_points", 0)
        
        # Medal emoji based on rank
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "🏆"
        
        # House emoji
        house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}.get(house_name, "🏠")
        
        # Create colored container
        house_color = HOUSE_COLORS.get(house_name, "#ffffff")
        
        st.markdown(f"""
        <div style="
            background: linear-gradient(45deg, {house_color}22, {house_color}44);
            border-left: 5px solid {house_color};
            padding: 1rem;
            margin: 0.5rem 0;
            border-radius: 5px;
        ">
            <h3 style="margin: 0; color: #333;">
                {medal} #{rank} - {house_emoji} {house_name} House
            </h3>
            <h2 style="margin: 0.5rem 0; color: #333; font-size: 2rem;">
                {total_points} Points
            </h2>
            <p style="margin: 0; color: #666; font-size: 0.9rem;">
                Individual: {individual_points} | Relay: {relay_points}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Visual chart
    if len(house_data) > 1:
        st.subheader("📊 Points Comparison")
        
        # Create bar chart
        df = pd.DataFrame(house_data)
        fig = px.bar(
            df,
            x="house",
            y="total_points",
            color="house",
            color_discrete_map=HOUSE_COLORS,
            title="Total House Points"
        )
        fig.update_layout(
            showlegend=False,
            height=300,
            xaxis_title="House",
            yaxis_title="Points"
        )
        st.plotly_chart(fig, use_container_width=True)

def show_event_summaries():
    """Display event results with podium finishes"""
    st.subheader("🎯 Event Results Summary")
    
    all_events = get_all_events()
    
    if not all_events:
        st.warning("No events found")
        return
    
    # Filter events with results
    events_with_results = []
    for event in all_events:
        if event.get('is_relay', False):
            results = get_relay_results(event['event_id'])
        else:
            results = get_event_results(event['event_id'])
        
        if results:
            events_with_results.append({
                'event': event,
                'results': results,
                'is_relay': event.get('is_relay', False)
            })
    
    if not events_with_results:
        st.info("No completed events yet")
        return
    
    # Group events by type
    track_events = [e for e in events_with_results if e['event']['event_type'] == 'Track']
    field_events = [e for e in events_with_results if e['event']['event_type'] == 'Field']
    
    # Display by category
    if track_events:
        st.markdown("### 🏃 Track Events")
        for event_data in track_events:
            show_event_podium(event_data)
    
    if field_events:
        st.markdown("### 🏋️ Field Events")
        for event_data in field_events:
            show_event_podium(event_data)

def show_event_podium(event_data):
    """Display podium (top 3) for an event"""
    event = event_data['event']
    results = event_data['results']
    is_relay = event_data['is_relay']
    
    event_name = event['event_name']
    event_type = event['event_type']
    
    # Get top 3 results
    podium_results = []
    for result in results[:3]:
        if result.get('position') and result.get('position') <= 3:
            podium_results.append(result)
    
    if not podium_results:
        return
    
    # Create expandable section for each event
    with st.expander(f"🏆 {event_name} - {'Relay' if is_relay else 'Individual'} {event_type}"):
        
        # Show podium
        cols = st.columns(3)
        
        for i, result in enumerate(podium_results):
            position = result.get('position', i + 1)
            medal = "🥇" if position == 1 else "🥈" if position == 2 else "🥉"
            
            with cols[i]:
                if is_relay:
                    # Relay team display
                    team_name = result.get('team_name', 'Unknown Team')
                    house = result.get('house', 'Unknown')
                    result_value = result.get('result_value', 0)
                    points = result.get('points', 0)
                    
                    house_color = HOUSE_COLORS.get(house, "#cccccc")
                    
                    st.markdown(f"""
                    <div style="
                        text-align: center;
                        background: {house_color}22;
                        border: 2px solid {house_color};
                        padding: 1rem;
                        border-radius: 10px;
                        margin: 0.5rem 0;
                    ">
                        <div style="font-size: 2rem;">{medal}</div>
                        <h4 style="margin: 0.5rem 0; color: #333;">{position}. {team_name}</h4>
                        <p style="margin: 0; color: #666;"><strong>{house} House</strong></p>
                        <p style="margin: 0; color: #666;">
                            {format_result_display(result_value, event_type)}
                        </p>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">
                            {points} points
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Show team members
                    members = []
                    for j in range(1, 5):
                        member_name = result.get(f'member{j}_name')
                        if member_name and member_name != 'None None':
                            members.append(member_name)
                    
                    if members:
                        st.caption("Team: " + " | ".join(members))
                
                else:
                    # Individual athlete display
                    student_data = result.get('students', {})
                    if isinstance(student_data, list):
                        student_data = student_data[0] if student_data else {}
                    
                    first_name = student_data.get('first_name', 'Unknown')
                    last_name = student_data.get('last_name', '')
                    house = student_data.get('house', 'Unknown')
                    bib_id = student_data.get('bib_id', 'N/A')
                    result_value = result.get('result_value', 0)
                    points = result.get('points', 0)
                    
                    house_color = HOUSE_COLORS.get(house, "#cccccc")
                    
                    st.markdown(f"""
                    <div style="
                        text-align: center;
                        background: {house_color}22;
                        border: 2px solid {house_color};
                        padding: 1rem;
                        border-radius: 10px;
                        margin: 0.5rem 0;
                    ">
                        <div style="font-size: 2rem;">{medal}</div>
                        <h4 style="margin: 0.5rem 0; color: #333;">{position}. {first_name} {last_name}</h4>
                        <p style="margin: 0; color: #666;"><strong>{house} House</strong></p>
                        <p style="margin: 0; color: #666;">Bib #{bib_id}</p>
                        <p style="margin: 0; color: #666;">
                            {format_result_display(result_value, event_type)}
                        </p>
                        <p style="margin: 0; color: #666; font-size: 0.9rem;">
                            {points} points
                        </p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Show all results in a compact table
        if len(results) > 3:
            st.markdown("**Complete Results:**")
            
            table_data = []
            for result in results:
                if is_relay:
                    name = result.get('team_name', 'Unknown Team')
                    house = result.get('house', 'Unknown')
                else:
                    student_data = result.get('students', {})
                    if isinstance(student_data, list):
                        student_data = student_data[0] if student_data else {}
                    name = f"{student_data.get('first_name', 'Unknown')} {student_data.get('last_name', '')}"
                    house = student_data.get('house', 'Unknown')
                
                table_data.append({
                    'Pos': result.get('position', 'N/A'),
                    'Name/Team': name,
                    'House': house,
                    'Result': format_result_display(result.get('result_value', 0), event_type),
                    'Points': result.get('points', 0)
                })
            
            df_results = pd.DataFrame(table_data)
            st.dataframe(df_results, hide_index=True, use_container_width=True)

if __name__ == "__main__":
    # Auto-refresh every 30 seconds
    import time
    
    # Add auto-refresh meta tag
    st.markdown("""
    <meta http-equiv="refresh" content="30">
    """, unsafe_allow_html=True)
    
    main()
    
    # Add refresh button
    if st.button("🔄 Refresh Results", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>Sports Meet Event Management System | Audience View</p>
        <p style="font-size: 0.8rem;">
            ⚠️ This display updates automatically but may contain errors. 
            Please verify important results with event officials.
        </p>
    </div>
    """, unsafe_allow_html=True)