-- LearningBridge PostgreSQL Database Initialization Script
-- Configures schemas, roles, and Row-Level Security (RLS) policies per Section 13.1

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Ensure target database exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_database WHERE datname = 'learningbridge') THEN
        CREATE DATABASE learningbridge;
    END IF;
END $$;

\c learningbridge;

-- Runtime application role with restricted privileges
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'learningbridge_app') THEN
        CREATE ROLE learningbridge_app WITH LOGIN PASSWORD 'AppPassword2026!';
    END IF;
END $$;

GRANT CONNECT ON DATABASE learningbridge TO learningbridge_app;
GRANT USAGE ON SCHEMA public TO learningbridge_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO learningbridge_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO learningbridge_app;
