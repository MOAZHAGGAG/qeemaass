-- Create the events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    location VARCHAR(255),
    event_date DATE NOT NULL,
    event_time TIME NOT NULL,
    organizer VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create the dcategories table for event categories
CREATE TABLE IF NOT EXISTS dcategories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Create an index on event_date for better query performance
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);

-- Create an index on category for filtering
CREATE INDEX IF NOT EXISTS idx_events_category ON events(category);

-- Insert some sample data (optional)
INSERT INTO events (title, description, category, location, event_date, event_time, organizer) 
VALUES 
    ('Sample Event', 'This is a sample event for testing', 'Conference', 'New York', '2025-09-01', '10:00:00', 'Admin'),
    ('Workshop', 'Programming workshop', 'Education', 'Online', '2025-09-15', '14:00:00', 'Tech Team')
ON CONFLICT DO NOTHING;

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create a trigger to automatically update the updated_at column
DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at
    BEFORE UPDATE ON events
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();




-- ✅ Set REPLICA IDENTITY to FULL for logical decoding support
ALTER TABLE events REPLICA IDENTITY FULL;
ALTER TABLE dcategories REPLICA IDENTITY FULL;
