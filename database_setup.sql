-- Corrected Point Allocation Fix for Live Sports Meet System
-- Execute this in your Supabase SQL Editor

-- STEP 1: Backup existing data (IMPORTANT!)
CREATE TABLE IF NOT EXISTS results_backup AS SELECT * FROM results;
CREATE TABLE IF NOT EXISTS events_backup AS SELECT * FROM events;

-- STEP 2: Update point allocations to match your requirements

-- Individual Events: 1st=10, 2nd=6, 3rd=3, 4th=1
UPDATE events 
SET point_allocation = '{"1": 10, "2": 6, "3": 3, "4": 1}'::jsonb,
    point_system_name = 'Individual Events'
WHERE is_relay = FALSE;

-- Relay Events: 1st=15, 2nd=9, 3rd=5, 4th=3  
UPDATE events 
SET point_allocation = '{"1": 15, "2": 9, "3": 5, "4": 3}'::jsonb,
    point_system_name = 'Relay Events'
WHERE is_relay = TRUE;

-- STEP 3: Create enhanced recalculation function
CREATE OR REPLACE FUNCTION recalculate_all_points_correct()
RETURNS TEXT AS $$
DECLARE
    event_record RECORD;
    result_record RECORD;
    position_counter INTEGER;
    points_to_assign INTEGER;
    events_processed INTEGER := 0;
    results_updated INTEGER := 0;
BEGIN
    -- Loop through all events
    FOR event_record IN 
        SELECT event_id, event_name, event_type, point_allocation, is_relay 
        FROM events 
        ORDER BY event_name
    LOOP
        position_counter := 1;
        
        -- Get results sorted appropriately (Track: lower time better, Field: higher distance better)
        FOR result_record IN
            SELECT result_id, result_value, curtin_id
            FROM results 
            WHERE event_id = event_record.event_id
            ORDER BY 
                CASE 
                    WHEN event_record.event_type = 'Track' THEN result_value
                    ELSE -result_value 
                END
        LOOP
            -- Get points from the correct point allocation
            points_to_assign := COALESCE(
                (event_record.point_allocation ->> position_counter::text)::integer, 
                0
            );
            
            -- Update the result with correct position and points
            UPDATE results 
            SET 
                position = position_counter, 
                points = points_to_assign
            WHERE result_id = result_record.result_id;
            
            position_counter := position_counter + 1;
            results_updated := results_updated + 1;
        END LOOP;
        
        events_processed := events_processed + 1;
    END LOOP;
    
    RETURN 'SUCCESS: Updated ' || results_updated || ' results across ' || events_processed || ' events';
END;
$$ LANGUAGE plpgsql;

-- STEP 4: Execute the recalculation
SELECT recalculate_all_points_correct();

-- STEP 5: Add relay team tracking table for team-based relay scoring
CREATE TABLE IF NOT EXISTS relay_teams (
    team_id SERIAL PRIMARY KEY,
    team_name VARCHAR NOT NULL,
    house VARCHAR NOT NULL CHECK (house IN ('Ignis', 'Nereus', 'Ventus', 'Terra')),
    event_id INTEGER REFERENCES events(event_id),
    member1_curtin_id VARCHAR REFERENCES students(curtin_id),
    member2_curtin_id VARCHAR REFERENCES students(curtin_id),
    member3_curtin_id VARCHAR REFERENCES students(curtin_id),
    member4_curtin_id VARCHAR REFERENCES students(curtin_id),
    result_value DECIMAL,
    points INTEGER DEFAULT 0,
    position INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(house, event_id)
);

-- STEP 6: Create view for relay team results
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
    s4.bib_id AS member4_bib
FROM relay_teams rt
JOIN events e ON rt.event_id = e.event_id
LEFT JOIN students s1 ON rt.member1_curtin_id = s1.curtin_id
LEFT JOIN students s2 ON rt.member2_curtin_id = s2.curtin_id
LEFT JOIN students s3 ON rt.member3_curtin_id = s3.curtin_id
LEFT JOIN students s4 ON rt.member4_curtin_id = s4.curtin_id;

-- STEP 7: CORRECTED house points view - no double counting
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
        -- Get all houses
        SELECT DISTINCT house FROM students
    ) h
    LEFT JOIN (
        -- Individual event points ONLY (exclude relay events from results table)
        SELECT 
            s.house,
            SUM(r.points) as points
        FROM students s
        JOIN results r ON s.curtin_id = r.curtin_id
        JOIN events e ON r.event_id = e.event_id
        WHERE e.is_relay = FALSE  -- Only individual events
        GROUP BY s.house
    ) ind ON h.house = ind.house
    LEFT JOIN (
        -- Relay team points ONLY (from relay_teams table)
        SELECT 
            house,
            SUM(points) as points
        FROM relay_teams
        WHERE result_value IS NOT NULL  -- Only completed relay teams
        GROUP BY house
    ) rel ON h.house = rel.house
) combined
ORDER BY total_points DESC;

-- STEP 8: Create function to calculate relay team positions and points
CREATE OR REPLACE FUNCTION calculate_relay_team_points(event_id_param INTEGER)
RETURNS void AS $$
DECLARE
    team_record RECORD;
    position_counter INTEGER := 1;
    points_to_assign INTEGER;
    event_points JSONB;
BEGIN
    -- Get the event's point allocation
    SELECT point_allocation INTO event_points
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

-- STEP 9: Add validation function for relay team members
CREATE OR REPLACE FUNCTION validate_relay_team_members(
    member1_id VARCHAR,
    member2_id VARCHAR, 
    member3_id VARCHAR,
    member4_id VARCHAR,
    team_house VARCHAR
)
RETURNS BOOLEAN AS $$
DECLARE
    member_count INTEGER;
BEGIN
    -- Check that all members exist and belong to the same house as the team
    SELECT COUNT(*) INTO member_count
    FROM students 
    WHERE curtin_id IN (member1_id, member2_id, member3_id, member4_id)
    AND house = team_house;
    
    -- Should have exactly 4 members from the same house
    RETURN member_count = 4;
END;
$$ LANGUAGE plpgsql;

-- STEP 10: Add constraint to relay_teams table
ALTER TABLE relay_teams 
DROP CONSTRAINT IF EXISTS valid_relay_team_members;

ALTER TABLE relay_teams 
ADD CONSTRAINT valid_relay_team_members 
CHECK (validate_relay_team_members(member1_curtin_id, member2_curtin_id, member3_curtin_id, member4_curtin_id, house));

-- STEP 11: Create comprehensive athlete performance view
CREATE OR REPLACE VIEW athlete_complete_performance AS
SELECT 
    s.curtin_id,
    s.bib_id,
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
    
    -- Combined totals (individual points only, as relay points go to teams)
    COALESCE(ind.total_events, 0) + COALESCE(rel.relay_teams, 0) as total_events_participation,
    COALESCE(ind.total_points, 0) as total_individual_points,
    
    -- Overall ranking based on individual points
    RANK() OVER (ORDER BY COALESCE(ind.total_points, 0) DESC, COALESCE(ind.gold_medals, 0) DESC) as overall_rank,
    RANK() OVER (PARTITION BY s.gender ORDER BY COALESCE(ind.total_points, 0) DESC, COALESCE(ind.gold_medals, 0) DESC) as gender_rank
    
FROM students s
LEFT JOIN (
    -- Individual performance (excluding relay events)
    SELECT 
        s2.curtin_id,
        COUNT(r.result_id) as total_events,
        SUM(r.points) as total_points,
        COUNT(CASE WHEN r.position = 1 THEN 1 END) as gold_medals,
        COUNT(CASE WHEN r.position = 2 THEN 1 END) as silver_medals,
        COUNT(CASE WHEN r.position = 3 THEN 1 END) as bronze_medals
    FROM students s2
    JOIN results r ON s2.curtin_id = r.curtin_id
    JOIN events e ON r.event_id = e.event_id
    WHERE e.is_relay = FALSE
    GROUP BY s2.curtin_id
) ind ON s.curtin_id = ind.curtin_id
LEFT JOIN (
    -- Relay participation count
    SELECT curtin_id, COUNT(*) as relay_teams FROM (
        SELECT member1_curtin_id as curtin_id FROM relay_teams
        UNION ALL
        SELECT member2_curtin_id FROM relay_teams  
        UNION ALL
        SELECT member3_curtin_id FROM relay_teams
        UNION ALL
        SELECT member4_curtin_id FROM relay_teams
    ) relay_members
    GROUP BY curtin_id
) rel ON s.curtin_id = rel.curtin_id
ORDER BY total_individual_points DESC NULLS LAST;

-- STEP 12: Verify the fix worked correctly
SELECT 
    e.event_name,
    e.is_relay,
    e.point_allocation,
    COUNT(r.result_id) as result_count,
    MIN(r.points) as min_points,
    MAX(r.points) as max_points
FROM events e
LEFT JOIN results r ON e.event_id = r.event_id
GROUP BY e.event_id, e.event_name, e.is_relay, e.point_allocation
ORDER BY e.event_name;

-- Display success message
SELECT 'CORRECTED point allocation fix completed successfully! Relay and individual points are now properly separated.' AS status;