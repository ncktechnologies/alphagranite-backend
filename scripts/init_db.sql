-- Database Initialization Script
-- This runs only on first database creation

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create database if not exists (this is handled by Docker)
-- The database is created by POSTGRES_DB environment variable

-- Grant necessary permissions
GRANT ALL PRIVILEGES ON DATABASE alpha_granite TO admin;
