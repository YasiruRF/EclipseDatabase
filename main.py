"""
Main Streamlit application for Sports Meet Event Management System
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
except ImportError as e:
    st.error(f"Failed to import page modules: {e}")
    st.stop()

# Custom CSS for better styling with new house colors
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
    
    /* House-specific styling */
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
                # Add some default events
                from config import EVENTS, DEFAULT_POINT_ALLOCATION
                
                success_count = 0
                for event_type, events_list in EVENTS.items():
                    for event_info in events_list[:2]:  # Add first 2 events of each type
                        if db.add_event(
                            event_name=event_info["name"],
                            event_type=event_type,
                            unit=event_info["unit"],
                            point_allocation=DEFAULT_POINT_ALLOCATION
                        ):
                            success_count += 1
                
                if success_count > 0:
                    st.success(f"Initialized {success_count} default events.")
                    
        except Exception as e:
            st.warning(f"Could not initialize default events: {str(e)}")
        
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        st.error("Please check your Supabase credentials and database setup.")
        return False

def show_database_setup():
    """Show database setup instructions"""
    st.markdown("""
    ## Database Setup Required
    
    To use this application, you need to:
    
    ### 1. Set up Supabase Database
    
    Run the SQL commands from `database_setup.sql` in your Supabase SQL editor to create the required tables.
    
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
    
    ### 3. Database Tables
    
    The following tables must be created in your Supabase project:
    - `students` - Student registration data
    - `events` - Event definitions
    - `results` - Competition results
    
    Refer to `database_setup.sql` for the complete schema.
    
    ### 4. House Information
    
    The system uses four houses:
    - **Ignis** (Red) 🔥
    - **Nereus** (Blue) 🌊
    - **Ventus** (Yellow) 💨
    - **Terra** (Green) 🌍
    
    ### 5. Troubleshooting
    
    If you continue to have issues:
    1. Verify your Supabase project URL and anon key
    2. Check that your database tables exist
    3. Ensure your Supabase project allows connections
    4. Check the Streamlit logs for specific error messages
    """)

def show_connection_error():
    """Show connection error page"""
    st.error("Database Connection Failed")
    st.markdown("""
    The application cannot connect to the database. This could be due to:
    
    - Missing or incorrect Supabase credentials
    - Database tables not created
    - Network connectivity issues
    - Supabase service issues
    
    Please check your configuration and try refreshing the page.
    """)
    
    if st.button("Retry Connection"):
        st.rerun()

def show_sidebar_stats(db):
    """Show sidebar statistics safely"""
    try:
        students_count = len(db.get_all_students())
        events_count = len(db.get_all_events())
        
        st.markdown("### Quick Stats")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Students", students_count)
        
        with col2:
            st.metric("Events", events_count)
            
    except Exception as e:
        st.error(f"Error loading stats: {str(e)}")

def main():
    """Main application function"""
    
    # App header
    st.markdown('<h1 class="main-header">Sports Meet Manager</h1>', unsafe_allow_html=True)
    
    # Initialize database
    if not initialize_database():
        show_database_setup()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## Navigation")
        
        # Quick stats in sidebar with error handling
        if "db_manager" in st.session_state:
            show_sidebar_stats(st.session_state.db_manager)
        
        st.markdown("---")
        
        # House legend
        st.markdown("""
        ### Houses
        🔥 **Ignis** (Red)  
        🌊 **Nereus** (Blue)  
        💨 **Ventus** (Yellow)  
        🌍 **Terra** (Green)
        """)
        
        st.markdown("---")
        
        # Tips section
        st.markdown("""
        ### Tips
        - Search students by Bib ID for quick entry
        - Results are automatically ranked
        - Points update in real-time
        - Export results as CSV
        """)
        
        st.markdown("---")
        st.markdown("*Built with Streamlit & Supabase*")
    
    # Main content tabs with error handling
    try:
        tab1, tab2, tab3, tab4 = st.tabs([
            "Students", 
            "Event Entry", 
            "Results", 
            "House Points"
        ])
        
        with tab1:
            show_student_management()
        
        with tab2:
            show_event_entry()
        
        with tab3:
            show_results_view()
        
        with tab4:
            show_house_points()
            
    except Exception as e:
        st.error(f"Application error: {str(e)}")
        st.info("Please refresh the page and try again.")
        
        # Show error details in expander for debugging
        with st.expander("Error Details"):
            st.exception(e)

if __name__ == "__main__":
    main()