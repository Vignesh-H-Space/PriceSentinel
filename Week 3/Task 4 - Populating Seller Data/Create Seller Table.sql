USE map_project;

CREATE TABLE IF NOT EXISTS seller (
    Seller_name VARCHAR(255),
    SKU VARCHAR(100),
    Region VARCHAR(50),
    Advertised_price DECIMAL(12, 4),
    Marketplace VARCHAR(100),
    Screenshot VARCHAR(255),
    Live_link TEXT,
    Last_time_collected DATE,
    INDEX idx_seller_sku (SKU),
    INDEX idx_seller_name (Seller_name),
    INDEX idx_collected_date (Last_time_collected)
);