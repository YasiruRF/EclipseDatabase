"""Student Management Page"""

import streamlit as st
from database import DatabaseManager
from config import HOUSES
from utils import (
    validate_curtin_id, 
    validate_bib_id, 
    display_success_message, 
    display_error_message,
    display_warning_message
)
import pandas as pd

def show_student_management():
    """Display student management interface"""
    st.header("👥 Student Management")
    
    # Initialize database manager
    if "db_manager" not in st.session_state:
        st.session_state.db_manager = DatabaseManager()
    
    db = st.session_state.db_manager
    
    # Create tabs for different student operations
    tab1, tab2, tab3 = st.tabs(["➕ Add Student", "🔍 Search Student", "📋 All Students"])
    
    with tab1:
        show_add_student_form(db)
    
    with tab2:
        show_search_student(db)
    
    with tab3:
        show_all_students(db)

def show_add_student_form(db: DatabaseManager):
    """Display form to add new student"""
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
            
            house = st.selectbox(
                "House",
                options=HOUSES,
                help="Select student's house"
            )
        
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
                # Add student to database
                success = db.add_student(
                    curtin_id=curtin_id,
                    bib_id=int(bib_id),
                    first_name=first_name.strip(),
                    last_name=last_name.strip(),
                    house=house
                )
                
                if success:
                    display_success_message(f"Student {first_name} {last_name} added successfully!")
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
                    st.metric("House", student["house"])
                    st.metric("Added", student["created_at"][:10])  # Show date only
                
                # Show student info card
                with st.container():
                    st.markdown("---")
                    st.markdown(f"""
                    ### 🏃‍♂️ {student['first_name']} {student['last_name']}
                    
                    - **Curtin ID:** {student['curtin_id']}
                    - **Bib ID:** {student['bib_id']}
                    - **House:** {student['house']}
                    - **Registered:** {student['created_at'][:10]}
                    """)
            else:
                display_warning_message(f"No student found with Bib ID {search_bib}")
        else:
            display_error_message("Please enter a valid Bib ID")

def show_all_students(db: DatabaseManager):
    """Display all students in a table"""
    st.subheader("All Registered Students")
    
    students = db.get_all_students()
    
    if not students:
        display_warning_message("No students registered yet.")
        return
    
    # Add search and filter options
    col1, col2, col3 = st.columns([2, 1, 1])
    
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
        st.metric("Total Students", len(students))
    
    # Filter students based on search criteria
    filtered_students = filter_students(students, search_term, house_filter)
    
    if not filtered_students:
        display_warning_message("No students match the current filters.")
        return
    
    # Create DataFrame for display
    df_data = []
    for student in filtered_students:
        df_data.append({
            "Curtin ID": student["curtin_id"],
            "Bib ID": student["bib_id"],
            "Name": f"{student['first_name']} {student['last_name']}",
            "First Name": student["first_name"],
            "Last Name": student["last_name"],
            "House": student["house"],
            "Registered": student["created_at"][:10]
        })
    
    df = pd.DataFrame(df_data)
    
    # Style the dataframe
    house_colors = {
        "Red": "#ffebee",
        "Blue": "#e3f2fd",
        "Green": "#e8f5e8", 
        "Yellow": "#fffde7"
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
    
    house_counts = df['House'].value_counts()
    
    col1, col2, col3, col4 = st.columns(4)
    for i, (house, count) in enumerate(house_counts.items()):
        with [col1, col2, col3, col4][i % 4]:
            st.metric(f"{house} House", count)

def filter_students(students, search_term="", house_filter="All"):
    """Filter students based on search criteria"""
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
    
    return filtered