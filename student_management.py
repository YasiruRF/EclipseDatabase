"""Enhanced Student Management Page with Gender Field"""

import streamlit as st
from database import DatabaseManager
from config import HOUSES, GENDER_OPTIONS
from utils import (
    validate_curtin_id, 
    validate_bib_id, 
    display_success_message, 
    display_error_message,
    display_warning_message
)
import pandas as pd
from typing import List, Dict

def show_student_management():
    """Display enhanced student management interface with gender"""
    st.header("👥 Student Management")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different student operations
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Student", "🔍 Search Student", "📋 All Students", "🏆 Top Athletes"])
    
    with tab1:
        show_add_student_form(db)
    
    with tab2:
        show_search_student(db)
    
    with tab3:
        show_all_students(db)
    
    with tab4:
        show_top_athletes(db)

def show_add_student_form(db: DatabaseManager):
    """Display form to add new student with gender"""
    st.subheader("Add New Student")
    
    with st.form("add_student_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            curtin_id = st.text_input(
                "Curtin ID",
                placeholder="Enter 8-digit Curtin ID",
                help="Enter student's 8-digit Curtin ID"
            )
            
            first_name = st.text_input(
                "First Name",
                placeholder="Enter first name"
            )
            
            bib_id = st.text_input(
                "Bib ID",
                placeholder="Enter bib number",
                help="Unique bib number for the student"
            )
        
        with col2:
            last_name = st.text_input(
                "Last Name", 
                placeholder="Enter last name"
            )
            
            # Gender selector
            gender = st.selectbox(
                "Gender",
                options=GENDER_OPTIONS,
                help="Select student's gender for athlete rankings"
            )
            
            # House selector with descriptions
            house_options = [f"{house} {'🔥' if house == 'Ignis' else '🌊' if house == 'Nereus' else '💨' if house == 'Ventus' else '🌱'}" for house in HOUSES]
            house_selection = st.selectbox(
                "House",
                options=house_options,
                help="Select student's house"
            )
            # Extract house name without emoji
            house = house_selection.split()[0]
        
        submitted = st.form_submit_button("Add Student", type="primary")
        
        if submitted:
            # Validate inputs
            errors = []
            
            if not curtin_id or not validate_curtin_id(curtin_id):
                errors.append("Please enter a valid 8-digit Curtin ID")
            
            if not bib_id or not validate_bib_id(bib_id):
                errors.append("Please enter a valid Bib ID (positive integer)")
            
            if not first_name.strip():
                errors.append("Please enter first name")
            
            if not last_name.strip():
                errors.append("Please enter last name")
            
            # Check if student already exists
            existing_student = db.get_student_by_bib(int(bib_id)) if validate_bib_id(bib_id) else None
            if existing_student:
                errors.append(f"Student with Bib ID {bib_id} already exists")
            
            if errors:
                for error in errors:
                    display_error_message(error)
            else:
                # Add student to database with gender
                success = db.add_student(
                    curtin_id=curtin_id,
                    bib_id=int(bib_id),
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    house=house,
                    gender=gender
                )
                
                if success:
                    display_success_message(f"Student {first_name} {last_name} ({gender}) added successfully!")
                    st.balloons()
                    # Clear form by rerunning
                    st.rerun()

def show_search_student(db: DatabaseManager):
    """Display student search functionality"""
    st.subheader("Search Student by Bib ID")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_bib = st.text_input(
            "Enter Bib ID to search",
            placeholder="Enter bib number",
            key="search_bib_input"
        )
    
    with col2:
        search_button = st.button("🔍 Search", type="primary")
    
    if search_button or search_bib:
        if validate_bib_id(search_bib):
            student = db.get_student_by_bib(int(search_bib))
            
            if student:
                # Display student details in a nice format
                st.success("Student found!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Curtin ID", student["curtin_id"])
                    st.metric("First Name", student["first_name"])
                
                with col2:
                    st.metric("Bib ID", student["bib_id"])
                    st.metric("Last Name", student["last_name"])
                
                with col3:
                    house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
                    emoji = house_emoji.get(student["house"], "🏆")
                    st.metric("House", f"{emoji} {student['house']}")
                    st.metric("Gender", student.get("gender", "Not specified"))
                
                # Show student info card
                with st.container():
                    st.markdown("---")
                    house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
                    emoji = house_emoji.get(student['house'], "🏆")
                    gender_emoji = {"Male": "👨", "Female": "👩", "Other": "🧑"}
                    gender_icon = gender_emoji.get(student.get('gender', 'Other'), "🧑")
                    
                    st.markdown(f"""
                    ### 🏃‍♂️ {student['first_name']} {student['last_name']}
                    
                    - **Curtin ID:** {student['curtin_id']}
                    - **Bib ID:** {student['bib_id']}
                    - **House:** {emoji} {student['house']}
                    - **Gender:** {gender_icon} {student.get('gender', 'Not specified')}
                    - **Registered:** {student['created_at'][:10]}
                    """)
            else:
                display_warning_message(f"No student found with Bib ID {search_bib}")
        else:
            display_error_message("Please enter a valid Bib ID")

def show_all_students(db: DatabaseManager):
    """Display all students in a table with gender"""
    st.subheader("All Registered Students")
    
    students = db.get_all_students()
    
    if not students:
        display_warning_message("No students registered yet.")
        return
    
    # Add search and filter options
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input(
            "Search students", 
            placeholder="Search by name, Curtin ID, or Bib ID",
            key="all_students_search"
        )
    
    with col2:
        house_filter = st.selectbox(
            "Filter by House",
            options=["All"] + HOUSES,
            key="all_students_house_filter"
        )
    
    with col3:
        gender_filter = st.selectbox(
            "Filter by Gender",
            options=["All"] + GENDER_OPTIONS,
            key="all_students_gender_filter"
        )
    
    with col4:
        st.metric("Total Students", len(students))
    
    # Filter students based on search criteria
    filtered_students = filter_students(students, search_term, house_filter, gender_filter)
    
    if not filtered_students:
        display_warning_message("No students match the current filters.")
        return
    
    # Create DataFrame for display
    df_data = []
    for student in filtered_students:
        house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
        emoji = house_emoji.get(student["house"], "🏆")
        gender_emoji = {"Male": "👨", "Female": "👩", "Other": "🧑"}
        gender_icon = gender_emoji.get(student.get("gender", "Other"), "🧑")
        
        df_data.append({
            "Curtin ID": student["curtin_id"],
            "Bib ID": student["bib_id"],
            "Name": f"{student['first_name']} {student['last_name']}",
            "House": f"{emoji} {student['house']}",
            "Gender": f"{gender_icon} {student.get('gender', 'Not specified')}",
            "Registered": student["created_at"][:10]
        })
    
    df = pd.DataFrame(df_data)
    
    # Style the dataframe with house colors
    house_colors = {
        "🔥 Ignis": "#ffebee",    # Light red
        "🌊 Nereus": "#e3f2fd",   # Light blue
        "💨 Ventus": "#fffde7",   # Light yellow
        "🌱 Terra": "#e8f5e8"     # Light green
    }
    
    def highlight_house(row):
        house = row["House"]
        color = house_colors.get(house, "#ffffff")
        return [f'background-color: {color}' if col == "House" else '' for col in row.index]
    
    # Display the styled dataframe
    styled_df = df.style.apply(highlight_house, axis=1)
    st.dataframe(styled_df, use_container_width=True)
    
    # Show summary statistics
    st.markdown("---")
    st.subheader("📊 Summary Statistics")
    
    # House statistics
    st.markdown("#### By House")
    house_names = [student['house'] for student in filtered_students]
    house_counts = pd.Series(house_names).value_counts()
    
    col1, col2, col3, col4 = st.columns(4)
    house_emojis = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
    
    for i, house in enumerate(HOUSES):
        count = house_counts.get(house, 0)
        emoji = house_emojis.get(house, "🏆")
        with [col1, col2, col3, col4][i]:
            st.metric(f"{emoji} {house}", count)
    
    # Gender statistics
    st.markdown("#### By Gender")
    gender_names = [student.get('gender', 'Not specified') for student in filtered_students]
    gender_counts = pd.Series(gender_names).value_counts()
    
    col1, col2, col3 = st.columns(3)
    gender_emojis = {"Male": "👨", "Female": "👩", "Other": "🧑"}
    
    for i, gender in enumerate(["Male", "Female", "Other"]):
        count = gender_counts.get(gender, 0)
        emoji = gender_emojis.get(gender, "🧑")
        if i < 3:
            with [col1, col2, col3][i]:
                st.metric(f"{emoji} {gender}", count)



def filter_students(students, search_term="", house_filter="All", gender_filter="All"):
    """Filter students based on search criteria including gender"""
    filtered = students
    
    # Apply search term filter
    if search_term:
        search_term = search_term.lower()
        filtered = [
            student for student in filtered
            if (search_term in student["first_name"].lower() or
                search_term in student["last_name"].lower() or
                search_term in student["curtin_id"].lower() or
                search_term in str(student["bib_id"]))
        ]
    
    # Apply house filter
    if house_filter != "All":
        filtered = [
            student for student in filtered
            if student["house"] == house_filter
        ]
    
    # Apply gender filter
    if gender_filter != "All":
        filtered = [
            student for student in filtered
            if student.get("gender", "Not specified") == gender_filter
        ]
    
    return filtered

def show_top_athletes(db: DatabaseManager):
    """Display top individual athletes"""
    st.subheader("🏆 Top Individual Athletes")
    
    # Get individual athlete performance
    athletes = db.get_individual_athlete_performance(limit=20)
    
    if not athletes:
        display_warning_message("No athlete performance data available yet. Add some results first!")
        return
    
    # Display overall top athletes
    st.markdown("### 🎯 Overall Top Athletes")
    
    # Create tabs for different rankings
    tab1, tab2, tab3 = st.tabs(["🏆 Overall Rankings", "👨 Best Male Athletes", "👩 Best Female Athletes"])
    
    with tab1:
        display_athlete_ranking(athletes, "Overall Top 10", limit=10)
    
    with tab2:
        male_athletes = [a for a in athletes if a.get('gender') == 'Male']
        display_athlete_ranking(male_athletes, "Top Male Athletes", limit=10)
    
    with tab3:
        female_athletes = [a for a in athletes if a.get('gender') == 'Female']
        display_athlete_ranking(female_athletes, "Top Female Athletes", limit=10)
    
    # Best athletes by gender summary
    st.markdown("---")
    st.markdown("### 🥇 Champions")
    
    best_athletes = db.get_best_athletes_by_gender()
    
    if best_athletes:
        cols = st.columns(len([k for k in best_athletes.keys() if k in ['Male', 'Female']]))
        col_idx = 0
        
        for gender in ['Male', 'Female']:
            if gender in best_athletes:
                athlete = best_athletes[gender]
                house_emoji = {"Ignis": "🔥", "Nereus": "🌊", "Ventus": "💨", "Terra": "🌱"}
                house_icon = house_emoji.get(athlete['house'], "🏆")
                
                with cols[col_idx]:
                    st.markdown(f"""
                    #### 🏆 Best {gender} Athlete
                    **{athlete['first_name']} {athlete['last_name']}**
                    - **House:** {house_icon} {athlete['house']}
                    - **Bib ID:** {athlete['bib_id']}
                    - **Total Points:** {athlete['total_points']}
                    - **Gold Medals:** {athlete['gold_medals']}
                    - **Events:** {athlete['total_events']}
                    """)
                col_idx += 1

def display_athlete_ranking(athletes: List[Dict], title: str, limit: int = 10):
    """Display athlete ranking table"""
    if not athletes:
        display_warning_message("No athlete data available.")
        return
    
    # Limit results
    display_athletes = athletes[:limit]
    
    # Create and display DataFrame
    from utils import create_athlete_performance_dataframe
    df = create_athlete_performance_dataframe(display_athletes)
    
    if not df.empty:
        # Style the dataframe
        def highlight_top_3(row):
            rank = row.get("Rank", 999)
            if rank == 1:
                return ['background-color: #FFD700; font-weight: bold'] * len(row)  # Gold
            elif rank == 2:
                return ['background-color: #C0C0C0; font-weight: bold'] * len(row)  # Silver
            elif rank == 3:
                return ['background-color: #CD7F32; font-weight: bold'] * len(row)  # Bronze
            else:
                return [''] * len(row)
        
        styled_df = df.style.apply(highlight_top_3, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Export option
        from utils import export_athletes_to_csv
        csv = export_athletes_to_csv(display_athletes)
        if csv:
            st.download_button(
                label=f"📥 Download {title}",
                data=csv,
                file_name=f"{title.replace(' ', '_').lower()}.csv",
                mime="text/csv"
            )