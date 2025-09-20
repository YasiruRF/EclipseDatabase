"""Updated Database operations with bib_id as primary key and gender-specific point allocation"""

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
        if not SUPABASE_AVAILABLE:
            raise ImportError("Supabase client not available. Install with: pip install supabase")

        url = self._get_credential("SUPABASE_URL")
        key = self._get_credential("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY")

        try:
            self.supabase: Client = create_client(url, key)
        except Exception as e:
            logger.error(f"Failed to create Supabase client: {e}")
            raise ConnectionError("Failed to create Supabase client") from e

        if not self._test_connection():
            raise ConnectionError("Failed to establish database connection")

        logger.info("Database connection established successfully")

        if recalc_on_startup:
            try:
                self.recalculate_all_points()
                logger.info("Gender-specific recalculation completed on startup.")
            except Exception as e:
                logger.warning(f"Recalculation on startup failed: {e}")

    def _get_credential(self, key: str) -> str:
        value = os.getenv(key)
        if value:
            return value
        try:
            if hasattr(st, 'secrets') and key in st.secrets:
                return st.secrets[key]
        except Exception as e:
            logger.warning(f"Could not access Streamlit secrets: {e}")
        return None

    def _test_connection(self) -> bool:
        try:
            self.supabase.table("students").select("count", count="exact").limit(1).execute()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {str(e)}")
            return False

    def _handle_database_error(self, operation: str, error: Exception):
        error_msg = f"Database error in {operation}: {str(error)}"
        logger.error(error_msg)
        if "duplicate key" in str(error).lower():
            st.error("A record with this ID already exists.")
        elif "foreign key" in str(error).lower():
            st.error("Referenced record does not exist.")
        elif "not-null constraint" in str(error).lower():
            st.error("Required field is missing.")
        else:
            st.error(f"Database operation failed: {operation}")

    # ------------------- Relay Team Operations (Updated to use bib_id) -------------------
    def add_relay_team(self, team_name: str, house: str, event_id: int, 
                       member1_bib: int, member2_bib: int, member3_bib: int, member4_bib: int) -> bool:
        try:
            result = self.supabase.table("relay_teams").insert({
                "team_name": team_name,
                "house": house,
                "event_id": event_id,
                "member1_bib_id": member1_bib,
                "member2_bib_id": member2_bib,
                "member3_bib_id": member3_bib,
                "member4_bib_id": member4_bib
            }).execute()
            if result.data:
                logger.info(f"Relay team added successfully: {team_name}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_relay_team", e)
            return False

    def add_relay_team_result(self, team_id: int, result_value: float) -> bool:
        try:
            result = self.supabase.table("relay_teams").update({
                "result_value": float(result_value)
            }).eq("team_id", team_id).execute()
            
            if result.data:
                # Get event info and calculate relay positions
                team_data = self.supabase.table("relay_teams").select("event_id").eq("team_id", team_id).execute()
                if team_data.data:
                    event_id = team_data.data[0]["event_id"]
                    self._calculate_relay_positions_and_points(event_id)
                logger.info(f"Relay team result added successfully for team {team_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_relay_team_result", e)
            return False

    def _calculate_relay_positions_and_points(self, event_id: int):
        """Calculate relay team positions and points (relay teams compete together regardless of gender)"""
        try:
            # Get event details
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                return
                
            event_data = event_result.data[0]
            # For relay events, use either relay-specific points or default relay points
            point_allocation = event_data.get("relay_male_points", {"1": 15, "2": 9, "3": 5, "4": 3})
            
            # Get all teams with results for this event
            teams_result = self.supabase.table("relay_teams").select("*").eq("event_id", event_id).execute()
            if not teams_result.data:
                return
            
            # Filter teams with results and sort by time (lower is better for track events)
            teams_with_results = [team for team in teams_result.data if team.get("result_value")]
            sorted_teams = sorted(teams_with_results, key=lambda x: float(x["result_value"]))
            
            # Assign positions and points
            for i, team in enumerate(sorted_teams):
                position = i + 1
                points = point_allocation.get(str(position), 0)
                
                self.supabase.table("relay_teams").update({
                    "position": position,
                    "points": points
                }).eq("team_id", team["team_id"]).execute()
            
            logger.info(f"Relay team positions calculated for event {event_id}: {len(sorted_teams)} teams")
            
        except Exception as e:
            self._handle_database_error("calculate_relay_positions_and_points", e)

    def get_relay_teams_by_event(self, event_id: int) -> List[Dict]:
        try:
            # Try to use the view first
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

    # ------------------- Top Athletes (Updated for gender-specific rankings) -------------------
    def get_top_individual_athletes(self, limit: int = 20, gender: str = None) -> List[Dict]:
        """Get top individual athletes, optionally filtered by gender"""
        try:
            # Build query with optional gender filter
            query = self.supabase.table("athlete_complete_performance").select("*")
            
            if gender:
                query = query.eq("gender", gender)
                query = query.order("gender_rank", desc=False)
            else:
                query = query.order("overall_rank", desc=False)
            
            query = query.limit(limit)
            result = query.execute()
            
            return result.data or []
            
        except Exception as e:
            # Fallback to manual calculation
            logger.warning(f"View not available, using manual calculation: {e}")
            return self._calculate_top_athletes_manually(limit, gender)

    def _calculate_top_athletes_manually(self, limit: int, gender: str = None) -> List[Dict]:
        """Manual calculation of top athletes when view is not available"""
        try:
            # Get all individual results (non-relay) with student info
            query = self.supabase.table("results").select("""
                *,
                students!inner(bib_id, curtin_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, is_relay)
            """)
            
            if gender:
                query = query.eq("students.gender", gender)
                
            results = query.execute()
            
            if not results.data:
                return []
            
            # Aggregate by student
            student_stats = {}
            for result in results.data:
                # Skip relay events
                if result["events"]["is_relay"]:
                    continue
                    
                bib_id = result["students"]["bib_id"]
                points = result.get("points", 0)
                position = result.get("position", 999)
                
                if bib_id not in student_stats:
                    student_stats[bib_id] = {
                        "bib_id": bib_id,
                        "curtin_id": result["students"]["curtin_id"],
                        "first_name": result["students"]["first_name"],
                        "last_name": result["students"]["last_name"],
                        "house": result["students"]["house"],
                        "gender": result["students"]["gender"],
                        "total_events": 0,
                        "total_points": 0,
                        "gold_medals": 0,
                        "silver_medals": 0,
                        "bronze_medals": 0
                    }
                
                student_stats[bib_id]["total_events"] += 1
                student_stats[bib_id]["total_points"] += points
                
                if position == 1:
                    student_stats[bib_id]["gold_medals"] += 1
                elif position == 2:
                    student_stats[bib_id]["silver_medals"] += 1
                elif position == 3:
                    student_stats[bib_id]["bronze_medals"] += 1
            
            # Convert to list and sort
            athletes = list(student_stats.values())
            athletes.sort(key=lambda x: (x["total_points"], x["gold_medals"]), reverse=True)
            
            # Add rankings
            for i, athlete in enumerate(athletes):
                athlete["overall_rank"] = i + 1
                athlete["gender_rank"] = i + 1  # Simplified for manual calc
            
            return athletes[:limit]
            
        except Exception as e:
            self._handle_database_error("calculate_top_athletes_manually", e)
            return []

    def get_best_athletes_by_gender(self) -> Dict[str, Dict]:
        """Get the best male and female athlete"""
        try:
            male_athletes = self.get_top_individual_athletes(limit=1, gender="Male")
            female_athletes = self.get_top_individual_athletes(limit=1, gender="Female")
            
            result = {}
            if male_athletes:
                result["Male"] = male_athletes[0]
            if female_athletes:
                result["Female"] = female_athletes[0]
                
            return result
            
        except Exception as e:
            self._handle_database_error("get_best_athletes_by_gender", e)
            return {}

    # ------------------- House Points (Updated) -------------------
    def get_house_points(self) -> List[Dict]:
        try:
            # Try to use the corrected view
            result = self.supabase.table("corrected_house_points").select("*").execute()
            if result.data:
                house_list = []
                for row in result.data:
                    individual_points = row.get("individual_points", 0) or 0
                    relay_points = row.get("relay_team_points", 0) or 0
                    total_points = row.get("total_points") or (individual_points + relay_points)
                    
                    house_list.append({
                        "house": row["house"],
                        "total_points": total_points,
                        "individual_points": individual_points,
                        "relay_team_points": relay_points
                    })
                
                house_list.sort(key=lambda x: x["total_points"], reverse=True)
                return house_list
                
        except Exception as e:
            logger.warning(f"Corrected house points view not available: {e}")

        # Fallback calculation
        return self._calculate_house_points_manually()

    def _calculate_house_points_manually(self) -> List[Dict]:
        """Manual house points calculation"""
        try:
            house_totals = {}
            
            # Get individual event points
            results = self.supabase.table("results").select("""
                *, 
                students!inner(house),
                events!inner(is_relay)
            """).execute()
            
            if results.data:
                for result in results.data:
                    house = result["students"]["house"]
                    points = result.get("points", 0) or 0
                    is_relay = result["events"]["is_relay"]
                    
                    if house not in house_totals:
                        house_totals[house] = {"individual_points": 0, "relay_team_points": 0}
                    
                    # Only count individual events here
                    if not is_relay:
                        house_totals[house]["individual_points"] += points
            
            # Get relay team points
            relay_results = self.supabase.table("relay_teams").select("house, points").execute()
            if relay_results.data:
                for team in relay_results.data:
                    house = team.get("house")
                    points = team.get("points", 0) or 0
                    
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
            
            house_list.sort(key=lambda x: x["total_points"], reverse=True)
            return house_list
            
        except Exception as e:
            logger.error(f"Error in manual house points calculation: {e}")
            return []

    # ------------------- Recalculation (Updated for gender-specific) -------------------
    def recalculate_all_points(self) -> bool:
        """Recalculate all points using gender-specific allocations"""
        try:
            # Try to use the SQL function first
            result = self.supabase.rpc("recalculate_points_by_gender").execute()
            if result.data:
                logger.info("All points recalculated with gender-specific allocations using SQL function")
                return True
        except Exception as e:
            logger.warning(f"SQL function not available, using manual recalculation: {e}")
        
        # Fallback: manual recalculation
        try:
            events = self.get_all_events()
            for event in events:
                if event.get("is_relay"):
                    self._calculate_relay_positions_and_points(event["event_id"])
                else:
                    self._calculate_gender_specific_positions(event["event_id"])
            
            logger.info("All points recalculated manually with gender-specific allocations")
            return True
            
        except Exception as e:
            self._handle_database_error("recalculate_all_points", e)
            return False 
    def add_student(self, curtin_id: str, bib_id: int, first_name: str, 
                    last_name: str, house: str, gender: str) -> bool:
        try:
            result = self.supabase.table("students").insert({
                "bib_id": bib_id,  # Now primary key
                "curtin_id": curtin_id,
                "first_name": first_name,
                "last_name": last_name,
                "house": house,
                "gender": gender
            }).execute()
            if result.data:
                logger.info(f"Student added successfully: {first_name} {last_name} ({gender}) - Bib #{bib_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_student", e)
            return False

    def get_student_by_bib(self, bib_id: int) -> Optional[Dict]:
        try:
            result = self.supabase.table("students").select("*").eq("bib_id", bib_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self._handle_database_error("get_student_by_bib", e)
            return None

    def get_student_by_curtin_id(self, curtin_id: str) -> Optional[Dict]:
        try:
            result = self.supabase.table("students").select("*").eq("curtin_id", curtin_id).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self._handle_database_error("get_student_by_curtin_id", e)
            return None

    def get_all_students(self) -> List[Dict]:
        try:
            result = self.supabase.table("students").select("*").order("last_name").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_all_students", e)
            return []

    # ------------------- Event Operations (Updated with gender-specific points) -------------------
    def add_event(self, event_name: str, event_type: str, unit: str, 
                  is_relay: bool = False, male_points: Dict = None, female_points: Dict = None) -> bool:
        try:
            if not male_points:
                male_points = {"1": 15, "2": 9, "3": 5, "4": 3} if is_relay else {"1": 10, "2": 6, "3": 3, "4": 1}
            if not female_points:
                female_points = {"1": 15, "2": 9, "3": 5, "4": 3} if is_relay else {"1": 10, "2": 6, "3": 3, "4": 1}
            
            # Ensure string keys for JSONB
            male_points = {str(k): v for k, v in male_points.items()}
            female_points = {str(k): v for k, v in female_points.items()}
            
            result = self.supabase.table("events").insert({
                "event_name": event_name,
                "event_type": event_type,
                "unit": unit,
                "is_relay": is_relay,
                "male_point_allocation": male_points,
                "female_point_allocation": female_points,
                # Keep legacy fields for compatibility
                "point_allocation": male_points,  # Default to male for legacy
                "point_system_name": "Relay Events" if is_relay else "Individual Events"
            }).execute()
            if result.data:
                logger.info(f"Event added successfully: {event_name} (Gender-specific points)")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_event", e)
            return False

    def get_event_by_name(self, event_name: str) -> Optional[Dict]:
        try:
            result = self.supabase.table("events").select("*").eq("event_name", event_name).execute()
            if result.data:
                return result.data[0]
            return None
        except Exception as e:
            self._handle_database_error("get_event_by_name", e)
            return None

    def get_all_events(self) -> List[Dict]:
        try:
            result = self.supabase.table("events").select("*").order("event_name").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_all_events", e)
            return []

    # ------------------- Result Operations (Updated to use bib_id) -------------------
    def add_result(self, bib_id: int, event_id: int, result_value: float) -> bool:
        """Add result using bib_id instead of curtin_id"""
        try:
            # Check if result already exists
            existing = self.supabase.table("results").select("*").eq("bib_id", bib_id).eq("event_id", event_id).execute()
            if existing.data:
                st.error("A result for this student in this event already exists.")
                return False
            
            result = self.supabase.table("results").insert({
                "bib_id": bib_id,
                "event_id": event_id,
                "result_value": float(result_value),
                "points": 0,
                "position": 999
            }).execute()
            
            if result.data:
                # Recalculate positions and points for this event with gender-specific logic
                self._calculate_gender_specific_positions(event_id)
                logger.info(f"Result added successfully for bib #{bib_id} in event {event_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_result", e)
            return False

    def _calculate_gender_specific_positions(self, event_id: int):
        """Calculate positions and points separately for male and female competitors"""
        try:
            # Get event details
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                logger.warning(f"Event {event_id} not found")
                return
                
            event_data = event_result.data[0]
            event_type = event_data["event_type"]
            male_points = event_data.get("male_point_allocation", {"1": 10, "2": 6, "3": 3, "4": 1})
            female_points = event_data.get("female_point_allocation", {"1": 10, "2": 6, "3": 3, "4": 1})
            
            # Get all results for this event with student gender
            results_query = self.supabase.table("results").select("""
                *, students!inner(gender)
            """).eq("event_id", event_id).execute()
            
            if not results_query.data:
                return
            
            # Separate by gender
            male_results = [r for r in results_query.data if r["students"]["gender"] == "Male"]
            female_results = [r for r in results_query.data if r["students"]["gender"] == "Female"]
            
            # Sort and assign positions/points for males
            if event_type == "Track":
                male_results.sort(key=lambda x: float(x["result_value"]))  # Lower is better
            else:
                male_results.sort(key=lambda x: float(x["result_value"]), reverse=True)  # Higher is better
                
            for i, result in enumerate(male_results):
                position = i + 1
                points = male_points.get(str(position), 0)
                self.supabase.table("results").update({
                    "position": position,
                    "points": points
                }).eq("result_id", result["result_id"]).execute()
            
            # Sort and assign positions/points for females
            if event_type == "Track":
                female_results.sort(key=lambda x: float(x["result_value"]))  # Lower is better
            else:
                female_results.sort(key=lambda x: float(x["result_value"]), reverse=True)  # Higher is better
                
            for i, result in enumerate(female_results):
                position = i + 1
                points = female_points.get(str(position), 0)
                self.supabase.table("results").update({
                    "position": position,
                    "points": points
                }).eq("result_id", result["result_id"]).execute()
            
            logger.info(f"Gender-specific positions calculated for event {event_id}: {len(male_results)} male, {len(female_results)} female")
            
        except Exception as e:
            self._handle_database_error("calculate_gender_specific_positions", e)

    def get_results_by_event(self, event_id: int) -> List[Dict]:
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(bib_id, curtin_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay)
            """).eq("event_id", event_id).order("position", desc=False).execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_results_by_event", e)
            return []

    def get_all_results(self) -> List[Dict]:
        try:
            result = self.supabase.table("results").select("""
                *,
                students!inner(bib_id, curtin_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay)
            """).order("result_id").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_all_results", e)
            return []

    def delete_last_result(self, bib_id: int) -> bool:
        """Delete the most recent result for a student"""
        try:
            # Get the most recent result for this student
            result = self.supabase.table("results").select("*").eq("bib_id", bib_id).order("result_id", desc=True).limit(1).execute()
            
            if not result.data:
                return False
                
            result_to_delete = result.data[0]
            event_id = result_to_delete["event_id"]
            
            # Delete the result
            delete_result = self.supabase.table("results").delete().eq("result_id", result_to_delete["result_id"]).execute()
            
            if delete_result.data:
                # Recalculate positions for the event
                self._calculate_gender_specific_positions(event_id)
                logger.info(f"Last result deleted for bib #{bib_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("delete_last_result", e)
            return False

    #