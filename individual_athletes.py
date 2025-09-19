"""Individual Athletes Performance Page for tracking best male and female athletes"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import DatabaseManager
from config import HOUSES, HOUSE_COLORS, GENDER_OPTIONS
from utils import (
    create_athlete_performance_dataframe,
    export_athletes_to_csv,
    display_warning_message,
    format_result_value
)

def show_individual_athletes():
    """Display individual athletes performance tracking"""
    st.header("Individual Athletes Performance")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs([
        "Overall Rankings", 
        "Male Athletes", 
        "Female Athletes", 
        "Performance Analysis"
    ])
    
    with tab1:
        show_overall_rankings(db)
    
    with tab2:
        show_gender_rankings(db, "Male")
    
    with tab3:
        show_gender_rankings(db, "Female")
    
    with tab4:
        show_performance_analysis(db)

def show_overall_rankings(db: DatabaseManager):
    """Display overall athlete rankings"""
    st.subheader("Overall Top Athletes")
    
    # Get athlete performance data
    athletes = db.get_individual_athlete_performance(limit=50)
    
    if not athletes:
        display_warning_message("No athlete performance data available yet. Add some results first!")
        return
    
    # Filter and display options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        house_filter = st.selectbox(
            "Filter by House",
            options=["All"] + HOUSES,
            key="overall_house_filter"
        )
    
    with col2:
        gender_filter = st.selectbox(
            "Filter by Gender",
            options=["All"] + GENDER_OPTIONS,
            key="overall_gender_filter"
        )
    
    with col3:
        display_limit = st.selectbox(
            "Show Top",
            options=[10, 20, 30, 50],
            index=0
        )
    
    # Apply filters
    filtered_athletes = athletes
    if house_filter != "All":
        filtered_athletes = [a for a in filtered_athletes if a.get('house') == house_filter]
    if gender_filter != "All":
        filtered_athletes = [a for a in filtered_athletes if a.get('gender') == gender_filter]
    
    # Limit results
    filtered_athletes = filtered_athletes[:display_limit]
    
    if not filtered_athletes:
        display_warning_message("No athletes match the current filters.")
        return
    
    # Display top 3 champions
    if len(filtered_athletes) >= 3:
        st.markdown("### Champions")
        
        champion_cols = st.columns(3)
        
        # Gold medalist
        with champion_cols[1]:  # Center column
            champion = filtered_athletes[0]
            house_emoji = {"Ignis": "fire", "Nereus": "water", "Ventus": "wind", "Terra": "earth"}
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; background: linear-gradient(45deg, #FFD700, #FFA500); border-radius: 10px; margin: 10px 0;">
                <h2>1st Place</h2>
                <h3>{champion['first_name']} {champion['last_name']}</h3>
                <p><strong>{champion['house']} House ({champion.get('gender', 'N/A')})</strong></p>
                <p>Total Points: {champion['total_points']}</p>
                <p>Gold Medals: {champion['gold_medals']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Silver medalist
        if len(filtered_athletes) >= 2:
            with champion_cols[0]:
                silver = filtered_athletes[1]
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #C0C0C0, #A9A9A9); border-radius: 10px; margin: 10px 0;">
                    <h3>2nd Place</h3>
                    <h4>{silver['first_name']} {silver['last_name']}</h4>
                    <p>{silver['house']} House ({silver.get('gender', 'N/A')})</p>
                    <p>{silver['total_points']} points</p>
                    <p>{silver['gold_medals']} golds</p>
                </div>
                """, unsafe_allow_html=True)
        
        # Bronze medalist
        if len(filtered_athletes) >= 3:
            with champion_cols[2]:
                bronze = filtered_athletes[2]
                st.markdown(f"""
                <div style="text-align: center; padding: 15px; background: linear-gradient(45deg, #CD7F32, #A0522D); border-radius: 10px; margin: 10px 0;">
                    <h3>3rd Place</h3>
                    <h4>{bronze['first_name']} {bronze['last_name']}</h4>
                    <p>{bronze['house']} House ({bronze.get('gender', 'N/A')})</p>
                    <p>{bronze['total_points']} points</p>
                    <p>{bronze['gold_medals']} golds</p>
                </div>
                """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Full rankings table
    st.markdown("### Complete Rankings")
    df = create_athlete_performance_dataframe(filtered_athletes)
    
    if not df.empty:
        # Style the dataframe
        def highlight_top_performers(row):
            rank = row.get("Rank", 999)
            if rank == 1:
                return ['background-color: #FFD700; font-weight: bold'] * len(row)
            elif rank == 2:
                return ['background-color: #C0C0C0; font-weight: bold'] * len(row)
            elif rank == 3:
                return ['background-color: #CD7F32; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = df.style.apply(highlight_top_performers, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv = export_athletes_to_csv(filtered_athletes)
        if csv:
            st.download_button(
                label="Download Rankings",
                data=csv,
                file_name="overall_athlete_rankings.csv",
                mime="text/csv"
            )

def show_gender_rankings(db: DatabaseManager, gender: str):
    """Display rankings for specific gender"""
    st.subheader(f"Top {gender} Athletes")
    
    # Get athlete performance data
    all_athletes = db.get_individual_athlete_performance()
    gender_athletes = [a for a in all_athletes if a.get('gender') == gender]
    
    if not gender_athletes:
        display_warning_message(f"No {gender.lower()} athlete performance data available yet.")
        return
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        house_filter = st.selectbox(
            "Filter by House",
            options=["All"] + HOUSES,
            key=f"{gender.lower()}_house_filter"
        )
    
    with col2:
        display_limit = st.selectbox(
            "Show Top",
            options=[10, 15, 20, 30],
            index=0,
            key=f"{gender.lower()}_limit"
        )
    
    # Apply house filter
    if house_filter != "All":
        gender_athletes = [a for a in gender_athletes if a.get('house') == house_filter]
    
    # Limit results
    gender_athletes = gender_athletes[:display_limit]
    
    if not gender_athletes:
        display_warning_message("No athletes match the current filters.")
        return
    
    # Display champion
    if gender_athletes:
        champion = gender_athletes[0]
        house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
        house_icon = house_emoji.get(champion['house'], "🏆")
        
        st.markdown(f"""
        ### Best {gender} Athlete
        **{champion['first_name']} {champion['last_name']}**
        - **House:** {house_icon} {champion['house']}
        - **Bib ID:** {champion['bib_id']}
        - **Total Points:** {champion['total_points']}
        - **Gold Medals:** {champion['gold_medals']}
        - **Silver Medals:** {champion['silver_medals']}
        - **Bronze Medals:** {champion['bronze_medals']}
        - **Total Events:** {champion['total_events']}
        """)
    
    st.markdown("---")
    
    # Rankings table
    df = create_athlete_performance_dataframe(gender_athletes)
    
    if not df.empty:
        # Style the dataframe
        def highlight_medals(row):
            rank = row.get("Rank", 999)
            if rank == 1:
                return ['background-color: #FFD700; font-weight: bold'] * len(row)
            elif rank == 2:
                return ['background-color: #C0C0C0; font-weight: bold'] * len(row)
            elif rank == 3:
                return ['background-color: #CD7F32; font-weight: bold'] * len(row)
            else:
                return [''] * len(row)
        
        styled_df = df.style.apply(highlight_medals, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Export option
        csv = export_athletes_to_csv(gender_athletes)
        if csv:
            st.download_button(
                label=f"Download {gender} Rankings",
                data=csv,
                file_name=f"{gender.lower()}_athlete_rankings.csv",
                mime="text/csv",
                key=f"download_{gender.lower()}"
            )

def show_performance_analysis(db: DatabaseManager):
    """Display performance analysis and visualizations"""
    st.subheader("Performance Analysis")
    
    # Get athlete performance data
    athletes = db.get_individual_athlete_performance()
    
    if not athletes:
        display_warning_message("No athlete performance data available for analysis.")
        return
    
    # Create analysis dataframe
    df_analysis = pd.DataFrame(athletes)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_athletes = len(athletes)
        st.metric("Total Athletes", total_athletes)
    
    with col2:
        avg_points = df_analysis['total_points'].mean()
        st.metric("Avg Points", f"{avg_points:.1f}")
    
    with col3:
        total_events = df_analysis['total_events'].sum()
        st.metric("Total Participations", total_events)
    
    with col4:
        total_medals = (df_analysis['gold_medals'] + df_analysis['silver_medals'] + df_analysis['bronze_medals']).sum()
        st.metric("Total Medals", total_medals)
    
    # Visualizations
    st.markdown("### Performance Visualizations")
    
    # Points distribution by house
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Points by House")
        house_points = df_analysis.groupby('house')['total_points'].sum().reset_index()
        
        fig_house = px.bar(
            house_points,
            x='house',
            y='total_points',
            color='house',
            color_discrete_map=HOUSE_COLORS,
            title="Total Points by House"
        )
        st.plotly_chart(fig_house, use_container_width=True)
    
    with col2:
        st.markdown("#### Performance by Gender")
        gender_performance = df_analysis.groupby('gender').agg({
            'total_points': 'mean',
            'gold_medals': 'sum',
            'total_events': 'mean'
        }).reset_index()
        
        fig_gender = px.bar(
            gender_performance,
            x='gender',
            y='total_points',
            title="Average Points by Gender"
        )
        st.plotly_chart(fig_gender, use_container_width=True)
    
    # Medal distribution
    st.markdown("#### Medal Distribution")
    medal_data = []
    for _, athlete in df_analysis.iterrows():
        medal_data.extend([
            {'athlete': f"{athlete['first_name']} {athlete['last_name']}", 'medal_type': 'Gold', 'count': athlete['gold_medals'], 'house': athlete['house']},
            {'athlete': f"{athlete['first_name']} {athlete['last_name']}", 'medal_type': 'Silver', 'count': athlete['silver_medals'], 'house': athlete['house']},
            {'athlete': f"{athlete['first_name']} {athlete['last_name']}", 'medal_type': 'Bronze', 'count': athlete['bronze_medals'], 'house': athlete['house']}
        ])
    
    medal_df = pd.DataFrame(medal_data)
    medal_df = medal_df[medal_df['count'] > 0]  # Only show athletes with medals
    
    if not medal_df.empty:
        fig_medals = px.bar(
            medal_df.groupby(['house', 'medal_type'])['count'].sum().reset_index(),
            x='house',
            y='count',
            color='medal_type',
            color_discrete_map={'Gold': '#FFD700', 'Silver': '#C0C0C0', 'Bronze': '#CD7F32'},
            title="Medal Distribution by House"
        )
        st.plotly_chart(fig_medals, use_container_width=True)
    
    # Top performers scatter plot
    st.markdown("#### Points vs Events Participation")
    fig_scatter = px.scatter(
        df_analysis,
        x='total_events',
        y='total_points',
        color='house',
        size='gold_medals',
        hover_data=['first_name', 'last_name', 'gender'],
        color_discrete_map=HOUSE_COLORS,
        title="Athlete Performance: Points vs Event Participation"
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Performance statistics table
    st.markdown("### Performance Statistics by House")
    house_stats = df_analysis.groupby('house').agg({
        'total_points': ['count', 'sum', 'mean', 'max'],
        'gold_medals': 'sum',
        'silver_medals': 'sum',
        'bronze_medals': 'sum',
        'total_events': 'mean'
    }).round(2)
    
    # Flatten column names
    house_stats.columns = ['Athletes', 'Total Points', 'Avg Points', 'Max Points', 'Gold', 'Silver', 'Bronze', 'Avg Events']
    house_stats = house_stats.reset_index()
    
    st.dataframe(house_stats, use_container_width=True)
    
    # Export comprehensive analysis
    if st.button("Download Complete Analysis"):
        # Create comprehensive export
        export_data = df_analysis.copy()
        csv = export_data.to_csv(index=False)
        
        st.download_button(
            label="Download Complete Athlete Data",
            data=csv,
            file_name="complete_athlete_analysis.csv",
            mime="text/csv"
        )