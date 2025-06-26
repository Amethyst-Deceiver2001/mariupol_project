-- 01_extensions.sql
-- Enable necessary PostgreSQL extensions for our toponymic database

-- PostGIS for geographic data (street locations, boundaries)
CREATE EXTENSION IF NOT EXISTS postgis;

-- UUID generation for unique identifiers
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptographic functions for data integrity
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Advanced indexing for temporal queries
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- Add comment explaining our database purpose
COMMENT ON DATABASE mariupol_toponyms IS 
'Bitemporal database tracking toponymic changes in Mariupol for historical preservation and legal documentation';