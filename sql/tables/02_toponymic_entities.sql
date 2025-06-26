-- 02_toponymic_entities.sql
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