"""Database operations using Supabase with improved error handling"""

import os
from typing import List, Dict, Optional
import streamlit as st
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Handle Supabase import gracefully
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.error("Supabase not available")

# Handle dotenv import gracefully
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    logger.info("python-dotenv not available, using environment variables directly")

class DatabaseManager:
    def __init__(self):
        """Initialize Supabase client with improved error handling"""
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")
            
        try:
            # Get credentials from environment variables or Streamlit secrets
            url = self._get_credential("SUPABASE_URL")
            key = self._get_credential("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY")
            
            # Create Supabase client
            self.supabase: Client = create_client(url, key)
            
            # Test connection
            if not self._test_connection():
                raise ConnectionError("Failed to establish database connection")
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    def _get_credential(self, key: str) -> str:
        """Get credential from environment or Streamlit secrets"""
        # First try environment variables
        value = os.getenv(key)
        if value:
            return value
        
        # Then try Streamlit secrets if available
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except Exception as e:
            logger.warning(f"Could not access Streamlit secrets: {e}")
        
        return None

    def _test_connection(self) -> bool:
        """Test database connection"""
        try:
            # Simple query to test connection
            result = self.supabase.table("students").select("count", count="exact").limit(1).execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    def _handle_database_error(self, operation: str, error: Exception):
        """Centralized error handling for database operations"""
        error_msg = f"Database error in {operation}: {str(error)}"
        logger.error(error_msg)
        
        # Show user-friendly error message
        if "duplicate key" in str(error).lower():
            st.error("A record with this ID already exists.")
        elif "foreign key" in str(error).lower():
            st.error("Referenced record does not exist.")
        elif "not-null constraint" in str(error).lower():
            st.error("Required field is missing.")
        else:
            st.error(f"Database operation failed: {operation}")

    def add_student(self, curtin_id: str, bib_id: int, first_name: str, 
                   last_name: str, house: str) -> bool:
        """Add a new student to the database"""
        try:
            result = self.supabase.table("students").insert({
                "curtin_id": curtin_id,
                "bib_id": bib_id,
                "first_name": first_name,
                "last_name": last_name,
                "house": house
            }).execute()
            
            if result.data:
                logger.info(f"Student added successfully: {first_name} {last_name}")
                return True
            else:
                logger.warning("Student insert returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_student", e)
            return False

    def get_student_by_bib(self, bib_id: int) -> Optional[Dict]:
        """Get student details by Bib ID"""
        try:
            result = self.supabase.table("students").select("*").eq("bib_id", bib_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self._handle_database_error("get_student_by_bib", e)
            return None

    def get_all_students(self) -> List[Dict]:
        """Get all students"""
        try:
            result = self.supabase.table("students").select("*").order("last_name").execute()
            return result.data or []
            
        except Exception as e:
            self._handle_database_error("get_all_students", e)
            return []

    def add_event(self, event_name: str, event_type: str, unit: str, 
                 point_allocation: Dict = None) -> bool:
        """Add a new event to the database"""
        try:
            # Convert point_allocation keys to strings for JSON compatibility
            if point_allocation:
                point_allocation = {str(k): v for k, v in point_allocation.items()}
            
            result = self.supabase.table("events").insert({
                "event_name": event_name,
                "event_type": event_type,
                "unit": unit,
                "point_allocation": point_allocation or {}
            }).execute()
            
            if result.data:
                logger.info(f"Event added successfully: {event_name}")
                return True
            else:
                logger.warning("Event insert returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_event", e)
            return False

    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type"""
        try:
            result = self.supabase.table("events").select("*").eq("event_type", event_type).order("event_name").execute()
            return result.data or []
            
        except Exception as e:
            self._handle_database_error("get_events_by_type", e)
            return []

    def get_all_events(self) -> List[Dict]:
        """Get all events"""
        try:
            result = self.supabase.table("events").select("*").order("event_name").execute()
            return result.data or []
            
        except Exception as e:
            self._handle_database_error("get_all_events", e)
            return []

    def add_result(self, curtin_id: str, event_id: int, result_value: float) -> bool:
        """Add a result and calculate points"""
        try:
            # First check if result already exists
            existing = self.supabase.table("results").select("*").eq("curtin_id", curtin_id).eq("event_id", event_id).execute()
            
            if existing.data:
                st.error("A result for this student in this event already exists.")
                return False
            
            # Insert result
            result = self.supabase.table("results").insert({
                "curtin_id": curtin_id,
                "event_id": event_id,
                "result_value": float(result_value),
                "points": 0,
                "position": 999
            }).execute()
            
            if result.data:
                # Recalculate positions and points for this event
                self._calculate_positions_and_points(event_id)
                logger.info(f"Result added successfully for event {event_id}")
                return True
            else:
                logger.warning("Result insert returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_result", e)
            return False

    def _calculate_positions_and_points(self, event_id: int):
        """Calculate positions and points for an event"""
        try:
            # Get event details
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                logger.warning(f"Event {event_id} not found")
                return
            
            event_data = event_result.data[0]
            event_type = event_data["event_type"]
            
            # Get all results for this event
            results_result = self.supabase.table("results").select("*").eq("event_id", event_id).execute()
            if not results_result.data:
                logger.info(f"No results found for event {event_id}")
                return
            
            # Sort results based on event type
            if event_type == "Running":
                # For running, lower time is better
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]))
            else:
                # For throwing/jumping, higher distance is better
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]), reverse=True)
            
            # Get point allocation
            from config import DEFAULT_POINT_ALLOCATION
            point_allocation = event_data.get("point_allocation") or DEFAULT_POINT_ALLOCATION
            
            # Update positions and points
            for i, result in enumerate(sorted_results):
                position = i + 1
                points = 0
                
                # Convert position to string for JSON lookup
                if str(position) in point_allocation:
                    points = point_allocation[str(position)]
                elif position in point_allocation:
                    points = point_allocation[position]
                
                # Update the result
                self.supabase.table("results").update({
                    "position": position,
                    "points": points
                }).eq("result_id", result["result_id"]).execute()
            
            logger.info(f"Positions and points calculated for event {event_id}")
                
        except Exception as e:
            self._handle_database_error("calculate_positions_and_points", e)

    def get_results_by_event(self, event_id: int) -> List[Dict]:
        """Get all results for a specific event with student details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).eq("event_id", event_id).order("position", desc=False).execute()
            
            return result.data or []
            
        except Exception as e:
            self._handle_database_error("get_results_by_event", e)
            return []

    def get_results_by_event_type(self, event_type: str) -> List[Dict]:
        """Get all results for events of a specific type"""
        try:
            # Get all events of the specified type
            events_result = self.supabase.table("events").select("event_id, event_name").eq("event_type", event_type).execute()
            
            if not events_result.data:
                return []
            
            # Get all results for these events
            all_results = []
            for event in events_result.data:
                event_results = self.get_results_by_event(event["event_id"])
                all_results.extend(event_results)
            
            # Sort by event name, then by position
            all_results.sort(key=lambda x: (x["events"]["event_name"], x.get("position", 999)))
            
            return all_results
            
        except Exception as e:
            self._handle_database_error("get_results_by_event_type", e)
            return []

    def get_house_points(self) -> List[Dict]:
        """Get total points by house"""
        try:
            # Get all results with student house information
            results = self.supabase.table("results").select("""
                points,
                students!inner(house)
            """).execute()
            
            if not results.data:
                return []
            
            # Calculate totals by house
            house_totals = {}
            for result in results.data:
                house = result["students"]["house"]
                points = result["points"] or 0
                house_totals[house] = house_totals.get(house, 0) + points
            
            # Convert to list format for display, sorted by points
            house_list = [{"house": house, "total_points": points} 
                         for house, points in house_totals.items()]
            
            # Sort by total points descending
            house_list.sort(key=lambda x: x["total_points"], reverse=True)
            
            return house_list
            
        except Exception as e:
            self._handle_database_error("get_house_points", e)
            return []

    def get_all_results(self) -> List[Dict]:
        """Get all results with student and event details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).execute()
            
            if not result.data:
                return []
            
            # Sort results by event name, then position
            sorted_results = sorted(result.data, key=lambda x: (
                x["events"]["event_name"], 
                x.get("position", 999)
            ))
            
            return sorted_results
            
        except Exception as e:
            self._handle_database_error("get_all_results", e)
            return []

    def get_results_by_house(self, house: str) -> List[Dict]:
        """Get all results for a specific house"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).eq("students.house", house).execute()
            
            return result.data or []
            
        except Exception as e:
            self._handle_database_error("get_results_by_house", e)
            return []
            
    def delete_result(self, result_id: int) -> bool:
        """Delete a result and recalculate positions"""
        try:
            # Get event_id before deleting
            result = self.supabase.table("results").select("event_id").eq("result_id", result_id).execute()
            if not result.data:
                st.error("Result not found")
                return False
            
            event_id = result.data[0]["event_id"]
            
            # Delete the result
            delete_result = self.supabase.table("results").delete().eq("result_id", result_id).execute()
            
            if delete_result:
                # Recalculate positions and points
                self._calculate_positions_and_points(event_id)
                logger.info(f"Result {result_id} deleted successfully")
                return True
            else:
                return False
                
        except Exception as e:
            self._handle_database_error("delete_result", e)
            return False