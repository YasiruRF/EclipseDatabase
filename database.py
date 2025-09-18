"""Database operations using Supabase"""

import os
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

class DatabaseManager:
    def __init__(self):
        """Initialize Supabase client"""
        try:
            url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError("Supabase credentials not found")
                
            self.supabase: Client = create_client(url, key)
            
            # Test connection
            self._test_connection()
            
        except Exception as e:
            st.error(f"Failed to initialize database: {str(e)}")
            raise

    def _test_connection(self):
        """Test database connection"""
        try:
            # Simple query to test connection
            result = self.supabase.table("students").select("count", count="exact").limit(1).execute()
            return True
        except Exception as e:
            st.warning(f"Database connection test failed: {str(e)}")
            return False

    def create_tables(self):
        """Create necessary tables if they don't exist"""
        try:
            # Students table
            students_sql = """
            CREATE TABLE IF NOT EXISTS students (
                curtin_id VARCHAR PRIMARY KEY,
                bib_id INTEGER UNIQUE NOT NULL,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                house VARCHAR NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # Events table
            events_sql = """
            CREATE TABLE IF NOT EXISTS events (
                event_id SERIAL PRIMARY KEY,
                event_name VARCHAR NOT NULL,
                event_type VARCHAR NOT NULL,
                unit VARCHAR NOT NULL,
                point_allocation JSONB DEFAULT '{}',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """
            
            # Results table
            results_sql = """
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
            """
            
            # Execute table creation (Note: In production, use Supabase dashboard)
            # This is a simplified approach for development
            print("Tables should be created via Supabase dashboard")
            return True
            
        except Exception as e:
            st.error(f"Error creating tables: {str(e)}")
            return False

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
            return True
        except Exception as e:
            st.error(f"Error adding student: {str(e)}")
            return False

    def get_student_by_bib(self, bib_id: int) -> Optional[Dict]:
        """Get student details by Bib ID"""
        try:
            result = self.supabase.table("students").select("*").eq("bib_id", bib_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            st.error(f"Error fetching student: {str(e)}")
            return None

    def get_all_students(self) -> List[Dict]:
        """Get all students"""
        try:
            result = self.supabase.table("students").select("*").execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching students: {str(e)}")
            return []

    def add_event(self, event_name: str, event_type: str, unit: str, 
                 point_allocation: Dict = None) -> bool:
        """Add a new event to the database"""
        try:
            result = self.supabase.table("events").insert({
                "event_name": event_name,
                "event_type": event_type,
                "unit": unit,
                "point_allocation": point_allocation or {}
            }).execute()
            return True
        except Exception as e:
            st.error(f"Error adding event: {str(e)}")
            return False

    def get_events_by_type(self, event_type: str) -> List[Dict]:
        """Get all events of a specific type"""
        try:
            result = self.supabase.table("events").select("*").eq("event_type", event_type).execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching events: {str(e)}")
            return []

    def get_all_events(self) -> List[Dict]:
        """Get all events"""
        try:
            result = self.supabase.table("events").select("*").execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching events: {str(e)}")
            return []

    def add_result(self, curtin_id: str, event_id: int, result_value: float) -> bool:
        """Add a result and calculate points"""
        try:
            # Insert result without triggers
            result = self.supabase.table("results").insert({
                "curtin_id": curtin_id,
                "event_id": event_id,
                "result_value": result_value,
                "points": 0,  # Will be calculated below
                "position": 999  # Temporary position
            }).execute()
            
            # Manually recalculate positions and points for this event
            self._calculate_positions_and_points(event_id)
            return True
        except Exception as e:
            st.error(f"Error adding result: {str(e)}")
            return False

    def _calculate_positions_and_points(self, event_id: int):
        """Calculate positions and points for an event"""
        try:
            # Get event details
            event_result = self.supabase.table("events").select("*").eq("event_id", event_id).execute()
            if not event_result.data:
                return
            
            event_data = event_result.data[0]
            event_type = event_data["event_type"]
            
            # Get all results for this event
            results_result = self.supabase.table("results").select("*").eq("event_id", event_id).execute()
            if not results_result.data:
                return
            
            # Sort results based on event type (lower is better for running, higher for others)
            if event_type == "Running":
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]))
            else:  # Throwing or Jumping
                sorted_results = sorted(results_result.data, key=lambda x: float(x["result_value"]), reverse=True)
            
            # Update positions and points in batch
            from config import DEFAULT_POINT_ALLOCATION
            point_allocation = event_data.get("point_allocation") or DEFAULT_POINT_ALLOCATION
            
            # Prepare batch updates
            updates = []
            for i, result in enumerate(sorted_results):
                position = i + 1
                points = point_allocation.get(str(position), 0)
                
                updates.append({
                    "result_id": result["result_id"],
                    "position": position,
                    "points": points
                })
            
            # Update all results in batch to avoid trigger issues
            for update in updates:
                self.supabase.table("results").update({
                    "position": update["position"],
                    "points": update["points"]
                }).eq("result_id", update["result_id"]).execute()
                
        except Exception as e:
            st.error(f"Error calculating positions: {str(e)}")
            # Log the specific error for debugging
            import logging
            logging.error(f"Position calculation error for event {event_id}: {str(e)}")

    def get_results_by_event(self, event_id: int) -> List[Dict]:
        """Get all results for a specific event with student details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).eq("event_id", event_id).order("position", desc=False).execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching results: {str(e)}")
            return []

    def get_results_by_event_type(self, event_type: str) -> List[Dict]:
        """Get all results for events of a specific type"""
        try:
            # Get all events of the specified type first
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
            st.error(f"Error fetching results by type: {str(e)}")
            return []

    def get_house_points(self) -> List[Dict]:
        """Get total points by house"""
        try:
            # Get all results with student house information
            results = self.supabase.table("results").select("""
                points,
                students!inner(house)
            """).execute()
            
            # Calculate totals by house
            house_totals = {}
            for result in results.data:
                house = result["students"]["house"]
                points = result["points"] or 0
                house_totals[house] = house_totals.get(house, 0) + points
            
            # Convert to list format for display
            return [{"house": house, "total_points": points} 
                   for house, points in sorted(house_totals.items(), 
                                             key=lambda x: x[1], reverse=True)]
        except Exception as e:
            st.error(f"Error calculating house points: {str(e)}")
            return []

    def get_all_results(self) -> List[Dict]:
        """Get all results with student and event details"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).execute()
            
            # Sort results in Python for reliability
            sorted_results = sorted(result.data, key=lambda x: (
                x["events"]["event_name"], 
                x.get("position", 999)
            ))
            
            return sorted_results
        except Exception as e:
            st.error(f"Error fetching all results: {str(e)}")
            return []

    def get_results_by_house(self, house: str) -> List[Dict]:
        """Get all results for a specific house"""
        try:
            result = self.supabase.table("results").select("""
                *, 
                students!inner(curtin_id, bib_id, first_name, last_name, house),
                events!inner(event_name, event_type, unit)
            """).eq("students.house", house).execute()
            return result.data
        except Exception as e:
            st.error(f"Error fetching results for house {house}: {str(e)}")
            return []
            
    def delete_result(self, result_id: int) -> bool:
        """Delete a result and recalculate positions"""
        try:
            # Get event_id before deleting
            result = self.supabase.table("results").select("event_id").eq("result_id", result_id).execute()
            if not result.data:
                return False
            
            event_id = result.data[0]["event_id"]
            
            # Delete the result
            self.supabase.table("results").delete().eq("result_id", result_id).execute()
            
            # Recalculate positions and points
            self._calculate_positions_and_points(event_id)
            return True
        except Exception as e:
            st.error(f"Error deleting result: {str(e)}")
            return False
        """Delete a result and recalculate positions"""
        try:
            # Get event_id before deleting
            result = self.supabase.table("results").select("event_id").eq("result_id", result_id).execute()
            if not result.data:
                return False
            
            event_id = result.data[0]["event_id"]
            
            # Delete the result
            self.supabase.table("results").delete().eq("result_id", result_id).execute()
            
            # Recalculate positions and points
            self._calculate_positions_and_points(event_id)
            return True
        except Exception as e:
            st.error(f"Error deleting result: {str(e)}")
            return False