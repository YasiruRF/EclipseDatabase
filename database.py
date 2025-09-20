"""Enhanced Database operations with corrected point allocation and relay team support"""

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
    def __init__(self, recalc_on_startup: bool = True):
    
        # Ensure the supabase client package is available
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")

        # Get credentials (uses your _get_credential method)
        url = self._get_credential("SUPABASE_URL")
        key = self._get_credential("SUPABASE_KEY")

        if not url or not key:
            # Fail fast — better than creating a partially-initialized object
            raise ValueError("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY")

        # Create Supabase client and test connection
        try:
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise ConnectionError("Failed to create Supabase client") from e

        if not self._test_connection():
            raise ConnectionError("Failed to establish database connection")

        logger.info("Database connection established successfully")

        # Optional: attempt to recalculate points after a successful connection.
        # We call your recalculate_all_points() method (which should handle RPC + manual fallback).
        if recalc_on_startup:
            try:
                # If recalculate_all_points returns a boolean, we ignore it here;
                # any exceptions will be handled/logged below.
                if hasattr(self, "recalculate_all_points"):
                    try:
                        self.recalculate_all_points()
                        logger.info("Recalculation attempted on startup.")
                    except Exception as e:
                        logger.warning(f"Recalculation on startup failed: {e}")
                        # Use your centralized handler so the UI sees a friendly message
                        self._handle_database_error("recalculate_on_init", e)
                else:
                    logger.debug("No recalculate_all_points() method found; skipping startup recalculation.")
            except Exception as e:
                # Defensive: log anything unexpected
                logger.error(f"Unexpected error during startup recalc: {e}")
                self._handle_database_error("recalculate_on_init_unexpected", e)

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

    def get_student_by_curtin_id(self, curtin_id: str) -> Optional[Dict]:
        """Get student details by Curtin ID"""
        try:
            result = self.supabase.table("students").select("*").eq("curtin_id", curtin_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            self._handle_database_error("get_student_by_curtin_id", e)
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
        """Add a new event to the database with corrected point allocation"""
        try:
            # Use corrected default point allocations
            if not point_allocation:
                if is_relay:
                    # Relay Events: 1st=15, 2nd=9, 3rd=5, 4th=3
                    point_allocation = {"1": 15, "2": 9, "3": 5, "4": 3}
                    point_system_name = "Relay Events"
                else:
                    # Individual Events: 1st=10, 2nd=6, 3rd=3, 4th=1
                    point_allocation = {"1": 10, "2": 6, "3": 3, "4": 1}
                    point_system_name = "Individual Events"
            
            # Convert point_allocation keys to strings for JSON compatibility
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
            all_results.sort(key=lambda x: (x.get("events", {}).get("event_name", ""), x.get("position", 999)))
            
            return all_results
            
        except Exception as e:
            self._handle_database_error("get_results_by_event_type", e)
            return []

    def get_house_points(self) -> List[Dict]:
        """Get total points by house using corrected view with fallback"""
        try:
            # First try the corrected house points view
            result = self.supabase.table("corrected_house_points").select("*").order("total_points", desc=True).execute()
            
            if result.data:
                # Convert to expected format
                house_list = []
                for row in result.data:
                    house_list.append({
                        "house": row["house"],
                        "total_points": row["total_points"],
                        "individual_points": row.get("individual_points", 0),
                        "relay_team_points": row.get("relay_team_points", 0)
                    })
                return house_list
                
        except Exception as e:
            logger.warning(f"Corrected house points view not available: {e}")
        
        # Fallback to manual calculation
        try:
            # Get individual event points
            individual_results = self.supabase.table("results").select("""
                points,
                students!inner(house),
                events!inner(is_relay)
            """).execute()
            
            # Get relay team points
            relay_results = []
            try:
                relay_results = self.supabase.table("relay_teams").select("house, points").execute().data or []
            except:
                pass
            
            house_totals = {}
            
            # Calculate individual points (exclude relay events)
            if individual_results.data:
                for result in individual_results.data:
                    event_data = result.get("events", {})
                    if isinstance(event_data, list):
                        event_data = event_data[0] if event_data else {}
                    
                    # Skip relay events for individual calculations
                    if event_data.get("is_relay", False):
                        continue
                    
                    student_data = result.get("students", {})
                    if isinstance(student_data, list):
                        student_data = student_data[0] if student_data else {}
                    
                    house = student_data.get("house", "Unknown")
                    points = result.get("points", 0) or 0
                    
                    if house not in house_totals:
                        house_totals[house] = {"individual_points": 0, "relay_team_points": 0}
                    house_totals[house]["individual_points"] += points
            
            # Add relay team points
            for relay in relay_results:
                house = relay.get("house", "Unknown")
                points = relay.get("points", 0) or 0
                
                if house not in house_totals:
                    house_totals[house] = {"individual_points": 0, "relay_team_points": 0}
                house_totals[house]["relay_team_points"] += points
            
            # Convert to list format
            house_list = []
            for house, points_data in house_totals.items():
                individual_points = points_data["individual_points"]
                relay_points = points_data["relay_team_points"]
                total_points = individual_points + relay_points
                
                house_list.append({
                    "house": house,
                    "total_points": total_points,
                    "individual_points": individual_points,
                    "relay_team_points": relay_points
                })
            
            # Sort by total points descending
            house_list.sort(key=lambda x: x["total_points"], reverse=True)
            
            return house_list
            
        except Exception as e:
            self._handle_database_error("get_house_points_fallback", e)
            return []

    def get_individual_athlete_performance(self, limit: int = None) -> List[Dict]:
        """Get individual athlete performance with fallback"""
        try:
            # First try the enhanced athlete performance view
            query = self.supabase.table("athlete_complete_performance").select("*").order("total_individual_points", desc=True)
            if limit:
                query = query.limit(limit)
            
            result = query.execute()
            if result.data:
                return result.data
                
        except Exception as e:
            logger.warning(f"Athlete performance view not available: {e}")
        
        # Fallback to manual calculation
        try:
            # Get all results with student information (exclude relay events)
            results = self.supabase.table("results").select("""
                *,
                students!inner(curtin_id, bib_id, first_name, last_name, house, gender),
                events!inner(is_relay)
            """).execute()
            
            if not results.data:
                return []
            
            # Group by student
            athlete_performance = {}
            for result in results.data:
                # Handle nested data structure
                event_data = result.get("events", {})
                if isinstance(event_data, list):
                    event_data = event_data[0] if event_data else {}
                
                # Skip relay events for individual performance
                if event_data.get("is_relay", False):
                    continue
                    
                student_data = result.get("students", {})
                if isinstance(student_data, list):
                    student_data = student_data[0] if student_data else {}
                
                key = student_data.get("curtin_id")
                if not key:
                    continue
                
                if key not in athlete_performance:
                    athlete_performance[key] = {
                        "curtin_id": student_data.get("curtin_id"),
                        "bib_id": student_data.get("bib_id"),
                        "first_name": student_data.get("first_name"),
                        "last_name": student_data.get("last_name"),
                        "house": student_data.get("house"),
                        "gender": student_data.get("gender"),
                        "total_events": 0,
                        "total_points": 0,
                        "gold_medals": 0,
                        "silver_medals": 0,
                        "bronze_medals": 0
                    }
                
                # Add stats
                athlete_performance[key]["total_events"] += 1
                athlete_performance[key]["total_points"] += result.get("points", 0) or 0
                
                position = result.get("position", 0)
                if position == 1:
                    athlete_performance[key]["gold_medals"] += 1
                elif position == 2:
                    athlete_performance[key]["silver_medals"] += 1
                elif position == 3:
                    athlete_performance[key]["bronze_medals"] += 1
            
            # Convert to list and sort
            performance_list = list(athlete_performance.values())
            performance_list.sort(key=lambda x: (x["total_points"], x["gold_medals"]), reverse=True)
            
            # Add rankings
            for i, athlete in enumerate(performance_list):
                athlete["overall_rank"] = i + 1
                athlete["total_individual_points"] = athlete["total_points"]  # Alias for compatibility
            
            return performance_list[:limit] if limit else performance_list
            
        except Exception as e:
            self._handle_database_error("get_individual_athlete_performance_fallback", e)
            return []

    def get_best_athletes_by_gender(self) -> Dict[str, Dict]:
        """Get best male and female athletes"""
        try:
            all_athletes = self.get_individual_athlete_performance()
            
            best_athletes = {}
            for athlete in all_athletes:
                gender = athlete.get("gender", "Other")
                total_points = athlete.get("total_points", 0) or athlete.get("total_individual_points", 0)
                
                if gender not in best_athletes or total_points > best_athletes[gender].get("total_points", 0):
                    best_athletes[gender] = athlete
            
            return best_athletes
            
        except Exception as e:
            self._handle_database_error("get_best_athletes_by_gender", e)
            return {}

    def delete_last_result(self, curtin_id: str) -> bool:
        """Delete the last result for a given student."""
        try:
            # Get the last result for the student
            last_result = self.supabase.table("results").select("result_id, event_id").eq("curtin_id", curtin_id).order("created_at", desc=True).limit(1).execute()
            
            if not last_result.data:
                st.warning("No results found for this student.")
                return False

            result_id_to_delete = last_result.data[0]['result_id']
            event_id = last_result.data[0]['event_id']

            # Delete the result
            delete_result = self.supabase.table("results").delete().eq("result_id", result_id_to_delete).execute()

            if delete_result:
                # Recalculate positions and points for this event
                self._calculate_positions_and_points(event_id)
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
                x.get("events", {}).get("event_name", "") if isinstance(x.get("events"), dict) 
                else (x.get("events")[0].get("event_name", "") if x.get("events") else ""), 
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

    def add_relay_team(self, team_name: str, house: str, event_id: int, 
                      member1_id: str, member2_id: str, member3_id: str, member4_id: str) -> bool:
        """Add a relay team to the database"""
        try:
            result = self.supabase.table("relay_teams").insert({
                "team_name": team_name,
                "house": house,
                "event_id": event_id,
                "member1_curtin_id": member1_id,
                "member2_curtin_id": member2_id,
                "member3_curtin_id": member3_id,
                "member4_curtin_id": member4_id
            }).execute()
            
            if result.data:
                logger.info(f"Relay team added successfully: {team_name}")
                return True
            else:
                logger.warning("Relay team insert returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_relay_team", e)
            return False

    def add_relay_team_result(self, team_id: int, result_value: float) -> bool:
        """Add result for a relay team and calculate points"""
        try:
            # Update the team with the result
            result = self.supabase.table("relay_teams").update({
                "result_value": float(result_value)
            }).eq("team_id", team_id).execute()
            
            if result.data:
                # Get the event_id to recalculate positions and points
                team_data = self.supabase.table("relay_teams").select("event_id").eq("team_id", team_id).execute()
                if team_data.data:
                    event_id = team_data.data[0]["event_id"]
                    # Try to call the database function, fallback to manual calculation
                    try:
                        self.supabase.rpc("calculate_relay_team_points", {"event_id_param": event_id}).execute()
                    except:
                        # Manual fallback for relay point calculation
                        self._calculate_relay_positions_and_points(event_id)
                
                logger.info(f"Relay team result added successfully for team {team_id}")
                return True
            else:
                logger.warning("Relay team result update returned no data")
                return False
                
        except Exception as e:
            self._handle_database_error("add_relay_team_result", e)
            return False

    def _calculate_relay_positions_and_points(self, event_id: int):
        """Manual fallback for calculating relay team positions and points"""
        try:
            # Get event details
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                return
            
            event_data = event_result.data[0]
            point_allocation = event_data.get("point_allocation", {})
            
            # Get all relay teams for this event with results
            teams_result = self.supabase.table("relay_teams").select("*").eq("event_id", event_id).execute()
            if not teams_result.data:
                return
            
            # Filter teams with results and sort by time (lower is better for track)
            teams_with_results = [team for team in teams_result.data if team.get("result_value")]
            sorted_teams = sorted(teams_with_results, key=lambda x: float(x["result_value"]))
            
            # Update positions and points
            for i, team in enumerate(sorted_teams):
                position = i + 1
                points = 0
                
                if str(position) in point_allocation:
                    points = point_allocation[str(position)]
                elif position in point_allocation:
                    points = point_allocation[position]
                
                self.supabase.table("relay_teams").update({
                    "position": position,
                    "points": points
                }).eq("team_id", team["team_id"]).execute()
                
        except Exception as e:
            logger.error(f"Error calculating relay positions: {e}")

    def get_relay_teams_by_event(self, event_id: int) -> List[Dict]:
        """Get all relay teams for a specific event"""
        try:
            # Try the view first
            result = self.supabase.table("relay_team_results").select("*").eq("event_id", event_id).order("position", desc=False).execute()
            if result.data:
                return result.data
        except:
            pass
        
        # Fallback to direct table query
        try:
            result = self.supabase.table("relay_teams").select("*").eq("event_id", event_id).order("position", desc=False).execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_relay_teams_by_event", e)
            return []

    def get_complete_house_points(self) -> List[Dict]:
        """Get complete house points including relay team points"""
        return self.get_house_points()  # Use the corrected method with fallback

    def recalculate_all_points(self) -> bool:
        """Manually trigger recalculation of all points"""
        try:
            # Try the SQL function first
            result = self.supabase.rpc("recalculate_all_points_correct").execute()
            if result.data:
                logger.info("All points recalculated successfully using SQL function")
                return True
        except Exception as e:
            logger.warning(f"SQL function not available, using manual recalculation: {e}")
        
        