"""Utility functions for the Sports Meet Management System"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any
import re

def format_time(seconds: float) -> str:
    """Convert seconds to MM:SS.ss format for display"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}:{secs:05.2f}"

def parse_time_input(time_str: str) -> float:
    """Parse time input in various formats to seconds"""
    time_str = time_str.strip()
    
    # Handle MM:SS.ss format
    if ':' in time_str:
        try:
            parts = time_str.split(':')
            minutes = float(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        except (ValueError, IndexError):
            raise ValueError("Invalid time format. Use MM:SS or SS.ss")
    
    # Handle seconds only
    try:
        return float(time_str)
    except ValueError:
        raise ValueError("Invalid time format. Use MM:SS or SS.ss")

def validate_curtin_id(curtin_id: str) -> bool:
    """Validate Curtin ID format"""
    # Assuming Curtin ID is 8 digits
    pattern = r'^\d{8}$'
    return bool(re.match(pattern, curtin_id))

def validate_bib_id(bib_id: str) -> bool:
    """Validate Bib ID (should be a positive integer)"""
    try:
        num = int(bib_id)
        return num > 0
    except ValueError:
        return False

def create_results_dataframe(results: List[Dict]) -> pd.DataFrame:
    """Create a formatted DataFrame from results data"""
    if not results:
        return pd.DataFrame()
    
    df_data = []
    for result in results:
        try:
            # Handle different possible data structures
            student_data = result.get("students", {})
            event_data = result.get("events", {})
            
            # If students/events data is a list, take first item
            if isinstance(student_data, list) and student_data:
                student_data = student_data[0]
            if isinstance(event_data, list) and event_data:
                event_data = event_data[0]
            
            df_data.append({
                "Position": result.get("position", "N/A"),
                "Curtin ID": student_data.get("curtin_id", "N/A"),
                "Bib ID": student_data.get("bib_id", "N/A"),
                "First Name": student_data.get("first_name", "Unknown"),
                "Last Name": student_data.get("last_name", ""),
                "House": student_data.get("house", "Unknown"),
                "Event": event_data.get("event_name", "Unknown"),
                "Result": format_result_value(
                    result.get("result_value", 0), 
                    event_data.get("event_type", "")
                ),
                "Points": result.get("points", 0)
            })
        except Exception as e:
            # Skip problematic records but log the issue
            print(f"Error processing result record: {e}")
            continue
    
    return pd.DataFrame(df_data)

def format_result_value(value: float, event_type: str) -> str:
    """Format result value based on event type"""
    if event_type == "Running":
        return format_time(value)
    else:  # Throwing or Jumping
        return f"{value:.2f}m"

def create_house_points_dataframe(house_points: List[Dict]) -> pd.DataFrame:
    """Create a formatted DataFrame from house points data"""
    if not house_points:
        return pd.DataFrame()
    
    df_data = []
    for i, house_data in enumerate(house_points):
        df_data.append({
            "Rank": i + 1,
            "House": house_data["house"],
            "Total Points": house_data["total_points"]
        })
    
    return pd.DataFrame(df_data)

def style_dataframe(df: pd.DataFrame, house_colors: Dict[str, str] = None) -> pd.DataFrame:
    """Apply styling to DataFrame for better presentation"""
    if df.empty:
        return df
    
    # Define house colors
    if house_colors is None:
        house_colors = {
            "Ignis": "#ffebee",    # Light red
            "Nereus": "#e3f2fd",   # Light blue
            "Ventus": "#fffde7",   # Light yellow
            "Terra": "#e8f5e8"     # Light green
        }
    
    def highlight_house(row):
        if "House" in row.index:
            house = row["House"]
            color = house_colors.get(house, "#ffffff")
            return [f'background-color: {color}' if col == "House" else '' for col in row.index]
        return [''] * len(row)
    
    # Apply styling if House column exists
    if "House" in df.columns:
        return df.style.apply(highlight_house, axis=1)
    else:
        return df

def display_success_message(message: str):
    """Display a success message with custom styling"""
    st.success(f"✅ {message}")

def display_error_message(message: str):
    """Display an error message with custom styling"""
    st.error(f"❌ {message}")

def display_warning_message(message: str):
    """Display a warning message with custom styling"""
    st.warning(f"⚠️ {message}")

def display_info_message(message: str):
    """Display an info message with custom styling"""
    st.info(f"ℹ️ {message}")

def create_metric_cards(house_points: List[Dict]):
    """Create metric cards for house points display"""
    if not house_points:
        st.write("No house points data available.")
        return
    
    # Create columns for metric cards
    cols = st.columns(len(house_points))
    
    for i, house_data in enumerate(house_points):
        with cols[i]:
            rank_emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i + 1, "🏆")
            st.metric(
                label=f"{rank_emoji} {house_data['house']} House",
                value=f"{house_data['total_points']} pts",
                delta=f"Rank #{i + 1}"
            )

def export_results_to_csv(results: List[Dict], filename: str = "sports_meet_results.csv"):
    """Export results to CSV format"""
    if not results:
        return None
    
    df = create_results_dataframe(results)
    return df.to_csv(index=False)

def search_and_filter_results(results: List[Dict], search_term: str = "", 
                            house_filter: str = "", event_filter: str = "") -> List[Dict]:
    """Filter results based on search criteria"""
    filtered_results = results
    
    # Apply search term filter
    if search_term:
        search_term = search_term.lower()
        filtered_results = []
        for result in results:
            try:
                student_data = result.get("students", {})
                if isinstance(student_data, list) and student_data:
                    student_data = student_data[0]
                
                # Search in student data
                if (search_term in student_data.get("first_name", "").lower() or
                    search_term in student_data.get("last_name", "").lower() or
                    search_term in str(student_data.get("curtin_id", "")) or
                    search_term in str(student_data.get("bib_id", ""))):
                    filtered_results.append(result)
            except Exception as e:
                print(f"Error filtering result: {e}")
                continue
    
    # Apply house filter
    if house_filter and house_filter != "All":
        temp_filtered = []
        for result in filtered_results:
            try:
                student_data = result.get("students", {})
                if isinstance(student_data, list) and student_data:
                    student_data = student_data[0]
                
                if student_data.get("house") == house_filter:
                    temp_filtered.append(result)
            except Exception as e:
                print(f"Error filtering by house: {e}")
                continue
        filtered_results = temp_filtered
    
    # Apply event filter
    if event_filter and event_filter != "All":
        temp_filtered = []
        for result in filtered_results:
            try:
                event_data = result.get("events", {})
                if isinstance(event_data, list) and event_data:
                    event_data = event_data[0]
                
                if event_data.get("event_name") == event_filter:
                    temp_filtered.append(result)
            except Exception as e:
                print(f"Error filtering by event: {e}")
                continue
        filtered_results = temp_filtered
    
    return filtered_results