-- 01_name_normalization.sql
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