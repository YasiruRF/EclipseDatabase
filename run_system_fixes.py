"""
System Fix Script - Run this to initialize events with correct point allocations
Run this script AFTER you have executed the SQL setup in your Supabase database.
"""

from database import DatabaseManager
import json
from config import DEFAULT_INDIVIDUAL_POINTS, DEFAULT_RELAY_POINTS
import streamlit as st

def initialize_events_from_json():
    """Initialize events from points.json with correct point allocations"""
    print("Initializing events from points.json...")
    
    try:
        # Initialize database
        db = DatabaseManager()
        
        # Load events from JSON
        with open('points.json', 'r') as f:
            events_data = json.load(f)
        
        events_added = 0
        events_skipped = 0
        
        # Process each event type
        for event_type, events_list in events_data.items():
            print(f"\nProcessing {event_type} events...")
            
            for event_info in events_list:
                event_name = event_info['name']
                unit = event_info['unit']
                is_relay = event_info.get('is_relay', False)
                
                # Check if event already exists
                existing_event = db.get_event_by_name(event_name)
                if existing_event:
                    print(f"  - Skipping {event_name} (already exists)")
                    events_skipped += 1
                    continue
                
                # Set correct point allocation based on event type
                if is_relay:
                    point_allocation = DEFAULT_RELAY_POINTS.copy()
                    point_system_name = "Relay Events"
                    print(f"  - Adding relay event: {event_name} (15-9-5-3 points)")
                else:
                    point_allocation = DEFAULT_INDIVIDUAL_POINTS.copy()
                    point_system_name = "Individual Events"
                    print(f"  - Adding individual event: {event_name} (10-6-3-1 points)")
                
                # Add event to database
                success = db.add_event(
                    event_name=event_name,
                    event_type=event_type,
                    unit=unit,
                    is_relay=is_relay,
                    point_allocation=point_allocation,
                    point_system_name=point_system_name
                )
                
                if success:
                    events_added += 1
                    print(f"    ✅ Added successfully")
                else:
                    print(f"    ❌ Failed to add")
        
        print(f"\n📊 Summary:")
        print(f"  - Events added: {events_added}")
        print(f"  - Events skipped: {events_skipped}")
        print(f"  - Total events: {events_added + events_skipped}")
        
        if events_added > 0:
            print(f"\n✅ Event initialization completed successfully!")
        else:
            print(f"\n⚠️  No new events were added (all events may already exist)")
            
    except Exception as e:
        print(f"❌ Error during event initialization: {str(e)}")
        return False
    
    return True

def verify_point_allocations():
    """Verify that all events have correct point allocations"""
    print("\nVerifying point allocations...")
    
    try:
        db = DatabaseManager()
        all_events = db.get_all_events()
        
        if not all_events:
            print("⚠️  No events found in database")
            return False
        
        correct_individual = {1: 10, 2: 6, 3: 3, 4: 1}
        correct_relay = {1: 15, 2: 9, 3: 5, 4: 3}
        
        issues_found = 0
        
        for event in all_events:
            event_name = event['event_name']
            is_relay = event.get('is_relay', False)
            point_allocation = event.get('point_allocation', {})
            
            # Convert string keys to int for comparison
            current_allocation = {}
            for k, v in point_allocation.items():
                try:
                    current_allocation[int(k)] = v
                except (ValueError, TypeError):
                    current_allocation[k] = v
            
            expected_allocation = correct_relay if is_relay else correct_individual
            
            if current_allocation != expected_allocation:
                print(f"  ❌ {event_name}: Expected {expected_allocation}, got {current_allocation}")
                issues_found += 1
            else:
                event_type = "Relay" if is_relay else "Individual"
                print(f"  ✅ {event_name}: {event_type} points correct")
        
        if issues_found == 0:
            print(f"\n✅ All {len(all_events)} events have correct point allocations!")
        else:
            print(f"\n⚠️  Found {issues_found} events with incorrect point allocations")
            print("Run the SQL script to fix point allocations")
        
        return issues_found == 0
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

def run_system_fixes():
    """Run all system fixes"""
    print("🔧 Starting Sports Meet System Fixes...")
    print("=" * 50)
    
    # Step 1: Initialize events
    print("Step 1: Initializing events from points.json")
    success1 = initialize_events_from_json()
    
    # Step 2: Verify point allocations
    print("\nStep 2: Verifying point allocations")
    success2 = verify_point_allocations()
    
    # Summary
    print("\n" + "=" * 50)
    print("🔧 System Fix Summary:")
    print(f"  - Event initialization: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"  - Point verification: {'✅ Success' if success2 else '❌ Failed'}")
    
    if success1 and success2:
        print("\n🎉 All fixes completed successfully!")
        print("Your Sports Meet system is ready to use.")
        print("\nNext steps:")
        print("1. Run 'streamlit run main.py' to start the application")
        print("2. Add students in the Student Management tab")
        print("3. Record event results")
        print("4. View house points leaderboard")
    else:
        print("\n⚠️  Some fixes failed. Please check:")
        print("1. Supabase database connection")
        print("2. Database setup SQL has been run")
        print("3. Environment variables are set")
    
    return success1 and success2

if __name__ == "__main__":
    run_system_fixes()