"""
Enhanced Main Streamlit application for Sports Meet Event Management System
"""

import streamlit as st
import os
from config import PAGE_CONFIG

# Configure page FIRST before any other Streamlit commands
st.set_page_config(**PAGE_CONFIG)

# Import database after page config
try:
    from database import DatabaseManager
    DATABASE_AVAILABLE = True
except ImportError as e:
    st.error(f"Database import failed: {e}")
    DATABASE_AVAILABLE = False

# Import page modules
try:
    from student_management import show_student_management
    from event_entry import show_event_entry
    from house_points import show_house_points
except ImportError as e:
    st.error(f"Failed to import page modules: {e}")
    st.stop()

# Enhanced CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #fce38a, #95e1d3);
        background-size: 400% 400%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient 15s ease infinite;
        margin-bottom: 2rem;
    }
    
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding: 10px 24px;
        background-color: transparent;
        border-radius: 10px 10px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #4ecdc4;
    }
    
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Enhanced house-specific styling */
    .ignis-house {
        background: linear-gradient(45deg, #ff6b6b, #ff8a80);
        color: white;
    }
    
    .nereus-house {
        background: linear-gradient(45deg, #4ecdc4, #80deea);
        color: white;
    }
    
    .ventus-house {
        background: linear-gradient(45deg, #fce38a, #fff59d);
        color: #333;
    }
    
    .terra-house {
        background: linear-gradient(45deg, #95e1d3, #b2dfdb);
        color: #333;
    }
    
    /* Enhanced performance cards */
    .performance-card {
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1rem 0;
        background: white;
        border-left: 5px solid #4ecdc4;
    }
    
    .champion-card {
        background: linear-gradient(135deg, #FFD700, #FFA500);
        color: #333;
        font-weight: bold;
        text-align: center;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def check_environment():
    """Check if required environment variables are set"""
    required_vars = ["SUPABASE_URL", "SUPABASE_KEY"]
    missing_vars = []
    
    for var in required_vars:
        # Check both environment variables and Streamlit secrets
        if not (os.getenv(var) or st.secrets.get(var, None)):
            missing_vars.append(var)
    
    return missing_vars



def show_database_setup():
    """Show enhanced database setup instructions"""
    st.markdown("""
    ## Database Setup Required
    
    To use this application, you need to:
    
    ### 1. Set up Supabase Database
    
    Run the SQL commands from the `database_setup.sql` in your Supabase SQL editor to create the required tables.
    
    ### 2. Configure Environment Variables
    
    **For local development**, create a `.env` file:
    ```
    SUPABASE_URL=your_supabase_project_url
    SUPABASE_KEY=your_supabase_anon_key
    ```
    
    **For Streamlit Cloud deployment**, add these to your app secrets:
    ```toml
    SUPABASE_URL = "your_supabase_project_url"
    SUPABASE_KEY = "your_supabase_anon_key"
    ```
    """)

def main():
    """Enhanced main application function"""
    
    # App header
    st.markdown('<h1 class="main-header">Sports Meet Manager</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        
        st.markdown("---")
        
        # Enhanced house legend
        st.markdown("""
        ### Houses
        🔥 **Ignis** (Fire/Red)  
        🌊 **Nereus** (Water/Blue)  
        💨 **Ventus** (Air/Yellow)  
        🌱 **Terra** (Earth/Green)
        """)
        
        st.markdown("---")
        
        # Enhanced tips section
        st.markdown("""
        ### Features
        - **Simplified event management** for Track and Field events.
        - **Flexible point systems** for individual and relay events.
        - **Real-time leaderboard** for house points.
        """)
        
        st.markdown("---")
        st.markdown("*Sports Meet Manager v2.0*")
    
    # Enhanced main content tabs
    try:
        tab1, tab2, tab3 = st.tabs([
            "Students", 
            "Event Entry", 
            "House Points"
        ])
        
        with tab1:
            show_student_management()
        
        with tab2:
            show_event_entry()
        
        with tab3:
            show_house_points()
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")
        
        # Show error details in expander for debugging
        with st.expander("Error Details"):
            st.exception(e)

if __name__ == "__main__":
    main()