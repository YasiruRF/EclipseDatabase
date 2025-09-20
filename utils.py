"""Enhanced utility functions for the Sports Meet Management System"""

import pandas as pd
import streamlit as st
from typing import List, Dict, Any
import re

def format_time_for_display(seconds: float) -> str:
    """Convert seconds to MM:SS.ms format for display"""
    if seconds < 60:
        return f"{seconds:.2f}s"
    else:
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:05.2f}"

def parse_time_input(time_str: str) -> float:
    """Parse time input in MM:SS.ms format to seconds"""
    time_str = time_str.strip()
    
    # Handle MM:SS.ms or MM:SS format
    if ':' in time_str:
        try:
            parts = time_str.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid time format")
            
            minutes = float(parts[0])
            seconds = float(parts[1])
            
            if minutes < 0 or seconds < 0 or seconds >= 60:
                raise ValueError("Invalid time values")
            
            total_seconds = minutes * 60 + seconds
            return total_seconds
        except (ValueError, IndexError):
            raise ValueError("Invalid time format. Use MM:SS.ms (e.g., 1:23.45)")
    
    # Handle seconds only (for sub-minute times)
    try:
        seconds = float(time_str)
        if seconds <= 0:
            raise ValueError("Time must be positive")
        return seconds
    except ValueError:
        raise ValueError("Invalid time format. Use MM:SS.ms or seconds")

def validate_time_input(time_str: str) -> bool:
    """Validate time input format"""
    try:
        parse_time_input(time_str)
        return True
    except ValueError:
        return False

def validate_distance_input(distance_str: str) -> bool:
    """Validate distance input for field events"""
    try:
        distance = float(distance_str)
        return distance > 0
    except ValueError:
        return False

def validate_curtin_id(curtin_id: str) -> bool:
    """Validate Curtin ID format (8 digits)"""
    pattern = r'^\d{8}$'
    return bool(re.match(pattern, curtin_id))

def validate_bib_id(bib_id: str) -> bool:
    """Validate Bib ID (should be a positive integer)"""
    try:
        num = int(bib_id)
        return num > 0
    except ValueError:
        return False

def validate_point_allocation(point_allocation: Dict) -> bool:
    """Validate point allocation dictionary"""
    try:
        # Check if all values are non-negative integers
        for position, points in point_allocation.items():
            if not isinstance(points, int) or points < 0:
                return False
        return True
    except:
        return False

def get_time_input_placeholder(event_name: str) -> str:
    """Get appropriate placeholder text for time input based on event"""
    if any(distance in event_name for distance in ['100m', '200m', '400m']):
        return "e.g., 12.34 (seconds)"
    else:
        return "e.g., 1:23.45 (MM:SS.ms)"

def is_relay_event(event_name: str) -> bool:
    """Check if an event is a relay event"""
    relay_keywords = ['relay', '4x', '4 x']
    return any(keyword in event_name.lower() for keyword in relay_keywords)

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

def format_result_value(value: float, event_type: str) -> str:
    """Format result value based on event type"""
    if event_type == "Track":
        return format_time_for_display(value)
    else:  # Field events
        return f"{value:.2f}m"

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
                "Name": f"{student_data.get('first_name', 'Unknown')} {student_data.get('last_name', '')}",
                "House": student_data.get("house", "Unknown"),
                "Gender": student_data.get("gender", "N/A"),
                "Event": event_data.get("event_name", "Unknown"),
                "Event Type": event_data.get("event_type", "Unknown"),
                "Result": format_result_value(
                    result.get("result_value", 0), 
                    event_data.get("event_type", "")
                ),
                "Points": result.get("points", 0),
                "Is Relay": "Yes" if event_data.get("is_relay", False) else "No"
            })
        except Exception as e:
            print(f"Error processing result record: {e}")
            continue
    
    return pd.DataFrame(df_data)

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

def create_athlete_performance_dataframe(athletes: List[Dict]) -> pd.DataFrame:
    """Create DataFrame for individual athlete performance"""
    if not athletes:
        return pd.DataFrame()
    
    df_data = []
    for athlete in athletes:
        try:
            df_data.append({
                "Rank": athlete.get("overall_rank", athlete.get("gender_rank", "N/A")),
                "Bib ID": athlete.get("bib_id", "N/A"),
                "Name": f"{athlete.get('first_name', 'Unknown')} {athlete.get('last_name', '')}",
                "House": athlete.get("house", "Unknown"),
                "Gender": athlete.get("gender", "N/A"),
                "Events": athlete.get("total_events", 0),
                "Total Points": athlete.get("total_points", 0),
                "Gold": athlete.get("gold_medals", 0),
                "Silver": athlete.get("silver_medals", 0),
                "Bronze": athlete.get("bronze_medals", 0),
                "Total Medals": athlete.get("gold_medals", 0) + athlete.get("silver_medals", 0) + athlete.get("bronze_medals", 0)
            })
        except Exception as e:
            print(f"Error processing athlete record: {e}")
            continue
    
    return pd.DataFrame(df_data)

def export_athletes_to_csv(athletes: List[Dict], filename: str = "athlete_performance.csv"):
    """Export athlete performance to CSV format"""
    if not athletes:
        return None
    
    df = create_athlete_performance_dataframe(athletes)
    return df.to_csv(index=False)