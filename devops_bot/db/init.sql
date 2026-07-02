CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

GRANT SELECT, INSERT ON phone_numbers TO CURRENT_USER;
GRANT SELECT, INSERT ON emails TO CURRENT_USER;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO CURRENT_USER;

SELECT pg_create_physical_replication_slot('replication_slot')
WHERE NOT EXISTS (
    SELECT 1 FROM pg_replication_slots WHERE slot_name = 'replication_slot'
);
