Let me guide you through building your toponymic database step by step. Think of this as constructing a digital library that will preserve the memory of every street name in Mariupol - we'll start with the foundation and build up carefully.
Understanding What We're Building
Before we write any code, let's establish what a toponymic database really is. Imagine you're creating a time machine for place names - one that can show you what any street was called on any given date, who changed it, and why. This isn't just data storage; it's preserving history in a legally defensible way.
Question to consider: Why do you think we need to track both when a name actually changed (like when a street sign was replaced) AND when we recorded that change in our database?
Step 1: Creating Your Project Structure
Let's start by creating a well-organized folder structure. Each folder has a specific purpose, like rooms in a house:
bash# Create your main project directory
mkdir ~/Desktop/mariupol_project/toponymic_database
cd ~/Desktop/mariupol_project/toponymic_database

# Create the folder structure
mkdir -p {config,scripts/{setup,import,utils},data/{raw,processed,backups},sql/{tables,functions,triggers,views},tests,logs,docs}

# Create a Python virtual environment (keeps our project isolated)
python3 -m venv venv
source venv/bin/activate  # On Mac/Linux
Your folder structure should look like this:
toponymic_database/
├── config/              # Database connections, settings
├── scripts/             # Python code for data processing
│   ├── setup/          # Installation and initialization
│   ├── import/         # Data import from various sources
│   └── utils/          # Helper functions
├── data/               # Data storage (git-ignored)
│   ├── raw/           # Original source files
│   ├── processed/     # Cleaned, ready-to-import data
│   └── backups/       # Database backups
├── sql/                # SQL code organized by type
│   ├── tables/        # Table definitions
│   ├── functions/     # Stored procedures
│   ├── triggers/      # Automated actions
│   └── views/         # Saved queries
├── tests/              # Test your code
├── logs/               # Track what happens
├── docs/               # Documentation
└── venv/               # Python environment (git-ignored)
Now, let's create essential configuration files:
Step 2: Environment Configuration
First, let's create a .env file to store sensitive information safely:
bash# Create .env file
cat > .env << 'EOF'
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mariupol_toponyms
DB_USER=mariupol_researcher
DB_PASSWORD=ChangeMeToSecurePassword2024!

# Application Settings
LOG_LEVEL=INFO
TIMEZONE=Europe/Kiev

# API Keys (we'll need these later)
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
EOF

# Create .gitignore to protect sensitive data
cat > .gitignore << 'EOF'
# Sensitive files
.env
*.log
*.key
*.pem

# Data files (too large for git)
data/raw/*
data/processed/*
data/backups/*
!data/*/README.md

# Python
venv/
__pycache__/
*.pyc
.pytest_cache/

# OS files
.DS_Store
Thumbs.db

# IDE
.vscode/
.idea/
EOF
Think about this: Why do we keep passwords in a separate .env file instead of hardcoding them in our scripts?
Step 3: Setting Up Docker for PostgreSQL
Since you're on a Mac Air with limited resources, we'll use Docker to run PostgreSQL efficiently. Create a docker-compose.yml file:
yaml# docker-compose.yml
version: '3.8'

services:
  postgis:
    image: postgis/postgis:16-3.4
    container_name: mariupol_postgis
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_DB: mariupol_toponyms
      POSTGRES_USER: mariupol_researcher
      POSTGRES_PASSWORD: ChangeMeToSecurePassword2024!
      
    volumes:
      # Data persistence
      - postgis_data:/var/lib/postgresql/data
      # Initialization scripts
      - ./sql/setup:/docker-entrypoint-initdb.d
      # Backup location
      - ./data/backups:/backups
      
    # Resource limits for Mac Air
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2.0'

volumes:
  postgis_data:
    driver: local
Now let's create a Makefile to simplify common operations:
makefile# Makefile
.PHONY: help up down logs psql backup restore clean

help:
	@echo "Available commands:"
	@echo "  make up       - Start the database"
	@echo "  make down     - Stop the database"
	@echo "  make logs     - View database logs"
	@echo "  make psql     - Connect to database"
	@echo "  make backup   - Create a backup"
	@echo "  make restore  - Restore from backup"
	@echo "  make clean    - Remove all data (careful!)"

up:
	docker-compose up -d
	@echo "Waiting for database to be ready..."
	@sleep 5
	@echo "Database is running!"

down:
	docker-compose down

logs:
	docker-compose logs -f postgis

psql:
	docker exec -it mariupol_postgis psql -U mariupol_researcher -d mariupol_toponyms

backup:
	@mkdir -p data/backups
	@DATE=$$(date +%Y%m%d_%H%M%S); \
	docker exec mariupol_postgis pg_dump -U mariupol_researcher mariupol_toponyms > data/backups/backup_$$DATE.sql
	@echo "Backup created!"

restore:
	@echo "Available backups:"
	@ls -la data/backups/*.sql
	@echo "To restore, run: docker exec -i mariupol_postgis psql -U mariupol_researcher mariupol_toponyms < data/backups/[backup_file]"

clean:
	@echo "WARNING: This will delete all data!"
	@echo "Press Ctrl+C to cancel, or Enter to continue"
	@read confirm
	docker-compose down -v
Step 4: Database Schema Creation
Now let's create the actual database structure. We'll build this in stages, starting with the core tables.
Create sql/setup/01_extensions.sql:
sql-- 01_extensions.sql
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
Create sql/setup/02_schemas.sql:
sql-- 02_schemas.sql
-- Create schemas to organize our database objects

-- Main schema for current data
CREATE SCHEMA IF NOT EXISTS toponyms;

-- Schema for audit trail and history
CREATE SCHEMA IF NOT EXISTS audit;

-- Schema for import staging
CREATE SCHEMA IF NOT EXISTS staging;

-- Set default search path
SET search_path TO toponyms, public;

-- Comments for documentation
COMMENT ON SCHEMA toponyms IS 'Current toponymic entities and names';
COMMENT ON SCHEMA audit IS 'Complete audit trail for legal compliance';
COMMENT ON SCHEMA staging IS 'Temporary tables for data import and validation';
Now, let's create our main tables. Create sql/tables/01_entity_types.sql:
sql-- 01_entity_types.sql
-- Define the types of geographic entities we'll track

CREATE TABLE toponyms.entity_types (
    type_code VARCHAR(20) PRIMARY KEY,
    type_name_uk VARCHAR(100) NOT NULL,  -- Ukrainian name
    type_name_en VARCHAR(100) NOT NULL,  -- English name
    hierarchy_level INTEGER NOT NULL,     -- 1=region, 2=district, 3=street, etc.
    description TEXT
);

-- Insert standard types
INSERT INTO toponyms.entity_types (type_code, type_name_uk, type_name_en, hierarchy_level, description) VALUES
('region', 'область', 'region', 1, 'Administrative region/oblast'),
('district', 'район', 'district', 2, 'City district or raion'),
('street', 'вулиця', 'street', 3, 'Street, avenue, or boulevard'),
('square', 'площа', 'square', 3, 'Public square or plaza'),
('park', 'парк', 'park', 3, 'Park or public garden'),
('building', 'будівля', 'building', 4, 'Named building or complex');

COMMENT ON TABLE toponyms.entity_types IS 'Reference table for types of toponymic entities';
Pause and reflect: Why do you think we're storing both Ukrainian and English names for entity types? How might this help with international legal proceedings?
Create sql/tables/02_toponymic_entities.sql:
sql-- 02_toponymic_entities.sql
-- Core table for all geographic entities (streets, districts, etc.)

CREATE TABLE toponyms.entities (
    -- Primary identification
    entity_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type VARCHAR(20) NOT NULL REFERENCES toponyms.entity_types(type_code),
    
    -- Bitemporal columns (this is crucial for legal evidence)
    valid_start TIMESTAMPTZ NOT NULL,      -- When the entity started existing in reality
    valid_end TIMESTAMPTZ DEFAULT NULL,    -- When it stopped (NULL = still exists)
    txn_start TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,  -- When we recorded this
    txn_end TIMESTAMPTZ DEFAULT NULL,      -- When this record was superseded
    
    -- Geographic data
    geometry GEOMETRY(GEOMETRY, 4326),     -- Can be point, line, or polygon
    centroid GEOMETRY(POINT, 4326),        -- Center point for quick lookups
    
    -- Legal tracking
    source_authority VARCHAR(255) NOT NULL,  -- Who declared this entity
    source_document VARCHAR(500),            -- Legal document reference
    source_date DATE,                        -- When it was officially declared
    
    -- Data integrity
    created_by VARCHAR(100) NOT NULL DEFAULT CURRENT_USER,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verification_status VARCHAR(20) DEFAULT 'pending',
    verification_notes TEXT,
    
    -- Ensure no temporal overlaps for the same entity
    EXCLUDE USING gist (
        entity_id WITH =,
        tstzrange(valid_start, valid_end) WITH &&
    ) WHERE (txn_end IS NULL)
);

-- Indexes for performance
CREATE INDEX idx_entities_type ON toponyms.entities(entity_type);
CREATE INDEX idx_entities_temporal ON toponyms.entities(valid_start, valid_end);
CREATE INDEX idx_entities_spatial ON toponyms.entities USING GIST(geometry);
CREATE INDEX idx_entities_centroid ON toponyms.entities USING GIST(centroid);

COMMENT ON TABLE toponyms.entities IS 'Master table of all toponymic entities with bitemporal tracking';
COMMENT ON COLUMN toponyms.entities.valid_start IS 'When this entity configuration became true in the real world';
COMMENT ON COLUMN toponyms.entities.txn_start IS 'When we recorded this information in our database';
Create sql/tables/03_toponymic_names.sql:
sql-- 03_toponymic_names.sql
-- Names for entities in multiple languages with historical tracking

CREATE TABLE toponyms.names (
    -- Identity
    name_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id UUID NOT NULL REFERENCES toponyms.entities(entity_id),
    
    -- The actual name
    name_text VARCHAR(500) NOT NULL,
    normalized_name VARCHAR(500),          -- Lowercase, no punctuation for searching
    
    -- Language and script
    language_code VARCHAR(3) NOT NULL,     -- ISO 639-2 (ukr, rus, eng)
    script_code VARCHAR(4) DEFAULT 'Cyrl', -- ISO 15924 (Cyrl, Latn)
    transliteration_system VARCHAR(50),    -- If transliterated, which system
    
    -- Name classification
    name_type VARCHAR(20) NOT NULL CHECK (name_type IN (
        'official',      -- Current official name
        'historical',    -- Former official name
        'traditional',   -- Long-standing local name
        'colloquial',    -- Informal name used by locals
        'memorial',      -- Commemorative name
        'occupational'   -- Name imposed by occupying forces
    )),
    
    -- Temporal tracking (when was this name valid?)
    valid_start TIMESTAMPTZ NOT NULL,
    valid_end TIMESTAMPTZ DEFAULT NULL,
    txn_start TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    txn_end TIMESTAMPTZ DEFAULT NULL,
    
    -- Legal documentation
    decree_number VARCHAR(200),            -- Official decree/order number
    decree_date DATE,                      -- When the decree was issued
    decree_authority VARCHAR(500),         -- Who issued it
    
    -- Quality tracking
    source_type VARCHAR(50),               -- 'official_document', 'osm', 'witness', etc.
    source_reliability VARCHAR(20) DEFAULT 'unverified',
    notes TEXT,
    
    -- No duplicate active names for same entity/language/type
    EXCLUDE USING gist (
        entity_id WITH =,
        language_code WITH =,
        name_type WITH =,
        tstzrange(valid_start, valid_end) WITH &&
    ) WHERE (txn_end IS NULL)
);

-- Performance indexes
CREATE INDEX idx_names_entity ON toponyms.names(entity_id);
CREATE INDEX idx_names_text ON toponyms.names(name_text);
CREATE INDEX idx_names_normalized ON toponyms.names(normalized_name);
CREATE INDEX idx_names_temporal ON toponyms.names(valid_start, valid_end);
CREATE INDEX idx_names_language ON toponyms.names(language_code);

-- Full text search for Cyrillic
CREATE INDEX idx_names_fulltext ON toponyms.names 
    USING gin(to_tsvector('simple', name_text));

COMMENT ON TABLE toponyms.names IS 'Multi-lingual names for toponymic entities with full temporal tracking';
Step 5: Creating Helper Functions
Now let's create some functions to make working with the database easier. Create sql/functions/01_name_normalization.sql:
sql-- 01_name_normalization.sql
-- Function to normalize names for searching (removes accents, converts to lowercase)

CREATE OR REPLACE FUNCTION toponyms.normalize_name(input_text VARCHAR)
RETURNS VARCHAR AS $$
BEGIN
    -- Convert to lowercase
    input_text := lower(input_text);
    
    -- Remove common punctuation
    input_text := regexp_replace(input_text, '[.,\-\'"`]', '', 'g');
    
    -- Normalize spaces
    input_text := regexp_replace(input_text, '\s+', ' ', 'g');
    input_text := trim(input_text);
    
    -- Handle Ukrainian-specific normalizations
    -- і → и for searching (though we keep original)
    input_text := replace(input_text, 'і', 'и');
    input_text := replace(input_text, 'ї', 'и');
    input_text := replace(input_text, 'є', 'е');
    
    RETURN input_text;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

COMMENT ON FUNCTION toponyms.normalize_name IS 'Normalizes names for fuzzy searching across languages';
Question for understanding: This normalization function makes searching easier but loses some information. Can you think of why we store BOTH the original name and the normalized version?
Step 6: Creating Your First Python Scripts
Let's create Python scripts to interact with our database. First, create scripts/utils/config.py:
python# scripts/utils/config.py
"""
Configuration management for the Mariupol Toponyms Database
Loads settings from environment variables and provides defaults
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import logging
from datetime import datetime

# Load environment variables from .env file
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
load_dotenv(env_path)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'mariupol_toponyms'),
    'user': os.getenv('DB_USER', 'mariupol_researcher'),
    'password': os.getenv('DB_PASSWORD', 'change_me_please!')
}

# Project paths
PROJECT_ROOT = project_root
DATA_DIR = PROJECT_ROOT / 'data'
RAW_DATA_DIR = DATA_DIR / 'raw'
PROCESSED_DATA_DIR = DATA_DIR / 'processed'
BACKUP_DIR = DATA_DIR / 'backups'
LOG_DIR = PROJECT_ROOT / 'logs'
SQL_DIR = PROJECT_ROOT / 'sql'

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, BACKUP_DIR, LOG_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Logging configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

def setup_logging(name: str) -> logging.Logger:
    """
    Set up logging for a module
    
    Args:
        name: Logger name (usually __name__ from the calling module)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(console_handler)
    
    # File handler (one log file per day)
    log_file = LOG_DIR / f"{datetime.now().strftime('%Y%m%d')}_toponyms.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)
    
    return logger

# API endpoints
OVERPASS_API_URL = os.getenv('OVERPASS_API_URL', 'https://overpass-api.de/api/interpreter')

# Important dates for the project
INVASION_DATE = '2022-02-24'  # Date of Russian invasion
PRE_WAR_DATE = '2022-02-23'   # Last day before invasion

# Common settings
DEFAULT_LANGUAGE = 'uk'  # Ukrainian
SUPPORTED_LANGUAGES = ['uk', 'ru', 'en']
Now create scripts/utils/database.py:
python# scripts/utils/database.py
"""
Database connection and utility functions
Handles all PostgreSQL/PostGIS interactions
"""

import psycopg
from psycopg.rows import dict_row
import pandas as pd
import geopandas as gpd
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import json

from .config import DB_CONFIG, setup_logging

logger = setup_logging(__name__)

class DatabaseConnection:
    """Manages database connections with proper error handling and logging"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize database connection manager
        
        Args:
            config: Database configuration dictionary. Uses default if None.
        """
        self.config = config or DB_CONFIG
        self.connection_string = self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string from config"""
        return (
            f"host={self.config['host']} "
            f"port={self.config['port']} "
            f"dbname={self.config['database']} "
            f"user={self.config['user']} "
            f"password={self.config['password']}"
        )
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections
        Automatically handles opening/closing and error handling
        
        Usage:
            with db.get_connection() as conn:
                # Do database operations
        """
        conn = None
        try:
            logger.debug("Opening database connection")
            conn = psycopg.connect(self.connection_string)
            yield conn
            conn.commit()
            logger.debug("Transaction committed successfully")
        except Exception as e:
            if conn:
                conn.rollback()
                logger.error(f"Transaction rolled back due to error: {e}")
            raise
        finally:
            if conn:
                conn.close()
                logger.debug("Database connection closed")
    
    def execute_sql_file(self, filepath: str) -> None:
        """
        Execute a SQL file
        
        Args:
            filepath: Path to SQL file
        """
        logger.info(f"Executing SQL file: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql_content)
        
        logger.info(f"Successfully executed: {filepath}")
    
    def test_connection(self) -> bool:
        """Test if database connection works"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version(), PostGIS_version()")
                    pg_version, postgis_version = cur.fetchone()
                    logger.info(f"Connected to PostgreSQL: {pg_version}")
                    logger.info(f"PostGIS version: {postgis_version}")
            return True
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def insert_entity(self, entity_type: str, geometry_wkt: str, 
                     source_authority: str, valid_start: str,
                     properties: Dict[str, Any] = None) -> str:
        """
        Insert a new toponymic entity
        
        Args:
            entity_type: Type code (e.g., 'street', 'district')
            geometry_wkt: Geometry in Well-Known Text format
            source_authority: Who created/declared this entity
            valid_start: When the entity started existing
            properties: Additional properties
            
        Returns:
            UUID of created entity
        """
        sql = """
        INSERT INTO toponyms.entities 
        (entity_type, geometry, centroid, source_authority, valid_start)
        VALUES (
            %(entity_type)s,
            ST_GeomFromText(%(geometry)s, 4326),
            ST_Centroid(ST_GeomFromText(%(geometry)s, 4326)),
            %(source_authority)s,
            %(valid_start)s::timestamptz
        )
        RETURNING entity_id
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, {
                    'entity_type': entity_type,
                    'geometry': geometry_wkt,
                    'source_authority': source_authority,
                    'valid_start': valid_start
                })
                entity_id = cur.fetchone()[0]
                
        logger.info(f"Created entity {entity_id} of type {entity_type}")
        return entity_id

# Create global database instance
db = DatabaseConnection()
Step 7: Testing Our Setup
Let's create a test script to make sure everything works. Create scripts/test_setup.py:
python#!/usr/bin/env python3
# scripts/test_setup.py
"""
Test script to verify our database setup
Run this after starting Docker to ensure everything works
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.utils.database import db
from scripts.utils.config import setup_logging, SQL_DIR

logger = setup_logging(__name__)

def main():
    """Run all setup tests"""
    print("🔍 Testing Mariupol Toponyms Database Setup\n")
    
    # Test 1: Database connection
    print("1. Testing database connection...")
    if not db.test_connection():
        print("❌ Database connection failed!")
        print("   Make sure Docker is running: make up")
        return False
    print("✅ Database connected successfully!\n")
    
    # Test 2: Create extensions
    print("2. Setting up PostgreSQL extensions...")
    try:
        db.execute_sql_file(SQL_DIR / 'setup' / '01_extensions.sql')
        print("✅ Extensions created!\n")
    except Exception as e:
        print(f"❌ Extension setup failed: {e}\n")
        return False
    
    # Test 3: Create schemas
    print("3. Creating database schemas...")
    try:
        db.execute_sql_file(SQL_DIR / 'setup' / '02_schemas.sql')
        print("✅ Schemas created!\n")
    except Exception as e:
        print(f"❌ Schema creation failed: {e}\n")
        return False
    
    # Test 4: Create tables
    print("4. Creating database tables...")
    table_files = [
        '01_entity_types.sql',
        '02_toponymic_entities.sql',
        '03_toponymic_names.sql'
    ]
    
    for table_file in table_files:
        try:
            filepath = SQL_DIR / 'tables' / table_file
            if filepath.exists():
                db.execute_sql_file(filepath)
                print(f"   ✅ Created tables from {table_file}")
            else:
                print(f"   ⚠️  File not found: {table_file}")
        except Exception as e:
            print(f"   ❌ Failed on {table_file}: {e}")
            return False
    
    print("\n🎉 All tests passed! Your database is ready to use.")
    print("\nNext steps:")
    print("1. You can connect to the database with: make psql")
    print("2. Start adding toponymic data!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
Step 8: Making It All Work
Now let's tie everything together. Create requirements.txt:
txt# requirements.txt
# Core database libraries
psycopg[binary]==3.1.19
psycopg-pool==3.2.0

# Geospatial processing
geopandas==0.14.4
shapely==2.0.4
pyproj==3.6.1

# Data processing
pandas==2.2.2
numpy==1.26.4

# Environment and configuration
python-dotenv==1.0.1

# API interactions
requests==2.31.0

# Testing
pytest==8.2.0
pytest-cov==5.0.0

# Utilities
click==8.1.7  # For command-line interfaces
tqdm==4.66.4  # Progress bars
Install the requirements:
bashpip install -r requirements.txt
Running Your First Test
Now let's put it all together:

Start the database:

bashmake up

Wait a moment for PostgreSQL to initialize, then run the test:

bashpython scripts/test_setup.py
You should see output like:
🔍 Testing Mariupol Toponyms Database Setup

1. Testing database connection...
✅ Database connected successfully!

2. Setting up PostgreSQL extensions...
✅ Extensions created!

3. Creating database schemas...
✅ Schemas created!

4. Creating database tables...
   ✅ Created tables from 01_entity_types.sql
   ✅ Created tables from 02_toponymic_entities.sql
   ✅ Created tables from 03_toponymic_names.sql

🎉 All tests passed! Your database is ready to use.
Understanding What We've Built
Let's reflect on what we've created:

A bitemporal database structure - This means we track two types of time:

Valid time: When something was true in the real world
Transaction time: When we recorded it in our database

Why is this important for documenting war crimes?
Multi-lingual support - We can store names in Ukrainian, Russian, and English. This helps when dealing with international investigators and courts.
Geographic capabilities - Using PostGIS, we can store and query the actual shapes and locations of streets, not just their names.
Audit trail - Every change is tracked, creating a legal chain of custody for our evidence.

Next Steps
You now have a working database! In the next phase, we'll:

Import historical street data from OpenStreetMap
Add tools for tracking name changes
Build the scraper for occupation government websites

Checkpoint question: Can you explain in your own words why we need both valid_start/valid_end AND txn_start/txn_end timestamps? Think about a street that was renamed last year, but we only discovered and recorded the change today.
Would you like to proceed with importing your first data, or would you like to explore any part of what we've built in more detail?