
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

\d users
\d dcategories  
\d events
\d event_registrations
\d user_event_registrations

SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

SELECT trigger_name, event_object_table, action_timing, event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;

SELECT table_name, table_type 
FROM information_schema.views 
WHERE table_schema = 'public';

SELECT COUNT(*) as event_count FROM events;

SELECT id, title, category, location, event_date, organizer 
FROM events 
ORDER BY event_date 
LIMIT 5;

SELECT table_name, privilege_type 
FROM information_schema.table_privileges 
WHERE grantee = 'eventuser' 
  AND table_schema = 'public'
ORDER BY table_name, privilege_type;
