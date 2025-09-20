"""Enhanced Database operations with improved point allocation and athlete tracking"""

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
                   last_name: str, house: str, gender: str) -> bool:
        """Add a new student to the database with gender"""
        try:
            result = self.supabase.table("students").insert({
                "curtin_id": curtin_id,
                "bib_id": bib_id,
                "first_name": first_name,
                "last_name": last_name,
                "house": house,
                "gender": gender
            }).execute()
            
            if result.data:
                logger.info(f"Student added successfully: {first_name} {last_name} ({gender})")
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
                 is_relay: bool = False, point_allocation: Dict = None, 
                 point_system_name: str = "Individual Events") -> bool:
        """Add a new event to the database with enhanced point allocation"""
        try:
            # Convert point_allocation keys to strings for JSON compatibility
            if point_allocation:
                point_allocation = {str(k): v for k, v in point_allocation.items()}
            
            # Default point allocation if none provided
            if not point_allocation:
                from config import DEFAULT_INDIVIDUAL_POINTS, DEFAULT_RELAY_POINTS
                point_allocation = DEFAULT_RELAY_POINTS if is_relay else DEFAULT_INDIVIDUAL_POINTS
                point_allocation = {str(k): v for k, v in point_allocation.items()}
            
            result = self.supabase.table("events").insert({
                "event_name": event_name,
                "event_type": event_type,
                "unit": unit,
                "is_relay": is_relay,
                "point_allocation": point_allocation,
                "point_system_name": point_system_name
            }).execute()
            
            if result.data:
                logger.info(f"Event added successfully: {event_name} ({point_system_name})")
                return True
            else:
                logger.warning("Event insert returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_event", e)
            return False

    def get_event_by_name(self, event_name: str) -> Optional[Dict]:
        """Get event details by event name"""
        try:
            result = self.supabase.table("events").select("*").eq("event_name", event_name).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self._handle_database_error("get_event_by_name", e)
            return None

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

    def add_result(self, curtin_id: str, event_id: int, result_value: float, house: str) -> bool:
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
                "house": house,
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
        """Calculate positions and points for an event using event-specific point allocation"""
        try:
            # Get event details including point allocation
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                logger.warning(f"Event {event_id} not found")
                return
            
            event_data = event_result.data[0]
            event_type = event_data["event_type"]
            point_allocation = event_data.get("point_allocation", {})
            
            # Get all results for this event
            results_result = self.supabase.table("results").select("*").eq("event_id", event_id).execute()
            if not results_result.data:
                logger.info(f"No results found for event {event_id}")
                return
            
            # Sort results based on event type
            if event_type == "Track":
                # For track events, lower time is better
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]))
            else:
                # For field events, higher distance/height is better
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]), reverse=True)
            
            # Update positions and points using event-specific allocation
            for i, result in enumerate(sorted_results):
                position = i + 1
                points = 0
                
                # Get points from event-specific allocation
                if str(position) in point_allocation:
                    points = point_allocation[str(position)]
                elif position in point_allocation:
                    points = point_allocation[position]
                
                # Update the result
                self.supabase.table("results").update({
                    "position": position,
                    "points": points
                }).eq("result_id", result["result_id"]).execute()
            
            logger.info(f"Positions and points calculated for event {event_id} using custom allocation")
                
        except Exception as e:
            self._handle_database_error("calculate_positions_and_points", e)

    def get_results_by_event(self, event_id: int) -> List[Dict]:
        """Get all results for a specific event with student details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay, point_system_name)
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

    def get_individual_athlete_performance(self, limit: int = None) -> List[Dict]:
        """Get individual athlete performance for finding best athletes"""
        try:
            query = self.supabase.table("individual_athlete_performance").select("*")
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            return result.data or []
            
        except Exception as e:
            # Fallback to manual calculation if view doesn't exist
            try:
                # Get all results with student information
                results = self.supabase.table("results").select("""
                    *,
                    students!inner(curtin_id, bib_id, first_name, last_name, house, gender)
                """).execute()
                
                if not results.data:
                    return []
                
                # Group by student
                athlete_performance = {}
                for result in results.data:
                    student = result["students"]
                    key = student["curtin_id"]
                    
                    if key not in athlete_performance:
                        athlete_performance[key] = {
                            "curtin_id": student["curtin_id"],
                            "bib_id": student["bib_id"],
                            "first_name": student["first_name"],
                            "last_name": student["last_name"],
                            "house": student["house"],
                            "gender": student["gender"],
                            "total_events": 0,
                            "total_points": 0,
                            "gold_medals": 0,
                            "silver_medals": 0,
                            "bronze_medals": 0
                        }
                    
                    # Add stats
                    athlete_performance[key]["total_events"] += 1
                    athlete_performance[key]["total_points"] += result.get("points", 0)
                    
                    if result.get("position") == 1:
                        athlete_performance[key]["gold_medals"] += 1
                    elif result.get("position") == 2:
                        athlete_performance[key]["silver_medals"] += 1
                    elif result.get("position") == 3:
                        athlete_performance[key]["bronze_medals"] += 1
                
                # Convert to list and sort
                performance_list = list(athlete_performance.values())
                performance_list.sort(key=lambda x: (x["total_points"], x["gold_medals"]), reverse=True)
                
                # Add rankings
                for i, athlete in enumerate(performance_list):
                    athlete["overall_rank"] = i + 1
                
                return performance_list[:limit] if limit else performance_list
                
            except Exception as inner_e:
                self._handle_database_error("get_individual_athlete_performance_fallback", inner_e)
                return []

    def get_best_athletes_by_gender(self) -> Dict[str, Dict]:
        """Get best male and female athletes"""
        try:
            all_athletes = self.get_individual_athlete_performance()
            
            best_athletes = {}
            for athlete in all_athletes:
                gender = athlete.get("gender", "Other")
                if gender not in best_athletes or athlete["total_points"] > best_athletes[gender]["total_points"]:
                    best_athletes[gender] = athlete
            
            return best_athletes
            
        except Exception as e:
            self._handle_database_error("get_best_athletes_by_gender", e)
            return {}

    def delete_last_result(self, curtin_id: str) -> bool:
        """Delete the last result for a given student."""
        try:
            # Get the last result for the student
            last_result = self.supabase.table("results").select("result_id").eq("curtin_id", curtin_id).order("created_at", desc=True).limit(1).execute()
            
            if not last_result.data:
                st.warning("No results found for this student.")
                return False

            result_id_to_delete = last_result.data[0]['result_id']

            # Delete the result
            delete_result = self.supabase.table("results").delete().eq("result_id", result_id_to_delete).execute()

            if delete_result:
                logger.info(f"Result {result_id_to_delete} deleted successfully.")
                return True
            else:
                return False

        except Exception as e:
            self._handle_database_error("delete_last_result", e)
            return False

    def get_all_results(self) -> List[Dict]:
        """Get all results with student and event details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay, point_system_name)
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

    def delete_event(self, event_id: int) -> bool:
        """Delete an event from the database"""
        try:
            result = self.supabase.table("events").delete().eq("event_id", event_id).execute()
            
            if result:
                logger.info(f"Event {event_id} deleted successfully")
                return True
            else:
                return False
                
        except Exception as e:
            self._handle_database_error("delete_event", e)
            return False
            
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