-- Fixed Sports Meet Database Schema - Handles Dependent Views
-- Execute this in your Supabase SQL Editor

-- STEP 1: Backup existing data
CREATE TABLE IF NOT EXISTS students_backup AS SELECT * FROM students;
CREATE TABLE IF NOT EXISTS events_backup AS SELECT * FROM events;
CREATE TABLE IF NOT EXISTS results_backup AS SELECT * FROM results;
CREATE TABLE IF NOT EXISTS relay_teams_backup AS SELECT * FROM relay_teams;

-- STEP 2: Drop dependent views first (CASCADE will handle dependencies)
DROP VIEW IF EXISTS athlete_complete_performance CASCADE;
DROP VIEW IF EXISTS complete_house_points CASCADE;
DROP VIEW IF EXISTS corrected_house_points CASCADE;
DROP VIEW IF EXISTS relay_team_results CASCADE;

-- STEP 3: Drop existing foreign key constraints
ALTER TABLE results DROP CONSTRAINT IF EXISTS results_curtin_id_fkey;
ALTER TABLE relay_teams DROP CONSTRAINT IF EXISTS relay_teams_member1_curtin_id_fkey;
ALTER TABLE relay_teams DROP CONSTRAINT IF EXISTS relay_teams_member2_curtin_id_fkey;
ALTER TABLE relay_teams DROP CONSTRAINT IF EXISTS relay_teams_member3_curtin_id_fkey;
ALTER TABLE relay_teams DROP CONSTRAINT IF EXISTS relay_teams_member4_curtin_id_fkey;
ALTER TABLE relay_teams DROP CONSTRAINT IF EXISTS valid_relay_team_members;

-- STEP 4: Modify students table to use bib_id as primary key
ALTER TABLE students DROP CONSTRAINT IF EXISTS students_pkey;
ALTER TABLE students DROP CONSTRAINT IF EXISTS students_bib_id_key;
ALTER TABLE students ADD CONSTRAINT students_pkey PRIMARY KEY (bib_id);
ALTER TABLE students ADD CONSTRAINT students_curtin_id_unique UNIQUE (curtin_id);

-- STEP 5: Add bib_id column to results table and populate it
ALTER TABLE results ADD COLUMN IF NOT EXISTS bib_id INTEGER;

-- Update bib_id in results table based on curtin_id lookup
UPDATE results 
SET bib_id = s.bib_id
FROM students s 
WHERE s.curtin_id = results.curtin_id 
AND results.bib_id IS NULL;

-- Remove any results that couldn't be matched (orphaned data)
DELETE FROM results WHERE bib_id IS NULL;

-- Now safe to drop curtin_id column and add foreign key
ALTER TABLE results DROP COLUMN IF EXISTS curtin_id;
ALTER TABLE results ADD CONSTRAINT results_bib_id_fkey FOREIGN KEY (bib_id) REFERENCES students(bib_id);

-- STEP 6: Update events table for gender-specific point allocations
ALTER TABLE events ADD COLUMN IF NOT EXISTS male_point_allocation JSONB DEFAULT '{"1": 10, "2": 6, "3": 3, "4": 1}';
ALTER TABLE events ADD COLUMN IF NOT EXISTS female_point_allocation JSONB DEFAULT '{"1": 10, "2": 6, "3": 3, "4": 1}';
ALTER TABLE events ADD COLUMN IF NOT EXISTS relay_male_points JSONB DEFAULT '{"1": 15, "2": 9, "3": 5, "4": 3}';
ALTER TABLE events ADD COLUMN IF NOT EXISTS relay_female_points JSONB DEFAULT '{"1": 15, "2": 9, "3": 5, "4": 3}';

-- Update existing events with gender-specific allocations
UPDATE events 
SET 
    male_point_allocation = CASE 
        WHEN is_relay = TRUE THEN '{"1": 15, "2": 9, "3": 5, "4": 3}'::jsonb
        ELSE '{"1": 10, "2": 6, "3": 3, "4": 1}'::jsonb
    END,
    female_point_allocation = CASE 
        WHEN is_relay = TRUE THEN '{"1": 15, "2": 9, "3": 5, "4": 3}'::jsonb
        ELSE '{"1": 10, "2": 6, "3": 3, "4": 1}'::jsonb
    END
WHERE male_point_allocation IS NULL OR female_point_allocation IS NULL;

-- STEP 7: Update relay_teams table to use bib_id
-- Add new bib_id columns
ALTER TABLE relay_teams ADD COLUMN IF NOT EXISTS member1_bib_id INTEGER;
ALTER TABLE relay_teams ADD COLUMN IF NOT EXISTS member2_bib_id INTEGER;
ALTER TABLE relay_teams ADD COLUMN IF NOT EXISTS member3_bib_id INTEGER;
ALTER TABLE relay_teams ADD COLUMN IF NOT EXISTS member4_bib_id INTEGER;

-- Update bib_id columns based on curtin_id lookup
UPDATE relay_teams 
SET 
    member1_bib_id = s1.bib_id,
    member2_bib_id = s2.bib_id,
    member3_bib_id = s3.bib_id,
    member4_bib_id = s4.bib_id
FROM 
    students s1,
    students s2, 
    students s3,
    students s4
WHERE 
    s1.curtin_id = relay_teams.member1_curtin_id
    AND s2.curtin_id = relay_teams.member2_curtin_id
    AND s3.curtin_id = relay_teams.member3_curtin_id
    AND s4.curtin_id = relay_teams.member4_curtin_id
    AND (relay_teams.member1_bib_id IS NULL OR relay_teams.member2_bib_id IS NULL 
         OR relay_teams.member3_bib_id IS NULL OR relay_teams.member4_bib_id IS NULL);

-- Remove relay teams that couldn't be matched (orphaned data)
DELETE FROM relay_teams 
WHERE member1_bib_id IS NULL OR member2_bib_id IS NULL 
   OR member3_bib_id IS NULL OR member4_bib_id IS NULL;

-- Drop old curtin_id columns
ALTER TABLE relay_teams DROP COLUMN IF EXISTS member1_curtin_id;
ALTER TABLE relay_teams DROP COLUMN IF EXISTS member2_curtin_id;
ALTER TABLE relay_teams DROP COLUMN IF EXISTS member3_curtin_id;
ALTER TABLE relay_teams DROP COLUMN IF EXISTS member4_curtin_id;

-- Add foreign key constraints
ALTER TABLE relay_teams ADD CONSTRAINT relay_teams_member1_fkey FOREIGN KEY (member1_bib_id) REFERENCES students(bib_id);
ALTER TABLE relay_teams ADD CONSTRAINT relay_teams_member2_fkey FOREIGN KEY (member2_bib_id) REFERENCES students(bib_id);
ALTER TABLE relay_teams ADD CONSTRAINT relay_teams_member3_fkey FOREIGN KEY (member3_bib_id) REFERENCES students(bib_id);
ALTER TABLE relay_teams ADD CONSTRAINT relay_teams_member4_fkey FOREIGN KEY (member4_bib_id) REFERENCES students(bib_id);

-- STEP 8: Create enhanced recalculation function with gender-specific points
CREATE OR REPLACE FUNCTION recalculate_points_by_gender()
RETURNS TEXT AS $$
DECLARE
    event_record RECORD;
    result_record RECORD;
    male_position INTEGER;
    female_position INTEGER;
    points_to_assign INTEGER;
    point_allocation_male JSONB;
    point_allocation_female JSONB;
    events_processed INTEGER := 0;
    results_updated INTEGER := 0;
BEGIN
    -- Loop through all events
    FOR event_record IN 
        SELECT event_id, event_name, event_type, male_point_allocation, female_point_allocation, is_relay 
        FROM events 
        ORDER BY event_name
    LOOP
        male_position := 1;
        female_position := 1;
        point_allocation_male := event_record.male_point_allocation;
        point_allocation_female := event_record.female_point_allocation;
        
        -- Skip relay events (they use different logic)
        IF event_record.is_relay = TRUE THEN
            CONTINUE;
        END IF;
        
        -- Process male results first
        FOR result_record IN
            SELECT r.result_id, r.result_value, r.bib_id, s.gender
            FROM results r
            JOIN students s ON r.bib_id = s.bib_id
            WHERE r.event_id = event_record.event_id AND s.gender = 'Male'
            ORDER BY 
                CASE 
                    WHEN event_record.event_type = 'Track' THEN r.result_value
                    ELSE -r.result_value 
                END
        LOOP
            points_to_assign := COALESCE(
                (point_allocation_male ->> male_position::text)::integer, 
                0
            );
            
            UPDATE results 
            SET 
                position = male_position, 
                points = points_to_assign
            WHERE result_id = result_record.result_id;
            
            male_position := male_position + 1;
            results_updated := results_updated + 1;
        END LOOP;
        
        -- Process female results
        FOR result_record IN
            SELECT r.result_id, r.result_value, r.bib_id, s.gender
            FROM results r
            JOIN students s ON r.bib_id = s.bib_id
            WHERE r.event_id = event_record.event_id AND s.gender = 'Female'
            ORDER BY 
                CASE 
                    WHEN event_record.event_type = 'Track' THEN r.result_value
                    ELSE -r.result_value 
                END
        LOOP
            points_to_assign := COALESCE(
                (point_allocation_female ->> female_position::text)::integer, 
                0
            );
            
            UPDATE results 
            SET 
                position = female_position, 
                points = points_to_assign
            WHERE result_id = result_record.result_id;
            
            female_position := female_position + 1;
            results_updated := results_updated + 1;
        END LOOP;
        
        events_processed := events_processed + 1;
    END LOOP;
    
    RETURN 'SUCCESS: Updated ' || results_updated || ' results across ' || events_processed || ' events with gender-specific points';
END;
$$ LANGUAGE plpgsql;

-- STEP 9: Recreate corrected house points view with new schema
CREATE OR REPLACE VIEW corrected_house_points AS
SELECT 
    house,
    individual_points + relay_team_points as total_points,
    individual_points,
    relay_team_points
FROM (
    SELECT 
        h.house,
        COALESCE(ind.points, 0) as individual_points,
        COALESCE(rel.points, 0) as relay_team_points
    FROM (
        SELECT DISTINCT house FROM students
    ) h
    LEFT JOIN (
        -- Individual event points (exclude relay events) - NOW USING BIB_ID
        SELECT 
            s.house,
            SUM(r.points) as points
        FROM students s
        JOIN results r ON s.bib_id = r.bib_id
        JOIN events e ON r.event_id = e.event_id
        WHERE e.is_relay = FALSE
        GROUP BY s.house
    ) ind ON h.house = ind.house
    LEFT JOIN (
        -- Relay team points
        SELECT 
            house,
            SUM(points) as points
        FROM relay_teams
        WHERE result_value IS NOT NULL
        GROUP BY house
    ) rel ON h.house = rel.house
) combined
ORDER BY total_points DESC;

-- STEP 10: Recreate relay team results view with new schema
CREATE OR REPLACE VIEW relay_team_results AS
SELECT 
    rt.team_id,
    rt.team_name,
    rt.house,
    rt.event_id,
    e.event_name,
    e.event_type,
    rt.result_value,
    rt.position,
    rt.points,
    s1.first_name || ' ' || s1.last_name AS member1_name,
    s2.first_name || ' ' || s2.last_name AS member2_name,
    s3.first_name || ' ' || s3.last_name AS member3_name,
    s4.first_name || ' ' || s4.last_name AS member4_name,
    s1.bib_id AS member1_bib,
    s2.bib_id AS member2_bib,
    s3.bib_id AS member3_bib,
    s4.bib_id AS member4_bib,
    -- Include bib_id columns for compatibility
    rt.member1_bib_id,
    rt.member2_bib_id,
    rt.member3_bib_id,
    rt.member4_bib_id
FROM relay_teams rt
JOIN events e ON rt.event_id = e.event_id
LEFT JOIN students s1 ON rt.member1_bib_id = s1.bib_id
LEFT JOIN students s2 ON rt.member2_bib_id = s2.bib_id
LEFT JOIN students s3 ON rt.member3_bib_id = s3.bib_id
LEFT JOIN students s4 ON rt.member4_bib_id = s4.bib_id;

-- STEP 11: Recreate athlete performance view with new schema
CREATE OR REPLACE VIEW athlete_complete_performance AS
SELECT 
    s.bib_id,
    s.curtin_id,
    s.first_name,
    s.last_name,
    s.house,
    s.gender,
    
    -- Individual event statistics
    COALESCE(ind.total_events, 0) as individual_events,
    COALESCE(ind.total_points, 0) as individual_points,
    COALESCE(ind.gold_medals, 0) as individual_gold,
    COALESCE(ind.silver_medals, 0) as individual_silver,
    COALESCE(ind.bronze_medals, 0) as individual_bronze,
    
    -- Relay participation count
    COALESCE(rel.relay_teams, 0) as relay_teams_count,
    
    -- Combined totals
    COALESCE(ind.total_events, 0) + COALESCE(rel.relay_teams, 0) as total_events_participation,
    COALESCE(ind.total_points, 0) as total_individual_points,
    
    -- Rankings by gender
    RANK() OVER (PARTITION BY s.gender ORDER BY COALESCE(ind.total_points, 0) DESC, COALESCE(ind.gold_medals, 0) DESC) as gender_rank,
    RANK() OVER (ORDER BY COALESCE(ind.total_points, 0) DESC, COALESCE(ind.gold_medals, 0) DESC) as overall_rank
    
FROM students s
LEFT JOIN (
    -- Individual performance (excluding relay events) - NOW USING BIB_ID
    SELECT 
        s2.bib_id,
        COUNT(r.result_id) as total_events,
        SUM(r.points) as total_points,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as gold_medals,
        COUNT(CASE WHEN r.position = 2 THEN 1 END) as silver_medals,
        COUNT(CASE WHEN r.position = 3 THEN 1 END) as bronze_medals
    FROM students s2
    JOIN results r ON s2.bib_id = r.bib_id
    JOIN events e ON r.event_id = e.event_id
    WHERE e.is_relay = FALSE
    GROUP BY s2.bib_id
) ind ON s.bib_id = ind.bib_id
LEFT JOIN (
    -- Relay participation count - NOW USING BIB_ID
    SELECT bib_id, COUNT(*) as relay_teams FROM (
        SELECT member1_bib_id as bib_id FROM relay_teams
        UNION ALL
        SELECT member2_bib_id FROM relay_teams  
        UNION ALL
        SELECT member3_bib_id FROM relay_teams
        UNION ALL
        SELECT member4_bib_id FROM relay_teams
    ) relay_members
    WHERE bib_id IS NOT NULL
    GROUP BY bib_id
) rel ON s.bib_id = rel.bib_id
ORDER BY total_individual_points DESC NULLS LAST;

-- STEP 12: Update relay team validation function
CREATE OR REPLACE FUNCTION validate_relay_team_members(
    member1_id INTEGER,
    member2_id INTEGER, 
    member3_id INTEGER,
    member4_id INTEGER,
    team_house VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    member_count INTEGER;
BEGIN
    -- Check that all members exist and belong to the same house as the team
    SELECT COUNT(*) INTO member_count
    FROM students 
    WHERE bib_id IN (member1_id, member2_id, member3_id, member4_id)
    AND house = team_house;
    
    -- Should have exactly 4 members from the same house
    RETURN member_count = 4;
END;
$$ LANGUAGE plpgsql;

-- Add constraint back to relay_teams table
ALTER TABLE relay_teams 
ADD CONSTRAINT valid_relay_team_members 
CHECK (validate_relay_team_members(member1_bib_id, member2_bib_id, member3_bib_id, member4_bib_id, house));

-- STEP 13: Execute the gender-specific recalculation
SELECT recalculate_points_by_gender();

-- STEP 14: Handle relay events separately (they don't use gender-specific scoring)
CREATE OR REPLACE FUNCTION calculate_relay_team_points(event_id_param INTEGER)
RETURNS void AS $$
DECLARE
    team_record RECORD;
    position_counter INTEGER := 1;
    points_to_assign INTEGER;
    event_points JSONB;
BEGIN
    -- Get the event's point allocation (use male points as default for relays)
    SELECT male_point_allocation INTO event_points
    FROM events 
    WHERE event_id = event_id_param AND is_relay = TRUE;
    
    -- Sort teams by result and assign positions/points
    FOR team_record IN
        SELECT team_id, result_value
        FROM relay_teams
        WHERE event_id = event_id_param AND result_value IS NOT NULL
        ORDER BY result_value ASC  -- For track events, lower time is better
    LOOP
        -- Get points for this position
        points_to_assign := COALESCE(
            (event_points ->> position_counter::text)::integer,
            0
        );
        
        -- Update team with position and points
        UPDATE relay_teams
        SET 
            position = position_counter,
            points = points_to_assign
        WHERE team_id = team_record.team_id;
        
        position_counter := position_counter + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Recalculate relay team points for all relay events
DO $$
DECLARE
    relay_event RECORD;
BEGIN
    FOR relay_event IN SELECT event_id FROM events WHERE is_relay = TRUE LOOP
        PERFORM calculate_relay_team_points(relay_event.event_id);
    END LOOP;
END $$;

-- STEP 15: Verification queries
SELECT 'Migration completed successfully!' as status;

-- Show updated table structures
SELECT 'Students Table Structure:' as info;
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'students' 
ORDER BY ordinal_position;

SELECT 'Events Table - Gender Columns:' as info;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'events' 
AND column_name LIKE '%point%';

SELECT 'Sample Results with Gender:' as info;
SELECT s.bib_id, s.first_name, s.last_name, s.gender, r.position, r.points, e.event_name
FROM results r
JOIN students s ON r.bib_id = s.bib_id
JOIN events e ON r.event_id = e.event_id
WHERE e.is_relay = FALSE
ORDER BY e.event_name, s.gender, r.position
LIMIT 10;