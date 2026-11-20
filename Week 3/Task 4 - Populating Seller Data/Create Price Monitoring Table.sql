USE map_project;

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