USE map_project;

-- =============================================================================
-- STEP 1: CREATE THE PRICE MONITORING TABLE
-- =============================================================================
DROP TABLE IF EXISTS price_monitoring;

CREATE TABLE price_monitoring (
    SKU VARCHAR(100),
    Violation_date DATE,
    PL VARCHAR(100),
    Category VARCHAR(100),
    Sub_category VARCHAR(100),
    Region VARCHAR(50),
    Marketplace VARCHAR(100),
    seller_name VARCHAR(255),
    homologated_name VARCHAR(255),
    MAP_Price DECIMAL(12, 4),
    LPP DECIMAL(12, 4),
    Advertised_price DECIMAL(12, 4),
    Season VARCHAR(50),
    Promotional_price DECIMAL(12, 4),
    INDEX idx_pm_sku (SKU),
    INDEX idx_pm_seller (seller_name),
    INDEX idx_pm_date (Violation_date)
);

-- =============================================================================
-- STEP 2: POPULATE PRICE MONITORING TABLE VIA HIGH-PERFORMANCE SQL JOIN
-- =============================================================================
-- We join the raw market observations (seller) with:
-- 1. category_mapping (to get PL, Category, Sub_category)
-- 2. seller_mapping   (to get standardized Homologated_Name)
-- 3. price_list       (to get MAP and LPP thresholds)
-- 4. promotion        (to factor in Q4 seasonal promotional discounts)
-- =============================================================================

INSERT INTO price_monitoring (
    SKU,
    Violation_date,
    PL,
    Category,
    Sub_category,
    Region,
    Marketplace,
    seller_name,
    homologated_name,
    MAP_Price,
    LPP,
    Advertised_price,
    Season,
    Promotional_price
)
SELECT 
    s.SKU,
    s.Last_time_collected AS Violation_date,
    cm.PL,
    cm.Category,
    cm.sub_category,
    s.Region,
    s.Marketplace,
    s.Seller_name,
    COALESCE(sm.Homologated_Name, s.Seller_name) AS homologated_name,
    p.MAP AS MAP_Price,
    p.LPP AS LPP,
    s.Advertised_price,
    pr.Season,
    -- Calculate Promotional_price based on seasonal promo discount:
    CASE 
        WHEN pr.Promotion = '15% off' THEN ROUND(p.MAP * 0.85, 4)
        WHEN pr.Promotion = '20% off ink' THEN ROUND(p.MAP * 0.80, 4)
        -- Converted $10 USD to INR equivalent (~83 INR/USD) = 830.00 off MAP
        WHEN pr.Promotion = '$10 off laser jet' THEN ROUND(p.MAP - 830.00, 4)
        ELSE NULL
    END AS Promotional_price
FROM seller s
-- Join category mapping to pull product hierarchy
JOIN category_mapping cm 
    ON s.SKU = cm.SKU
-- Join seller mapping to resolve raw seller names to clean brand names
LEFT JOIN seller_mapping sm 
    ON s.Seller_name = sm.Seller_Name
-- Join price list to pull official MAP and LPP thresholds
JOIN price_list p 
    ON s.SKU = p.SKU
-- Left join promotions for SKUs that have active seasonal offers
LEFT JOIN promotion pr 
    ON s.SKU = pr.SKU;

-- =============================================================================
-- STEP 3: VERIFY INGESTION RESULTS
-- =============================================================================
SELECT COUNT(*) AS total_monitored_records FROM price_monitoring;

-- Inspect 10 sample populated rows
SELECT 
    SKU, 
    Violation_date, 
    Category, 
    Sub_category, 
    seller_name, 
    homologated_name, 
    MAP_Price, 
    LPP, 
    Advertised_price, 
    Season, 
    Promotional_price
FROM price_monitoring 
LIMIT 10;
