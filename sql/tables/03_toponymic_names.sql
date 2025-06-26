-- 03_toponymic_names.sql
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