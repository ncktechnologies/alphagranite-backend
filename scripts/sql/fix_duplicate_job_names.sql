-- One-time cleanup for duplicate job names.
-- Keeps the first row per normalized name and renames the rest.
-- Normalization: lower(trim(name))

BEGIN;

-- Preview duplicates before update
SELECT
    lower(trim(name)) AS normalized_name,
    COUNT(*) AS duplicate_count,
    ARRAY_AGG(id ORDER BY created_at NULLS FIRST, id) AS job_ids
FROM business_jobs
WHERE name IS NOT NULL AND trim(name) <> ''
GROUP BY lower(trim(name))
HAVING COUNT(*) > 1
ORDER BY duplicate_count DESC, normalized_name;

WITH ranked AS (
    SELECT
        id,
        name,
        ROW_NUMBER() OVER (
            PARTITION BY lower(trim(name))
            ORDER BY created_at NULLS FIRST, id
        ) AS rn
    FROM business_jobs
    WHERE name IS NOT NULL AND trim(name) <> ''
),
updated AS (
    UPDATE business_jobs b
    SET
        name = CONCAT(b.name, ' (DUP-', b.id, ')'),
        updated_at = NOW()
    FROM ranked r
    WHERE b.id = r.id
      AND r.rn > 1
    RETURNING b.id, b.name
)
SELECT COUNT(*) AS renamed_rows FROM updated;

COMMIT;
