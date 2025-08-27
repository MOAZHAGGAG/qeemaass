-- Create user event registrations table
CREATE TABLE IF NOT EXISTS user_event_registrations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL, -- We'll reference events by ID from Weaviate
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'registered', -- registered, cancelled, attended
    UNIQUE(user_id, event_id)
);

-- Add index for better performance
CREATE INDEX IF NOT EXISTS idx_user_event_registrations_user_id ON user_event_registrations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_event_registrations_event_id ON user_event_registrations(event_id);
