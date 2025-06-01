DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'telegrambot') THEN
        CREATE DATABASE telegrambot OWNER postgres;
    END IF;
END
$$;

\c telegrambot;

CREATE TABLE IF NOT EXISTS phone_numbers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS emails (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL
);

CREATE USER botuser WITH password '12345';

GRANT SELECT, INSERT ON phone_numbers TO botuser;
GRANT SELECT, INSERT ON emails TO botuser;
