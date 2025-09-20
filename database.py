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
                if hasattr(self, "recalculate_all_points"):
                    try:
                        self.recalculate_all_points()
                        logger.info("Recalculation attempted on startup.")
                    except Exception as e:
                        logger.warning(f"Recalculation on startup failed: {e}")
                        self._handle_database_error("recalculate_on_init", e)
            except Exception as e:
                logger.error(f"Unexpected error during startup recalc: {e}")
                self._handle_database_error("recalculate_on_init_unexpected", e)

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

    # ------------------- Student Operations -------------------
    def add_student(self, curtin_id: str, bib_id: int, first_name: str, 
                    last_name: str, house: str, gender: str) -> bool:
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

    def get_top_individual_athletes(self, limit: int = 20) -> List[Dict]:
        try:
            # Fetch all individual results with student and event details
            results_query = self.supabase.table("results").select("""
                *,
                students!inner(curtin_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay)
            """).execute()

            if not results_query.data:
                return []

            student_points = {}
            for res in results_query.data:
                student_id = res["students"]["curtin_id"]
                points = res.get("points", 0)

                if student_id not in student_points:
                    student_points[student_id] = {
                        "curtin_id": student_id,
                        "first_name": res["students"]["first_name"],
                        "last_name": res["students"]["last_name"],
                        "house": res["students"]["house"],
                        "gender": res["students"]["gender"],
                        "total_points": 0,
                        "events_participated": 0
                    }
                student_points[student_id]["total_points"] += points
                student_points[student_id]["events_participated"] += 1

            # Convert to list and sort by total_points
            top_athletes = sorted(student_points.values(), key=lambda x: x["total_points"], reverse=True)

            return top_athletes[:limit]

        except Exception as e:
            self._handle_database_error("get_top_individual_athletes", e)
            return []

    # ------------------- Event Operations -------------------
    def add_event(self, event_name: str, event_type: str, unit: str, 
                  is_relay: bool = False, point_allocation: Dict = None, 
                  point_system_name: str = "Individual Events") -> bool:
        try:
            if not point_allocation:
                if is_relay:
                    point_allocation = {"1": 15, "2": 9, "3": 5, "4": 3}
                    point_system_name = "Relay Events"
                else:
                    point_allocation = {"1": 10, "2": 6, "3": 3, "4": 1}
                    point_system_name = "Individual Events"
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

    def get_events_by_type(self, event_type: str) -> List[Dict]:
        try:
            result = self.supabase.table("events").select("*").eq("event_type", event_type).order("event_name").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_events_by_type", e)
            return []

    def get_all_events(self) -> List[Dict]:
        try:
            result = self.supabase.table("events").select("*").order("event_name").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_all_events", e)
            return []

    # ------------------- Result Operations -------------------
    def add_result(self, curtin_id: str, event_id: int, result_value: float, house: str) -> bool:
        try:
            existing = self.supabase.table("results").select("*").eq("curtin_id", curtin_id).eq("event_id", event_id).execute()
            if existing.data:
                st.error("A result for this student in this event already exists.")
                return False
            result = self.supabase.table("results").insert({
                "curtin_id": curtin_id,
                "event_id": event_id,
                "result_value": float(result_value),
                "house": house,
                "points": 0,
                "position": 999
            }).execute()
            if result.data:
                self._calculate_positions_and_points(event_id)
                logger.info(f"Result added successfully for event {event_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_result", e)
            return False

    def _calculate_positions_and_points(self, event_id: int):
        try:
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                logger.warning(f"Event {event_id} not found")
                return
            event_data = event_result.data[0]
            event_type = event_data["event_type"]
            point_allocation = event_data.get("point_allocation", {})
            results_result = self.supabase.table("results").select("*").eq("event_id", event_id).execute()
            if not results_result.data:
                return
            if event_type == "Track":
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]))
            else:
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]), reverse=True)
            for i, result in enumerate(sorted_results):
                position = i + 1
                points = point_allocation.get(str(position), 0)
                self.supabase.table("results").update({
                    "position": position,
                    "points": points
                }).eq("result_id", result["result_id"]).execute()
            logger.info(f"Positions and points calculated for event {event_id}")
        except Exception as e:
            self._handle_database_error("calculate_positions_and_points", e)

    def get_results_by_event(self, event_id: int) -> List[Dict]:
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

    def get_all_results(self) -> List[Dict]:
        try:
            result = self.supabase.table("results").select("""
                *,
                students!inner(curtin_id, bib_id, first_name, last_name, house, gender),
                events!inner(event_name, event_type, unit, is_relay, point_system_name)
            """).order("result_id").execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_all_results", e)
            return []

    # ------------------- Relay Team Operations -------------------
    def add_relay_team(self, team_name: str, house: str, event_id: int, 
                       member1_id: str, member2_id: str, member3_id: str, member4_id: str) -> bool:
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
                team_data = self.supabase.table("relay_teams").select("event_id").eq("team_id", team_id).execute()
                if team_data.data:
                    event_id = team_data.data[0]["event_id"]
                    try:
                        self.supabase.rpc("calculate_relay_team_points", {"event_id_param": event_id}).execute()
                    except:
                        self._calculate_relay_positions_and_points(event_id)
                logger.info(f"Relay team result added successfully for team {team_id}")
                return True
            return False
        except Exception as e:
            self._handle_database_error("add_relay_team_result", e)
            return False

    def _calculate_relay_positions_and_points(self, event_id: int):
        try:
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                return
            event_data = event_result.data[0]
            point_allocation = event_data.get("point_allocation", {"1": 15, "2": 9, "3": 5, "4": 3})
            teams_result = self.supabase.table("relay_teams").select("*").eq("event_id", event_id).execute()
            if not teams_result.data:
                return
            teams_with_results = [team for team in teams_result.data if team.get("result_value")]
            sorted_teams = sorted(teams_with_results, key=lambda x: float(x["result_value"] or 9999))
            for i, team in enumerate(sorted_teams):
                position = i + 1
                points = point_allocation.get(str(position), 0)
                self.supabase.table("relay_teams").update({
                    "position": position,
                    "points": points
                }).eq("team_id", team["team_id"]).execute()
            logger.info(f"Relay team positions and points calculated for event {event_id}")
        except Exception as e:
            self._handle_database_error("calculate_relay_positions_and_points", e)

    def get_relay_teams_by_event(self, event_id: int) -> List[Dict]:
        try:
            result = self.supabase.table("relay_team_results").select("*").eq("event_id", event_id).order("position", desc=False).execute()
            if result.data:
                return result.data
        except:
            pass
        try:
            result = self.supabase.table("relay_teams").select("*").eq("event_id", event_id).order("position", desc=False).execute()
            return result.data or []
        except Exception as e:
            self._handle_database_error("get_relay_teams_by_event", e)
            return []

    # ------------------- House Points -------------------
    def get_house_points(self) -> List[Dict]:
        try:
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
        try:
            house_totals = {}
            house_list = []
            results = self.supabase.table("results").select("*, events!inner(is_relay)").execute()
            relay_results = self.supabase.table("relay_teams").select("house, points").execute()
            if results.data:
                for result in results.data:
                    house = result.get("house")
                    points = result.get("points", 0) or 0
                    event_data = result.get("events", {})
                    if isinstance(event_data, list):
                        event_data = event_data[0] if event_data else {}
                    is_relay = event_data.get("is_relay", False)
                    if house not in house_totals:
                        house_totals[house] = {"individual_points": 0, "relay_team_points": 0}
                    if is_relay:
                        house_totals[house]["relay_team_points"] += points
                    else:
                        house_totals[house]["individual_points"] += points
            if relay_results.data:
                for team in relay_results.data:
                    house = team.get("house")
                    points = team.get("points", 0) or 0
                    if house not in house_totals:
                        house_totals[house] = {"individual_points": 0, "relay_team_points": 0}
                    house_totals[house]["relay_team_points"] += points
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
            logger.error(f"Error in fallback house points calculation: {e}")
            return []

    # ------------------- Recalculation -------------------
    def recalculate_all_points(self) -> bool:
        try:
            result = self.supabase.rpc("recalculate_all_points_correct").execute()
            if result.data:
                logger.info("All points recalculated successfully using SQL function")
                return True
        except Exception as e:
            logger.warning(f"SQL function not available, using manual recalculation: {e}")
        # Fallback: recalc all individual and relay positions manually
        try:
            events = self.get_all_events()
            for event in events:
                if event.get("is_relay"):
                    self._calculate_relay_positions_and_points(event["event_id"])
                else:
                    self._calculate_positions_and_points(event["event_id"])
            logger.info("All points recalculated manually")
            return True
        except Exception as e:
            self._handle_database_error("recalculate_all_points", e)
            return False
