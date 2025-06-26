# scripts/utils/database.py
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