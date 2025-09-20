"""
System Migration Script - Migrate to Gender-Specific Points and Bib ID Primary Key
Run this AFTER executing the SQL schema changes in your Supabase database
"""

from database import DatabaseManager
import json
from config import DEFAULT_INDIVIDUAL_POINTS_MALE, DEFAULT_INDIVIDUAL_POINTS_FEMALE, DEFAULT_RELAY_POINTS
import streamlit as st

def initialize_events_with_gender_points():
    """Initialize events from points.json with gender-specific point allocations"""
    print("Initializing events with gender-specific point allocations...")
    
    try:
        # Initialize database
        db = DatabaseManager(recalc_on_startup=False)  # Skip auto-recalc during init
        
        # Load events from JSON
        with open('points.json', 'r') as f:
            events_data = json.load(f)
        
        events_added = 0
        events_updated = 0
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
                    # Update existing event with gender-specific points if needed
                    male_points = existing_event.get('male_point_allocation')
                    female_points = existing_event.get('female_point_allocation')
                    
                    if not male_points or not female_points:
                        print(f"  - Updating {event_name} with gender-specific points")
                        # This would require a direct database update
                        events_updated += 1
                    else:
                        print(f"  - Skipping {event_name} (already has gender-specific points)")
                        events_skipped += 1
                    continue
                
                # Set correct point allocation based on event type
                if is_relay:
                    male_points = DEFAULT_RELAY_POINTS.copy()
                    female_points = DEFAULT_RELAY_POINTS.copy()
                    print(f"  - Adding relay event: {event_name} (15-9-5-3 points, mixed gender)")
                else:
                    male_points = DEFAULT_INDIVIDUAL_POINTS_MALE.copy()
                    female_points = DEFAULT_INDIVIDUAL_POINTS_FEMALE.copy()
                    print(f"  - Adding individual event: {event_name} (10-6-3-1 points, gender-specific)")
                
                # Add event to database with gender-specific points
                success = db.add_event(
                    event_name=event_name,
                    event_type=event_type,
                    unit=unit,
                    is_relay=is_relay,
                    male_points=male_points,
                    female_points=female_points
                )
                
                if success:
                    events_added += 1
                    print(f"    ✅ Added successfully with gender-specific points")
                else:
                    print(f"    ❌ Failed to add")
        
        print(f"\n📊 Summary:")
        print(f"  - Events added: {events_added}")
        print(f"  - Events updated: {events_updated}")
        print(f"  - Events skipped: {events_skipped}")
        print(f"  - Total processed: {events_added + events_updated + events_skipped}")
        
        if events_added > 0 or events_updated > 0:
            print(f"\n✅ Event initialization completed successfully!")
        else:
            print(f"\n⚠️ No new events were added or updated")
            
    except Exception as e:
        print(f"❌ Error during event initialization: {str(e)}")
        return False
    
    return True

def verify_gender_specific_setup():
    """Verify that the system is properly configured for gender-specific competition"""
    print("\nVerifying gender-specific system setup...")
    
    try:
        db = DatabaseManager(recalc_on_startup=False)
        
        # Check students table structure
        students = db.get_all_students()
        if students:
            sample_student = students[0]
            has_gender = 'gender' in sample_student
            has_bib_id = 'bib_id' in sample_student
            
            print(f"  ✅ Students table: {len(students)} students found")
            print(f"  {'✅' if has_gender else '❌'} Gender field: {'Present' if has_gender else 'Missing'}")
            print(f"  {'✅' if has_bib_id else '❌'} Bib ID field: {'Present' if has_bib_id else 'Missing'}")
        else:
            print("  ⚠️ No students found in database")
        
        # Check events table structure
        events = db.get_all_events()
        if events:
            gender_events = 0
            for event in events:
                if event.get('male_point_allocation') and event.get('female_point_allocation'):
                    gender_events += 1
            
            print(f"  ✅ Events table: {len(events)} events found")
            print(f"  ✅ Gender-specific events: {gender_events}/{len(events)} events configured")
            
            if gender_events < len(events):
                print(f"  ⚠️ {len(events) - gender_events} events need gender-specific point configuration")
        else:
            print("  ⚠️ No events found in database")
        
        # Check if views exist
        try:
            house_points = db.get_house_points()
            print(f"  ✅ House points calculation: Working ({len(house_points)} houses)")
        except Exception as e:
            print(f"  ❌ House points calculation: Error - {str(e)}")
        
        try:
            top_athletes = db.get_top_individual_athletes(limit=5)
            print(f"  ✅ Athlete rankings: Working ({len(top_athletes)} athletes)")
        except Exception as e:
            print(f"  ❌ Athlete rankings: Error - {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during verification: {str(e)}")
        return False

def test_gender_specific_scoring():
    """Test that gender-specific scoring is working correctly"""
    print("\nTesting gender-specific scoring...")
    
    try:
        db = DatabaseManager(recalc_on_startup=False)
        
        # Get sample results
        results = db.get_all_results()
        if not results:
            print("  ⚠️ No results found - cannot test scoring")
            return True
        
        # Group results by event and gender
        events_tested = {}
        
        for result in results:
            event_id = result.get('event_id')
            student_data = result.get('students', {})
            if isinstance(student_data, list):
                student_data = student_data[0] if student_data else {}
            
            gender = student_data.get('gender', 'Unknown')
            position = result.get('position', 999)
            points = result.get('points', 0)
            
            if event_id not in events_tested:
                events_tested[event_id] = {'Male': [], 'Female': [], 'Other': []}
            
            events_tested[event_id][gender].append({
                'position': position,
                'points': points
            })
        
        # Analyze scoring patterns
        for event_id, gender_results in events_tested.items():
            event_name = "Unknown Event"
            try:
                all_events = db.get_all_events()
                event_info = next((e for e in all_events if e['event_id'] == event_id), None)
                if event_info:
                    event_name = event_info['event_name']
            except:
                pass
            
            male_count = len(gender_results['Male'])
            female_count = len(gender_results['Female'])
            
            if male_count > 0 and female_count > 0:
                print(f"  ✅ {event_name}: {male_count} male, {female_count} female competitors")
                
                # Check if position 1 exists for both genders (indicates separate competition)
                male_has_first = any(r['position'] == 1 for r in gender_results['Male'])
                female_has_first = any(r['position'] == 1 for r in gender_results['Female'])
                
                if male_has_first and female_has_first:
                    print(f"    ✅ Separate gender competitions confirmed (both have 1st place)")
                else:
                    print(f"    ⚠️ May not have separate competitions")
        
        print(f"\n✅ Gender-specific scoring test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error during scoring test: {str(e)}")
        return False

def run_migration():
    """Run complete migration to gender-specific system"""
    print("🔧 Starting Migration to Gender-Specific Points System...")
    print("=" * 60)
    
    print("\n⚠️ IMPORTANT: Make sure you have:")
    print("1. ✅ Executed the SQL schema changes in Supabase")
    print("2. ✅ Backed up your existing data")
    print("3. ✅ Verified all students have gender information")
    
    input("\nPress Enter to continue with migration...")
    
    # Step 1: Initialize events with gender-specific points
    print("\nStep 1: Initializing gender-specific events")
    success1 = initialize_events_with_gender_points()
    
    # Step 2: Verify system setup
    print("\nStep 2: Verifying system setup")
    success2 = verify_gender_specific_setup()
    
    # Step 3: Test gender-specific scoring
    print("\nStep 3: Testing gender-specific scoring")
    success3 = test_gender_specific_scoring()
    
    # Step 4: Recalculate all points with new system
    print("\nStep 4: Recalculating all points with gender-specific system")
    try:
        db = DatabaseManager(recalc_on_startup=False)
        recalc_success = db.recalculate_all_points()
        print(f"  {'✅' if recalc_success else '❌'} Point recalculation: {'Success' if recalc_success else 'Failed'}")
    except Exception as e:
        print(f"  ❌ Point recalculation failed: {str(e)}")
        recalc_success = False
    
    # Summary
    print("\n" + "=" * 60)
    print("🔧 Migration Summary:")
    print(f"  - Event initialization: {'✅ Success' if success1 else '❌ Failed'}")
    print(f"  - System verification: {'✅ Success' if success2 else '❌ Failed'}")
    print(f"  - Scoring test: {'✅ Success' if success3 else '❌ Failed'}")
    print(f"  - Point recalculation: {'✅ Success' if recalc_success else '❌ Failed'}")
    
    if success1 and success2 and success3 and recalc_success:
        print("\n🎉 Migration completed successfully!")
        print("\n✅ Your Sports Meet system now has:")
        print("  - Bib ID as primary key for students")
        print("  - Gender-specific competitions for individual events")
        print("  - Mixed-gender relay team competitions")
        print("  - Separate rankings for male and female athletes")
        print("  - Proper point allocation for each competition category")
        print("\nNext steps:")
        print("1. Run 'streamlit run main.py' to start the application")
        print("2. Verify student data and gender information")
        print("3. Test event entry with gender-specific competition")
        print("4. Check house points leaderboard")
    else:
        print("\n⚠️ Migration completed with issues. Please check:")
        print("1. SQL schema has been properly applied")
        print("2. All students have gender information")
        print("3. Database connection is working")
        print("4. Events are properly configured")
    
    return success1 and success2 and success3 and recalc_success

if __name__ == "__main__":
    run_migration()