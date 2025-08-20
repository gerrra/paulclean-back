-- PostgreSQL initialization script for Cleaning Service API
-- This script runs when the PostgreSQL container starts for the first time

-- Create database if it doesn't exist (this is usually handled by POSTGRES_DB env var)
-- CREATE DATABASE cleaning_service;

-- Connect to the cleaning_service database
\c cleaning_service;

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom functions for timestamp handling
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE cleaning_service TO cleaning_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO cleaning_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO cleaning_user;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO cleaning_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO cleaning_user;

-- Create indexes for better performance (these will be created by Alembic, but good to have)
-- CREATE INDEX IF NOT EXISTS idx_orders_scheduled_date ON orders(scheduled_date);
-- CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
-- CREATE INDEX IF NOT EXISTS idx_orders_client_id ON orders(client_id);
-- CREATE INDEX IF NOT EXISTS idx_orders_cleaner_id ON orders(cleaner_id);

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'PostgreSQL database initialized successfully for Cleaning Service API';
    RAISE NOTICE 'Database: %', current_database();
    RAISE NOTICE 'User: %', current_user();
    RAISE NOTICE 'Schema: %', current_schema();
END $$;
