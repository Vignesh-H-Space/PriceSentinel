USE map_project;

-- 1. Total number of violation incidents detected across all 15 days
SELECT COUNT(*) AS total_violations_count FROM violation;

-- 2. Breakdown by violation type
SELECT 
    Violation_Type, 
    COUNT(*) AS incident_count,
    COUNT(DISTINCT SKU) AS affected_skus,
    COUNT(DISTINCT seller_name) AS violating_sellers
FROM violation 
GROUP BY Violation_Type;