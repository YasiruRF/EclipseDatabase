"""House Points Leaderboard Page - Updated with corrected point calculations"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import DatabaseManager
from config import HOUSES, HOUSE_COLORS
from utils import (
    create_house_points_dataframe,
    create_metric_cards,
    display_warning_message
)

def show_house_points():
    """Display house points leaderboard with corrected calculations"""
    st.header("🏆 House Points Leaderboard")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🏆 Leaderboard", "📊 Analytics", "🎯 Detailed Breakdown", "⚡ Manual Refresh"])