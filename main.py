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
    from results_view import show_results_view
    from house_points import show_house_points
    from individual_athletes import show_individual_athletes
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

def initialize_database():
    """Initialize database connection and create tables if needed"""
    if not DATABASE_AVAILABLE:
        return False
        
    # Check environment variables first
    missing_vars = check_environment()
    if missing_vars:
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        st.error("Please set SUPABASE_URL and SUPABASE_KEY in your environment or Streamlit secrets.")
        return False
    
    try:
        # Initialize database manager if not already in session state
        if "db_manager" not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
            
        # Verify database connection
        db = st.session_state.db_manager
        if not db._test_connection():
            st.error("Failed to connect to database. Please check your Supabase configuration.")
            return False
            
        # Initialize some default events if none exist
        try:
            existing_events = db.get_all_events()
            
            if not existing_events:
                # Add some default events with proper point allocations
                from config import EVENTS, DEFAULT_INDIVIDUAL_POINTS, DEFAULT_RELAY_POINTS
                
                success_count = 0
                for event_type, events_list in EVENTS.items():
                    for event_info in events_list[:3]:  # Add first 3 events of each type
                        is_relay = event_info.get("is_relay", False)
                        point_allocation = DEFAULT_RELAY_POINTS if is_relay else DEFAULT_INDIVIDUAL_POINTS
                        point_system_name = "Relay Events" if is_relay else "Individual Events"
                        
                        if db.add_event(
                            event_name=event_info["name"],
                            event_type=event_type,
                            unit=event_info["unit"],
                            is_relay=is_relay,
                            point_allocation=point_allocation,
                            point_system_name=point_system_name
                        ):
                            success_count += 1
                
                if success_count > 0:
                    st.success(f"Initialized {success_count} default events with proper point allocations.")
                    
        except Exception as e:
            st.warning(f"Could not initialize default events: {str(e)}")
        
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        st.error("Please check your Supabase credentials and database setup.")
        return False

def show_database_setup():
    """Show enhanced database setup instructions"""
    st.markdown("""
    ## Enhanced Database Setup Required
    
    To use this application, you need to:
    
    ### 1. Set up Supabase Database
    
    Run the SQL commands from the enhanced `database_setup.sql` in your Supabase SQL editor to create the required tables with new features:
    - **Gender field** for individual athlete tracking
    - **Enhanced point allocation** system
    - **Relay event support**
    - **Individual athlete performance views**
    
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
    
    ### 3. Enhanced Features
    
    The system now includes:
    - **Individual athlete tracking** with gender-based rankings
    - **Flexible point allocation** for different event types
    - **Enhanced time input** for track events (MM:SS.ms format)
    - **Field event distance tracking** in meters
    - **Relay event support** with higher point allocations
    
    ### 4. House & Gender System
    
    The system uses four houses with gender-based athlete tracking:
    - **Ignis** (Red) - Fire element
    - **Nereus** (Blue) - Water element  
    - **Ventus** (Yellow) - Air element
    - **Terra** (Green) - Earth element
    
    Gender options: Male, Female, Other
    
    ### 5. Point Allocation Systems
    
    - **Individual Events**: 10, 8, 6, 5, 4, 3, 2, 1 points
    - **Relay Events**: 20, 16, 12, 10, 8, 6, 4, 2 points
    - **Custom**: Define your own point system
    """)

def show_sidebar_stats(db):
    """Show enhanced sidebar statistics"""
    try:
        students_count = len(db.get_all_students())
        events_count = len(db.get_all_events())
        
        # Get athlete performance for additional stats
        athletes = db.get_individual_athlete_performance(limit=5)
        top_performers = len(athletes)
        
        st.markdown("### Quick Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Students", students_count)
            st.metric("Active Athletes", top_performers)
        
        with col2:
            st.metric("Events", events_count)
            
        # Show best athletes summary
        if athletes:
            st.markdown("### Champions")
            best_athletes = db.get_best_athletes_by_gender()
            
            for gender in ['Male', 'Female']:
                if gender in best_athletes:
                    athlete = best_athletes[gender]
                    st.markdown(f"""
                    **Best {gender}**: {athlete['first_name']} {athlete['last_name']}  
                    ({athlete['house']} - {athlete['total_points']} pts)
                    """)
            
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")

def main():
    """Enhanced main application function"""
    
    # App header
    st.markdown('<h1 class="main-header">Sports Meet Manager</h1>', unsafe_allow_html=True)
    
    # Initialize database
    if not initialize_database():
        show_database_setup()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        
        # Enhanced stats in sidebar
        if "db_manager" in st.session_state:
            show_sidebar_stats(st.session_state.db_manager)
        
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
        ### New Features
        - **Gender-based rankings** for best male/female athletes
        - **Flexible point systems** for different event types
        - **Enhanced time input** (MM:SS.ms format)
        - **Relay event support** with higher points
        - **Individual athlete tracking** and performance analysis
        """)
        
        st.markdown("---")
        st.markdown("*Enhanced Sports Meet Manager v1.0*")
    
    # Enhanced main content tabs
    try:
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Students", 
            "Event Entry", 
            "Results", 
            "House Points",
            "Individual Athletes"
        ])
        
        with tab1:
            show_student_management()
        
        with tab2:
            show_event_entry()
        
        with tab3:
            show_results_view()
        
        with tab4:
            show_house_points()
        
        with tab5:
            show_individual_athletes()
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")
        
        # Show error details in expander for debugging
        with st.expander("Error Details"):
            st.exception(e)

if __name__ == "__main__":
    main()