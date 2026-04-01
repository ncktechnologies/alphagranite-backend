BEGIN;

-- ============================================================
-- PURPOSE
-- ============================================================
-- Replace the current stone type / stone color catalog using:
--   Sheet1 -> stone types
--   Sheet2 -> stone colors with their related stone type
--
-- Expected CSV exports:
--   1. sheet1_stone_types.csv
--      Required columns: stone_type_name, description
--
--   2. sheet2_stone_colors.csv
--      Required columns: stone_type_name, stone_color_name, color_code, description
--
-- Adjust the \copy paths below before running in psql.
--
-- This script does NOT blindly truncate referenced tables.
-- It imports the new catalog, relinks existing FAB rows by name, then shows
-- any obsolete rows that are still referenced before deleting only safe rows.


-- ============================================================
-- 0. STAGING TABLES
-- ============================================================
DROP TABLE IF EXISTS tmp_sheet1_stone_types;
DROP TABLE IF EXISTS tmp_sheet2_stone_colors;

CREATE TEMP TABLE tmp_sheet1_stone_types (
    stone_type_name VARCHAR(255) NOT NULL,
    description VARCHAR(255) NULL
);

CREATE TEMP TABLE tmp_sheet2_stone_colors (
    stone_type_name VARCHAR(255) NOT NULL,
    stone_color_name VARCHAR(255) NOT NULL,
    color_code VARCHAR(50) NULL,
    description TEXT NULL
);

-- Example imports from psql:
-- \copy tmp_sheet1_stone_types(stone_type_name, description) FROM '/absolute/path/sheet1_stone_types.csv' CSV HEADER;
-- \copy tmp_sheet2_stone_colors(stone_type_name, stone_color_name, color_code, description) FROM '/absolute/path/sheet2_stone_colors.csv' CSV HEADER;


-- ============================================================
-- 1. NORMALIZE AND VALIDATE THE IMPORT DATA
-- ============================================================
DROP TABLE IF EXISTS tmp_import_stone_types;
DROP TABLE IF EXISTS tmp_import_stone_colors;

CREATE TEMP TABLE tmp_import_stone_types AS
SELECT DISTINCT
    UPPER(TRIM(stone_type_name)) AS stone_type_name,
    NULLIF(TRIM(description), '') AS description
FROM tmp_sheet1_stone_types
WHERE NULLIF(TRIM(stone_type_name), '') IS NOT NULL;

CREATE TEMP TABLE tmp_import_stone_colors AS
SELECT DISTINCT
    UPPER(TRIM(stone_type_name)) AS stone_type_name,
    TRIM(stone_color_name) AS stone_color_name,
    NULLIF(TRIM(color_code), '') AS color_code,
    NULLIF(TRIM(description), '') AS description
FROM tmp_sheet2_stone_colors
WHERE NULLIF(TRIM(stone_type_name), '') IS NOT NULL
  AND NULLIF(TRIM(stone_color_name), '') IS NOT NULL;

-- Validation 1: duplicate type names in Sheet1 after normalization.
SELECT stone_type_name, COUNT(*) AS duplicate_count
FROM (
    SELECT UPPER(TRIM(stone_type_name)) AS stone_type_name
    FROM tmp_sheet1_stone_types
    WHERE NULLIF(TRIM(stone_type_name), '') IS NOT NULL
) src
GROUP BY stone_type_name
HAVING COUNT(*) > 1
ORDER BY stone_type_name;

-- Validation 2: duplicate color names within the same type in Sheet2.
SELECT stone_type_name, stone_color_name, COUNT(*) AS duplicate_count
FROM tmp_import_stone_colors
GROUP BY stone_type_name, stone_color_name
HAVING COUNT(*) > 1
ORDER BY stone_type_name, stone_color_name;

-- Validation 3: Sheet2 rows whose type does not exist in Sheet1.
SELECT c.*
FROM tmp_import_stone_colors c
LEFT JOIN tmp_import_stone_types t
    ON t.stone_type_name = c.stone_type_name
WHERE t.stone_type_name IS NULL
ORDER BY c.stone_type_name, c.stone_color_name;


-- ============================================================
-- 2. SNAPSHOT CURRENT FAB REFERENCES BY NAME
-- ============================================================
DROP TABLE IF EXISTS tmp_existing_fab_stone_refs;

CREATE TEMP TABLE tmp_existing_fab_stone_refs AS
SELECT
    f.id AS fab_id,
    f.stone_type_id AS old_stone_type_id,
    f.stone_color_id AS old_stone_color_id,
    UPPER(TRIM(st.name)) AS old_stone_type_name,
    TRIM(sc.name) AS old_stone_color_name
FROM fabs f
LEFT JOIN stone_types st
    ON st.id = f.stone_type_id
LEFT JOIN stone_colors sc
    ON sc.id = f.stone_color_id;


-- ============================================================
-- 3. UPSERT STONE TYPES FROM SHEET1
-- ============================================================
INSERT INTO stone_types (
    name,
    description,
    status_id,
    created_at,
    created_by,
    updated_at,
    updated_by
)
SELECT
    t.stone_type_name,
    COALESCE(t.description, t.stone_type_name),
    1,
    NOW(),
    1,
    NOW(),
    1
FROM tmp_import_stone_types t
WHERE NOT EXISTS (
    SELECT 1
    FROM stone_types st
    WHERE UPPER(TRIM(st.name)) = t.stone_type_name
);

UPDATE stone_types st
SET
    description = COALESCE(t.description, st.description),
    status_id = 1,
    updated_at = NOW(),
    updated_by = 1
FROM tmp_import_stone_types t
WHERE UPPER(TRIM(st.name)) = t.stone_type_name;


-- ============================================================
-- 4. UPSERT STONE COLORS FROM SHEET2 WITH TYPE RELATIONSHIP
-- ============================================================
INSERT INTO stone_colors (
    stone_type_id,
    name,
    color_code,
    description,
    status_id,
    created_at,
    created_by,
    updated_at,
    updated_by
)
SELECT
    st.id,
    c.stone_color_name,
    c.color_code,
    c.description,
    1,
    NOW(),
    1,
    NOW(),
    1
FROM tmp_import_stone_colors c
JOIN stone_types st
    ON UPPER(TRIM(st.name)) = c.stone_type_name
WHERE NOT EXISTS (
    SELECT 1
    FROM stone_colors sc
    WHERE sc.stone_type_id = st.id
      AND UPPER(TRIM(sc.name)) = UPPER(TRIM(c.stone_color_name))
);

UPDATE stone_colors sc
SET
    stone_type_id = st.id,
    color_code = COALESCE(c.color_code, sc.color_code),
    description = COALESCE(c.description, sc.description),
    status_id = 1,
    updated_at = NOW(),
    updated_by = 1
FROM tmp_import_stone_colors c
JOIN stone_types st
    ON UPPER(TRIM(st.name)) = c.stone_type_name
WHERE UPPER(TRIM(sc.name)) = UPPER(TRIM(c.stone_color_name));


-- ============================================================
-- 5. RELINK FABS TO THE IMPORTED TYPE/COLOR STRUCTURE
-- ============================================================
UPDATE fabs f
SET stone_type_id = st.id
FROM tmp_existing_fab_stone_refs refs
JOIN stone_types st
    ON UPPER(TRIM(st.name)) = refs.old_stone_type_name
WHERE f.id = refs.fab_id
  AND refs.old_stone_type_name IS NOT NULL;

UPDATE fabs f
SET stone_color_id = sc.id
FROM tmp_existing_fab_stone_refs refs
JOIN stone_types st
    ON UPPER(TRIM(st.name)) = refs.old_stone_type_name
JOIN stone_colors sc
    ON sc.stone_type_id = st.id
   AND UPPER(TRIM(sc.name)) = UPPER(TRIM(refs.old_stone_color_name))
WHERE f.id = refs.fab_id
  AND refs.old_stone_color_name IS NOT NULL;


-- ============================================================
-- 6. REPORT OBSOLETE ROWS BEFORE DELETE
-- ============================================================
-- Stone colors still in DB but not present in Sheet2.
SELECT
    sc.id,
    st.name AS stone_type_name,
    sc.name AS stone_color_name,
    COUNT(f.id) AS fab_reference_count
FROM stone_colors sc
LEFT JOIN stone_types st
    ON st.id = sc.stone_type_id
LEFT JOIN fabs f
    ON f.stone_color_id = sc.id
LEFT JOIN tmp_import_stone_colors ic
    ON ic.stone_type_name = UPPER(TRIM(st.name))
   AND UPPER(TRIM(ic.stone_color_name)) = UPPER(TRIM(sc.name))
WHERE ic.stone_color_name IS NULL
GROUP BY sc.id, st.name, sc.name
ORDER BY st.name, sc.name;

-- Stone types still in DB but not present in Sheet1.
SELECT
    st.id,
    st.name AS stone_type_name,
    COUNT(f.id) AS fab_reference_count
FROM stone_types st
LEFT JOIN fabs f
    ON f.stone_type_id = st.id
LEFT JOIN tmp_import_stone_types it
    ON it.stone_type_name = UPPER(TRIM(st.name))
WHERE it.stone_type_name IS NULL
GROUP BY st.id, st.name
ORDER BY st.name;


-- ============================================================
-- 7. DELETE SAFE OBSOLETE ROWS
-- ============================================================
-- Delete colors not in Sheet2 only when not referenced by any FAB.
DELETE FROM stone_colors sc
WHERE NOT EXISTS (
    SELECT 1
    FROM stone_types st
    JOIN tmp_import_stone_colors ic
      ON ic.stone_type_name = UPPER(TRIM(st.name))
     AND ic.stone_color_name IS NOT NULL
    WHERE st.id = sc.stone_type_id
      AND UPPER(TRIM(ic.stone_color_name)) = UPPER(TRIM(sc.name))
)
AND NOT EXISTS (
    SELECT 1
    FROM fabs f
    WHERE f.stone_color_id = sc.id
);

-- Delete types not in Sheet1 only when not referenced by any FAB or stone color.
DELETE FROM stone_types st
WHERE NOT EXISTS (
    SELECT 1
    FROM tmp_import_stone_types it
    WHERE it.stone_type_name = UPPER(TRIM(st.name))
)
AND NOT EXISTS (
    SELECT 1
    FROM fabs f
    WHERE f.stone_type_id = st.id
)
AND NOT EXISTS (
    SELECT 1
    FROM stone_colors sc
    WHERE sc.stone_type_id = st.id
);


-- ============================================================
-- 8. FINAL VALIDATION
-- ============================================================
-- FAB rows still pointing to mismatched type/color pairs.
SELECT f.id, f.stone_type_id, f.stone_color_id, sc.stone_type_id AS color_stone_type_id
FROM fabs f
JOIN stone_colors sc
    ON sc.id = f.stone_color_id
WHERE sc.stone_type_id IS NOT NULL
  AND sc.stone_type_id <> f.stone_type_id
ORDER BY f.id;

-- Imported stone colors left without a stone type.
SELECT id, name
FROM stone_colors
WHERE stone_type_id IS NULL
ORDER BY name;

COMMIT;
