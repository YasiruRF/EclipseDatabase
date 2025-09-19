-- Sports Meet Event Management System Database Setup
-- Run this SQL script in your Supabase SQL Editor

-- Enable Row Level Security (optional but recommended)
-- You can adjust these policies based on your security requirements

-- Students table
CREATE TABLE IF NOT EXISTS students (
    curtin_id VARCHAR PRIMARY KEY,
    bib_id INTEGER UNIQUE NOT NULL CHECK (bib_id > 0),
    first_name VARCHAR NOT NULL CHECK (length(first_name) > 0),
    last_name VARCHAR NOT NULL CHECK (length(last_name) > 0),
    house VARCHAR NOT NULL CHECK (house IN ('Ignis', 'Nereus', 'Ventus', 'Terra')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id SERIAL PRIMARY KEY,
    event_name VARCHAR NOT NULL CHECK (length(event_name) > 0),
    event_type VARCHAR NOT NULL CHECK (event_type IN ('Running', 'Throwing', 'Jumping')),
    unit VARCHAR NOT NULL,
    point_allocation JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Results table
CREATE TABLE IF NOT EXISTS results (
    result_id SERIAL PRIMARY KEY,
    curtin_id VARCHAR REFERENCES students(curtin_id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(event_id) ON DELETE CASCADE,
    result_value DECIMAL NOT NULL CHECK (result_value > 0),
    points INTEGER DEFAULT 0 CHECK (points >= 0),
    position INTEGER CHECK (position > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curtin_id, event_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_students_bib_id ON students(bib_id);
CREATE INDEX IF NOT EXISTS idx_students_house ON students(house);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_results_event_id ON results(event_id);
CREATE INDEX IF NOT EXISTS idx_results_position ON results(position);

-- Insert some default events (optional - you can also add these through the UI)
INSERT INTO events (event_name, event_type, unit, point_allocation) VALUES 
    ('100m Sprint', 'Running', 'seconds', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}'),
    ('200m Sprint', 'Running', 'seconds', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}'),
    ('Long Jump', 'Jumping', 'meters', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}'),
    ('High Jump', 'Jumping', 'meters', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}'),
    ('Shot Put', 'Throwing', 'meters', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}'),
    ('Javelin', 'Throwing', 'meters', '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}')
ON CONFLICT DO NOTHING;

-- Sample students for testing (optional - remove if you don't want test data)
INSERT INTO students (curtin_id, bib_id, first_name, last_name, house) VALUES 
    ('12345678', 101, 'John', 'Smith', 'Ignis'),
    ('12345679', 102, 'Jane', 'Doe', 'Nereus'),
    ('12345680', 103, 'Mike', 'Johnson', 'Terra'),
    ('12345681', 104, 'Sarah', 'Wilson', 'Ventus'),
    ('12345682', 105, 'Alex', 'Brown', 'Ignis'),
    ('12345683', 106, 'Emily', 'Davis', 'Nereus')
ON CONFLICT DO NOTHING;

-- Views for easier querying (optional but helpful)

-- View for results with student and event details
CREATE OR REPLACE VIEW results_detailed AS
SELECT 
    r.result_id,
    r.result_value,
    r.points,
    r.position,
    r.created_at as result_date,
    s.curtin_id,
    s.bib_id,
    s.first_name,
    s.last_name,
    s.house,
    e.event_id,
    e.event_name,
    e.event_type,
    e.unit
FROM results r
JOIN students s ON r.curtin_id = s.curtin_id
JOIN events e ON r.event_id = e.event_id
ORDER BY e.event_name, r.position;

-- View for house points summary
CREATE OR REPLACE VIEW house_points_summary AS
SELECT 
    s.house,
    COUNT(r.result_id) as total_participations,
    SUM(r.points) as total_points,
    AVG(r.points) as average_points,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as first_places,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as second_places,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as third_places,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as podium_finishes
FROM students s
LEFT JOIN results r ON s.curtin_id = r.curtin_id
GROUP BY s.house
ORDER BY total_points DESC NULLS LAST;

-- Function to automatically recalculate positions and points when results change
CREATE OR REPLACE FUNCTION recalculate_event_positions(event_id_param INTEGER)
RETURNS VOID AS $$
DECLARE
    event_rec RECORD;
    result_rec RECORD;
    pos INTEGER := 1;
    points_allocation JSONB;
BEGIN
    -- Get event details
    SELECT event_type, point_allocation INTO event_rec FROM events WHERE event_id = event_id_param;
    
    -- Get point allocation, use default if not set
    points_allocation := COALESCE(event_rec.point_allocation, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}');
    
    -- Update positions and points based on event type
    FOR result_rec IN 
        SELECT result_id, result_value 
        FROM results 
        WHERE event_id = event_id_param 
        ORDER BY 
            CASE 
                WHEN event_rec.event_type = 'Running' THEN result_value 
                ELSE -result_value 
            END
    LOOP
        -- Update position and points
        UPDATE results 
        SET 
            position = pos,
            points = COALESCE((points_allocation->>pos::text)::INTEGER, 0)
        WHERE result_id = result_rec.result_id;
        
        pos := pos + 1;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically recalculate positions when results are added/updated
CREATE OR REPLACE FUNCTION trigger_recalculate_positions()
RETURNS TRIGGER AS $$
BEGIN
    -- Recalculate for the affected event
    PERFORM recalculate_event_positions(COALESCE(NEW.event_id, OLD.event_id));
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Create triggers
DROP TRIGGER IF EXISTS results_change_trigger ON results;
CREATE TRIGGER results_change_trigger
    AFTER INSERT OR UPDATE OR DELETE ON results
    FOR EACH ROW
    EXECUTE FUNCTION trigger_recalculate_positions();