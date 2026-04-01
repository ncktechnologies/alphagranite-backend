BEGIN;

-- 1. Add the new dependency column.
ALTER TABLE stone_colors
ADD COLUMN IF NOT EXISTS stone_type_id INTEGER;

-- 2. Add the index and FK.
CREATE INDEX IF NOT EXISTS ix_stone_colors_stone_type_id
    ON stone_colors (stone_type_id);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_stone_colors_stone_type_id_stone_types'
          AND table_name = 'stone_colors'
    ) THEN
        ALTER TABLE stone_colors
        ADD CONSTRAINT fk_stone_colors_stone_type_id_stone_types
        FOREIGN KEY (stone_type_id)
        REFERENCES stone_types (id);
    END IF;
END $$;

-- 3. Drop the old global unique-on-name constraint if present.
DO $$
DECLARE existing_constraint text;
BEGIN
    SELECT tc.constraint_name
    INTO existing_constraint
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
    WHERE tc.table_name = 'stone_colors'
      AND tc.constraint_type = 'UNIQUE'
      AND kcu.column_name = 'name'
    LIMIT 1;

    IF existing_constraint IS NOT NULL THEN
        EXECUTE format('ALTER TABLE stone_colors DROP CONSTRAINT %I', existing_constraint);
    END IF;
END $$;

-- 4. Add the new scoped uniqueness.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.table_constraints
        WHERE constraint_name = 'uq_stone_colors_type_name'
          AND table_name = 'stone_colors'
    ) THEN
        ALTER TABLE stone_colors
        ADD CONSTRAINT uq_stone_colors_type_name UNIQUE (stone_type_id, name);
    END IF;
END $$;

COMMIT;


-- ------------------------------------------------------------
-- BACKFILL TEMPLATE
-- ------------------------------------------------------------
-- Use this section after you extract the spreadsheet mapping into a CSV
-- with two columns: stone_type_name, stone_color_name
-- Example CSV rows:
-- CAMBRIA,BRITTANICCA
-- GS,ABSOLUTE BLACK
-- QZ,TAJ MAHAL
--
-- Import example from psql:
-- \copy tmp_stone_color_type_map(stone_type_name, stone_color_name) FROM '/absolute/path/mapping.csv' CSV HEADER;

DROP TABLE IF EXISTS tmp_stone_color_type_map;

CREATE TEMP TABLE tmp_stone_color_type_map (
    stone_type_name VARCHAR(255) NOT NULL,
    stone_color_name VARCHAR(255) NOT NULL
);

-- Populate tmp_stone_color_type_map before running the update below.

-- 5. Optional preview: see which mappings will resolve cleanly.
SELECT
    m.stone_type_name,
    m.stone_color_name,
    st.id AS resolved_stone_type_id,
    sc.id AS resolved_stone_color_id,
    sc.stone_type_id AS current_stone_type_id
FROM tmp_stone_color_type_map m
LEFT JOIN stone_types st
    ON UPPER(TRIM(st.name)) = UPPER(TRIM(m.stone_type_name))
LEFT JOIN stone_colors sc
    ON UPPER(TRIM(sc.name)) = UPPER(TRIM(m.stone_color_name))
ORDER BY m.stone_type_name, m.stone_color_name;

-- 6. Backfill stone_colors.stone_type_id from the mapping table.
UPDATE stone_colors sc
SET stone_type_id = st.id
FROM tmp_stone_color_type_map m
JOIN stone_types st
    ON UPPER(TRIM(st.name)) = UPPER(TRIM(m.stone_type_name))
WHERE UPPER(TRIM(sc.name)) = UPPER(TRIM(m.stone_color_name))
  AND (sc.stone_type_id IS NULL OR sc.stone_type_id <> st.id);

-- 7. Validation queries.

-- Unmapped stone colors after backfill.
SELECT id, name
FROM stone_colors
WHERE stone_type_id IS NULL
ORDER BY name;

-- Duplicate color names within the same type after backfill.
SELECT stone_type_id, name, COUNT(*) AS duplicate_count
FROM stone_colors
GROUP BY stone_type_id, name
HAVING COUNT(*) > 1
ORDER BY stone_type_id, name;

-- FAB rows whose stone_color no longer matches the selected stone_type.
SELECT f.id, f.stone_type_id, f.stone_color_id, sc.stone_type_id AS color_stone_type_id
FROM fabs f
JOIN stone_colors sc
    ON sc.id = f.stone_color_id
WHERE sc.stone_type_id IS NOT NULL
  AND sc.stone_type_id <> f.stone_type_id
ORDER BY f.id;


-- ------------------------------------------------------------
-- FINAL HARDENING
-- ------------------------------------------------------------
-- Run only after the unmapped/invalid validation queries above return no rows.

-- ALTER TABLE stone_colors
-- ALTER COLUMN stone_type_id SET NOT NULL;
