"""
Main Streamlit application for Sports Meet Event Management System
"""

import streamlit as st
from config import PAGE_CONFIG
from database import DatabaseManager

# Import page modules
from student_management import show_student_management
from event_entry import show_event_entry
from results_view import show_results_view
from house_points import show_house_points

# Configure page
st.set_page_config(**PAGE_CONFIG)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #95e1d3, #fce38a);
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
</style>
""", unsafe_allow_html=True)

def initialize_database():
    """Initialize database connection and create tables if needed"""
    try:
        if "db_manager" not in st.session_state:
            st.session_state.db_manager = DatabaseManager()
            
        # Initialize some default events if none exist
        db = st.session_state.db_manager
        existing_events = db.get_all_events()
        
        if not existing_events:
            # Add some default events
            from config import EVENTS, DEFAULT_POINT_ALLOCATION
            
            for event_type, events_list in EVENTS.items():
                for event_info in events_list[:2]:  # Add first 2 events of each type
                    db.add_event(
                        event_name=event_info["name"],
                        event_type=event_type,
                        unit=event_info["unit"],
                        point_allocation=DEFAULT_POINT_ALLOCATION
                    )
        
        return True
    except Exception as e:
        st.error(f"Failed to initialize database: {str(e)}")
        st.error("Please check your Supabase credentials in the .env file or Streamlit secrets.")
        return False

def show_database_setup():
    """Show database setup instructions"""
    st.markdown("""
    ## 🔧 Database Setup Required
    
    To use this application, you need to set up Supabase tables. Please run the following SQL commands in your Supabase SQL editor:
    
    ```sql
    -- Students table
    CREATE TABLE IF NOT EXISTS students (
        curtin_id VARCHAR PRIMARY KEY,
        bib_id INTEGER UNIQUE NOT NULL,
        first_name VARCHAR NOT NULL,
        last_name VARCHAR NOT NULL,
        house VARCHAR NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Events table
    CREATE TABLE IF NOT EXISTS events (
        event_id SERIAL PRIMARY KEY,
        event_name VARCHAR NOT NULL,
        event_type VARCHAR NOT NULL,
        unit VARCHAR NOT NULL,
        point_allocation JSONB DEFAULT '{}',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Results table
    CREATE TABLE IF NOT EXISTS results (
        result_id SERIAL PRIMARY KEY,
        curtin_id VARCHAR REFERENCES students(curtin_id),
        event_id INTEGER REFERENCES events(event_id),
        result_value DECIMAL NOT NULL,
        points INTEGER DEFAULT 0,
        position INTEGER,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(curtin_id, event_id)
    );
    ```
    
    ### Environment Setup
    
    1. Create a `.env` file with your Supabase credentials:
    ```
    SUPABASE_URL=your_supabase_project_url
    SUPABASE_KEY=your_supabase_anon_key
    ```
    
    2. Or set them in Streamlit Cloud secrets if deploying online.
    
    3. Refresh this page after setting up the database.
    """)

def main():
    """Main application function"""
    
    # App header
    st.markdown('<h1 class="main-header">🏃‍♂️ Sports Meet Manager</h1>', unsafe_allow_html=True)
    
    # Initialize database
    if not initialize_database():
        show_database_setup()
        return
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("## 🏆 Navigation")
        
        # Quick stats in sidebar
        if "db_manager" in st.session_state:
            db = st.session_state.db_manager
            
            with st.container():
                students_count = len(db.get_all_students())
                events_count = len(db.get_all_events())
                
                st.markdown("### 📊 Quick Stats")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("👥 Students", students_count)
                
                with col2:
                    st.metric("🎯 Events", events_count)
        
        st.markdown("---")
        
        # Recent activity or tips
        st.markdown("""
        ### 💡 Tips
        - Search students by Bib ID for quick entry
        - Results are automatically ranked
        - Points update in real-time
        - Export results as CSV
        """)
        
        st.markdown("---")
        st.markdown("*Built with Streamlit & Supabase*")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "👥 Students", 
        "📝 Event Entry", 
        "🏆 Results", 
        "🏠 House Points"
    ])
    
    with tab1:
        show_student_management()
    
    with tab2:
        show_event_entry()
    
    with tab3:
        show_results_view()
    
    with tab4:
        show_house_points()

if __name__ == "__main__":
    main()