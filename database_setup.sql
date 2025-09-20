-- Complete Point Allocation Fix for Live Sports Meet System
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

-- STEP 7: Update house points view to include relay team points
CREATE OR REPLACE VIEW complete_house_points AS
SELECT 
    house,
    SUM(individual_points + relay_points) AS total_points,
    SUM(individual_points) AS individual_points,
    SUM(relay_points) AS relay_points
FROM (
    -- Individual event points
    SELECT 
        s.house,
        COALESCE(SUM(r.points), 0) AS individual_points,
        0 AS relay_points
    FROM students s
    LEFT JOIN results r ON s.curtin_id = r.curtin_id
    LEFT JOIN events e ON r.event_id = e.event_id
    WHERE e.is_relay = FALSE OR e.is_relay IS NULL
    GROUP BY s.house
    
    UNION ALL
    
    -- Individual points from relay events (for individual tracking)
    SELECT 
        s.house,
        0 AS individual_points,
        COALESCE(SUM(r.points), 0) AS relay_points
    FROM students s
    LEFT JOIN results r ON s.curtin_id = r.curtin_id
    LEFT JOIN events e ON r.event_id = e.event_id
    WHERE e.is_relay = TRUE
    GROUP BY s.house
    
    UNION ALL
    
    -- Team relay points (when implemented)
    SELECT 
        rt.house,
        0 AS individual_points,
        COALESCE(SUM(rt.points), 0) AS relay_points
    FROM relay_teams rt
    GROUP BY rt.house
) combined_points
GROUP BY house
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

-- STEP 9: Verify the fix worked correctly
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

-- STEP 10: Clean up functions (keep the calculation functions for future use)
-- DROP FUNCTION recalculate_all_points_correct(); -- Keep this for future recalculations

-- Display success message
SELECT 'Point allocation fix completed successfully! Check the verification query above to confirm.' AS status;