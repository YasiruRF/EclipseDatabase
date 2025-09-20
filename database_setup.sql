-- Enhanced Sports Meet Event Management System Database Setup
-- Run this SQL script in your Supabase SQL Editor

-- Students table with gender field added
DROP TABLE IF EXISTS results CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS students CASCADE;

CREATE TABLE students (
    curtin_id VARCHAR PRIMARY KEY,
    bib_id INTEGER UNIQUE NOT NULL CHECK (bib_id > 0),
    first_name VARCHAR NOT NULL CHECK (length(first_name) > 0),
    last_name VARCHAR NOT NULL CHECK (length(last_name) > 0),
    house VARCHAR NOT NULL CHECK (house IN ('Ignis', 'Nereus', 'Ventus', 'Terra')),
    gender VARCHAR NOT NULL CHECK (gender IN ('Male', 'Female', 'Other')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced events table with better point allocation support
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    event_name VARCHAR NOT NULL CHECK (length(event_name) > 0),
    event_type VARCHAR NOT NULL CHECK (event_type IN ('Track', 'Field')),
    unit VARCHAR NOT NULL,
    is_relay BOOLEAN DEFAULT FALSE,
    point_allocation JSONB NOT NULL DEFAULT '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}',
    point_system_name VARCHAR DEFAULT 'Individual Events',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Results table (unchanged but with cascade dependencies)
CREATE TABLE results (
    result_id SERIAL PRIMARY KEY,
    curtin_id VARCHAR REFERENCES students(curtin_id) ON DELETE CASCADE,
    event_id INTEGER REFERENCES events(event_id) ON DELETE CASCADE,
    house VARCHAR NOT NULL,
    result_value DECIMAL NOT NULL CHECK (result_value > 0),
    points INTEGER DEFAULT 0 CHECK (points >= 0),
    position INTEGER CHECK (position > 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(curtin_id, event_id)
);

-- Indexes for better performance
CREATE INDEX idx_students_bib_id ON students(bib_id);
CREATE INDEX idx_students_house ON students(house);
CREATE INDEX idx_students_gender ON students(gender);
CREATE INDEX idx_events_type ON events(event_type);
CREATE INDEX idx_events_relay ON events(is_relay);
CREATE INDEX idx_results_event_id ON results(event_id);
CREATE INDEX idx_results_position ON results(position);
CREATE INDEX idx_results_points ON results(points);

-- Insert enhanced default events with proper point allocations
INSERT INTO events (event_name, event_type, unit, is_relay, point_allocation, point_system_name) VALUES 
    ('100m Sprint', 'Track', 'time', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('200m Sprint', 'Track', 'time', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('400m Sprint', 'Track', 'time', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('800m Run', 'Track', 'time', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('1500m Run', 'Track', 'time', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('4x100m Relay', 'Track', 'time', TRUE, '{"1": 20, "2": 16, "3": 12, "4": 10, "5": 8, "6": 6, "7": 4, "8": 2}', 'Relay Events'),
    ('4x400m Relay', 'Track', 'time', TRUE, '{"1": 20, "2": 16, "3": 12, "4": 10, "5": 8, "6": 6, "7": 4, "8": 2}', 'Relay Events'),
    ('Long Jump', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('High Jump', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('Triple Jump', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('Shot Put', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('Discus Throw', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events'),
    ('Javelin Throw', 'Field', 'meters', FALSE, '{"1": 10, "2": 8, "3": 6, "4": 5, "5": 4, "6": 3, "7": 2, "8": 1}', 'Individual Events');

-- Sample students with gender for testing
INSERT INTO students (curtin_id, bib_id, first_name, last_name, house, gender) VALUES 
    ('12345678', 101, 'John', 'Smith', 'Ignis', 'Male'),
    ('12345679', 102, 'Jane', 'Doe', 'Nereus', 'Female'),
    ('12345680', 103, 'Mike', 'Johnson', 'Terra', 'Male'),
    ('12345681', 104, 'Sarah', 'Wilson', 'Ventus', 'Female'),
    ('12345682', 105, 'Alex', 'Brown', 'Ignis', 'Male'),
    ('12345683', 106, 'Emily', 'Davis', 'Nereus', 'Female')
ON CONFLICT DO NOTHING;

-- Enhanced views for better data analysis

-- View for individual athlete performance (for finding best male/female athletes)
CREATE OR REPLACE VIEW individual_athlete_performance AS
SELECT 
    s.curtin_id,
    s.bib_id,
    s.first_name,
    s.last_name,
    s.house,
    s.gender,
    COUNT(r.result_id) as total_events,
    SUM(r.points) as total_points,
    AVG(r.points) as average_points,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as gold_medals,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as silver_medals,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as bronze_medals,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_medals,
    RANK() OVER (ORDER BY SUM(r.points) DESC, COUNT(CASE WHEN r.position = 1 THEN 1 END) DESC) as overall_rank,
    RANK() OVER (PARTITION BY s.gender ORDER BY SUM(r.points) DESC, COUNT(CASE WHEN r.position = 1 THEN 1 END) DESC) as gender_rank
FROM students s
LEFT JOIN results r ON s.curtin_id = r.curtin_id
GROUP BY s.curtin_id, s.bib_id, s.first_name, s.last_name, s.house, s.gender
HAVING COUNT(r.result_id) > 0
ORDER BY total_points DESC NULLS LAST;